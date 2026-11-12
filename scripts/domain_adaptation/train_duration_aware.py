"""Train a real waveform-to-endpoint specialist, with an isolated validation set."""
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import torch
from build_code_development import PROTOCOL, ROOT, digest, write_json
from torch import nn

from titan_v45.data.duration_aware_preprocessing import normalize
from titan_v45.evaluation.revision_report import binary_metrics
from titan_v45.models.factory import build_titan_v45_backbone
from titan_v45.models.frozen_pathology import verified_assets
from titan_v45.models.frozen_rhythm import BACKBONE

MODES = {
    "frozen_backbone_mlp": (),
    "partial_transformer_mlp": ("transformer.layers.7.", "transformer.layers.8.", "final_norm."),
    "partial_transformer_resnet_mlp": ("transformer.layers.7.", "transformer.layers.8.", "final_norm.",
                                      "res_layers.5.", "token_projection."),
    "full_regularized": ("",),
}


class TemporalSpecialist(nn.Module):
    def __init__(self, backbone):
        super().__init__()
        self.backbone = backbone
        self.head = nn.Sequential(nn.LayerNorm(backbone.d_model + 9), nn.Linear(backbone.d_model + 9, 128),
                                  nn.SiLU(), nn.Dropout(.2), nn.Linear(128, 5))

    def forward(self, wave, descriptors):
        features = self.backbone.forward_features(wave)
        duration = features.new_zeros((len(wave), 2))
        duration[:, int(wave.shape[-1] == 1250)] = 1
        return self.head(torch.cat([features, descriptors, duration], dim=1))


def read_bank(bank, split, normalizer):
    receipt = json.loads((bank / "CODE_DEVELOPMENT_RECEIPT.json").read_bytes())
    path = bank / f"private_{split}.json"
    if receipt["protocol_sha256"] != digest(PROTOCOL) or digest(path) != receipt["splits"][split]["private_manifest_sha256"]:
        raise ValueError("CODE bank manifest differs from sealed input")
    records = json.loads(path.read_bytes())
    groups, folders = defaultdict(list), {}
    multiplicity = Counter(row["patient"] for row in records)
    for row in records:
        if row["split"] != split:
            raise ValueError("wrong split in private waveform manifest")
        groups[row["file"]].append(row)
    tensors = defaultdict(list)
    for name, rows in groups.items():
        relative = Path(name)
        if relative.is_absolute() or len(relative.parts) != 2 or ".." in relative.parts:
            raise ValueError("unexpected waveform-bank path")
        folder = relative.parent
        if folder not in folders:
            folders[folder] = json.loads((bank / folder / "receipt.json").read_bytes())
        if digest(bank / relative) != folders[folder]["artifacts"][relative.name]:
            raise ValueError("waveform bank file hash mismatch")
        with np.load(bank / relative, allow_pickle=False) as data:
            indices = [row["row"] for row in rows]
            wave, desc = data["wave"][indices], data["descriptors"][indices]
        if wave.shape[1:] not in ((12, 917), (12, 1250)) or desc.shape != (len(wave), 7):
            raise ValueError("waveform or descriptor shape differs from frozen contract")
        tensors[wave.shape[-1]].append((normalize(wave, normalizer), desc,
                                        np.asarray([row["labels"] for row in rows], dtype=np.float32),
                                        np.asarray([1 / multiplicity[row["patient"]] for row in rows], dtype=np.float32),
                                        np.asarray([row["exam"] for row in rows]),
                                        np.asarray([row["patient"] for row in rows])))
    return {length: tuple(np.concatenate(parts) for parts in zip(*groups, strict=True))
            for length, groups in tensors.items()}


def batches(data, size, rng=None):
    work = []
    for length, arrays in data.items():
        n = len(arrays[0])
        order = rng.permutation(n) if rng is not None else np.arange(n)
        work.extend((length, order[i:i + size]) for i in range(0, n, size))
    if rng is not None:
        rng.shuffle(work)
    for length, indices in work:
        yield tuple(x[indices] for x in data[length])


def device_batch(wave, desc, labels, patient_weight):
    return [torch.as_tensor(a, dtype=torch.float32, device="cuda") for a in (wave, desc, labels, patient_weight)]


def evaluate(model, data, size):
    model.eval()
    labels, scores = [], []
    with torch.no_grad():
        for wave, desc, y, *_ in batches(data, size):
            p = model(torch.as_tensor(wave, device="cuda"), torch.as_tensor(desc, device="cuda")).sigmoid()
            labels.append(y)
            scores.append(p.cpu().numpy())
    return np.concatenate(labels), np.concatenate(scores)


def validation_summary(y, p):
    rows = []
    for index in range(y.shape[1]):
        keep = y[:, index] >= 0
        truth, prob = y[keep, index], p[keep, index]
        if len(set(truth)) != 2:
            raise ValueError("validation lacks endpoint support")
        rows.append(binary_metrics(truth.astype(int), prob >= .5, prob))
    return rows


def configure(backbone, mode, cfg):
    backbone.requires_grad_(False)
    groups, anchors = defaultdict(list), []
    for name, parameter in backbone.named_parameters():
        if not name.startswith(MODES[mode]):
            continue
        parameter.requires_grad_(True)
        rate = (cfg["full_backbone_lr"] if mode == "full_regularized" else
                cfg["transformer_lr"] if name.startswith(("transformer.", "final_norm.")) else cfg["resnet_lr"])
        groups[rate].append(parameter)
        anchors.append((parameter, parameter.detach().clone()))
    return [{"params": params, "lr": rate} for rate, params in groups.items()], anchors


def run(bank, assets, out, mode, seed, normalizer):
    cfg = json.loads(PROTOCOL.read_bytes())
    hp = cfg["training"]
    if seed not in hp["seeds"] or normalizer not in cfg["waveform"]["normalizations"]:
        raise ValueError("unregistered seed or normalization")
    if not torch.cuda.is_available():
        raise RuntimeError("a CEDIA CUDA allocation is required")
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    rng = np.random.default_rng(seed)
    if torch.cuda.is_bf16_supported():
        torch.set_float32_matmul_precision("high")
    train, val = (read_bank(bank, split, normalizer) for split in ("train", "validation"))
    out.mkdir(mode=0o700, exist_ok=False)
    paths, hashes = verified_assets(ROOT, assets, {BACKBONE})
    backbone = build_titan_v45_backbone()
    state = torch.load(paths[BACKBONE], map_location="cpu", weights_only=True)
    backbone.load_state_dict(state["state_dict"], strict=True)
    del state
    model = TemporalSpecialist(backbone).cuda()
    groups, anchors = configure(backbone, mode, hp)
    optimizer = torch.optim.AdamW([{"params": model.head.parameters(), "lr": hp["head_lr"]}, *groups],
                                  weight_decay=hp["weight_decay"])
    labels = np.concatenate([arrays[2] for arrays in train.values()])
    pos = (labels == 1).sum(axis=0)
    neg = (labels == 0).sum(axis=0)
    if np.any(pos == 0) or np.any(neg == 0):
        raise ValueError("training lacks positive or negative endpoint support")
    weights = torch.as_tensor(np.sqrt(neg / pos).clip(1, 16), dtype=torch.float32, device="cuda")
    best, best_epoch = -np.inf, 0
    checkpoint = out / "best.pt"
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    with (out / "FINETUNING_LEARNING_CURVES.csv").open("x", newline="", encoding="utf-8") as stream:
        names = ["epoch", "train_loss", "max_gradient_norm", "validation_macro_ap", "validation_macro_f1_at_half"]
        names += [f"{name}_{metric}" for name in cfg["endpoints"] for metric in ("ap", "f1")]
        writer = csv.DictWriter(stream, fieldnames=names, lineterminator="\n")
        writer.writeheader()
        for epoch in range(1, hp["max_epochs"] + 1):
            model.train()
            model.backbone.eval()
            loss_total, max_grad, n = 0.0, 0.0, 0
            for wave, desc, y, patient_weight, *_ in batches(train, hp["batch_size"], rng):
                x, d, target, w = device_batch(wave, desc, y, patient_weight)
                optimizer.zero_grad(set_to_none=True)
                with torch.autocast("cuda", dtype=torch.bfloat16, enabled=torch.cuda.is_bf16_supported()):
                    logits = model(x, d)
                    cell = nn.functional.binary_cross_entropy_with_logits(
                        logits.float(), target.clamp_min(0), pos_weight=weights, reduction="none")
                    valid = (target >= 0) * w[:, None]
                    loss = (cell * valid).sum() / valid.sum().clamp_min(1)
                    if anchors:
                        loss = loss + hp["anchor_lambda"] * sum(
                            (p - initial).square().mean() for p, initial in anchors) / len(anchors)
                if not torch.isfinite(loss):
                    raise FloatingPointError("non-finite training loss")
                loss.backward()
                grad = nn.utils.clip_grad_norm_((p for p in model.parameters() if p.requires_grad),
                                                hp["gradient_clip"], error_if_nonfinite=True)
                optimizer.step()
                n += len(wave)
                loss_total += float(loss.detach()) * len(wave)
                max_grad = max(max_grad, float(grad))
            y, p = evaluate(model, val, hp["batch_size"])
            metrics = validation_summary(y, p)
            ap = float(np.mean([r["average_precision"] for r in metrics]))
            f1 = float(np.mean([r["f1"] for r in metrics]))
            row = {"epoch": epoch, "train_loss": loss_total / n, "max_gradient_norm": max_grad,
                   "validation_macro_ap": ap, "validation_macro_f1_at_half": f1}
            for endpoint, metric in zip(cfg["endpoints"], metrics, strict=True):
                row[f"{endpoint}_ap"], row[f"{endpoint}_f1"] = metric["average_precision"], metric["f1"]
            writer.writerow(row)
            stream.flush()
            print(json.dumps(row, sort_keys=True), flush=True)
            if ap > best:
                best, best_epoch = ap, epoch
                best_f1 = f1
                temp = out / "best.pt.tmp"
                torch.save({"state_dict": model.state_dict(), "seed": seed, "mode": mode,
                            "normalizer": normalizer, "epoch": epoch, "protocol_sha256": digest(PROTOCOL)}, temp)
                temp.replace(checkpoint)
            if epoch - best_epoch >= hp["early_stop_patience"]:
                break
    result = {"mode": mode, "seed": seed, "normalization": normalizer, "best_epoch": best_epoch,
              "validation_macro_ap": best, "validation_macro_f1_at_half": best_f1, "trainable_parameters": trainable,
              "source": "CODE-15% development only", "calibration_or_test_opened": False,
              "protocol_sha256": digest(PROTOCOL), "baseline_assets": hashes, "checkpoint_sha256": digest(checkpoint),
              "code_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "bank_receipt_sha256": digest(bank / "CODE_DEVELOPMENT_RECEIPT.json"),
              "curves_sha256": digest(out / "FINETUNING_LEARNING_CURVES.csv"),
              "slurm_job": os.getenv("SLURM_JOB_ID"), "torch_version": torch.__version__,
              "gpu": torch.cuda.get_device_name()}
    write_json(out / "TRAINING_RECEIPT.json", result)
    print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("bank", "assets", "output"):
        parser.add_argument(name, type=Path)
    parser.add_argument("mode", choices=MODES)
    parser.add_argument("seed", type=int)
    parser.add_argument("normalizer", choices=("per_lead_zscore", "robust_shared_gain"))
    args = parser.parse_args()
    run(args.bank, args.assets, args.output, args.mode, args.seed, args.normalizer)
