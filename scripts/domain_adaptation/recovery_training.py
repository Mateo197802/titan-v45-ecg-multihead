"""Continue pretrained TITAN weights under a fixed development-only study."""
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import traceback
from functools import lru_cache
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from recovery_inputs import (
    RECOVERY,
    ROOT,
    SOURCES,
    authorized_bank,
    authorized_extra,
    config,
    parent_model,
    score_model,
)
from train_duration_aware import batches, digest, validation_summary, write_json

from titan_v45.models.frozen_pathology import verified_assets
from titan_v45.models.frozen_rhythm import BACKBONE


class RecoveryNet(torch.nn.Module):
    def __init__(self, base, kind):
        super().__init__()
        self.base, self.kind = base, kind
        if kind != "shared":
            n = base.backbone.d_model + 9
            indices = (0, 1, 4) if kind == "residual" else range(5)
            self.branches = torch.nn.ModuleDict({
                str(i): torch.nn.Sequential(torch.nn.LayerNorm(n + (4 if kind == "residual" and i < 2 else
                                                                   12 if kind == "residual" and i == 4 else 0)),
                                            torch.nn.Linear(n + (4 if kind == "residual" and i < 2 else
                                                                 12 if kind == "residual" and i == 4 else 0), 64),
                                            torch.nn.SiLU(), torch.nn.Linear(64, 1))
                for i in indices
            })
            for branch in self.branches.values():
                torch.nn.init.zeros_(branch[-1].weight)
                torch.nn.init.zeros_(branch[-1].bias)
        if kind == "residual":
            self.conduction = torch.nn.Sequential(torch.nn.Conv1d(2, 12, 15, padding=7),
                                                  torch.nn.SiLU(), torch.nn.Conv1d(12, 12, 31, padding=15),
                                                  torch.nn.SiLU(), torch.nn.AdaptiveAvgPool1d(1))
            self.rate = torch.nn.Linear(base.backbone.d_model, 1)

    def forward(self, wave, descriptors, rr=None, return_rate=False):
        features = self.base.backbone.forward_features(wave)
        duration = features.new_zeros((len(wave), 2))
        duration[:, int(wave.shape[-1] == 1250)] = 1
        joined = torch.cat((features, descriptors, duration), dim=1)
        logits = self.base.head(joined)
        if self.kind != "shared":
            extra = logits.new_zeros(logits.shape)
            for key, branch in self.branches.items():
                local = joined
                if self.kind == "residual" and int(key) < 2:
                    if rr is None:
                        raise ValueError("AFIB/SB branches require a QRS confidence feature vector")
                    local = torch.cat((joined, rr / rr.new_tensor((100., 1., 1., 1.))), dim=1)
                elif self.kind == "residual" and key == "4":
                    local = torch.cat((joined, self.conduction(wave[:, [1, 7]]).squeeze(-1)), dim=1)
                extra[:, int(key)] = branch(local).squeeze(-1)
            logits = logits + extra
        if return_rate:
            return logits, self.rate(features).squeeze(-1) if self.kind == "residual" else None
        return logits


def loss_cell(logits, target, weight, kind, hard_score=None):
    valid_target = target.clamp_min(0)
    loss = F.binary_cross_entropy_with_logits(logits, valid_target, pos_weight=weight, reduction="none")
    if kind in ("asymmetric", "focal"):
        prob = logits.sigmoid()
        if kind == "asymmetric":
            focus = torch.where(valid_target == 1, 1., prob.square())
        else:
            focus = torch.where(valid_target == 1, (1 - prob).square(), prob.square())
        loss = loss * focus
    if kind == "hard_negative":
        hp = config()["training"]
        loss = loss * torch.where((target == 0) & (hard_score >= hp["hard_negative_score"]), hp["hard_negative_weight"], 1.)
    return loss


def depth_settings(name, epoch, depth, hp):
    if not name.startswith("base.backbone."):
        return hp["head_lr"], 1
    inner = name.removeprefix("base.backbone.")
    usable = ("stem.", "res_layers.", "transformer.", "token_projection.", "final_norm.", "lead_mask_projection.")
    if not inner.startswith(usable):
        return 0., 999
    if depth == "full":
        return hp["earlier_lr"], 1
    if inner.startswith(("transformer.layers.7.", "transformer.layers.8.", "final_norm.")):
        return hp["transformer_lr"], 1
    if inner.startswith(("res_layers.5.", "token_projection.")):
        return hp["resnet_lr"], 1
    if inner.startswith(("transformer.layers.6.", "res_layers.4.")):
        return hp["earlier_lr"], 2
    if inner.startswith(("transformer.layers.5.", "res_layers.3.")):
        return hp["earlier_lr"], 3
    return 0., 999


def init_mimic_delta(model, previous, assets):
    path = previous / "mimic-masked/masked_mimic_backbone.pt"
    cfg = config()
    if digest(path) != cfg["mimic_ssl_sha256"]:
        raise ValueError("MIMIC weights do not match the approved training-only seal")
    receipt = json.loads((path.parent / "SSL_TRAINING_RECEIPT.json").read_bytes())
    if (receipt["checkpoint_sha256"] != cfg["mimic_ssl_sha256"] or receipt["label_files_opened"]
            or receipt["heldout_waveforms_opened"]):
        raise ValueError("SSL receipt is not train-only")
    paths, hashes = verified_assets(ROOT, assets, {BACKBONE})
    ssl = torch.load(path, map_location="cpu", weights_only=True)
    released = torch.load(paths[BACKBONE], map_location="cpu", weights_only=True)
    if ssl["parent_sha256"] != hashes[BACKBONE] or ssl["protocol_sha256"] != receipt["protocol_sha256"]:
        raise ValueError("SSL lineage is not the frozen V3F initialization")
    with torch.no_grad():
        for name, param in model.base.backbone.named_parameters():
            if name.startswith(("transformer.layers.7.", "transformer.layers.8.", "final_norm.")):
                param.add_(cfg["training"]["mimic_delta_scale"] * (ssl["state_dict"][name] - released["state_dict"][name]))


@lru_cache(maxsize=5)
def get_code(previous, split, normalization):
    return authorized_bank(previous / "code-bank", split, normalization)


@lru_cache(maxsize=8)
def get_other(previous, name, split, normalization):
    return authorized_extra(previous / "additional-sources-v2", name, split, normalization)


def aux_data(diagnostics, scope):
    name = "training_aux" if scope == "train" else scope
    path = diagnostics / f"private_{name}.npz"
    receipt = json.loads((diagnostics / "DEVELOPMENT_SCORING_RECEIPT.json").read_bytes())
    if receipt["protocol_sha256"] != digest(RECOVERY) or digest(path) != receipt["private_artifact_sha256"][path.name]:
        raise ValueError("training-only auxiliary measurements not sealed")
    with np.load(path, allow_pickle=False) as data:
        return {str(e): r for e, r in zip(data["exams"], data["rr"], strict=True)}, {
            str(e): p for e, p in zip(data["exams"], data["p"], strict=True)}


def stream_batches(training, size, rng, fraction):
    code = list(batches(training["code"], size, rng))
    sources = [name for name in training if name != "code"]
    n_external = round(len(code) * fraction / (1 - len(sources) * fraction))
    tagged = [("code", i) for i in range(len(code))] + [(s, i) for s in sources for i in range(n_external)]
    rng.shuffle(tagged)
    queues = {name: iter(batches(training[name], size, rng)) for name in sources}
    for source, i in tagged:
        if source == "code":
            yield source, code[i]
        else:
            sample = next(queues[source], None)
            if sample is None:
                queues[source] = iter(batches(training[source], size, rng))
                sample = next(queues[source])
            yield source, sample


def write_scores(path, model, bank, rr):
    scores = score_model(model, bank, rr=rr)
    np.savez_compressed(path, **scores)
    return scores


def train(previous, assets, diagnostics, out, mode, seed):
    cfg = config()
    hp, variant = cfg["training"], cfg["training"]["screen"][mode]
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    rng = np.random.default_rng(seed)
    normalize = variant["normalization"]
    training = {"code": get_code(previous, "train", normalize)}
    if variant["sources"] in ("code_chapman", "code_chapman_cpsc"):
        training["chapman"] = get_other(previous, "chapman_shaoxing", "train", normalize)
    if variant["sources"] == "code_chapman_cpsc":
        training["cpsc"] = get_other(previous, "cpsc2018", "train", normalize)
    validation = get_code(previous, "validation", normalize)
    model = RecoveryNet(parent_model(previous, seed), variant["head"])
    if mode == "mimic":
        init_mimic_delta(model, previous, assets)
    model.cuda()
    if variant["head"] == "independent":
        model.base.head.requires_grad_(False)
    groups, anchor = [], {}
    for name, param in model.named_parameters():
        lr, start = depth_settings(name, 1, variant["depth"], hp)
        if not lr or not param.requires_grad:
            param.requires_grad_(False)
            continue
        param.requires_grad_(start == 1)
        groups.append({"params": [param], "lr": lr, "activation_epoch": start})
        if name.startswith("base.backbone."):
            anchor[param] = param.detach().clone()
    optimizer = torch.optim.AdamW(groups, weight_decay=hp["weight_decay"])
    ref = np.concatenate([a[2] for a in training["code"].values()])
    w = torch.as_tensor(np.sqrt((ref == 0).sum(axis=0) / (ref == 1).sum(axis=0)).clip(1, 12),
                        dtype=torch.float32, device="cuda")
    rr_train, p_train = aux_data(diagnostics, "train") if mode == "specialist" else ({}, {})
    rr_val = aux_data(diagnostics, "validation")[0] if mode == "specialist" else None
    out.mkdir(mode=0o700, exist_ok=False)
    checkpoint, curves = out / "best.pt", out / "FINETUNING_LEARNING_CURVES.csv"
    best = (-1., -1.)
    best_epoch = 0
    with curves.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["epoch", "mean_loss", "macro_ap", "guard_ap", "macro_f1_at_0_5", "max_gradient_norm",
                         "trainable_parameters", "code_batches", "chapman_batches", "cpsc_batches"])
        for epoch in range(1, hp["epochs"] + 1):
            for group in optimizer.param_groups:
                for param in group["params"]:
                    param.requires_grad_(epoch >= group["activation_epoch"])
            model.train()
            model.base.backbone.eval()
            if variant["head"] == "independent":
                model.base.head.eval()
            total, steps, norm = 0., 0, 0.
            counts = dict.fromkeys(("code", "chapman", "cpsc"), 0)
            for source, (wave, desc, labels, weight, exams, _) in stream_batches(
                    training, hp["batch_size"], rng, hp["external_batch_fraction_each"]):
                x, d, y, patient_w = (torch.as_tensor(a, device="cuda") for a in (wave, desc, labels, weight))
                rr = torch.as_tensor(np.asarray([rr_train[str(e)] for e in exams]), device="cuda") if mode == "specialist" else None
                hard = torch.as_tensor(np.asarray([p_train[str(e)] for e in exams]), device="cuda") if mode == "specialist" else None
                optimizer.zero_grad(set_to_none=True)
                with torch.autocast("cuda", dtype=torch.bfloat16, enabled=torch.cuda.is_bf16_supported()):
                    z, hr = model(x, d, rr, return_rate=True)
                    valid = (y >= 0) * patient_w[:, None]
                    loss = (loss_cell(z.float(), y, w, variant["loss"], hard) * valid).sum() / valid.sum().clamp_min(1)
                    if hr is not None:
                        have = rr[:, 3] > 0
                        if torch.any(have):
                            loss = loss + .05 * F.smooth_l1_loss(hr[have].float(), rr[have, 0] / 100.)
                    penalties = [(p - old).square().mean() for p, old in anchor.items() if p.requires_grad]
                    if penalties:
                        loss = loss + hp["anchor_lambda"] * sum(penalties) / len(penalties)
                if not torch.isfinite(loss):
                    raise FloatingPointError("nonfinite training loss")
                loss.backward()
                gradient = torch.nn.utils.clip_grad_norm_(model.parameters(), hp["gradient_clip"], error_if_nonfinite=True)
                optimizer.step()
                total += float(loss.detach())
                norm = max(norm, float(gradient))
                counts[source] += 1
                steps += 1
            scored = score_model(model, validation, rr=rr_val)
            metrics = validation_summary(scored["labels"], scored["p"])
            aps = [r["average_precision"] for r in metrics]
            score = float(np.mean(aps)), float(np.mean([aps[i] for i in (0, 1, 4)]))
            f1 = float(np.mean([r["f1"] for r in metrics]))
            params = sum(p.numel() for p in model.parameters() if p.requires_grad)
            writer.writerow([epoch, total / steps, *score, f1, norm, params, *counts.values()])
            stream.flush()
            print(json.dumps({"mode": mode, "seed": seed, "epoch": epoch, "macro_ap": score[0],
                              "macro_f1_at_0_5": f1, "trainable": params}), flush=True)
            if score > best:
                best, best_epoch, best_f1, best_params = score, epoch, f1, params
                temp = out / "checkpoint.tmp"
                torch.save({"state_dict": model.state_dict(), "variant": variant, "mode": mode, "seed": seed,
                            "epoch": epoch, "protocol_sha256": digest(RECOVERY)}, temp)
                temp.replace(checkpoint)
            if epoch - best_epoch >= hp["patience"]:
                break
    model.load_state_dict(torch.load(checkpoint, map_location="cpu", weights_only=True)["state_dict"], strict=True)
    private = {}
    for scope in ("validation", "chapman", "cpsc"):
        if scope == "cpsc" and "cpsc" in training:
            continue
        data = validation if scope == "validation" else get_other(previous, *SOURCES[scope], normalize)
        rr = aux_data(diagnostics, scope)[0] if mode == "specialist" else None
        path = out / f"private_{scope}.npz"
        write_scores(path, model, data, rr)
        private[path.name] = digest(path)
    result = {"mode": mode, "seed": seed, "variant": variant, "training_sources": list(training), "best_epoch": best_epoch,
              "validation_macro_ap": best[0], "validation_guard_ap": best[1], "validation_f1_at_0_5": best_f1,
              "trainable_at_best": best_params, "checkpoint_sha256": digest(checkpoint),
              "parent_sha256": cfg["parent_checkpoints"][str(seed)], "curves_sha256": digest(curves),
              "calibration_opened": False, "old_test_opened": False, "private_score_sha256": private,
              "protocol_sha256": digest(RECOVERY), "slurm_job": os.getenv("SLURM_JOB_ID"),
              "code_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()}
    write_json(out / "MODEL_RECOVERY_FIT_RECEIPT.json", result)


def fit_group(previous, assets, diagnostics, fits, modes, seeds, gate_path):
    cfg = config()
    if any(m not in cfg["training"]["screen"] for m in modes) or any(s not in cfg["training"]["seeds"] for s in seeds):
        raise ValueError("unregistered mode or seed")
    if ("full" in modes or any(s != cfg["training"]["screen_seed"] for s in seeds)) and not gate_path:
        raise ValueError("conditional runs require a sealed decision")
    if gate_path:
        gate = json.loads(gate_path.read_bytes())
        if gate["protocol_sha256"] != digest(RECOVERY):
            raise ValueError("gate belongs to another study")
        if "full" in modes and not gate["allow_full"]:
            raise ValueError("full fine-tuning gate did not pass")
        if any(seed != cfg["training"]["screen_seed"] for seed in seeds) and set(modes) != set(gate["repeat_modes"]):
            raise ValueError("repeat modes do not match frozen selection")
    failures = 0
    fits.mkdir(mode=0o700, exist_ok=True)
    if len(modes) != len(set(modes)) or len(seeds) != len(set(seeds)):
        raise ValueError("duplicate fit in allocation")
    if sum(path.is_dir() for path in fits.iterdir()) + len(modes) * len(seeds) > cfg["training"]["max_supervised_fits"]:
        raise ValueError("frozen supervised fit budget exceeded")
    for mode in modes:
        for seed in seeds:
            path = fits / f"{mode}-{seed}"
            if path.exists():
                raise FileExistsError(path)
            try:
                train(previous, assets, diagnostics, path, mode, seed)
            except (ValueError, RuntimeError, FloatingPointError, OSError) as exc:
                traceback.print_exc()
                path.mkdir(mode=0o700, exist_ok=True)
                write_json(path / "FAILED_FIT_RECEIPT.json", {"mode": mode, "seed": seed, "exception_class": type(exc).__name__,
                                                             "slurm_job": os.getenv("SLURM_JOB_ID")})
                failures += 1
                torch.cuda.empty_cache()
    if failures:
        raise RuntimeError(f"{failures} frozen fits failed; retained their receipts")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("previous", "assets", "diagnostics", "fits"):
        parser.add_argument(key, type=Path)
    parser.add_argument("modes", help="comma-separated registered modes")
    parser.add_argument("seeds", help="comma-separated registered seeds")
    parser.add_argument("--gate", type=Path)
    args = parser.parse_args()
    fit_group(args.previous, args.assets, args.diagnostics, args.fits, args.modes.split(","),
              [int(s) for s in args.seeds.split(",")], args.gate)
