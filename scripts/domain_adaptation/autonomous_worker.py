"""Targeted development fitting with immutable off-target predictions."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from corrective_evaluate import aligned, calibrate, measure, summarize
from corrective_fit import oof
from recovery_calibration import choose_cut, fit_map, load_score, transform
from recovery_inputs import ROOT, SOURCES, config, parent_model
from recovery_training import aux_data, get_code, get_other
from train_duration_aware import batches, digest, write_json

PROTOCOL = ROOT / "docs/performance_recovery/AUTONOMOUS_LOOP_PROTOCOL.json"
SCOPES = ("validation", *SOURCES)


def settings():
    return json.loads(PROTOCOL.read_bytes())


class Specialist(torch.nn.Module):
    def __init__(self, width, arm):
        super().__init__()
        self.arm = arm
        self.conv = None
        if arm == "conduction":
            self.conv = torch.nn.Sequential(torch.nn.Conv1d(2, 12, 17, padding=8), torch.nn.SiLU(),
                                            torch.nn.Conv1d(12, 12, 33, padding=16), torch.nn.SiLU(),
                                            torch.nn.AdaptiveAvgPool1d(1), torch.nn.Flatten())
            width += 12
        if arm == "rr_temporal":
            width += 4
        self.head = (torch.nn.Linear(width, 1) if arm in {"linear", "shared_gain", "balanced"} else
                     torch.nn.Sequential(torch.nn.Linear(width, 48), torch.nn.SiLU(), torch.nn.Linear(48, 1)))

    def forward(self, features, wave=None, rr=None):
        if self.conv is not None:
            features = torch.cat((features, self.conv(wave[:, [1, 7]])), 1)
        if self.arm == "rr_temporal":
            features = torch.cat((features, rr / rr.new_tensor([100., 1., 1., 1.])), 1)
        return self.head(features).flatten()


def score_anchor(rows, endpoint, policy):
    use = rows["labels"][:, endpoint] >= 0
    p = rows["p"][use, endpoint]
    return measure(rows["labels"][use, endpoint], p, transform(p, policy["maps"][endpoint]), policy["cuts"][endpoint])


class Runner:
    def __init__(self, previous, archive):
        self.previous, self.archive = previous, archive
        self.c = settings()
        self.data = {s: load_score(archive, s) for s in ("calibration", *SCOPES)}
        self.baseline = json.loads((archive / "DEVELOPMENT_SCORING_RECEIPT.json").read_bytes())
        self.policy = {"cuts": config()["incumbent_thresholds"], "maps": [{"kind": "identity"}] * 5}
        self.initial_summary, _, _ = summarize(self.data["validation"], self.data["validation"]["p"],
                                               self.policy, self.baseline, {"ece": 1., "brier_score": 1.})
        self.cache = {}
        self.cache_context = None

    def bank(self, scope, normalizer):
        if scope == "chapman_train":
            return get_other(self.previous, "chapman_shaoxing", "train", normalizer)
        if scope in SOURCES:
            return get_other(self.previous, *SOURCES[scope], normalizer)
        return get_code(self.previous, scope, normalizer)

    def features(self, scope, normalizer, seed, model):
        key = (scope, normalizer, seed)
        if key in self.cache:
            return self.cache[key]
        result = []
        with torch.no_grad():
            for wave, desc, label, weight, exams, group in batches(self.bank(scope, normalizer), 64):
                x, d = (torch.as_tensor(z, device="cuda") for z in (wave, desc))
                feat = model.backbone.forward_features(x)
                length = feat.new_zeros((len(wave), 2))
                length[:, int(wave.shape[-1] == 1250)] = 1
                raw = model.head(torch.cat((feat, d, length), 1)).sigmoid()
                result.append((feat.cpu().numpy(), raw.cpu().numpy(), wave, label, weight, exams, group))
        self.cache[key] = result
        return result

    def fit(self, path, endpoint, arm, seed, anchor, job):
        c = self.c
        j = config()["endpoints"].index(endpoint)
        hp = c["optimization"]
        torch.manual_seed(seed)
        rng = np.random.default_rng(seed)
        norm = "robust_shared_gain" if arm == "shared_gain" else "per_lead_zscore"
        if (seed, norm) != self.cache_context:
            self.cache.clear()
            self.cache_context = seed, norm
        model = parent_model(self.previous, seed).cuda().eval().requires_grad_(False)
        special = Specialist(model.backbone.d_model, arm).cuda()
        late = arm == "late"
        if late:
            for name, param in model.backbone.named_parameters():
                param.requires_grad_(name.startswith(("transformer.layers.8.", "final_norm.", "res_layers.5.")))
        parameters = [p for p in model.parameters() if p.requires_grad]
        optim = torch.optim.AdamW([{"params": special.parameters(), "lr": hp["readout_lr"]},
                                   {"params": parameters, "lr": hp["backbone_lr"]}], weight_decay=hp["weight_decay"])
        rr = {s: aux_data(self.archive, s)[0] for s in ("train", "calibration", *SCOPES)} if arm == "rr_temporal" else {}
        train_scopes = ("train", "chapman_train") if arm == "balanced" else ("train",)
        # Reserve provider groups from Chapman training, never validation, for the source-specific mapping.
        source_fit = self.features("chapman_train", norm, seed, model) if arm == "shared_gain" else []

        def one(row, scope):
            feat, old, wave, y, weights, exams, _ = row
            xx = torch.as_tensor(wave, device="cuda") if late or arm == "conduction" else None
            x = model.backbone.forward_features(xx) if late else torch.as_tensor(feat, device="cuda")
            proxy = torch.as_tensor(np.asarray([rr[scope][str(k)] for k in exams]), device="cuda") if rr else None
            z = special(x, xx, proxy)
            if arm in {"residual", "late"}:
                z = z + torch.logit(torch.as_tensor(old[:, j], device="cuda").clamp(1e-6, 1 - 1e-6))
            return z, torch.as_tensor(y[:, j], device="cuda"), torch.as_tensor(weights, device="cuda"), old[:, j]

        def predict(scope):
            rows = self.features(scope, norm, seed, model)
            with torch.no_grad():
                p = np.concatenate([one(row, scope)[0].sigmoid().cpu().numpy() for row in rows])
            truth = np.concatenate([row[3] for row in rows])
            info = {k: np.concatenate([row[i] for row in rows]) for k, i in (("exams", 5), ("patients", 6))}
            info.update(labels=truth, durations=np.concatenate([np.full(len(r[3]), r[2].shape[-1]) for r in rows]))
            if scope in self.data:
                aligned({**info, "p": p}, self.data[scope])
            return p, truth[:, j], info["patients"]

        base = {s: anchor["scores"][s].copy() for s in ("calibration", *SCOPES)}
        train = {s: self.features(s, norm, seed, model) for s in train_scopes}
        prevalence = {s: np.concatenate([r[3][:, j] for r in rows]) for s, rows in train.items()}
        weights = {s: float(np.sqrt((y == 0).sum() / (y == 1).sum()).clip(1, 12)) for s, y in prevalence.items()}
        best, history, anchor_weights = None, [], [p.detach().clone() for p in parameters]
        for epoch in range(1, c["epochs"]["late" if late else "readout"] + 1):
            order = [(s, i) for s, rows in train.items() for i in range(len(rows))]
            if arm == "balanced":
                external = [("chapman_train", i) for i in rng.choice(
                    len(train["chapman_train"]), size=len(train["train"]), replace=True)]
                order = [item for item in order if item[0] == "train"] + external
            rng.shuffle(order)
            losses = []
            for s, i in order:
                optim.zero_grad(set_to_none=True)
                z, y, w, p = one(train[s][i], s)
                keep = y >= 0
                if not bool(keep.any()):
                    continue
                ref = torch.as_tensor(p, device="cuda")
                hard = ((y == 1) & (ref < config()["incumbent_thresholds"][j]) if arm == "hard_positive" else
                        (y == 0) & (ref >= config()["incumbent_thresholds"][j]) if arm == "hard_negative" else
                        torch.zeros_like(keep))
                if arm in {"hard_positive", "hard_negative"}:
                    w = w * torch.where(hard, hp["hard_multiplier"], 1.)
                loss = (F.binary_cross_entropy_with_logits(z[keep], y[keep], reduction="none",
                        pos_weight=z.new_tensor(weights[s])) * w[keep]).sum() / w[keep].sum()
                if parameters:
                    loss += hp["anchor"] * torch.stack([(p - q).square().mean()
                                                        for p, q in zip(parameters, anchor_weights, strict=True)]).mean()
                loss.backward()
                torch.nn.utils.clip_grad_norm_([*special.parameters(), *parameters], 1., error_if_nonfinite=True)
                optim.step()
                losses.append(float(loss.detach()))
            v = base["validation"].copy()
            v[:, j] = predict("validation")[0]
            metrics = oof(self.data["validation"], v, self.baseline)
            rank = (*metrics[:2], -metrics[2], -metrics[3])
            history.append({"epoch": epoch, "loss": float(np.mean(losses)), "oof": metrics})
            if best is None or rank < best[0]:
                best = rank, epoch
                checkpoint = {"readout": special.state_dict(), "protocol_sha256": digest(PROTOCOL),
                              "endpoint": endpoint, "arm": arm, "seed": seed,
                              "ancestor_checkpoint_sha256": anchor["checkpoint_sha256"], "epoch": epoch,
                              "backbone_updates": {name: param.detach() for name, param in model.backbone.named_parameters()
                                                   if param.requires_grad}}
                torch.save(checkpoint, path / "best.pt")
            if epoch - best[1] >= c["epochs"]["patience"]:
                break
        ck = torch.load(path / "best.pt", map_location="cuda", weights_only=True)
        special.load_state_dict(ck["readout"], strict=True)
        with torch.no_grad():
            for name, p in model.backbone.named_parameters():
                if name in ck["backbone_updates"]:
                    p.copy_(ck["backbone_updates"][name])
        for scope in base:
            base[scope][:, j] = predict(scope)[0]
        policy = calibrate(self.data["calibration"], base["calibration"], self.baseline)
        for k in range(5):
            if k != j:
                policy["cuts"][k], policy["maps"][k] = anchor["policy"]["cuts"][k], anchor["policy"]["maps"][k]
        chapman_policy = json.loads(json.dumps(policy))
        for k in range(5):
            if k != j:
                chapman_policy["cuts"][k] = anchor["chapman_policy"]["cuts"][k]
                chapman_policy["maps"][k] = anchor["chapman_policy"]["maps"][k]
        if source_fit:
            p, y, group = predict("chapman_train")
            keep = np.asarray([int.from_bytes(hashlib.sha256(str(g).encode()).digest()[:4], "big") % 3 == 0
                               for g in group]) & (y >= 0)
            if set(y[keep]) == {0, 1}:
                chapman_policy["cuts"][j] = choose_cut(y[keep], p[keep], {"ppv_min": .30, "sensitivity_min": .60})["threshold"]
                chapman_policy["maps"][j] = fit_map(y[keep], p[keep], "platt")
        summary, guards, calib_ok = summarize(self.data["validation"], base["validation"], policy, self.baseline,
                                               self.initial_summary)
        points, source_summary = [], {}
        for scope in SCOPES:
            use_policy = chapman_policy if scope == "chapman" else policy
            for k, name in enumerate(config()["endpoints"]):
                row = {**self.data[scope], "p": base[scope]}
                if set(row["labels"][row["labels"][:, k] >= 0, k]) != {0, 1}:
                    continue
                m = score_anchor(row, k, use_policy)
                points.append({"scope": scope, "endpoint": name, **{x: m[x] for x in (
                    "tp", "tn", "fp", "fn", "recall", "precision", "f1", "average_precision", "brier_score", "ece")}})
            source_summary[scope] = float(np.mean([r["f1"] for r in points if r["scope"] == scope]))
        np.savez_compressed(path / "private_scores.npz", **base)
        result = {"endpoint": endpoint, "arm": arm, "seed": seed, "job": job, "epoch": best[1], "history": history,
                  "trainable": sum(p.numel() for p in [*special.parameters(), *parameters]),
                  "checkpoint_sha256": digest(path / "best.pt"), "scores_sha256": digest(path / "private_scores.npz"),
                  "policy": policy, "chapman_policy": chapman_policy, "points": points, "sources": source_summary,
                  "summary": summary, "guards": guards, "calibration_guard": calib_ok, "test_opened": False,
                  "parent_sha256": config()["parent_checkpoints"][str(seed)],
                  "anchor_sha256": anchor["checkpoint_sha256"], "protocol_sha256": digest(PROTOCOL)}
        write_json(path / "fit.json", result)
        return result


def read_fit(path: Path):
    r = json.loads((path / "fit.json").read_bytes())
    if (r["checkpoint_sha256"] != digest(path / "best.pt") or r["scores_sha256"] != digest(path / "private_scores.npz")
            or r["protocol_sha256"] != digest(PROTOCOL) or r["test_opened"]):
        raise ValueError("loop fit seal mismatch")
    return r
