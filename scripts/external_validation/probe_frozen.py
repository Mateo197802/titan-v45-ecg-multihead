"""Label-blind smoke test on hash-verified MIMIC waveforms; no performance."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from collections import Counter
from itertools import islice
from pathlib import Path

import numpy as np
import torch
import wfdb
from acquire_mimic import checksum_index, fetch, select

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts/specialist_experiments")]
from extract_features import _baseline_thresholds, _pathology_batch, _rhythm_batch, _safe_morphology

from titan_v45.data.external_ecg import physical_mv, prepare_external
from titan_v45.models.frozen_pathology import BACKBONE as PATH_BACKBONE
from titan_v45.models.frozen_pathology import SPECIALIST, FrozenPathology, verified_assets
from titan_v45.models.frozen_rhythm import (
    BACKBONE,
    HEADS,
    FrozenRhythm,
    load_recorded_event_extractor,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("study", type=Path)
    parser.add_argument("assets", type=Path)
    args = parser.parse_args()
    device = "cuda"
    if not torch.cuda.is_available():
        raise RuntimeError("GPU probe requires CUDA")
    protocol = json.loads((ROOT / "docs/external_validation_20261111/FROZEN_EXTERNAL_EVALUATION_PROTOCOL.json").read_text())
    assets, hashes = verified_assets(ROOT, args.assets, {BACKBONE, *HEADS.values(), PATH_BACKBONE, SPECIALIST})
    if hashes != protocol["baseline"]:
        raise ValueError("baseline assets differ from pinned protocol")
    contract = json.loads((ROOT / "outputs/models/heads/global_head_contracts.json").read_text())
    morphology = _safe_morphology(ROOT)
    source = args.study / "probe"
    index = (args.study / "mimic/record_list.csv").read_bytes()
    checksum_file = args.study / "mimic/SHA256SUMS.txt"
    if hashlib.sha256(index).hexdigest() != checksum_index(checksum_file, {"record_list.csv"})["record_list.csv"]:
        raise ValueError("record list checksum mismatch")
    acquisition = protocol["mimic_acquisition"]
    cohort = select(csv.DictReader(io.StringIO(index.decode("utf-8-sig"))),
                    seed=acquisition["seed"], patient_limit=acquisition["patient_limit"],
                    max_records=acquisition["max_records_per_patient"])
    examples = [row["path"] for row in islice(cohort, 3) if row["split"] == "train"]
    paths = {stem + suffix for stem in examples for suffix in (".hea", ".dat")}
    expected = checksum_index(checksum_file, paths)
    samples = []
    errors = Counter()
    for stem in examples:
        try:
            for suffix in (".hea", ".dat"):
                path = stem + suffix
                fetch(source, path, expected[path], 262144)
            header = wfdb.rdheader(str(source / stem))
            if set(header.file_name) != {Path(stem).name + ".dat"}:
                raise ValueError("unsafe_or_unexpected_wfdb_component")
            if header.fs != 500 or header.sig_len != 5000 or any(
                not np.isfinite(gain) or gain <= 0 for gain in header.adc_gain
            ):
                raise ValueError("invalid_wfdb_header")
            record = wfdb.rdrecord(str(source / stem), physical=True)
            signal = physical_mv(record.p_signal, header.sig_name, header.units, 500)
            samples.append(prepare_external(signal, 500, morphology))
        except (ValueError, OSError, RuntimeError) as error:
            errors[type(error).__name__] += 1
    if not samples:
        raise RuntimeError("no physically valid probe inputs")
    rhythm = FrozenRhythm(
        assets, contract,
        load_recorded_event_extractor(ROOT / "docs/provenance/recovered-original-sources-20261029.zip"),
        device,
    )
    pathology = FrozenPathology(assets, contract, device)
    _baseline_thresholds(ROOT, pathology)
    scores = {key: values[1] for key, values in _rhythm_batch(rhythm, samples).items()}
    scores["P4"] = _pathology_batch(pathology, samples)[1]
    if set(scores) != {"P4", "P6", "P8"} or any(not np.isfinite(value).all() for value in scores.values()):
        raise RuntimeError("baseline probe produced invalid output")
    receipt = {
        "scope": "LABEL_BLIND_FIRST_THREE_TRAINING_RECORDS_SMOKE_ONLY",
        "attempted_ecg": len(examples),
        "scored_ecg": len(samples),
        "errors": dict(errors),
        "baseline_sha256": hashes,
        "shape_by_profile": {key: list(value.shape) for key, value in scores.items()},
        "torch": torch.__version__,
        "cuda": torch.version.cuda,
        "gpu": torch.cuda.get_device_name(),
        "reports_read": False,
        "performance_computed": False,
    }
    text = json.dumps(receipt, sort_keys=True, indent=2) + "\n"
    (args.study / "probe_receipt.json").write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
