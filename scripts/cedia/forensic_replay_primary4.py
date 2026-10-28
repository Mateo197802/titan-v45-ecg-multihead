"""Forensic replay using declared public contracts and a recovered morphology candidate.

No tuning. Agreement with archived scores is an outcome, not a selection criterion.
"""

import argparse
import csv
import hashlib
import importlib.util
import json
import os
import sys
import tarfile
from pathlib import Path

print("Importing numpy", flush=True)
import numpy as np

print("Importing torch", flush=True)
import torch

print("Importing wfdb", flush=True)
import wfdb

print("Importing scipy", flush=True)
import zstandard
from scipy.signal import butter, lfilter, resample_poly

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--repo-root", type=Path, required=True)
parser.add_argument("--release-root", type=Path, required=True)
parser.add_argument("--morphology-module", type=Path, required=True)
parser.add_argument("--work-dir", type=Path, required=True)
parser.add_argument("--scratch-dir", type=Path, required=True)
parser.add_argument("--limit", type=int, default=0)
args = parser.parse_args()
if args.limit < 0:
    parser.error("--limit must be nonnegative")
work = args.work_dir.resolve()
work.mkdir(parents=True, exist_ok=True)
print("Imports completed", flush=True)
repo = args.repo_root.resolve()
assets = args.release_root.resolve()
sys.path.insert(0, str(repo / "src"))
from titan_v45.models.factory import build_titan_v45_backbone
from titan_v45.models.features import SpecialistFeatureLayout, compose_specialist_features
from titan_v45.models.specialists import ClassWiseBinaryMLP

spec = importlib.util.spec_from_file_location("recovered_morphology", args.morphology_module)
morphology = importlib.util.module_from_spec(spec)
spec.loader.exec_module(morphology)
torch.set_num_threads(2)
torch.manual_seed(2026)
device = "cuda" if torch.cuda.is_available() else "cpu"
out = work / ("p4_replay_declared_contract_" + str(args.limit))
out.mkdir(exist_ok=True)
root = args.scratch_dir.resolve() / "unpacked_pathology"
archive_path = assets / "data/external_dev/pathology/external-dev-pathology-ptbxl-fold10.tar.zst"
if not (root / ".complete").exists():
    root.mkdir(exist_ok=True)
    with (
        archive_path.open("rb") as handle,
        zstandard.ZstdDecompressor().stream_reader(handle) as reader,
    ):
        with tarfile.open(fileobj=reader, mode="r|") as archive:
            for member in archive:
                if not member.isfile():
                    continue
                target = (root / member.name).resolve()
                if not target.is_relative_to(root.resolve()):
                    raise ValueError("archive traversal")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.extractfile(member).read())
    (root / ".complete").write_text("completed")
package = root / "external-dev-pathology-ptbxl-fold10"
head_contract = json.loads((repo / "outputs/models/heads/global_head_contracts.json").read_text())
global_rhythm = head_contract["heads"]["rhythm"]["classes"]
global_pathology = head_contract["heads"]["pathology"]["classes"]
release_manifest = json.loads((repo / "release-manifest.json").read_text())
for entry in release_manifest["assets"]:
    if entry["name"] in {
        "backbone-v3ag-pathology.pt",
        "specialists-v3ag-primary4-calibrated.pt",
        archive_path.name,
    }:
        asset_path = assets / entry["path"]
        digest = hashlib.sha256()
        with asset_path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        if digest.hexdigest() != entry["sha256"] or asset_path.stat().st_size != entry["bytes"]:
            raise ValueError("Release asset checksum/size mismatch: " + entry["name"])
backbone = torch.load(
    assets / "outputs/models/backbones/backbone-v3ag-pathology.pt",
    map_location="cpu",
    weights_only=True,
)
specialist = torch.load(
    assets / "outputs/models/specialists/pathology/specialists-v3ag-primary4-calibrated.pt",
    map_location="cpu",
    weights_only=True,
)
model = build_titan_v45_backbone()
model.load_state_dict(backbone["state_dict"], strict=True)
model = model.to(device).eval()
state = specialist["pathology4_specialist_state_dict"]
head = ClassWiseBinaryMLP(
    state["heads.0.0.weight"].numel(), 4, hidden_dim=state["heads.0.1.weight"].shape[0]
)
head.load_state_dict(state, strict=True)
head = head.to(device).eval()
layout = SpecialistFeatureLayout(
    rhythm_indices=tuple(global_rhythm.index(c) for c in specialist["primary8_classes"]),
    specialist_rhythm_indices=tuple(
        global_rhythm.index(c) for c in specialist["specialist_rhythm_classes"]
    ),
    pathology_indices=tuple(global_pathology.index(c) for c in specialist["pathology4_classes"]),
)
rows = []
for label in specialist["pathology4_classes"]:
    path = (
        repo
        / f"outputs/results/external_dev/evidence/pathology_primary4_{label}_record_predictions.csv"
    )
    rows.extend(csv.DictReader(path.open(newline="")))
unique = {r["record_id"]: r["record_base"] for r in rows}
limit = args.limit
if limit:
    unique = dict(list(unique.items())[:limit])
leads = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]


def preprocess(record_base):
    header = wfdb.rdheader(str(record_base))
    fs = int(header.fs)
    # The surviving historical loader uses two seconds of zero context at edges.
    record = wfdb.rdrecord(str(record_base), sampfrom=0, sampto=min(header.sig_len, 12 * fs))
    signal = np.pad(record.p_signal, ((2 * fs, max(0, 12 * fs - header.sig_len)), (0, 0)))
    values = np.zeros((12, signal.shape[0]), dtype=np.float32)
    mask = np.zeros(12, dtype=bool)
    for i, lead in enumerate(leads):
        if lead in record.sig_name:
            values[i] = np.nan_to_num(signal[:, record.sig_name.index(lead)])
            mask[i] = True
    for i in range(12):
        if np.std(values[i]) > 1e-6:
            b, a = butter(3, [0.5 / (fs / 2), min(45 / (fs / 2), 0.99)], btype="band")
            values[i] = lfilter(b, a, values[i])
    from math import gcd

    divisor = gcd(fs, 125)
    values = resample_poly(values, 125 // divisor, fs // divisor, axis=1)[:, 250:1500]
    if values.shape[1] != 1250:
        raise ValueError("unexpected resampled length")
    sd = values.std(axis=1, keepdims=True)
    sd[sd < 1e-6] = 1
    values = (values - values.mean(axis=1, keepdims=True)) / sd
    return values, mask, morphology.normalized_morphology_features(values, fs=125)


predictions = {}
items = list(unique.items())
with torch.inference_mode():
    for start in range(0, len(items), 16):
        batch = items[start : start + 16]
        prepared = [preprocess(package / base) for _, base in batch]
        x = torch.as_tensor(np.stack([p[0] for p in prepared]), device=device)
        mask = torch.as_tensor(np.stack([p[1] for p in prepared]), device=device)
        morph = torch.as_tensor(np.stack([p[2] for p in prepared]), device=device)
        r, q, b, p, features = model(
            x, morphology_features=morph, lead_mask=mask, return_features=True
        )
        inputs = compose_specialist_features(
            backbone_features=features,
            rhythm_probabilities=r.sigmoid(),
            pathology_probabilities=p.sigmoid(),
            morphology=morph,
            layout=layout,
        )
        probabilities = head(inputs).sigmoid().cpu().numpy()
        for (record_id, _), scores in zip(batch, probabilities, strict=True):
            predictions[record_id] = scores.tolist()
        print(f"Processed {min(start + 16, len(items))}/{len(items)}", flush=True)
results = []
for row in rows:
    if row["record_id"] not in predictions:
        continue
    c = specialist["pathology4_classes"].index(row["pathology"])
    score = predictions[row["record_id"]][c]
    expected = float(row["probability"])
    results.append(
        {
            "record_id": row["record_id"],
            "class": row["pathology"],
            "target": int(row["target"]),
            "archived_probability": expected,
            "replayed_probability": score,
            "absolute_difference": abs(score - expected),
            "replayed_predicted": int(score >= specialist["pathology4_thresholds"][c]),
            "archived_predicted": int(row["predicted"]),
        }
    )
with (out / "comparison.csv").open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(results[0]))
    writer.writeheader()
    writer.writerows(results)
report = {
    "scope": "forensic_replay_declared_contract",
    "device": device,
    "torch": torch.__version__,
    "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
    "implementation_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "records": len(predictions),
    "panel_rows": len(results),
    "max_absolute_probability_difference": max(r["absolute_difference"] for r in results),
    "mean_absolute_probability_difference": float(
        np.mean([r["absolute_difference"] for r in results])
    ),
    "decision_disagreements": sum(
        r["replayed_predicted"] != r["archived_predicted"] for r in results
    ),
    "morphology_candidate_sha256": hashlib.sha256(
        (args.morphology_module).read_bytes()
    ).hexdigest(),
    "historical_preprocessing_certified": False,
    "note": "Single declared public feature layout and surviving loader reconstruction. Not tuned to labels; mismatch is retained as a reproducibility finding.",
}
(out / "replay_report.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2), flush=True)
