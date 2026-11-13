"""Read immutable Git objects and archival evidence; publish only hashes and aggregates."""
import argparse
import csv
import hashlib
import io
import json
import re
import statistics
import subprocess
import tarfile
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from posixpath import normpath
from urllib.parse import unquote

MAIN = "6f50a6337fc3e8b518655b05916ced7447598b47"
PR15 = "732ecb1c8e697997cdedf85f67db70d38bd765ed"
PR11 = "2d1f8432177835e189cfa769e7880d4f0165cdcb"
PR16 = "8a2d8aab60f9d017ce515847bfa96c8de97ce565"
ROOT = Path(__file__).resolve().parents[2]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, obj):
    path.write_bytes((json.dumps(obj, indent=2, ensure_ascii=True, sort_keys=True) + "\n").encode())


def write_csv(path, rows, fields=None):
    with path.open("w", encoding="utf-8", newline="") as stream:
        w = csv.DictWriter(stream, fieldnames=fields or list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def snapshot(ref):
    with tarfile.open(fileobj=io.BytesIO(git("archive", ref))) as archive:
        return {m.name: archive.extractfile(m).read() for m in archive if m.isfile()}


def add(rows, sha, size, source, locator, kind, status, experiment="", commit="", job="", note=""):
    rows.append(dict(artifact_id="sha256:"+sha, bytes=size, source=source, locator=locator,
                     type=kind, verification=status, experiment_id=experiment, commit=commit, job=job, limits=note))


def archive_members(raw, locator, rows, disclose, source):
    try:
        archive = zipfile.ZipFile(io.BytesIO(raw))
    except zipfile.BadZipFile:
        return {"status": "INVALID_ZIP"}
    with archive:
        names = [m.filename for m in archive.infolist() if not m.is_dir()]
        if len(names) != len(set(names)):
            raise ValueError("duplicate ZIP member")
        members, manifests = {}, {}
        for name in names:
            if name.startswith(("/", "\\")) or ".." in Path(name.replace("\\", "/")).parts:
                raise ValueError("unsafe ZIP member")
            data = archive.read(name)
            sha = digest(data)
            members[name] = sha
            if Path(name).name.upper() in {"SHA256SUMS", "SHA256SUMS.TXT"}:
                manifests[name] = data.decode("utf-8-sig")
            suffix = Path(name).suffix.lower()
            identity = name if disclose else "member:"+digest(name.encode())
            add(rows, sha, len(data), source, locator+"!"+identity, suffix or "file", "BYTE_VERIFIED",
                note="CRC checked; membership does not authenticate producing execution")
        checks, unmatched = 0, 0
        for manifest, body in manifests.items():
            parent = str(Path(manifest).parent).replace("\\", "/")
            for line in body.splitlines():
                m = re.fullmatch(r"([0-9a-fA-F]{64})\s+[*]?(.*)", line)
                if not m:
                    continue
                target = m[2].removeprefix("./")
                options = (target, f"{parent}/{target}")
                matching = next((members[x] for x in options if x in members), None)
                if matching == m[1].lower():
                    checks += 1
                else:
                    unmatched += 1
        return {"status": "CRC_OK", "members": len(names), "internal_sha_matches": checks,
                "internal_sha_missing_or_mismatch": unmatched}


def git_history_blobs(heads, known, rows):
    objects = git("rev-list", "--objects", *heads).decode().splitlines()
    ids = [line.split()[0] for line in objects]
    format_ = "%(objectname) %(objecttype) %(objectsize)"
    desc = subprocess.run(["git", "cat-file", "--batch-check="+format_], cwd=ROOT,
                          input=("\n".join(ids)+"\n").encode(), capture_output=True, check=True).stdout
    blobs = [(oid, int(size)) for oid, typ, size in (line.split() for line in desc.decode().splitlines())
             if typ == "blob" and oid not in known]
    with subprocess.Popen(["git", "cat-file", "--batch"], cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE) as proc:
        for oid, expected in blobs:
            proc.stdin.write((oid+"\n").encode())
            proc.stdin.flush()
            header = proc.stdout.readline().decode().split()
            if header != [oid, "blob", str(expected)]:
                raise ValueError("Git object metadata differs")
            h = hashlib.sha256()
            left = expected
            while left:
                chunk = proc.stdout.read(min(left, 1024 * 1024))
                if not chunk:
                    raise ValueError("truncated Git object")
                h.update(chunk)
                left -= len(chunk)
            if proc.stdout.read(1) != b"\n":
                raise ValueError("missing Git object separator")
            add(rows, h.hexdigest(), expected, "GIT_HISTORY", "blob:"+oid, "historical_blob",
                "GIT_CONTENT_VERIFIED", note="Object bytes verified; individual experiment binding not inferred")
        proc.stdin.close()
        if proc.wait():
            raise ValueError("git cat-file failed")
    return len(blobs)


def metrics(main, optuna):
    out = []
    p = "outputs/results/external_dev/evidence/"
    profile = json.loads(main["outputs/results/primary/canonical_profiles.json"])["profiles"]

    def add_metric(exp, endpoint, metric, got, reported, files, n, unit, tol=1e-10):
        out.append(dict(experiment_id=exp, endpoint=endpoint, metric=metric, denominator=n, unit=unit,
                        recomputed=got, reported=reported if reported is not None else "",
                        status=("REPRODUCED_INDEPENDENTLY" if abs(got-reported) <= tol else "CONTRADICTED")
                        if got is not None and reported is not None else "DERIVED_FROM_VERIFIED_INPUT",
                        artifact_ids=";".join("sha256:"+digest(main[f]) for f in files)))

    def rows(name):
        return list(csv.DictReader(io.StringIO(main[name].decode("utf-8-sig"))))

    def binary(y, c, s):
        tp = sum(a and b for a, b in zip(y, c, strict=True))
        fp = sum(not a and b for a, b in zip(y, c, strict=True))
        fn = sum(a and not b for a, b in zip(y, c, strict=True))
        tn = len(y)-tp-fp-fn
        divide = lambda a, b: a/b if b else None  # noqa: E731
        recall, spec = divide(tp, tp+fn), divide(tn, tn+fp)
        order = sorted(zip(s, y, strict=True), reverse=True)
        ap, auc, t, f, last = 0.0, 0.0, 0, 0, 0
        bins = defaultdict(list)
        for prob, truth in order:
            bins[min(9, int(prob*10))].append((prob, truth))
        while last < len(order):
            i = last+1
            while i < len(order) and order[i][0] == order[last][0]:
                i += 1
            pos = sum(v[1] for v in order[last:i])
            neg = i-last-pos
            auc += neg*(t+pos/2)
            t, f, last = t+pos, f+neg, i
            ap += (pos/(tp+fn))*(t/(t+f)) if tp+fn else 0
        return {"tp": tp, "tn": tn, "fp": fp, "fn": fn, "accuracy": (tp+tn)/len(y),
                "balanced_accuracy": (recall+spec)/2 if recall is not None and spec is not None else None,
                "precision": divide(tp, tp+fp), "recall": recall, "specificity": spec,
                "npv": divide(tn, tn+fn), "f1": divide(2*tp, 2*tp+fp+fn),
                "auroc": divide(auc, (tp+fn)*(tn+fp)), "average_precision": ap if tp+fn else None,
                "brier": statistics.mean((x-z)**2 for x, z in zip(s, y, strict=True)),
                "ece10": sum(abs(sum(x-z for x, z in v)) for v in bins.values())/len(y)}

    for exp, label, definition in (("RELEASE-P6", "primary6", profile[1]), ("RELEASE-P8", "primary8", profile[0])):
        pred = p+f"rhythm_{label}_record_predictions.csv"
        summary = f"outputs/results/external_dev/rhythm_{label}_metrics.json"
        data, reported = rows(pred), json.loads(main[summary])
        cuts = dict(zip(reported["classes"], reported["thresholds"], strict=True))
        truth = [set(r["true_labels" if label == "primary6" else "accepted_labels"].split("|")) for r in data]
        correct = [r["pred_label" if label == "primary6" else "predicted_label"] in y
                   for y, r in zip(truth, data, strict=True)]
        prefix = "prob_" if label == "primary6" else "membership_prob_"
        no_cut = [not any(float(r[prefix+c]) >= cuts[c] for c in cuts) for r in data]
        add_metric(exp, "ALL", "top1_accuracy", sum(correct)/len(data), definition["accuracy"],
                   [pred, summary], len(data), "selected ECG")
        for key, got, expected in (("no_score_over_threshold", sum(no_cut), 79 if label=="primary6" else 58),
                                    ("no_threshold_top1_correct", sum(x and y for x, y in zip(correct, no_cut, strict=True)),
                                     64 if label=="primary6" else 22)):
            add_metric(exp, "ALL", key, got, expected, [pred, summary], len(data), "selected ECG")
        macro = []
        all_counts = Counter()
        for c in cuts:
            scores = [float(r[prefix+c]) for r in data]
            y = [r["truth_"+c] == "True" for r in data] if label == "primary6" else [c in t for t in truth]
            calls = ([r["threshold_pass_"+c] == "True" for r in data] if label == "primary6" else
                     [c in r["predicted_labels"].split("|") for r in data])
            got = binary(y, calls, scores)
            panel = reported["panels"][c]
            macro.append(got["f1"])
            all_counts.update({k: got[k] for k in ("tp", "fp", "fn", "tn")})
            for k, v in got.items():
                add_metric(exp, c, k, v, panel.get(k) if k in {"tp","fp","fn","tn","f1","accuracy","precision","recall","specificity"} else None,
                           [pred, summary], len(data), "known binary opportunity")
        add_metric(exp, "ALL", "macro_f1", statistics.mean(macro), definition["macro_f1"], [pred, summary], len(data), "selected ECG")
        add_metric(exp, "ALL", "micro_f1", 2*all_counts["tp"]/(2*all_counts["tp"]+all_counts["fp"]+all_counts["fn"]),
                   None, [pred, summary], len(data)*len(cuts), "known binary opportunity")
    summary = "outputs/results/external_dev/pathology_primary4_metrics.json"
    reported = json.loads(main[summary])
    panels, ids, paths = [], set(), []
    for c in reported["classes"]:
        pred = p+f"pathology_primary4_{c}_record_predictions.csv"
        paths.append(pred)
        data = rows(pred)
        ids.update(r["record_base"] for r in data)
        s = [float(r["probability"]) for r in data]
        got = binary([int(r["target"]) for r in data], [v >= float(r["threshold"]) for v, r in zip(s,data,strict=True)], s)
        panels.append((len(data), got))
        for key, value in got.items():
            add_metric("RELEASE-P4", c, key, value, reported.get("panels", {}).get(c, {}).get(key),
                       [pred, summary], len(data), "selected panel observation")
    for key, x, y in (("panel_rows", sum(n for n,_ in panels), 962), ("unique_ecg", len(ids), 733),
                      ("macro_f1", statistics.mean(r["f1"] for _,r in panels), profile[2]["macro_f1"]),
                      ("mean_panel_accuracy", statistics.mean(r["accuracy"] for _,r in panels), profile[2]["accuracy"])):
        add_metric("RELEASE-P4", "ALL", key, x, y, [*paths, summary], sum(n for n,_ in panels), "panel observations")
    if optuna:
        sha, entries = optuna
        for trial, values, expected in entries:
            value = statistics.mean(values)-.25*statistics.pstdev(values)
            out.append(dict(experiment_id="HIST-V3C", endpoint=f"trial-{trial}", metric="tail_ranking",
                            denominator=3, unit="archived tail epochs", recomputed=value, reported=expected,
                            status="REPRODUCED_INDEPENDENTLY" if abs(value-expected)<1e-12 else "CONTRADICTED",
                            artifact_ids="sha256:"+sha))
    base = "outputs/results/reviewer_two_comment_rigorous/"
    route_file = base+"R2_4K_COVERAGE_RISK_AND_FALSE_NEGATIVES.json"
    route = json.loads(main[route_file])
    for source, group in route["cohorts"].items():
        no = group["rules"]["no_abstention"]
        joint = group["rules"]["frozen_joint"]
        for method, record in (("all",no),("accepted",joint)):
            errs = sum(e["fp"]+e["fn_emitted"] for e in record["endpoints"].values())
            known = sum(sum(e[k] for k in ("tp","tn","fp","fn_emitted")) for e in record["endpoints"].values())
            add_metric("ABSTENTION",source,method+"_risk_from_counts",errs/known,record["accepted_risk"],
                       [route_file],known,"known ECG-endpoint")
        denom = no["known_emitted"]
        for cost, value in joint["full_scored_cost"].items():
            loss = (joint["emitted_errors"]+float(cost)*(denom-joint["known_emitted"]))/denom
            add_metric("ABSTENTION",source,"joint_cost_"+cost,loss,value,[route_file],denom,"known ECG-endpoint")
    fallback_file = base+"RUNTIME_AND_CASCADE_AGGREGATE.json"
    fallback = json.loads(main[fallback_file])["fallback"]
    for key in ("known_total","corrected","introduced","positive_unresolved","final_false_negatives"):
        value = sum(row.get(key,0) for row in fallback["endpoint_accounting"].values())
        add_metric("CASCADE-P6","LUDB",key,value,fallback["totals"][key],[fallback_file],
                   fallback["totals"]["known_total"],"known ECG-endpoint")
    morph_file = base+"R2_3F_ABLATION_CONFIRMATORY_RESULTS.json"
    ablation = json.loads(main[morph_file])
    for name, group in ablation["profiles"].items():
        deltas = []
        for seed in ablation["seeds"]:
            total = []
            for arm in ("with_morphology","without_morphology"):
                endpoint = []
                for e in group["endpoints"].values():
                    if e["status"] != "evaluated":
                        continue
                    row = e["seeds"][str(seed)][arm]
                    d = 2*row["tp"]+row["fp"]+row["fn"]
                    endpoint.append(2*row["tp"]/d if d else 0)
                total.append(statistics.mean(endpoint))
            deltas.append(total[0]-total[1])
        add_metric("MORPH-ROBUST",name,"mean_seed_macro_f1_delta",statistics.mean(deltas),
                   group["contrast"]["with_minus_without"],[morph_file],len(deltas),"paired seeds")
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--native", type=Path, action="append", default=[])
    p.add_argument("--local-zip", action="append", type=Path, default=[])
    p.add_argument("--archived-v3c", type=Path, help="Hash-authenticated recovered historical JSON")
    p.add_argument("--github", type=Path, help="Sanitized GitHub PR and release metadata snapshot")
    p.add_argument("--local-v3f", type=Path, help="Optional authorized copy of the public V3F release weight")
    p.add_argument("--native-release-smoke", type=Path)
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    main, pr15, pr16 = snapshot(MAIN), snapshot(PR15), snapshot(PR16)
    github = json.loads(a.github.read_bytes()) if a.github else {}
    pr_delta = set(git("diff", "--name-only", PR11, PR15).decode().splitlines())
    ledger, archives = [], []
    links = []
    pr16_delta = set(git("diff","--name-only",PR15,PR16).decode().splitlines())
    for ref, source, tree, delta in ((MAIN, "GIT_MAIN", main, set(main)),
                                     (PR15, "GIT_PR15_DELTA", pr15, pr_delta),
                                     (PR16, "GIT_PR16_DELTA", pr16, pr16_delta)):
        for path, raw in tree.items():
            if path not in delta:
                continue
            add(ledger, digest(raw), len(raw), source, path, Path(path).suffix.lower() or "file",
                "GIT_CONTENT_VERIFIED", commit=ref)
            if path.endswith(".zip"):
                archives.append({"artifact_id":"sha256:"+digest(raw), **archive_members(raw,path,ledger,True,source)})
            if source == "GIT_MAIN" and path.startswith("docs/") and path.endswith(".md"):
                prose = re.sub(r"```.*?```", "", raw.decode("utf-8-sig"), flags=re.S)
                for match in re.finditer(r"\]\(([^\s)]+)\)", prose):
                    target = unquote(match[1].split("#",1)[0])
                    if target and "://" not in target and not target.startswith("mailto:"):
                        normalized = normpath(str(Path(path).parent.as_posix())+"/"+target)
                        if normalized not in main and not any(x.startswith(normalized+"/") for x in main):
                            links.append({"artifact_id":"sha256:"+digest(raw),"file":path,"target":target})
    known = {line.split()[2] for ref in (MAIN, PR15, PR16)
             for line in git("ls-tree", "-r", ref).decode().splitlines() if " blob " in line}
    extra = sorted({oid for p in github.get("prs",[]) for oid in
                    [p["headRefOid"], (p.get("mergeCommit") or {}).get("oid")] if oid})
    history_n = git_history_blobs([MAIN, PR15, PR16, *extra], known, ledger)
    for i,path in enumerate(a.local_zip,1):
        raw = path.read_bytes()
        locator = f"local-recovery-{i:02d}"
        add(ledger,digest(raw),len(raw),"LOCAL_RESTRICTED_ZIP",locator,"zip","BYTE_VERIFIED",
            note="Source archive remains local and is not included")
        archives.append({"artifact_id":"sha256:"+digest(raw),**archive_members(raw,locator,ledger,False,"LOCAL_RESTRICTED_ZIP")})
    native = {"artifacts":[],"scheduler":[],"roots":{},"read_failures":[],"receipt_ids":[]}
    for receipt in a.native:
        raw = receipt.read_bytes()
        obj = json.loads(raw)
        if obj["restricted_paths_or_rows_exported"] is not False:
            raise ValueError("unexpected native export scope")
        native["receipt_ids"].append("sha256:"+digest(raw))
        native["roots"].update(obj["roots"])
        for key in ("artifacts","scheduler","read_failures"):
            native[key].extend(obj[key])
    native["scheduler"] = list({r["job"]:r for r in native["scheduler"]}.values())
    release = json.loads(main["release-manifest.json"])["assets"]
    matches = defaultdict(set)
    for item in native["artifacts"]:
        add(ledger,item["sha256"],item["bytes"],"CEDIA:"+item["source"],
            "locator-sha256:"+item["locator_sha256"],item["format"],"BYTE_VERIFIED",
            note="Contents hashed; filename and path not exported; job hint not producer")
        if item["release_name"]:
            matches[item["release_name"]].add((item["sha256"],item["bytes"]))
    if a.native_release_smoke:
        raw = a.native_release_smoke.read_bytes()
        smoke = json.loads(raw)
        if smoke["model_inference_performed"] or len(smoke["assets"]) != 5:
            raise ValueError("release smoke contract differs")
        for x in smoke["assets"]:
            if not x["weights_only_load"] or (x["sha256"],x["bytes"]) not in matches[x["name"]]:
                raise ValueError("release smoke and native inventory disagree")
        add(ledger,digest(raw),len(raw),"CEDIA_RECEIPT","33847-weights-only-release-smoke","json","RECEIPT_VERIFIED",
            experiment="RELEASE-ASSETS",job="33847")
    for item in release:
        expected = (item["sha256"], item["bytes"])
        actual = matches[item["name"]]
        status = "BYTE_VERIFIED" if expected in actual else "HASH_MISMATCH" if actual else "RELEASE_METADATA_ONLY"
        add(ledger,*expected,"RELEASE_MANIFEST",item["name"],item["category"],status,
            experiment="RELEASE-ASSETS",commit=MAIN,note="Native copies compared to release declaration")
        entry = next((x for x in github.get("release_assets",[]) if x["name"]==item["name"]),None)
        if entry and (entry["digest"] != "sha256:"+expected[0] or entry["size"] != expected[1]):
            raise ValueError("GitHub release metadata disagrees with declared bytes")
    if a.local_v3f:
        h = hashlib.sha256()
        with a.local_v3f.open("rb") as f:
            for chunk in iter(lambda: f.read(4*1024*1024), b""):
                h.update(chunk)
        v3f = next(x for x in release if x["name"]=="backbone-v3f-original.pt")
        if (h.hexdigest(),a.local_v3f.stat().st_size)!=(v3f["sha256"],v3f["bytes"]):
            raise ValueError("local V3F differs from release")
        add(ledger,v3f["sha256"],v3f["bytes"],"LOCAL_RELEASE_COPY",v3f["name"],"model","BYTE_VERIFIED",
            experiment="RELEASE-ASSETS",note="Directly read local bytes, not job provenance")
    counts = Counter(row["artifact_id"] for row in ledger)
    for row in ledger:
        row["locations_of_same_content"] = counts[row["artifact_id"]]
    write_csv(a.out/"MASTER_ARTIFACT_SHA256_LEDGER.csv",ledger)
    archived = None
    if a.archived_v3c:
        raw = a.archived_v3c.read_bytes()
        sha = digest(raw)
        if sha != "42d4f46da9d8e8bb4983d3c753826b91a0164fb8553ebca292ada413d513349e":
            raise ValueError("historical V3C archive does not match historical SHA-256")
        obj = json.loads(raw)
        entries = [(r["trial_number"], r["tail_composite_scores"], r["ranking_score"])
                   for r in obj["top_candidates"]]
        if len(entries) != 9:
            raise ValueError("historical V3C snapshot is not the nine expected candidates")
        archived = (sha, entries)
        add(ledger,sha,len(raw),"LOCAL_HISTORICAL_COPY","v3c-summary-historical-digest",
            "json","BYTE_VERIFIED","HIST-V3C",note="Restored JSON matches historical local and CEDIA digest; not SQLite")
        counts = Counter(row["artifact_id"] for row in ledger)
        for row in ledger:
            row["locations_of_same_content"] = counts[row["artifact_id"]]
        write_csv(a.out/"MASTER_ARTIFACT_SHA256_LEDGER.csv",ledger)
    rows = metrics(main, archived)
    write_csv(a.out/"METRICS_INDEPENDENT_RECALCULATION.csv",rows)
    index = build_register(a.out, main, pr15, pr16, native)
    write_json(a.out/"POSTMERGE_VERIFICATION_RESULTS.json",{
        "main":MAIN,"tree":git("rev-parse",MAIN+"^{tree}").decode().strip(),"pr15":PR15,
        "pr15_payload_delta":git("diff","--name-status",PR11,PR15).decode().splitlines(),
        "pr15_payload_presence_in_main":{path:("absent" if path not in main else "identical" if
                                             main[path]==pr15[path] else "earlier_or_different") for path in sorted(pr_delta)},
        "first_parent_merges":git("log","--first-parent","--merges","--format=%H %P %s",MAIN).decode().splitlines(),
        "github":github,
        "main_files":len(main),"history_only_blobs":history_n,"locations":len(ledger),"content_identities":len(counts),
        "history_additional_pr_refs":extra,
        "duplicate_location_count":len(ledger)-len(counts),"empty_locations":sum(r["bytes"]==0 for r in ledger),
        "archives":archives,"native":{k:v for k,v in native.items() if k!="artifacts"},
        "native_checkpoint_locations":sum(x["checkpoint"] for x in native["artifacts"]),
        "native_checkpoint_unique":len({x["sha256"] for x in native["artifacts"] if x["checkpoint"]}),
        "metric_states":dict(Counter(r["status"] for r in rows)),
        "experiment_index":index,
        "local_link_candidates":links,
        "release_declared_assets":len(release),"release_native_exact_match":sum(
            (x["sha256"],x["bytes"]) in matches[x["name"]] for x in release),
    })


def build_register(out, main, pr15, pr16, native):
    anchors = json.loads((ROOT/"docs/postmerge_forensic/EXPERIMENT_ANCHORS.json").read_bytes())
    experiments, training, lineage = [], [], []
    observed = {r["sha256"]: r for r in native["artifacts"] if r["checkpoint"]}
    expected = set()

    def exp(eid, version, label, jobs, path, status, limit, ref=MAIN):
        tree = {MAIN:main,PR15:pr15,PR16:pr16}[ref]
        aid = "sha256:"+digest(tree[path]) if path in tree else ""
        experiments.append(dict(experiment_id=eid, version=version, experiment=label, job=jobs,
                                artifact_id=aid, locator=path, git_ref=ref, finding=status, chain_limit=limit))
        return aid

    def weight(eid, name, sha, parent="", job="", commit="", seed="", origin="receipt", detail=""):
        if sha:
            expected.add(sha)
        hit = observed.get(sha)
        lineage.append(dict(experiment_id=eid, name=name, artifact_id="sha256:"+sha if sha else "",
                            sha256=sha, bytes=hit["bytes"] if hit else "", parent_sha256=parent,
                            producer_job=job, code_commit=commit, seed=seed,
                            status="BYTE_VERIFIED" if hit else "RECEIPT_VERIFIED" if sha else "NOT_ACCESSIBLE",
                            binding_source=origin, limitations=detail))

    for eid, (version, label, jobs, path, status, limit) in anchors.items():
        ref = {"CORRECTIVE-PR15":PR15,"AUTONOMOUS-PR16":PR16}.get(eid,MAIN)
        exp(eid,version,label,jobs,path,status,limit,ref)
    for item in json.loads(main["release-manifest.json"])["assets"]:
        if item["category"] == "model":
            weight("RELEASE-ASSETS",item["name"],item["sha256"],origin="release manifest and CEDIA physical copy",
                   detail="Identity does not authenticate historical producing job or consumed training manifest")
    for eid, name, job in (("HIST-16768","titan_v4_final_best.pt","16768"),
                           ("HIST-V3F","historical job parent read digest","16781")):
        weight(eid,name,"",job=job,detail="No recovered content SHA or binding to the producing job")
    inputs = [
        ("ADAPT", "docs/domain_adaptation/evidence/TRAINING_EXPERIMENTS_COMPLETE.csv", main, MAIN),
        ("REC", "docs/performance_recovery/evidence/FINETUNING_EXPERIMENTS.csv", main, MAIN),
        ("CORR", "docs/performance_recovery/corrective_evidence/CORRECTIVE_FITS.json", pr15, PR15),
    ]
    accounting = {r["job"]:r for r in native["scheduler"]}
    for prefix,path,tree,ref in inputs:
        batch = json.loads(tree[path]) if path.endswith(".json") else list(csv.DictReader(io.StringIO(tree[path].decode())))
        for i,r in enumerate(batch,1):
            job = str(r.get("slurm_job",""))
            name = str(r.get("mode",r.get("arm",prefix)))
            eid = f"{prefix}-{i:02d}"
            aid = exp(eid,"V4.5",name,job,path,"VERIFIED_WITH_SCOPE_LIMITATION",
                      "Per-run report; calibration and evaluation depend on family protocol",ref)
            sha, parent = r.get("checkpoint_sha256",""),r.get("parent_sha256","")
            weight(eid,name,sha,parent,job,r.get("code_commit",""),r.get("seed",""),aid,
                   "Same SHA is not by itself proof of all data consumed")
            training.append(dict(experiment_id=eid, artifact_id=aid, job=job,
                                 state=accounting.get(job,{}).get("state","NOT_QUERIED_OR_STEP"),
                                 exit=accounting.get(job,{}).get("exit",""), code_commit=r.get("code_commit",""),
                                 seed=r.get("seed",""), checkpoint_id="sha256:"+sha if sha else "",
                                 parent_id="sha256:"+parent if parent else "", statement="effective training reported; no retraining"))
    for job,eid in (("16768","HIST-16768"),("16781","HIST-V3F")):
        a = next(x for x in experiments if x["experiment_id"]==eid)
        training.append(dict(experiment_id=eid,artifact_id=a["artifact_id"],job=job,
                             state=accounting.get(job,{}).get("state","NOT_QUERIED"),
                             exit=accounting.get(job,{}).get("exit",""),code_commit="",seed="",
                             checkpoint_id="",parent_id="",statement=a["chain_limit"]))
    for e in json.loads(main["docs/benchmarkmax/BENCHMARKMAX_EXPERIMENT_REGISTRY.json"])["experiments"]:
        location = e.get("artifact","")
        if not location or "://" in location:
            path = "docs/benchmarkmax/BENCHMARKMAX_EXPERIMENT_REGISTRY.json"
        else:
            path = normpath("docs/benchmarkmax/"+location)
        jobs = ";".join(map(str,e.get("cedia_jobs",[e.get("cedia_job","")])))
        exp("BM-"+e["id"],"V4.5 reference" if "V45" in e["id"] else "V4.6",e["id"],jobs,path,
            "RECEIPT_ONLY_VERIFICATION",e["status"])
    # One entry per result file not already given a more specific scientific anchor.
    anchored = {e["locator"] for e in experiments}
    for path in sorted(main):
        if path in anchored or not path.startswith("outputs/results/") or not path.endswith((".json",".csv")):
            continue
        match = re.search(r"(?:_|-)([123]\d{4})(?=[_.-])",path)
        exp("RESULT-"+digest(path.encode())[:12],"V4.6" if "/benchmarkmax/" in path else "V4.5",
            Path(path).stem,match[1] if match else "",path,"PARTIALLY_VERIFIED",
            "Artifact-level inventory; filename job is a hint, not producer proof; may duplicate another experiment")
    for sha, hit in sorted(observed.items()):
        if sha not in expected:
            weight("UNASSIGNED-CHECKPOINT",hit["source"],sha,origin="native CEDIA inventory",
                   detail="Physical bytes read; architecture, producing job and relationship to public metrics not authenticated")
    write_csv(out/"MASTER_EXPERIMENT_INVENTORY.csv",experiments)
    write_csv(out/"TRAINING_JOB_PROVENANCE_MATRIX.csv",training)
    write_csv(out/"CHECKPOINT_IDENTITY_AND_LINEAGE.csv",lineage)
    write_csv(out/"EXPERIMENT_TO_CLAIM_TRACEABILITY.csv",[
        dict(experiment_id=x["experiment_id"],artifact_id=x["artifact_id"],job=x["job"],
             result=x["experiment"],source=x["locator"],scope=x["chain_limit"],status=x["finding"])
        for x in experiments])
    claim_rows = [dict(claim_id="CLAIM-"+e["experiment_id"],**e) for e in experiments
                  if not e["experiment_id"].startswith("RESULT-")]
    write_csv(out/"SCIENTIFIC_CLAIM_VERIFICATION_MATRIX.csv",claim_rows)
    return {"entries":len(experiments),"family_or_run_rows":len(claim_rows),
            "catalog_only_rows":sum(x["experiment_id"].startswith("RESULT-") for x in experiments),
            "family_or_run_states":dict(Counter(x["finding"] for x in claim_rows)),
            "checkpoint_rows":len(lineage),"training_rows":len(training)}


if __name__ == "__main__":
    main()
