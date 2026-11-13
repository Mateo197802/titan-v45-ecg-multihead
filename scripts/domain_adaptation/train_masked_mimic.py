"""Masked waveform reconstruction on the sealed, authorized MIMIC training subset."""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as functional
from build_code_development import PROTOCOL, ROOT, digest, stable, write_json
from torch import nn
from train_duration_aware import configure

sys.path.insert(0, str(ROOT / "scripts/external_validation"))
from audit_mimic_signals import read_physical

from titan_v45.data.duration_aware_preprocessing import normalize, prepare_observed
from titan_v45.data.external_ecg import physical_digest
from titan_v45.models.factory import build_titan_v45_backbone
from titan_v45.models.frozen_pathology import verified_assets
from titan_v45.models.frozen_rhythm import BACKBONE

SSL = ROOT / "docs/domain_adaptation/MASKED_MIMIC_PROTOCOL.json"


def acquire_train(source, cfg):
    path = source / "private_mimic_waveform_eligibility.jsonl"
    if digest(path) != cfg["eligible_manifest_sha256"]:
        raise ValueError("MIMIC waveform eligibility receipt changed")
    by_patient = {}
    for line in path.read_bytes().splitlines():
        row = json.loads(line)
        if row["split"] != "train" or row["analysis_status"] != "waveform_eligible":
            continue
        patient = row["subject_id"]
        if patient not in by_patient or str(row["study_id"]) < str(by_patient[patient]["study_id"]):
            by_patient[patient] = row
    keys = sorted(by_patient, key=lambda p: stable(str(cfg["seed"]), p))[:cfg["patient_cap"]]
    waves, private = [], []
    for patient in keys:
        row = by_patient[patient]
        relative = Path(row["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("MIMIC waveform path escaped the authorized study")
        mv, _ = read_physical(source / "mimic" / relative)
        if physical_digest(mv, 500) != row["physical_digest"]:
            raise ValueError("MIMIC physical signal changed")
        waves.append(normalize(prepare_observed(mv.T, 500), "per_lead_zscore"))
        private.append({"patient": patient, "study": row["study_id"], "waveform_sha256": row["physical_digest"]})
    if not waves:
        raise ValueError("no authorized training signals")
    return np.stack(waves), private


def reconstruction(backbone, decoder, wave, mask, stride):
    width = wave.shape[-1]
    masked = mask.repeat_interleave(stride, dim=1)[:, :width]
    value = wave.masked_fill(masked[:, None, :], 0)
    latents = backbone.token_projection(backbone.res_layers(backbone.stem(value))).transpose(1, 2)
    tokens = backbone.transformer(backbone.position(latents))
    if tokens.shape[1] != mask.shape[1]:
        raise ValueError("SSL token and observed waveform contract mismatch")
    recovered = decoder(backbone.final_norm(tokens)).reshape(len(wave), -1, 12, stride)
    recovered = recovered.permute(0, 2, 1, 3).reshape(len(wave), 12, -1)[..., :width]
    cell = functional.smooth_l1_loss(recovered.float(), wave.float(), reduction="none")
    return (cell * masked[:, None, :]).sum() / (12 * masked.sum().clamp_min(1))


def run(source, assets, out):
    cfg = json.loads(SSL.read_bytes())
    protocol = json.loads(PROTOCOL.read_bytes())
    if digest(PROTOCOL) != cfg["frozen_parent_protocol_sha256"]:
        raise ValueError("SSL and parent protocol differ")
    if not torch.cuda.is_available():
        raise RuntimeError("a CEDIA CUDA allocation is required")
    torch.manual_seed(cfg["seed"])
    rng = np.random.default_rng(cfg["seed"])
    waves, private = acquire_train(source, cfg)
    out.mkdir(mode=0o700, exist_ok=False)
    write_json(out / "private_mimic_train_manifest.json", private)
    paths, hashes = verified_assets(ROOT, assets, {BACKBONE})
    backbone = build_titan_v45_backbone()
    weights = torch.load(paths[BACKBONE], map_location="cpu", weights_only=True)
    backbone.load_state_dict(weights["state_dict"], strict=True)
    backbone.cuda().eval()
    del weights
    groups, anchors = configure(backbone, "partial_transformer_mlp", protocol["training"])
    if any(g["lr"] != cfg["learning_rate"] for g in groups):
        raise ValueError("SSL learning rate differs from protocol")
    stride = cfg["mask_samples"]
    decoder = nn.Linear(backbone.d_model, 12 * stride).cuda()
    optimizer = torch.optim.AdamW([*groups, {"params": decoder.parameters(), "lr": cfg["decoder_learning_rate"]}])
    curves = out / "SSL_LEARNING_CURVES.csv"
    with curves.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(("epoch", "mean_masked_loss", "ecgs"))
        for epoch in range(1, cfg["epochs"] + 1):
            total = 0.
            for indices in np.array_split(rng.permutation(len(waves)), int(np.ceil(len(waves) / cfg["batch"]))):
                wave = torch.as_tensor(waves[indices], device="cuda")
                mask = torch.rand((len(wave), int(np.ceil(wave.shape[-1] / stride))), device="cuda") < cfg["mask_probability"]
                mask[:, 0] = True
                optimizer.zero_grad(set_to_none=True)
                with torch.autocast("cuda", dtype=torch.bfloat16, enabled=torch.cuda.is_bf16_supported()):
                    loss = reconstruction(backbone, decoder, wave, mask, stride)
                    loss = loss + protocol["training"]["anchor_lambda"] * sum(
                        (p - initial).square().mean() for p, initial in anchors) / len(anchors)
                if not torch.isfinite(loss):
                    raise FloatingPointError("non-finite masked signal loss")
                loss.backward()
                nn.utils.clip_grad_norm_([p for p in backbone.parameters() if p.requires_grad] + list(decoder.parameters()),
                                         1., error_if_nonfinite=True)
                optimizer.step()
                total += float(loss.detach()) * len(indices)
            writer.writerow((epoch, total / len(waves), len(waves)))
            stream.flush()
            print(json.dumps({"epoch": epoch, "mean_masked_loss": total / len(waves), "ecgs": len(waves)}), flush=True)
    checkpoint = out / "masked_mimic_backbone.pt"
    torch.save({"state_dict": backbone.state_dict(), "protocol_sha256": digest(SSL),
                "parent_sha256": hashes[BACKBONE]}, checkpoint)
    result = {"scope": cfg["scope"], "ecgs": len(waves), "patients": len(private),
              "protocol_sha256": digest(SSL), "input_manifest_sha256": cfg["eligible_manifest_sha256"],
              "private_train_manifest_sha256": digest(out / "private_mimic_train_manifest.json"),
              "checkpoint_sha256": digest(checkpoint), "curves_sha256": digest(curves),
              "label_files_opened": False, "heldout_waveforms_opened": False, "slurm_job": os.getenv("SLURM_JOB_ID")}
    write_json(out / "SSL_TRAINING_RECEIPT.json", result)
    print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "assets", "output"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    run(args.source, args.assets, args.output)
