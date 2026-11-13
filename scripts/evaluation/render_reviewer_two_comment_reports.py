"""Render the scientific findings only after the native evidence passes readback."""
import argparse
import csv
from pathlib import Path

from verify_reviewer_two_comment_rigorous import (
    check_ablation,
    check_runtime,
    check_selective,
    load,
    require,
)


def pct(x):
    return "not estimable" if x is None else f"{100*x:.2f}%"


def pp(x):
    return f"{100*x:+.2f} pp"


def ci(bounds):
    return "not estimable" if not bounds else "["+", ".join(map(pp, bounds))+"]"


def write(root, name, lines):
    with (root / name).open("x", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines)+"\n")


def morphology(docs, m, r):
    fixture = r["fixture"]
    lines = [
        "# R2-3f: Final morphology validation", "",
        '> Figure 5 - What are the 10 morphology features and how are they calculated? Why there is an arrow going in the "Pathology specialist" but such arrow is not present for "Rhythm specialist". Check the arrows in all block-diagrams – are they necessary everywhere (do they show any relation between the blocks)? For example, what is the meaning of the arrows between the blocks in Figure 6?',
        "", "**IMPLEMENTATION_VERIFIED; EXPERIMENT_COMPLETED for the reconstructed candidate.**",
        "", f"CEDIA GPU job {r['job']} ran the hash-verified extractor, both backbones and all three specialists on {r['traced_ecgs']} label-blind selected LUDB ECGs. Both same-batch forwards agreed exactly on these inputs. This is a repeatability statement for the reconstructed configuration, not a historical reproduction guarantee.",
        "", "## Executed signal and tensor contract", "",
        "WFDB physical mV, canonical I, II, III, aVR, aVL, aVF, V1–V6, original 500 Hz. The executable trace checked a causal third-order Butterworth 0.5–45 Hz on nonconstant leads, polyphase 1:4 downsampling, the padded central ten seconds, per-lead z-score, and a 125 Hz morphology call. The independent fixture pipeline and actual preprocessor agreed within its fixed numeric check. Signal: 12×1250; lead mask: 12; morphology: 10. The extractor selects II when nonflat, otherwise the highest-variance lead. It thresholds median-centered magnitude at max(p88, mean + 0.8 SD) and enforces 0.28 s peak spacing.",
        "", "| Observed consumer | Input width | Morphology |", "| --- | ---: | --- |",
        "| Both V3F/V3AG backbones | 12×1250 + mask + 10 | Distinct auxiliary input |",
        "| Global rhythm, both backbones | 650 | Direct 640–649 (zero-based) |",
        "| Global pathology, both backbones | 640 | No morphology path; consumes the waveform/mask embedding |",
        "| P6 and P8 specialist | 681 | Direct 640–649 plus separate score/event fields |",
        "| P4 specialist | 670 | Direct 640–649 plus separate score fields |",
        "", f"Strict weight loading bound all five published artifacts to their SHA-256. Stored widths, not redundant metadata, govern loading (rhythm declared/stored: {r['architecture']['rhythm_width']}; P4 stored hidden width: {r['architecture']['p4_hidden_width']}). Both specialist arrows therefore denote direct feature input. The pathology specialist can additionally receive the indirect effect via global rhythm probabilities; the shared waveform/mask embedding and global pathology head do not consume the morphology vector. An arrow between blocks is justified only by a tensor or rule actually passed.",
        f"The loaded V3F and V3AG model objects each contained {r['architecture']['model_parameters']['V3F']:,} parameters including their global heads, before attaching the separate specialists. This is a direct runtime count for these two released assets, not a count for the different historical 41M experiments.",
        "", "## Ten formulas and numerical checks", "",
        "| Descriptor | Raw computation | Scale | Fixture observed |", "| --- | --- | ---: | ---: |",
    ]
    formulae = (
        ("hr_median_bpm", "60 / median positive RR in seconds", 220),
        ("rrv_cv", "population SD(RR) / mean(RR)", 1),
        ("rrv_rmssd_ms", "1,000 × RMS of successive RR differences", 500),
        ("qrs_width_proxy_ms", "median span above max(35% local maximum, p70) within ±0.18 s", 220),
        ("p_to_r_proxy_ms", "median lag to maximal pre-peak median-centered deflection 0.08–0.28 s before peak; retain 60–320 ms", 320),
        ("qrs_band_ratio", "5–18 Hz / total one-sided FFT power", 1),
        ("lowfreq_ratio", "0–0.7 Hz / total one-sided FFT power", 1),
        ("hf_ratio", "35 Hz–Nyquist / total one-sided FFT power", 1),
        ("lead_corr_abs_mean", "mean absolute off-diagonal Pearson r across nonflat leads", 1),
        ("limb_qrs_asymmetry", "(I−aVF) / max(I+aVF, 1e−12) in 5–18 Hz power", 1),
    )
    lines += [f"| {name} | {description} | {scale} | {fixture['observed'][name]:.7g} |"
              for name, description, scale in formulae]
    lines += [
        "", f"Ratios use mean power across leads unless indicated. Nonfinite samples are replaced with zero; nonfinite features default to zero, and normalized values clip to [0,1] (signed asymmetry [−1,1]) as float32. The pulse fixture found three expected peaks. **Detected failure mode:** the flat/invalid-sample fixture produced {fixture['flat_line_artifact']['peaks']} spurious plateau peaks, a nonzero heart-rate proxy and a nonzero P-to-R proxy. The formulas match controlled examples; they are not universally physiologically valid or validated interval measurements. No retrospective patch was applied.",
        "", "## New paired head training", "",
        f"CPU job {m['job']} fit five matched seeds per arm, same MLP size and same ECG masks. Both arms use fixed backbone representations. The 98.333% paired component intervals control the three primary profile contrasts; the minimum effect is ±2.00 points. The class-wise JSON includes sensitivity, specificity, AUROC, average precision, Brier, ECE, support, training time and per-seed results. File name notwithstanding, this study is **exploratory**, not confirmatory.",
        "", "| Profile | Endpoints evaluated | Mean Δ macro-F1 | Simultaneous interval | Interpretation | CPU fit seconds |",
        "| --- | ---: | ---: | --- | --- | ---: |",
    ]
    for profile, row in m["profiles"].items():
        c = row["contrast"]
        n = sum(x["status"] == "evaluated" for x in row["endpoints"].values())
        lines.append(f"| {profile} | {n}/{len(row['endpoints'])} | {pp(c['with_minus_without'])} | {ci(c['bounds'])} | {c['classification']} | {row['training_seconds']:.1f} |")
    lines += ["", "| Profile | Class | Held positive/negative | Mean paired Δ F1 | Range across seeds |",
              "| --- | --- | ---: | ---: | --- |"]
    for profile, row in m["profiles"].items():
        for label, e in row["endpoints"].items():
            sup = e["support"]["held"]
            diff = [x["with_morphology"]["f1"]-x["without_morphology"]["f1"] for x in e.get("seeds", {}).values()]
            effect = f"{pp(sum(diff)/len(diff))} | {ci([min(diff), max(diff)])}" if diff else "not estimable | not estimable"
            lines.append(f"| {profile} | {label} | {sup['positive']}/{sup['negative']} | {effect} |")
    lines += [
        "", "Ranges are training variability, not confidence intervals. Endpoint contrasts are descriptive and rare classes can have large instability; no class-wise significance claims are made. This is not a full-network retraining experiment, an effect on the released weights, or proof of transfer to a new source. Same-target cross-source transport and verified patient independence for Chapman are not established.",
        "", "The PR #9 P8 linear-head estimate was +1.46 pp, exploratory IC95% [+0.16,+2.76] pp, post-hoc Holm p=0.1356. It is a prior study on inspected data, not another independent replication sample. The new comparisons, including adverse effects, are reported without replacing the earlier results.",
        "", "## Fixed-input perturbations", "",
        f"Runtime: {r['gpu']}; PyTorch {r['torch']}, CUDA {r['cuda']}, NumPy {r['numpy']}, SciPy {r['scipy']}. Below are maximum absolute differences versus the reconstructed same-batch reference, not differences versus June output.",
        "", "| Perturbation | P6 logit | P8 logit | P4 probability | P4 > 1e−5 |", "| --- | ---: | ---: | ---: | ---: |",
    ]
    for name, effect in r["effects_rhythm_logits_pathology_probabilities"].items():
        lines.append(f"| {name} | {effect['P6']['max_abs']:.7g} | {effect['P8']['max_abs']:.7g} | {effect['P4']['max_abs']:.7g} | {effect['P4']['p4_outside_unchanged_tolerance']} |")
    lines += [
        "", "**Historical inference:** [root-cause report](R2_3F_HISTORICAL_REPLAY_ROOT_CAUSE.md). Exact June input and loader identity are not demonstrated. The new instrumented job does not erase the 836/962 out-of-tolerance historical P4 comparisons.",
    ]
    write(docs, "R2_3F_MORPHOLOGY_FINAL_VALIDATION.md", lines)


def selective(docs, s):
    lines = [
        "# R2-4k: Selective prediction utility", "",
        '> How are estimated “Quarantine Rate”, “Pre-Quarantine Accuracy”, “Pre-Quarantine Accuracy”? Explain this in the methodology section.',
        "", f"**IMPLEMENTATION_VERIFIED; EXPERIMENT_COMPLETED for the new policy.** CEDIA job {s['job']} recomputed every native route from scores and frozen class thresholds; no reference enters the per-ECG decision. P8/P4 cuts are {s['cutoffs']['P8']:.9f}/{s['cutoffs']['P4']:.9f}. The two cuts were fitted to coverage on separate SPH components, not on LUDB or on held reference values. The primary emits both original outputs if both score and both margins meet their cutoffs; otherwise it emits neither. Technical inability to score is distinct from abstention.",
        "", "Historical June disposition: **WITHDRAW_HISTORICAL_CLAIM**. These are November score-only decisions, not an original quarantine estimate, human review or clinical referral. The reviewer's repeated term is quoted as written; we do not assume that a missing historical post-quarantine result exists.",
        "", "## Utility on fixed denominators", "",
        "Coverage is accepted/scored ECGs, also reported against all enrolled ECGs. Baseline and accepted risk are membership FP+FN per known ECG–endpoint opportunity, not multiclass ECG accuracy. Withheld risk uses the same original predictions counterfactually; withheld positives are neither emitted FN nor TP. Reported PPV/NPV are only for observed source references; a missing LUDB statement is not a negative. SPH mapped absence is not independent clinical adjudication.",
        "", "| Cohort | Rule | Accepted/scored ECGs | Known emitted | Accepted risk | Withheld risk | Withheld positives |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for cohort, data in s["cohorts"].items():
        for name, r in data["rules"].items():
            lines.append(f"| {cohort} | {name} | {r['accepted']:.0f}/{data['scored_ecgs']} | {r['known_emitted']:.1f} | {pct(r['accepted_risk'])} | {pct(r['withheld_risk'])} | {r['withheld_positive']:.1f} |")
    lines += ["", "Random results are expectations, hence fractional opportunities. Primary paired contrasts use patient/exact-waveform components and a conservative 98.75% interval across two contrasts and two cohorts. The random expected risk equals the all-scored risk; the two primary comparisons have identical risk estimates under that definition.", ""]
    for cohort, data in s["cohorts"].items():
        delta = data["paired_risk_difference_vs_no_abstention_and_random_expected"]
        a = data["rules"]["frozen_joint"]
        b = data["rules"]["no_abstention"]
        emitted_fn = sum(e["fn_emitted"] for e in a["endpoints"].values())
        withheld_fn = sum(e["fn_emitted"] for e in b["endpoints"].values())-emitted_fn
        emitted_fp = sum(e["fp"] for e in a["endpoints"].values())
        withheld_fp = sum(e["fp"] for e in b["endpoints"].values())-emitted_fp
        lines.append(f"- **{cohort}:** difference {pp(delta['difference'])}, simultaneous interval {ci(delta['ci98_75'])}; {a['withheld_errors']:.0f} original errors ({withheld_fn:.0f} FN, {withheld_fp:.0f} FP) and {a['withheld_correct']:.0f} original correct known opportunities withheld. Emitted: {emitted_fn:.0f} FN, {emitted_fp:.0f} FP. {a['ecgs_with_at_least_one_withheld_positive']:.0f} ECGs contained at least one withheld known positive. {data['technical_unscored']} technically unscored ECGs; {data['unknown_scored_opportunities']} scored endpoint references unknown.")
    lines += [
        "", "The original joint policy need not dominate simpler uncertainty rankings. The JSON includes tied-score risk–coverage curves, AURC, score Brier/ECE, signed-margin reliability and adverse endpoint effects. None of these alternatives was adopted by choosing the best retrospective result.",
        "", "| Cohort | Joint AURC | Raw distance AURC | Entropy AURC | Break-even λ | Joint cost at λ=.25 | No-abstention cost |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for cohort, data in s["cohorts"].items():
        r = data["rules"]["frozen_joint"]
        lines.append(f"| {cohort} | "+" | ".join(pct(v["aurc"]) for v in data["ranking"].values())
                     +f" | {pct(r['break_even_vs_no_abstention'])} | {pct(r['full_scored_cost']['0.25'])} | {pct(data['rules']['no_abstention']['accepted_risk'])} |")
    lines += [
        "", "The full scored denominator charges one unit for each emitted error plus λ for each withheld known opportunity. It never counts a withheld opportunity as correct. The break-even λ is the fraction of withheld known opportunities that would have been wrong. This sensitivity grid is not a clinical cost model, and unknown references or technical failures are not silently scored as successes.",
        "", "Neither SPH nor LUDB was newly unseen when this analysis was specified. Different cohort mappings limit portability. A significant result on either cohort would not establish a clinically useful reduction on a new independent population. See the [partial cascade experiment](R2_4K_CASCADE_EXPERIMENT.md) for a separate actual second stage.",
    ]
    lines += ["", "## Endpoint effects of the frozen rule", "",
              "| Source/endpoint | Known positives | FN emitted | Positive withheld | Full sensitivity | PPV accepted | NPV accepted |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for cohort, data in s["cohorts"].items():
        for label, e in data["rules"]["frozen_joint"]["endpoints"].items():
            lines.append(f"| {cohort}/{label} | {e['positive_total']} | {e['fn_emitted']:.0f} | {e['positive_withheld']:.0f} | {pct(e['full_scored_sensitivity'])} | {pct(e['ppv'])} | {pct(e['npv'])} |")
    write(docs, "R2_4K_SELECTIVE_PREDICTION_FINAL_VALIDATION.md", lines)


def cascade(docs, r):
    c = r["fallback"]
    t = c["totals"]
    counts = c["routes"]
    lines = [
        "# R2-4k: Executed partial P6 fallback", "",
        f"**EXPERIMENT_COMPLETED on LUDB** (CEDIA job {r['job']}). Stage one reads the sealed P8/P4 scores and route. Every original abstention is routed to an actual new waveform preparation and inference through V3F and the released P6 specialist. Accepted ECGs are never scored again by the fallback. No labels enter selection or P6 inference. The output uses the published P6 thresholds without a top-1 override.",
        "", f"P6 completed on {counts['fallback_executed']}/{counts['abstained']} original abstentions, with {counts.get('fallback_technical_failure', 0)} fallback technical failures. At least partial coverage: {pct(c['at_least_partial_coverage'])}; complete original profile coverage: {pct(c['full_profile_coverage'])}, unchanged. Fallback adds only AFIB, SB, STACH, RBBB, 1AVB and PVC membership calls. P8 NSR/PAC and all P4 calls remain unresolved for those ECGs. No patient received review or referral.",
        "", "| Strategy | Enrolled ECGs | Known opportunities emitted / original | Errors emitted | Known unresolved |",
        "| --- | ---: | ---: | ---: | ---: |",
        "| No abstention | 200 | 924/924 | 192 | 0 |",
        "| Joint withholding only | 200 | 697/924 | 139 | 227 |",
        f"| Joint plus P6 fallback | {c['full_ecgs']} | {t['known_emitted']}/{t['known_total']} | {t['final_errors']} | {t['known_unresolved']} |",
        "", f"On the comparable fallback opportunities, it corrected **{t.get('corrected', 0)}** original errors and introduced **{t.get('introduced', 0)}** original errors. Final emitted FN: **{t['final_false_negatives']}**; known positives still unresolved: **{t['positive_unresolved']}**. Overall known emitted risk is {pct(t['final_errors']/t['known_emitted'])}; this is not a full-denominator accuracy. Treating unresolved responses as pending at λ=.25 gives cost {pct((t['final_errors']+.25*t['known_unresolved'])/t['known_total'])} on the original known denominator.",
        "", f"Incremental waveform preparation plus batch-one P6 latency on this allocation: median {c['fallback_seconds_median']:.3f} s, p95 {c['fallback_seconds_p95']:.3f} s, total {c['fallback_seconds_total']:.2f} s. Model startup and the cached original primary runtime are not included. These timings are descriptive, not prospective service latency.",
        "", "**Scope:** This is a new partial two-stage execution with a restricted ledger and sealed aggregates. The published P6 cutoffs were not calibrated for the subset rejected by the primary route. This is not the original system, not a complete pathology/rhythm cascade, and not evidence for June quarantine, referral effectiveness or clinical safety.",
    ]
    write(docs, "R2_4K_CASCADE_EXPERIMENT.md", lines)


def verdict(docs, m, r, s):
    supported = [p for p, x in m["profiles"].items() if x["contrast"]["classification"] == "benefit_above_margin"]
    within = [p for p, x in m["profiles"].items() if
              x["contrast"]["classification"] == "effects_within_prespecified_margin"]
    reduced = [p for p, x in s["cohorts"].items() if
               x["paired_risk_difference_vs_no_abstention_and_random_expected"]["ci98_75"][1] < 0]
    rows = [
        ("R2-3f", "Ten formulas and actual specialist tensor paths in reconstructed candidate", "IMPLEMENTATION_VERIFIED", "runtime", "flat-input and clinical proxy limitations"),
        ("R2-3f", "Exact historical preprocessing and original probabilities", "HISTORICAL_PROVENANCE_UNVERIFIED", "historical replay", "original loader missing; strict P4 tolerance fails"),
        ("R2-3f", "Macro-F1 benefit above 2 pp in at least one tested development profile", "CLAIM_SUPPORTED" if supported else "CLAIM_NOT_SUPPORTED", "paired ablation", "restricted to matched frozen features and new heads; no external confirmation"),
        ("R2-3f", "Effects inside both sides of the 2 pp interval", "CLAIM_SUPPORTED" if within else "CLAIM_NOT_SUPPORTED", ", ".join(within) or "paired ablation", "only tested development heads; not equivalence of every class or end-to-end system"),
        ("R2-3f", "Generalizable full-network morphology benefit", "STILL_OPEN", "paired ablation", "no end-to-end paired retraining or unseen same-target cohort"),
        ("R2-4k", "November joint abstention executed and reproducible", "IMPLEMENTATION_VERIFIED", "sealed rowwise audit", "not June quarantine"),
        ("R2-4k", "Accepted-risk improvement over all scored and random expectation on at least one tested cohort", "CLAIM_SUPPORTED" if reduced else "CLAIM_NOT_SUPPORTED", "paired utility", "retrospective and conditional on coverage; not clinical benefit"),
        ("R2-4k", "Actual limited P6 second-stage inference", "EXPERIMENT_COMPLETED", "runtime/cascade", "six membership outputs only; no human review"),
        ("R2-4k", "Original quarantine rate and complete clinical cascade", "HISTORICAL_PROVENANCE_UNVERIFIED", "prior original workflow audit", "WITHDRAW_HISTORICAL_CLAIM"),
        ("R2-4k", "Independent clinical utility or safety", "STILL_OPEN", "selective and fallback studies", "prospective/independent references and real resolution costs absent"),
    ]
    with (docs/"SCIENTIFIC_CLAIM_VERIFICATION_MATRIX.csv").open("x", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(("reviewer", "claim", "status", "evidence", "boundary"))
        w.writerows(rows)
    lines = [
        "# Final scientific verdict: R2-3f and R2-4k", "",
        "These verdicts address scientific evidence, not editor acceptance or changes already made in the manuscript.",
        "", "## What was demonstrated and reproduced", "",
        f"- **R2-3f:** Job {r['job']} verified all ten formulas on numerical fixtures and both specialist input paths during actual inference on {r['traced_ecgs']} authorized ECGs. Fixed-batch replay agreed exactly. New matched five-seed fitting ran in job {m['job']}; the relevant-effect criterion was met in {', '.join(supported) if supported else 'no tested profile'}. That criterion applies only to this exploratory head training.",
        f"- **R2-4k:** Job {s['job']} reproduced original November score-only route assignments and evaluated full-denominator tradeoffs. Multiplicity-controlled accepted-risk reduction versus all scored and random expectation was supported in {', '.join(reduced) if reduced else 'neither cohort'}. This does not measure benefit on all ECGs or clinical utility. Job {r['job']} executed the distinct partial P6 fallback on the previously withheld LUDB group.",
        "", "## Errors, rejected hypotheses and irreducible limits", "",
        "- The flat-line fixture exposed false morphology peaks. The strict P4 archival probability test still fails; the documented named-lead bug explains earlier decision disagreement but not all residuals. The original loader, full June runtime and exact historical input provenance remain unverified. A new reconstruction cannot authenticate them retroactively.",
        f"- A positive point estimate is not robust evidence of a practically relevant gain. Simultaneous intervals were entirely inside the predefined ±2 pp bounds in {', '.join(within) if within else 'no tested profile'}. Unseen same-target cross-source robustness and the effect of end-to-end retraining remain open.",
        "- Retained correct opportunities and positives, reference missingness, and nonzero costs are material. The partial cascade does not restore NSR/PAC or pathology output, let alone establish safety, clinical benefit or historical referral.",
        "", "## What may be used and what must be withdrawn", "",
        "- In a future authorized revision, use the ten proxy definitions, correct direct arrows into both specialists, distinguish the global pathology head, document the reconstructed signal path and report the candidate's limitations.",
        "- Describe only the explicitly named November abstention protocol, risk accounting and partial exploratory cascade. Withdraw the unauthenticated June quarantine rate, original secondary/human pathway effectiveness and unsupported full-workflow validation. Do not replace absence of evidence with 0%.",
        "", "## Can the comments close?", "",
        "- **R2-3f:** `SCIENTIFICALLY_CLOSED_WITH_EXPLICIT_SCOPE` for the literal formulas and data-flow question, if the subsequent revision labels the source-backed reconstruction accurately and removes exact historical or clinical interval claims. A generalized performance claim remains `STILL_OPEN`.",
        "- **R2-4k:** `SCIENTIFICALLY_CLOSED_WITH_EXPLICIT_SCOPE` as a methodological answer only by withdrawing the unauthenticated historical claim and distinguishing the later experiment. Keeping a claim of June quarantine or independent clinical utility leaves it `STILL_OPEN`.",
        "", "No manuscript, figures, response letter, existing PR or released weights were changed in this experiment. Confirmatory claims require new authorized evaluation and the specified references; a favorable numerical threshold is not a release decision.",
    ]
    write(docs, "FINAL_TWO_COMMENT_SCIENTIFIC_VERDICT.md", lines)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--docs", type=Path, required=True)
    p.add_argument("--results", type=Path, required=True)
    a = p.parse_args()
    s, m, r = (load(a.results/n) for n in ("R2_4K_COVERAGE_RISK_AND_FALSE_NEGATIVES.json",
                                          "R2_3F_ABLATION_CONFIRMATORY_RESULTS.json",
                                          "RUNTIME_AND_CASCADE_AGGREGATE.json"))
    receipt = load(a.results/"CEDIA_EXECUTION_RECEIPTS.json")
    for n, data, check in (("selective", s, check_selective), ("morphology", m, check_ablation), ("runtime", r, check_runtime)):
        require(receipt["experiments"][n]["job"] == data["job"] and receipt["experiments"][n]["state"] == "COMPLETED",
                "unverified input")
        check(data)
    morphology(a.docs, m, r)
    selective(a.docs, s)
    cascade(a.docs, r)
    verdict(a.docs, m, r, s)


if __name__ == "__main__":
    main()
