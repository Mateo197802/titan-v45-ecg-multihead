"""Verify LUDB and seal published-model predictions before joining diagnoses."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

from compare_reviewer_baseline import digest
from freeze_reviewer_selective_policy import confidence

PROFILES = ("P6", "P8", "P4")
PREFIX = "lobachevsky-university-electrocardiography-database-1.0.1/"
ARCHIVE_SHA256 = "d03192c7361ab5deeaba3f0d46e274b9ecb0b74c9caf8964151e20f1b5a7df06"
PROTOCOL_SHA256 = "d4f8157e762ba411781c5a04f0b0a7a51a2ff7cd764ffe0bc2bfae1681d6ef6f"


def write_new(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def source_manifest(stream):
    result = {}
    for line in stream.splitlines():
        check, name = line.split(maxsplit=1)
        name = name.removeprefix("*").removeprefix("./")
        if not re.fullmatch("[0-9a-f]{64}", check) or name in result:
            raise ValueError("invalid or duplicate publisher checksum")
        result[name] = check
    return result


def inventory(archive, output, expected):
    with zipfile.ZipFile(archive) as zipped:
        names = zipped.namelist()
        if len(set(names)) != len(names):
            raise ValueError("duplicate archive members")
        manifest = zipped.read(PREFIX + "SHA256SUMS.txt")
        seals = source_manifest(manifest.decode("utf-8"))
        records = zipped.read(PREFIX + "RECORDS")
        entries = records.decode("ascii").splitlines()
        if (len(entries) != expected or len(set(entries)) != expected
                or any(not re.fullmatch(r"data/[1-9][0-9]{0,2}", x) for x in entries)):
            raise ValueError("unexpected publisher enrollment")
        if sha256(records) != seals["RECORDS"]:
            raise ValueError("publisher RECORDS checksum mismatch")
        raw = output / "private-waveforms"
        raw.mkdir(mode=0o700)
        (raw / "data").mkdir(mode=0o700)
        for entry in entries:
            for suffix in (".hea", ".dat"):
                name = entry + suffix
                payload = zipped.read(PREFIX + name)
                if sha256(payload) != seals[name]:
                    raise ValueError("publisher waveform checksum mismatch")
                (raw / name).write_bytes(payload)
    return raw, entries, {
        "publisher_manifest_sha256": sha256(manifest), "enrollment_sha256": sha256(records),
        "publisher_verified_waveform_files": 2 * len(entries),
    }


def route(profiles, thresholds, policy):
    if any(profiles[p]["status"] != "scored" for p in ("P8", "P4")):
        return {"state": "technical_unscored", "signed_margin": None, "emitted": None}
    margin = {p: confidence(profiles[p]["scores"], thresholds[p]) - policy["cutoffs"][p]
              for p in ("P8", "P4")}
    decision = min(margin.values())
    return {
        "state": "accepted" if decision >= 0 else "abstained", "signed_margin": decision,
        "profile_signed_margins": margin,
        "emitted": {p: profiles[p]["labels"] for p in margin} if decision >= 0 else None,
    }


class TensorAudit:
    """Check actual module inputs against the prepared batch, never export tensors."""

    def __init__(self, torch):
        self.torch = torch
        self.expected = None
        self.counts = defaultdict(Counter)
        self.handles = []

    def start(self, samples):
        import numpy as np

        self.expected = tuple(self.torch.as_tensor(np.stack([s[i] for s in samples]))
                              for i in (1, 2))
        if self.expected[0].shape != (len(samples), 12) or self.expected[1].shape != (len(samples), 10):
            raise ValueError("unexpected prepared lead-mask or morphology contract")
        if not self.torch.isfinite(self.expected[1]).all():
            raise ValueError("nonfinite prepared morphology")

    def attach_backbone(self, label, module):
        def audit(_, args, kwargs):
            lead, morphology = self.expected
            x = args[0]
            if (tuple(x.shape[1:]) != (12, 1250)
                    or not self.torch.equal(kwargs["lead_mask"].detach().cpu(), lead)
                    or not self.torch.equal(kwargs["morphology_features"].detach().cpu(), morphology)):
                raise ValueError("backbone did not receive the prepared inputs")
            self.counts[label].update(batches=1, windows=int(x.shape[0]))

        self.handles.append(module.register_forward_pre_hook(audit, with_kwargs=True))

    def attach_head(self, label, module, width, *, includes_morphology=True):
        def audit(_, args):
            x = args[0]
            _, morphology = self.expected
            if (tuple(x.shape) != (len(morphology), width)
                    or (includes_morphology
                        and not self.torch.equal(x[:, 640:650].detach().cpu(), morphology.float()))):
                raise ValueError("head did not receive the declared feature layout")
            self.counts[label].update(batches=1, windows=int(x.shape[0]))

        self.handles.append(module.register_forward_pre_hook(audit))

    def remove(self):
        for handle in self.handles:
            handle.remove()


def score(args, protocol, policy, raw, entries):
    import numpy as np
    import torch
    import wfdb

    from titan_v45.data.reconstructed import prepare_p4_record, prepare_rhythm_record
    from titan_v45.models import frozen_pathology as fp
    from titan_v45.models import frozen_rhythm as fr

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA allocation required")
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False

    spec = importlib.util.spec_from_file_location(
        "stage_a_feature_contract", args.repo / "scripts/specialist_experiments/extract_features.py")
    if spec is None or spec.loader is None:
        raise ValueError("missing pinned feature contract")
    stage = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(stage)
    morphology = stage._safe_morphology(args.repo)
    names = {fr.BACKBONE, *fr.HEADS.values(), fp.BACKBONE, fp.SPECIALIST}
    assets, hashes = fp.verified_assets(args.repo, args.assets, names)
    contract = json.loads((args.repo / "outputs/models/heads/global_head_contracts.json").read_bytes())
    rhythm = fr.FrozenRhythm(assets, contract, fr.load_recorded_event_extractor(
        args.repo / "docs/provenance/recovered-original-sources-20261029.zip"), "cuda")
    pathology = fp.FrozenPathology(assets, contract, "cuda")
    thresholds = stage._baseline_thresholds(args.repo, pathology)

    audit = TensorAudit(torch)
    audit.attach_backbone("V3F_backbone", rhythm.model)
    audit.attach_backbone("V3AG_backbone", pathology.model)
    for name, model in (("V3F", rhythm.model), ("V3AG", pathology.model)):
        audit.attach_head(name + "_global_rhythm", model.head_rhythm, 650)
        audit.attach_head(name + "_global_pathology", model.head_pathology, 640, includes_morphology=False)
    for name, head in rhythm.heads.items():
        audit.attach_head(name, head, 681)
    audit.attach_head("P4", pathology.head, 670)

    profiles_count, routes, failures = {p: Counter() for p in PROFILES}, Counter(), Counter()
    pending = []

    def flush(stream):
        all_windows = [w for _, _, _, windows, _ in pending if windows for w in windows]
        if all_windows:
            audit.start(all_windows)
            logits, aux = rhythm(all_windows)
        p4_batch = [(key, p4) for key, _, _, _, p4 in pending if p4 is not None]
        p4_scores = {}
        if p4_batch:
            audit.start([x for _, x in p4_batch])
            p4_scores = dict(zip((k for k, _ in p4_batch),
                                 pathology([x for _, x in p4_batch]), strict=True))
        offset = 0
        for key, fingerprint, waveform_hash, windows, p4 in pending:
            profiles = {p: {"status": "technical_unscored"} for p in PROFILES}
            if windows:
                span = slice(offset, offset + len(windows))
                aux_scores = dict(zip((f"backbone_{i}" for i in range(6)),
                                      aux[span].mean(axis=0, dtype=np.float64).tolist(), strict=True))
                for p in ("P6", "P8"):
                    profiles[p] = {"status": "scored", "auxiliary_scores": aux_scores,
                                   **fr.aggregate_rhythm(logits[p][span], thresholds[p], profile=p)}
                offset += len(windows)
            if p4 is not None:
                values, auxiliary = p4_scores[key]
                profiles["P4"] = {"status": "scored", "scores": values, "auxiliary_scores": auxiliary,
                                  "labels": [k for k, p in values.items() if p >= thresholds["P4"][k]]}
            outcome = route(profiles, thresholds, policy)
            for p, item in profiles.items():
                profiles_count[p][item["status"]] += 1
            routes[outcome["state"]] += 1
            row = {"key": key, "physical_waveform_digest": fingerprint,
                   "raw_waveform_digest": waveform_hash, "profiles": profiles, "route": outcome}
            stream.write(json.dumps(row, allow_nan=False, separators=(",", ":")) + "\n")
        pending.clear()

    ledger = args.output / "private-scored-and-routed.jsonl"
    with ledger.open("x", encoding="utf-8") as stream:
        for key in entries:
            path = raw / key
            fingerprint, windows, p4 = None, None, None
            waveform_hash = digest(path.with_suffix(".dat"))
            try:
                record = wfdb.rdrecord(str(path))
                rule = protocol["source"]
                if (record.fs != rule["sample_rate_hz"] or record.sig_len != rule["samples"]
                        or tuple(x.lower() for x in record.sig_name) != tuple(rule["leads"])
                        or any(unit.lower() != "mv" for unit in record.units)
                        or not np.isfinite(record.p_signal).all()):
                    raise ValueError("source signal shape, lead order, units or finiteness failed")
                fingerprint = sha256(np.asarray(record.p_signal.T, dtype="<f8", order="C").tobytes())
            except (ValueError, OSError, IndexError) as exc:
                failures[f"source:{type(exc).__name__}"] += 1
            if fingerprint is not None:
                try:
                    windows = prepare_rhythm_record(path, morphology, wfdb_module=wfdb)
                except (ValueError, OSError, IndexError) as exc:
                    failures[f"rhythm:{type(exc).__name__}"] += 1
                try:
                    p4 = prepare_p4_record(path, morphology, wfdb_module=wfdb)
                except (ValueError, OSError, IndexError) as exc:
                    failures[f"P4:{type(exc).__name__}"] += 1
            pending.append((key, fingerprint, waveform_hash, windows, p4))
            if len(pending) == 16:
                flush(stream)
        flush(stream)
    audit.remove()
    if not routes.get("accepted", 0) + routes.get("abstained", 0):
        raise ValueError("no eligible ECG was routed")
    if sum(routes.values()) != len(entries) or any(sum(c.values()) != len(entries) for c in profiles_count.values()):
        raise ValueError("scoring or route denominator does not reconcile")
    return {
        "eligible_ecgs": len(entries), "scored_by_profile": profiles_count, "routes": routes,
        "technical_failure_types": failures, "reference_values_used": False, "route_reference_values_used": False,
        "thresholds": thresholds, "model_hashes": hashes, "private_score_route_ledger_sha256": digest(ledger),
        "torch": torch.__version__, "device": torch.cuda.get_device_name(),
        "architecture": {"rhythm_hidden_width_metadata": rhythm.widths,
                         "P4_hidden_width_from_loaded_tensor": int(pathology.head.heads[0][1].weight.shape[0]),
                         "specialist_input_widths": {"P6": 681, "P8": 681, "P4": 670},
                         "global_head_input_widths": {"rhythm": 650, "pathology": 640},
                         "forward_input_checks": audit.counts,
                         "zero_based_morphology_slice_start": 640, "morphology_dim": 10,
                         "strict_state_dict_load": True},
        "preprocessor_sha256": digest(args.repo / "src/titan_v45/data/reconstructed.py"),
        "morphology_source_sha256": digest(
            args.repo / "scripts/cedia/recovery_candidates/morphology_features_v4.py"),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("archive", "output", "repo", "assets", "protocol", "policy"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    if digest(args.protocol) != PROTOCOL_SHA256 or digest(args.archive) != ARCHIVE_SHA256:
        raise ValueError("closure protocol or publisher archive changed")
    protocol = json.loads(args.protocol.read_bytes())
    if digest(args.policy) != protocol["route"]["policy_sha256"]:
        raise ValueError("not the frozen November routing policy")
    policy = json.loads(args.policy.read_bytes())
    if policy["cutoffs"] != protocol["route"]["cutoffs"] or policy["reference_used_for_routing"] is not False:
        raise ValueError("frozen routing policy contract differs")
    args.output.mkdir(mode=0o700)
    raw, entries, provenance = inventory(args.archive, args.output, protocol["source"]["records"])
    result = score(args, protocol, policy, raw, entries)
    write_new(args.output / "scoring-receipt.json", {
        "schema": "TITAN_V45_CLOSURE_LUDB_SCORE_V1", "job": os.environ.get("SLURM_JOB_ID"),
        "source_archive_sha256": ARCHIVE_SHA256, "protocol_sha256": PROTOCOL_SHA256,
        "policy_sha256": protocol["route"]["policy_sha256"], "source_commit": protocol["native_scorer_commit"],
        "no_individual_records_exported": True, **provenance, **result,
    })


if __name__ == "__main__":
    main()
