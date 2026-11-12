"""Export class coverage from the two hash-verified released backbone payloads."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import torch

ASSETS = {"V3F": "backbone-v3f-original.pt", "V3AG": "backbone-v3ag-pathology.pt"}
ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_SHA = "2935deb7eaaa9ba6b040610cf810ddc6e1c82a212b260170ec9b6b02e3727d07"
V3AG_LOG = "PRIMARY_EXCERPTS/job17285_epochs_and_scheduler.txt"
V3AG_LOG_SHA = "b71e48e5483f753af26e1fa4ebb416e579384e90290c2a956b682dd2bf17e88b"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for data in iter(lambda: f.read(1024*1024), b""):
            digest.update(data)
    return digest.hexdigest()


def read_checkpoint(path, asset):
    if path.stat().st_size != asset["bytes"] or sha256(path) != asset["sha256"]:
        raise ValueError(f"checkpoint size or digest mismatch for {asset['name']}")
    return torch.load(path, map_location="cpu", weights_only=True)


def panel_support(panel):
    counts = {k: panel[k] for k in ("tp", "tn", "fp", "fn")}
    if any(type(v) is not int or v < 0 for v in counts.values()):
        raise ValueError("expected nonnegative integer confusion counts")
    return {"validation_positive": counts["tp"] + counts["fn"],
            "validation_negative": counts["tn"] + counts["fp"],
            "validation_observations": sum(counts.values())}


def validation_coverage(checkpoint, head, classes):
    name, saved = {"rhythm": ("primary8_classes", "rhythm"),
                   "pathology": ("pathology4_classes", "pathology4")}[head]
    target = checkpoint[name]
    panels = checkpoint["reports"]["final_validation"][saved]["panels"]
    if len(target) != len(set(target)) or not set(target) <= set(classes) or set(panels) != set(target):
        raise ValueError("embedded validation panels do not match declared subset")
    return {"declared_finetune_classes": list(target), "embedded_validation_panels": {
        c: panel_support(panels[c]) for c in target},
        "no_embedded_validation_panel": [c for c in classes if c not in panels]}


def tensor_rows(before, after, head, classes):
    states = [x["state_dict"] for x in (before, after)]
    prefix = f"head_{head}."
    name = {k for k in states[0] if k.startswith(prefix)}
    if name != {k for k in states[1] if k.startswith(prefix)}:
        raise ValueError("incompatible head key sets")
    for k in name:
        a, b = (x[k] for x in states)
        if a.shape != b.shape or a.dtype != b.dtype or any(not t.isfinite().all() for t in (a, b)):
            raise ValueError("incompatible or nonfinite head tensor")
    w, b = (prefix + f"4.{suffix}" for suffix in ("weight", "bias"))
    aw, bw = (x[w] for x in states)
    ab, bb = (x[b] for x in states)
    if aw.ndim != 2 or ab.ndim != 1 or aw.shape[0] != len(classes) or ab.shape[0] != len(classes):
        raise ValueError("output rows do not match the release output contract")
    return {
        "final_weight_elements_per_class": aw.shape[1],
        "final_row_numeric_differences": {c: {
            "weight_elements_different": int((aw[i] != bw[i]).sum().item()),
            "bias_different": bool(ab[i] != bb[i]),
        } for i, c in enumerate(classes)},
        "shared_head_tensor_equal": {k: bool(torch.equal(states[0][k], states[1][k]))
                                     for k in sorted(name-{w, b})},
    }


def v3ag_epoch_binding(archive, checkpoint):
    if sha256(archive) != ARCHIVE_SHA:
        raise ValueError("historical source archive checksum differs")
    with ZipFile(archive) as package:
        raw = package.read(V3AG_LOG)
    if hashlib.sha256(raw).hexdigest() != V3AG_LOG_SHA:
        raise ValueError("job 17285 excerpt checksum differs")
    lines = raw.decode("utf-8").splitlines()
    epochs = [json.loads(line)["v3f_partial_finetune"] for line in lines
              if line.startswith('{"v3f_partial_finetune":')]
    if len(epochs) != 10 or epochs != checkpoint["reports"]["log"]:
        raise ValueError("job 17285 epochs do not match the checkpoint report")
    statuses = [line.split("|")[2:4] for line in lines if line.startswith("17285|")]
    if statuses != [["FAILED", "1:0"]]:
        raise ValueError("job 17285 scheduler evidence differs")
    return {"scheduler_job": 17285, "parent_job_status": statuses[0][0], "parent_job_exit_code": statuses[0][1],
            "matching_embedded_epoch_rows": len(epochs), "source_archive_sha256": ARCHIVE_SHA,
            "source_member": V3AG_LOG, "source_member_sha256": V3AG_LOG_SHA}


def build(repo, paths, source_archive):
    manifest_path = repo / "release-manifest.json"
    contract_path = repo / "outputs/models/heads/global_head_contracts.json"
    assets = {a["name"]: a for a in json.loads(manifest_path.read_bytes())["assets"]}
    contract = json.loads(contract_path.read_bytes())["heads"]
    models = {k: read_checkpoint(paths[k], assets[n]) for k, n in ASSETS.items()}
    dims = {head: contract[head]["classes"] for head in ("rhythm", "pathology")}
    for x in models.values():
        if (x["num_rhythm"] != len(dims["rhythm"]) or x["num_pathology"] != len(dims["pathology"])
                or x["morphology_dim"] != 10):
            raise ValueError("checkpoint dimensions differ from the release")
    return {
        "schema": "TITAN_V45_RELEASE_BACKBONE_HEAD_SUPPORT_V1",
        "scope": "read-only checkpoint byte and embedded internal report audit; no inference or training",
        "release_manifest_sha256": sha256(manifest_path),
        "global_head_contract_sha256": sha256(contract_path),
        "checkpoint_assets": {k: {field: assets[n][field] for field in ("name", "sha256", "bytes")}
                              for k, n in ASSETS.items()},
        "declared_parent_path_strings_equal": models["V3F"]["parent_checkpoint"] == models["V3AG"]["parent_checkpoint"],
        "parent_bytes_verified": False,
        "embedded_report_epoch_count": {k: len(x["reports"]["log"]) for k, x in models.items()},
        "V3AG_historical_log_binding": v3ag_epoch_binding(source_archive, models["V3AG"]),
        "heads": {head: {
            "release_output_order": classes,
            "coverage_by_asset": {k: validation_coverage(x, head, classes) for k, x in models.items()},
            "V3F_vs_V3AG": tensor_rows(models["V3F"], models["V3AG"], head, classes),
        } for head, classes in dims.items()},
        "limitations": [
            "Embedded confusion counts describe internal development observations, not distinct patients or new test outcomes.",
            "Tensor row differences do not authenticate direct supervision, gradient history or the consumed training manifest.",
            "Identical final rows do not imply identical outputs: the shared feature path can differ.",
            "A matching parent path is not a matching parent digest.",
        ],
        "contains_checkpoint_tensors_or_record_identifiers": False,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for n in ("v3f", "v3ag", "source-archive", "output"):
        p.add_argument(f"--{n}", type=Path, required=True)
    a = p.parse_args()
    report = build(ROOT, {"V3F": a.v3f, "V3AG": a.v3ag}, a.source_archive)
    with a.output.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, indent=2, allow_nan=False)
        f.write("\n")


if __name__ == "__main__":
    main()
