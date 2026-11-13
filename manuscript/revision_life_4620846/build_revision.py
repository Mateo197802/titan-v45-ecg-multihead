"""Apply scoped, checked interventions to the exact submitted Life source."""
import csv
import json
import re
import shutil
from pathlib import Path

from reviewer_map import REPO, ROOT
from revision_data import pct, sha, table

ORIGINAL = Path.home() / ".codex/recovery/life-4620846-canonical-submission/extracted/mdpi_Articulo"
LATEX = ROOT / "latex"
ORIGINAL_SHA = "cd1a31ccfaf882cbffa6749bb9795d0e54531f810f563f6423c3006c0d0717b6"
changes = []


def build():
    src = ORIGINAL / "manuscrito.tex"
    assert sha(src) == ORIGINAL_SHA
    (LATEX / "Definitions").mkdir(exist_ok=True)
    for dependency in (ORIGINAL / "Definitions").iterdir():
        target = LATEX / "Definitions" / dependency.name
        if dependency.is_file() and "-converted-to" not in dependency.name:
            if not target.exists():
                shutil.copyfile(dependency, target)
            assert sha(dependency) == sha(target)
    source = src.read_text(encoding="utf-8")
    s = source

    def edit(start, stop, new, comment, evidence):
        nonlocal s
        assert s.count(start) == 1, start
        i = s.index(start)
        j = s.index(stop, i + len(start))
        s = s[:i] + new.rstrip() + "\n\n" + s[j:]
        line = next((n for n, text in enumerate(source.splitlines(), 1) if start in text), None)
        changes.append((comment, line, start, evidence))

    def replace(old, new, count=1):
        nonlocal s
        assert s.count(old) == count, (old, s.count(old))
        s = s.replace(old, new)

    def table_edit(label, new, comment, evidence):
        nonlocal s
        at = s.index(r"\label{" + label + "}")
        i, j = s.rindex(r"\begin{table}", 0, at), s.index(r"\end{table}", at)
        s = s[:i] + new + s[j+len(r"\end{table}"):]
        line = next(n for n, text in enumerate(source.splitlines(), 1) if label in text)
        changes.append((comment, line, label, evidence))

    edit(r"\abstract{", r"\keyword", r"""
\abstract{This study designed and evaluated modular convolutional neural network (CNN)--Transformer specialists for ten-second 12-lead electrocardiograms (ECGs). The architecture uses a 58.35-million-parameter waveform backbone design with separate fitted rhythm and pathology versions. Primary6 is a six-output rhythm profile for atrial fibrillation, sinus bradycardia, sinus tachycardia, right bundle branch block, first-degree atrioventricular block, and premature ventricular contractions. Primary4 comprises four binary pathology panels: anteroseptal myocardial infarction, left ventricular hypertrophy, inferior myocardial infarction, and ischemic ST--T change. In the selected retrospective development evaluations, Primary6 achieved 95.19\% top-1 accuracy and 80.09\% mean binary F1 across 1,643 ECGs; Primary4 achieved 80.23\% mean binary accuracy and 79.35\% macro-F1 across 962 ECG--label observations from 733 ECGs. These estimates are conditional on profile eligibility and do not represent a complete diagnostic workflow. Separate retrospective analyses quantify sensitivity to denominator selection and distinguish score-based abstention from top-1 output. Five released weight files have verified SHA-256 digests; archived results can be recalculated, but the complete historical training chain and independence of all partitions cannot be established. Independent external evaluation remains in progress.}
""", "R1-1/R1-2/R1-4/R2-1", "Release prediction ledgers; release weight manifest")

    edit("Automated interpretation of the twelve-lead", r"\begin{figure}", r"""
Automated ECG interpretation has been studied with convolutional models on single-lead ambulatory recordings and large 12-lead datasets \citep{Hannun2019Cardiologist,Ribeiro2020Automatic}. Multi-label datasets and benchmarks provide a basis for evaluating rhythm, conduction and structural statements, but endpoints and annotation procedures vary by source \citep{Zhu2020Automatic,Strodthoff2021Deep,Wagner2020PTBXL,Reyna2022Challenge}. Evaluation design matters when class support varies and when uncertain predictions are deferred \citep{Vranken2021Uncertainty}. Aggregate accuracy alone does not quantify how a model performs on an underrepresented statement, nor does restricting a denominator establish clinical reliability.

ECGs encode local waveform morphology and sequential rhythm information. A residual convolutional network provides local temporal features, while self-attention can model relationships across a signal window \citep{He2016Deep,Vaswani2017Attention}. The present study separates a rhythm reporting profile from binary pathology panels. Primary6 reports six selected rhythm and conduction statements; Primary4 reports four separate structural or ischemic statement endpoints. Separate backbones of the same design are paired with their specialists. The design does not imply that all other ECGs are correctly routed or evaluated.

Figures~\ref{fig:fig00_ecg_ai_context} and \ref{fig:fig00b_ecg_ai_evolution_gap} are newly drawn study schematics. The first introduces the input and reporting workflow; the second distinguishes beat, ECG and longitudinal endpoints. Neither is a clinical tracing, outcome, or assertion of superiority.
""", "R2-2a/R2-2b", "Primary literature and rebuilt schematic sources")
    edit(r"\caption{Timeline of automated", r"\end{figure}",
         r"\caption{Conceptual comparison of beat, ECG and longitudinal reference units. The study evaluates ECG-level statements only.\label{fig:fig00b_ecg_ai_evolution_gap}}",
         "R2-2b/R2-5", "New original schematic")
    edit("Despite these notable achievements", r"\begin{table}", r"""
Table~\ref{tab:comparison} is a purposive comparison, not a systematic review or ranking. Direct ECG-AI comparators are studies sharing a multi-lead ECG input or related ECG statement outputs; beat-level and clinical workflow studies provide context only. Venue was not a selection criterion. NR denotes not reported or not comparable on the cited basis. Differences in labels, population, unit of analysis and validation design prevent direct ranking by published scores.
""", "R2-2c", "Primary literature and task-specific comparison")
    replace("Representative prior Life/MDPI ECG-related papers and direct ECG-AI comparators.", "Selected ECG-AI studies across venues, compared by input, task and evaluation unit.")
    replace(r"p{0.30\textwidth}@{}}", r"p{0.28\textwidth}@{}}")
    edit("The evolution of deep learning methodologies", "Table~\\ref{tab:comparison} is a purposive", r"""
Single-lead ambulatory classification and 12-lead statement classification are distinct tasks \citep{Hannun2019Cardiologist,Ribeiro2020Automatic}. PTB-XL and the PhysioNet Challenge make label and population differences explicit \citep{Wagner2020PTBXL,Strodthoff2021Deep,Reyna2022Challenge}. A dual-view CNN--Transformer has combined within-beat and recording-scale information \citep{Li2024DualView}. Other studies illustrate heterogeneous alternatives: uncertainty assessment on ECGs \citep{Vranken2021Uncertainty}, evaluation against expert consensus \citep{Herman2024}, and beat-level feature extraction and classification \citep{Mastoi2022DERMA,Elsheikhy2025Lightweight,Zhou2025Classification}. Their results cannot be placed on the same scale as the selected TITAN ECG and panel endpoints.
""", "R2-2a/R2-2c", "Primary bibliographic verification")
    replace("DNN fusion; comparable params NR", "DERMA and FrIFT; SVM or KNN")
    replace("Bai et al. (2024) & Hybrid 12-lead arrhythmia diagnosis & Hybrid DNN; comparable params NR & Arrhythmia task; recent 12-lead rhythm comparator without pathology specialist contract",
            "Li et al. (2024) & ECG abnormality classification & Dual-view CNN--Transformer & Beat and recording-scale information; distinct targets")
    replace("Lightweight multi-lead arrhythmia detection & Lightweight DNN; comparable params NR & Arrhythmia task; recent MDPI comparator without pathology specialist contract",
            "Beat classification in MIT-BIH and INCART & CNN with channel attention & Five beat classes, not P6/P4")
    replace("Multi-lead classification; recent comparator without explicit primary/cascade reporting",
            "Beat classification on MIT-BIH and CCDD; not an ECG-level clinical cascade")
    intro_start = s.index("To establish an unequivocal baseline")
    method_start = s.index(r"\section{Materials and Methods}", intro_start)
    intro_tables = re.findall(r"\\begin\{table\}.*?\\end\{table\}", s[intro_start:method_start], re.S)
    assert len(intro_tables) == 2
    edit("To establish an unequivocal baseline", r"\section{Materials and Methods}", r"""
The objective was to design a modular 12-lead ECG classifier, characterize its specialist input and output contracts, and quantify accuracy, per-class discrimination and calibration on explicitly defined retrospective populations. The analysis separates evaluation of the released reporting profiles from later experiments addressing denominator sensitivity, morphology and selective prediction.
""", "R2-2d/R2-3b", "Original Tables 2 and 3 moved to Methods")

    edit("This investigation establishes", r"\begin{figure}", r"""
\label{sec:boundary}
This study designed and evaluated CNN--Transformer specialists on standardized ECG windows. The original release identifier \texttt{external\_dev}, termed external-development in the submission, refers to the archived selected development evaluations, not a single untouched test set. V3H used its 2,193-ECG P8 holdout for development validation; the selected P6 profile comprises 1,643 ECGs and its epoch selection used the reported P6 population. P4 uses four selected binary panels; 962 panel observations correspond to 733 unique ECGs, not 962 distinct patients. The panels are not all evaluated for every ECG. Table~\ref{tab:presentstudy} defines the profiles, and Table~\ref{tab:challengeposition} separates reporting choices from clinical decisions.

Independent external evaluation is a separate, unfinished analysis. Its intended confirmatory design binds cohort eligibility, source and patient/signal overlap checks, label mappings, frozen checkpoint bytes, preprocessing, thresholds and analysis endpoints before outcome review. Cohorts inspected during model selection, threshold fitting or domain adaptation are not counted as independent. Any unresolved overlap or reference incompatibility must be reported rather than assumed absent. No performance estimate from the ongoing independent evaluation is presented.
""" + "\n".join(intro_tables), "R1-1/R2-4a", "V3H jobs 17314/17315; release cohort reports")
    replace("Rhythm specialist & Primary6 top-1 rhythm reporting plus cascade review", "Rhythm specialist & Selected Primary6 top-1 and binary membership")
    replace("Pathology specialist & Primary4 one-vs.-rest pathology reporting plus cascade review", "Pathology specialist & Selected Primary4 binary panels")
    replace("Supports reproducible comparison without changing class definitions", "Supports selected-result calculation; not historical replay")
    replace("report source-stratified external-development behavior", "report source-stratified selected development results")
    replace("Separate Primary6 rhythm, Primary4 pathology, cascade/quarantine classes, and auxiliary outputs.", "Separate Primary6 rhythm, Primary4 pathology, and unreported outputs.")
    replace("Report entropy, margin, MC-dropout-compatible equations, calibration, and quarantine review logic.", "Distinguish score uncertainty, top-1, and explicitly tested withholding.")
    edit(r"\caption{Proposed modular operational architecture", r"\end{figure}",
         r"\caption{Specialist design. The P6/P8 and P4 evaluations use different fitted versions of the backbone design, V3F and V3AG, respectively.\label{fig:fig01_graphical_abstract}}",
         "R2-3f", "Separate release backbones")
    edit(r"\caption{Data curation and harmonization pipeline", r"\end{figure}",
         r"\caption{Signal preprocessing and distinct evidence stages. Selected development sets do not establish historical patient separation.\label{fig:fig02_data_processing_bias_workflow}}",
         "R1-1/R2-3a", "Historical split disposition")
    edit("The data curation and cohort isolation pipeline", r"\begin{figure}", r"""
Figure~\ref{fig:fig02_data_processing_bias_workflow} separates the reconstructed preprocessing steps from the provenance of the historical selected profiles and the unfinished independent assessment. Harmonizing waveform dimensions does not harmonize source annotation standards or demonstrate patient isolation.
""", "R1-1/R2-3a", "Verified preprocessing and bounded split evidence")
    edit(r"\subsubsection{Clinical Rationale", r"\subsection{Dataset Curation", r"""
\subsubsection{Rationale for profile-specific reporting}
NSR is a physiologic rhythm and may be frequent in unselected populations. Its omission from P6 defines a narrower classification problem; it does not correct selection bias or establish a method for separating normal from abnormal ECGs. Similarly, the four P4 panels test specified statements, not every infarct territory or all structural disease. The role table distinguishes evaluation eligibility from proposed handling outside the profile.
""", "R1-2/R2-general/R2-3c", "Released P6, P8 and P4 contracts")
    edit("Rigorous isolation of patient cohorts", "Throughout this mathematical formulation", r"""
\label{sec:data}
Separating patients and waveform duplicates is important because multiple ECGs or windows from one patient can share distinctive morphology. We distinguish source aliases, record-level exclusion and demonstrated patient/signal independence. The exact historical data loader and job-consumed train, calibration and validation rosters are not available for all checkpoints. The historical counts and the verified retrospective preprocessing are therefore reported separately below.
""", "R1-1/R2-3a", "Historical loader and checkpoint-to-split evidence")
    edit("This mapping standardizes heterogeneous", "Inter-electrode contact impedance", r"""
The tensor contract uses 125 Hz and ten seconds. Signal resampling and named-lead alignment are distinct from inference over the label ontology. A lead-validity mask is passed to the model separately from waveform values. This representation does not guarantee preservation of every high-frequency diagnostic feature or reconstruction of absent leads.
""", "R2-3a/R2-3f", "Instrumented reconstructed preprocessing")
    replace("thereby yielding a unified patient-level calibrated probability $p_{i,c}$. This linear logit pooling mechanism ensures that multi-window evaluation metrics reflect singular clinical instances rather than allowing repeated windows from a single subject to inflate true-positive counts or distort class-prevalence denominators.",
            "This illustrates record-level pooling before activation. It prevents counting each window as a separate ECG in this score, but does not convert ECG counts into patient counts. The released profiles use their documented score and activation paths.")
    replace("avoids reliance on global population metrics and inherently prevents the leakage of statistical distribution parameters across training and test partitions.",
            "avoids estimating a global normalization constant from pooled partitions; it does not prevent patient or signal overlap.")

    edit("Surface twelve-lead electrocardiograms", r"Formally, let", r"""
Convolution and attention operate at different temporal scales. The former builds local waveform features, while the latter integrates information across the ten-second window. The description below summarizes the model design; the observed tensor widths and branch connectivity are reported separately.
""", "R2-3f", "Architecture and instrumented runtime")
    replace("The shared CNN--Transformer representation backbone encompasses 58,352,219 trainable parameters.", "Each loaded CNN--Transformer backbone object contains 58,352,219 parameters including its global heads.")
    replace("From this common latent trunk, the model bifurcates into a 63,930,847-parameter rhythm specialist branch and a 65,694,183-parameter pathology specialist branch, each tailored with distinct classification topologies.",
            "The rhythm package and pathology package comprise 63,930,847 and 65,694,183 parameters, respectively, including their separate fitted backbones.")
    replace("Structural interconnectivity and hierarchical cascade contracts are illustrated schematically", "Reconstructed tensor interconnectivity and reporting roles are illustrated")
    replace("Primary, quarantine-cascade, and auxiliary class contracts.", "Primary, secondary-candidate and auxiliary class contracts.")
    replace("Rhythm & Cascade &", "Rhythm & Secondary candidate &")
    replace("Pathology & Cascade &", "Pathology & Secondary candidate &")
    edit(r"\caption{Detailed component diagram", r"\end{figure}",
         r"\caption{Instrumented CNN--Transformer and specialist data flow. Arrows denote tensors passed in the reconstructed runtime. The ten morphology proxies feed both specialists directly; the global pathology head does not consume them directly.\label{fig:fig03_internal_architecture}}",
         "R2-3f", "Job 33796; reconstructed runtime contract")
    edit(r"\caption{Class routing and output constraints", r"\end{figure}",
         r"\caption{Reporting and output contracts. Groupings do not describe a clinical dispatch rule and no arrow implies movement between groups.\label{fig:fig03_cascade_contract}}",
         "R2-general/R2-3e", "Released profile class contracts")
    addition = (ROOT / "methods_addendum.tex").read_text(encoding="ascii")
    for idx, marker in [(0, r"\subsection{Architecture and Specialist Branches}"),
                        (2, r"\subsection{Loss Function, Optuna Search, Fine-Tuning, and Calibration}")]:
        parts = re.split(r"(?=\\subsubsection\{)", addition)
        block = "".join(parts[1:3] if idx == 0 else parts[3:])
        replace(marker, block+"\n"+marker)
    changes.extend([("R1-3/R2-3a", 171, "Historical development populations and reference statements", "CEDIA job receipts; AF and SCP mapping audits"),
                    ("R2-3c/R2-3d/R2-3e/R2-3f", 199, "Supervision, morphology and later analyses", "Recovered fine-tuning code; job 33796; matched-head ablation")])

    edit("Severe prevalence disparities", r"\begin{table}", r"""
\label{sec:optimization}
Class imbalance motivated a focal binary term \citep{Lin2017Focal}. For a known binary target $y_{ic}$, let $p_{t,ic}=p_{ic}$ when $y_{ic}=1$ and $p_{t,ic}=1-p_{ic}$ otherwise. With eligibility mask $m_{ic}$, the focal term is
\begin{equation}
\mathcal L_{\mathrm{focal}}=-\frac{\sum_{ic}m_{ic}\alpha_{ic}(1-p_{t,ic})^\gamma\log(p_{t,ic}+\epsilon)}{\sum_{ic}m_{ic}}.
\end{equation}
Here $\alpha_{ic}$ denotes a class/target weight when used. Masked or unrecognized labels do not contribute to the corresponding term. The categorical component uses $-\sum_c q_{ic}\log \mathrm{softmax}(z_i)_c$ for target vector $q_i$. The archived 50-epoch development run records auxiliary clinical-axis losses; it does not show that the released specialist decision has a validated auxiliary function. Exact historical configuration and label support are not available for all prior stages.

The V3C Optuna selection used a TPE sampler (recorded seed 197813, multivariate mode, ten startup trials), with 12 planned trials and nine retained completed candidates, distinct from V4 and the 41M screening series \citep{Akiba2019Optuna}. The recorded epoch composite was
\begin{equation}
J_e=0.6F1_{\mathrm{P8},e}+0.4F1_{\mathrm{P4},e}-0.05M_{\mathrm{P8},e}-0.05M_{\mathrm{P4},e},
\end{equation}
where $M$ denotes missing target classes or labels, not mini-batch variance. Candidate ranking uses the mean of the last three composites less 0.25 times their population standard deviation. Trial 6 led that ranking (0.624512); trial 8 had the highest single-epoch peak (0.650940). The selection JSON and archived effective configuration agree on the parameters in Table~\ref{tab:optuna}. Job 16768 ran 50 epochs; job 16781 subsequently declared its intermediate checkpoint as the initialization for V3F. The V3F report records eight epochs. The historical V3F output digest agrees with the published backbone. The original Optuna database, intermediate checkpoint bytes and job-level input/output digest binding remain unavailable; neither scheduler completion nor the output digest proves the complete byte-level lineage.
""", "R1-4/R2-3a/R2-3c/R2-3d", "V3C source snapshot; job 16768 and V3F reports")
    replace("Selected hyperparameters from the Optuna search.", "Recorded V3C trial 6 hyperparameters used in the archived job 16768 configuration.")
    edit("In clinical deployment environments", r"\subsection{Grad-CAM", r"""
\subsubsection{Thresholds, top-1 and empty prediction sets}
\label{sec:decision}
For a binary statement, the thresholded decision is $\hat y_{ic}=\mathbb{1}[p_{ic}\ge \tau_c]$. For rhythm, the released top-1 output is distinct from the membership set. P6 retains the top-1 label on every selected ECG even when the binary set is empty; empty membership remains all-negative in P6 binary metrics. P8 fills an empty predicted set with the recorded top-1 class. The top-1 correctness criterion is membership in the accepted reference set. P4 remains a binary panel evaluation: below threshold is negative and remains in the panel denominator. Thresholds are the released values in Tables~\ref{tab:rhythmclass}, \ref{tab:pathclass} and \ref{tab:p8class}. None of these cases is automatically a clinical abstention.

\subsection{Uncertainty and selective prediction}
\label{sec:selective}
Predictive entropy $H(p)=-\sum_c p_c\log p_c$ and the difference between the two highest probabilities can describe uncertainty for a categorical score. With $T$ stochastic passes, the difference between entropy of the mean probability and mean entropy is a model-dependent diagnostic; it is not proof of out-of-distribution status. The original June report has no authenticated decision ledger connecting these statistics to actual withholding, secondary inference or expert review. Historical quarantine rates and pre/post accuracy are therefore not reported.

In the later score-based P8/P4 experiment, profile confidence was the minimum absolute distance between class scores and the respective released cutoffs. The profile cutoffs (P8: 0.037162775; P4: 0.014417143) were fitted for target coverage on 12,901 SPH calibration ECGs without reference labels. The frozen joint rule emits both decisions only if both profile cutoffs are met. Failure to produce scores is distinct from abstention. With $N_s$ scored ECGs and $N_a$ accepted ECGs, coverage is $N_a/N_s$ and the scored abstention rate is $(N_s-N_a)/N_s$. Coverage relative to all enrolled ECGs is reported separately when some cannot be scored. Pre-policy risk is FP plus FN divided by known binary opportunities over all scored ECGs; post-policy risk uses only accepted opportunities. Withheld positives are separate from emitted false negatives. The full-denominator cost counts emitted errors plus $\lambda$ times withheld known opportunities. A separate LUDB experiment runs actual P6 fallback only on withheld ECGs, with frozen P6 membership thresholds, no top-1 override and no clinician review.
""", "R2-4e/R2-4k", "Release decisions; jobs 33414, 33799 and 33796")
    replace("Every generated Grad-CAM saliency artifact is immutably linked to metadata recording the specific model checkpoint, target diagnostic class, target convolutional layer, and input verification SHA-256 hash.",
            "This defines an explainability method and recommended metadata, not a validated explanation of decision causality or an inventory of all historical artifacts.")
    replace("This formulation yields localized temporal heatmaps that directly highlight relevant electrophysiological complexes (such as P-wave absence in atrial fibrillation, wide QRS duration in bundle branch blocks, or ST-segment elevation in myocardial infarction).",
            "The temporal heatmap indicates local gradient-weighted activation, not validated identification of an electrophysiological complex.")

    edit("To ensure comprehensive, uncompromised", r"\begin{table}", r"""
\label{sec:metrics}
For each known binary opportunity, TP, TN, FP and FN count true positives, true negatives, false positives and false negatives. With $N=TP+TN+FP+FN$,
\begin{align}
\mathrm{Acc}_{\mathrm{bin}}&=(TP+TN)/N,&
\mathrm{PPV}=\mathrm{Precision}&=TP/(TP+FP),\\
\mathrm{Sensitivity}=\mathrm{Recall}&=TP/(TP+FN),&
\mathrm{Specificity}&=TN/(TN+FP),\\
\mathrm{NPV}&=TN/(TN+FN),&
F1&=2TP/(2TP+FP+FN).
\end{align}
Undefined denominators are not treated as clinical zeros. With $C$ class endpoints, $\mathrm{MacroF1}=C^{-1}\sum_c F1_c$; mean binary accuracy is $C^{-1}\sum_c\mathrm{Acc}_{\mathrm{bin},c}$. Top-1 accuracy is $n^{-1}\sum_i\mathbb{1}[\hat c_i\in S_i]$ for the accepted reference set $S_i$ and one emitted top-1 class $\hat c_i$. P6 top-1 and mean binary F1 use different decision units; P4 mean binary accuracy is not top-1 or pooled panel accuracy.

With $\mathrm{TPR}$ and $\mathrm{FPR}$ denoting the true- and false-positive rates, $\mathrm{AUROC}=\int_0^1\mathrm{TPR}\,d\mathrm{FPR}$ for the binary ranking curve \citep{Hanley1982meaning}. Average precision (AP) is $\sum_k (R_k-R_{k-1})P_k$ at successive distinct score thresholds, not trapezoidal PR area. Brier score is $n^{-1}\sum_i(p_i-y_i)^2$. For ten equally spaced probability bins, binary expected calibration error (ECE) is $\sum_b(n_b/n)|\bar p_b-\bar y_b|$ over nonempty bins. The vertical axis of the reliability plots is $\bar y_b$, the fraction of reference-positive observations in bin $b$.

The Wilson 95\% interval for $k/n=\hat p$ is
\begin{equation}
\frac{\hat p+z^2/(2n)\ \pm\ z\sqrt{\hat p(1-\hat p)/n+z^2/(4n^2)}}{1+z^2/n},\quad z=1.96.
\end{equation}
Selected-source Wilson intervals use ECGs as observations \citep{Wilson1927Probable}. Classwise F1 bars use the 2.5th and 97.5th percentiles of 1,000 row-level bootstrap draws from their observed binary confusion counts \citep{Efron1979Bootstrap}. These are descriptive within-panel intervals, not patient-level uncertainty. The later SPH studies report component intervals for their own contrasts.
""", "R2-3g/R2-3h/R2-4j/R2-4l", "Archived scores, thresholds and statistical definitions")
    replace("Area-equivalent summary of precision-recall ranking", "Recall-weighted precision at distinct score thresholds")

    rec = json.loads((ROOT / "RELEASE_RECALCULATION.json").read_text())
    edit("Quantitative evaluation on the frozen", r"\begin{table}", r"""
Table~\ref{tab:overall} reports the selected development evaluations. P6 correctly assigned a top-1 class to 1,564 of 1,643 ECGs (95.19\%) and had thresholded mean binary F1 of 80.09\%. P4 had mean panel accuracy of 80.23\% and macro-F1 of 79.35\% across 962 ECG--label observations from 733 unique ECGs. The P8 development profile achieved 90.61\% top-1 and 76.14\% mean binary F1 across 2,193 ECGs. The profiles overlap and are not independent comparators. None estimates a clinical all-input workflow.
""", "R1-1/R1-2/R2-4a", "Release metrics recomputation")
    replace("Overall specialist performance on the external-development evidence package. Both rows use the frozen external-development evaluation contract.", "Selected development performance. Rhythm denominators count ECGs; P4 counts panel observations.")
    replace(r"\textbf{Records} & \textbf{Primary Accuracy}", r"\textbf{Observations} & \textbf{Primary Accuracy}")
    for p, old in [(6,r"96.53\% & 86.82\%"), (4,r"87.46\% & 72.84\%")]:
        replace(old, pct(rec[f"P{p}"]["macro_auroc"])+" & "+pct(rec[f"P{p}"]["macro_ap"]))
    edit("Detailed multiclass confusion dynamics", r"\begin{figure}", r"""
Figure~\ref{fig:fig06_rhythm_confusion} reports top-1 classification for the 1,460 ECGs with exactly one accepted class. The overall top-1 denominator also includes 183 ECGs with more than one accepted class. Figure~\ref{fig:fig08_class_metrics} and Table~\ref{tab:rhythmclass} report thresholded binary precision, recall and F1 on all 1,643 ECGs, not the single-reference subset. The 1AVB F1 of 62.58\% and PVC F1 of 65.64\% indicate substantial residual errors; neither supports reliable clinical performance.
""", "R2-4b/R2-4c/R2-4d", "Recomputed class counts and F1")
    edit(r"\caption{Primary6 rhythm specialist confusion", r"\end{figure}",
         r"\caption{Primary6 top-1 confusion on the 1,460 single-reference ECGs. Cells are row percentages.\label{fig:fig06_rhythm_confusion}}", "R2-4f", "P6 archived references and decisions")
    edit(r"\caption{Classwise Primary6 rhythm macro-F1", r"\end{figure}",
         r"\caption{Primary6 classwise precision, recall and F1 on 1,643 ECGs. F1 bars include 95\% row-bootstrap intervals; the plotted quantities are classwise, not macro averages.\label{fig:fig08_class_metrics}}", "R2-4d", "P6 archived binary decisions; seeded bootstrap")
    table_edit("tab:rhythmclass", r"\input{tables/classes_p6}", "R2-4d/R2-4e", "P6 archived binary flags and thresholds")
    edit("Diagnostic performance metrics across", r"\input{tables/classes_p4}" if r"\input{tables/classes_p4}" in s else r"\begin{table}", r"""
Table~\ref{tab:pathclass} and Figures~\ref{fig:fig07_pathology_confusion} and \ref{fig:fig08b_pathology_class_metrics} report the four binary panels. ASMI, LVH, IMI and ISC\_ contribute 294, 224, 206 and 238 observations, respectively. One ECG may occur in multiple panels. ISC\_ had F1 of 91.56\%, compared with 65.73\% for LVH; this difference does not establish performance in unselected clinical patients.
""", "R1-2/R2-4g", "P4 panel predictions")
    table_edit("tab:pathclass", r"\input{tables/classes_p4}", "R1-2/R2-4e", "P4 panel decisions and thresholds")
    edit(r"\caption{Primary4 pathology binary confusion", r"\end{figure}",
         r"\caption{Primary4 confusion matrices for the four binary panels. Cells are row percentages; per-panel denominators are shown above each matrix.\label{fig:fig07_pathology_confusion}}", "R2-4f", "P4 panel predictions")
    at = s.index(r"\caption{Primary4 pathology classwise macro-F1")
    start = s.rindex(r"\includegraphics", 0, at)
    edit(s[start:at]+r"\caption{Primary4 pathology classwise macro-F1", r"\end{figure}", r"""
\includegraphics[width=\linewidth]{fig08b_pathology_class_metrics}
\caption{Primary4 classwise precision, recall and F1. F1 bars show 95\% row-bootstrap intervals. These four pathology panels are distinct from the six rhythm classes.\label{fig:fig08b_pathology_class_metrics}}
""", "R2-4g", "P4 panel predictions, not duplicated P6")
    edit("Continuous receiver operating characteristic", r"\begin{figure}", r"""
Figures~\ref{fig:fig09_roc_curves} and \ref{fig:fig10_precision_recall_curves} show classwise ranking for P6 ECGs and P4 panel observations. Macro-AUROC was 96.53\% and 87.46\%, respectively. The estimates refer to different selected tasks and neither establishes calibration or clinical discrimination in an unselected population. With average precision defined as the recall-weighted sum, macro-AP was 85.61\% and 87.85\%. Brier scores ranged from 0.024 (SB) to 0.042 (1AVB) in P6 and 0.078 (ISC\_) to 0.224 (LVH) in P4. Figure~\ref{fig:fig11_calibration} compares mean predicted probability with observed positive frequency in each populated bin.
""", "R2-3g/R2-4h/R2-4i/R2-4j", "Recomputed ROC, AP, Brier and calibration")
    edit(r"\caption{Probability calibration reliability diagrams", r"\end{figure}",
         r"\caption{Reliability diagrams in ten equal-width probability bins. The vertical axis is the observed positive reference fraction; empty bins have no estimate.\label{fig:fig11_calibration}}",
         "R2-4j", "Binned reference proportions")
    edit("Table~\\ref{tab:uncertainty_quarantine} documents", r"\subsection{Source-Stratified", r"""
Threshold-empty output counts are reported separately in Section~\ref{sec:selective-results}. No historical pre/post-quarantine estimate can be computed from the retained records.
""", "R2-4k", "No authenticated historical operational ledger")
    edit("To verify multi-center generalization", r"\begin{figure}", r"""
Figure~\ref{fig:fig12_source_performance} describes P6 top-1 accuracy by retained source alias. The support varies substantially: Chapman--Shaoxing contributes 1,514 ECGs, while five to 19 ECGs are represented in several other groups. The resulting Wilson intervals should not be interpreted as evidence of stable transport across institutions.
""", "R1-1/R2-4m", "P6 source-stratified recalculation")
    edit(r"\caption{Sankey diagram of diagnostic error flows", r"\end{figure}",
         r"\caption{Frequent P6 reference-to-top-1 errors in the single-reference subset. Bars count ECGs; no bar represents a quarantine or referral.\label{fig:fig13_error_flows}}",
         "R2-4k/R2-4m", "P6 archived reference-to-prediction pairs")
    edit(r"Figure~\ref{fig:fig13_error_flows} illustrates", r"\section{Discussion}",
         (ROOT / "results_addendum.tex").read_text(encoding="ascii"), "R1-2/R2-general/R2-3f/R2-4k",
         "SPH and LUDB aggregates; new head ablations; selective prediction CEDIA receipts")
    edit("The 15.10-percentage-point difference", r"\begin{table}", r"""
The 15.10-point difference between P6 top-1 accuracy and macro-F1 reflects different metrics and decision units as well as the role of uneven class support. Top-1 accepts a class in the reference set; the unweighted binary F1 average gives equal weight to endpoints and uses thresholded membership. The comparison does not show that specialization eliminates bias. Class-level errors, the concentration of the selected source mix, and the marked dependence on denominator selection in SPH constrain interpretation.

\subsection{ECG-level PVC and AF endpoints}
\label{sec:pvc}
The PVC endpoint is a statement associated with the ten-second ECG. It does not report whether every ectopic beat was detected, counted, or localized. An alternative design would detect PVC beats against timing-annotated references and aggregate detected events to an ECG-level output. This requires an explicit matching tolerance, adjudicated beat labels, and assessment of both beat-level and ECG-level false positives. The present study did not test that approach. AF similarly denotes an ECG-associated rhythm statement, not first-diagnosed or incident AF \citep{Rossi2026AF}.

Tables~\ref{tab:sota_results} and \ref{tab:sota_metrics_comparison} place these findings in the context of different ECG tasks. A shared input modality does not establish comparability of performance; the studies differ in their acquisition, annotation, cohort definitions and units of analysis.
""", "R1-3/R2-5/R2-6", "PVC and AF reference audits; reviewer clinical reference")
    table_edit("tab:sota_results", table(
        "Architecture and task context across selected published ECG studies.", "tab:sota_results",
        ["Study", "Architecture or method", "Evaluation unit and scope"],
        [["Ribeiro et al.", "Residual convolutional network", "12-lead ECG abnormalities"],
         ["Strodthoff et al.", "Multiple deep learning baselines", "PTB-XL multi-label benchmark"],
         ["Vranken et al.", "Uncertainty-aware deep network", "12-lead ECG and clinical simulation"],
         ["Herman et al.", "Six specialized deep networks", "12-lead diagnostic statements"],
         ["Li et al.", "Dual-view CNN--Transformer", "ECG abnormalities; beat and recording features"],
         ["Elsheikhy et al.", "CNN with channel attention", "Five beat classes; MIT-BIH and INCART"],
         ["Zhou and Fang", "Multiscale hierarchical CNN", "Beat classification; MIT-BIH and CCDD"],
         ["TITAN", "Residual CNN--Transformer", "Selected ECG and binary panel endpoints"]],
        r"@{}p{.22\linewidth}p{.36\linewidth}p{.36\linewidth}@{}"), "R2-2c/R2-6", "Primary publications")
    table_edit("tab:sota_metrics_comparison", table(
        "Endpoint and evaluation units for cross-study interpretation. Scores are not a common benchmark.",
        "tab:sota_metrics_comparison", ["Study or profile", "Evaluation unit", "Task"],
        [["Hannun et al.", "Ambulatory ECG segment", "Single-lead rhythm classification"],
         ["Ribeiro et al.", "12-lead ECG", "Six source-defined abnormalities"],
         ["Strodthoff et al.", "12-lead ECG", "PTB-XL statement benchmark"],
         ["Mastoi et al.", "Heartbeat", "Beat classification"],
         ["TITAN P6", "Selected ECG", "Top-1 and binary statement F1"],
         ["TITAN P4", "ECG--label observation", "Mean binary panel accuracy"]],
        "@{}p{.24\\linewidth}p{.26\\linewidth}p{.43\\linewidth}@{}"), "R2-2c/R2-6",
        "Source publications; unlike tasks not numerically ranked")
    replace("While essential for cross-device stability, this step constrains sensitivity for amplitude-dependent structural conditions", "This can remove information needed for amplitude-dependent structural conditions")
    replace("While this architectural separation prevents gradient interference between disparate clinical tasks, executing two independent multi-million-parameter forward passes doubles computational memory requirements, preventing efficient single-pass inference on resource-constrained ambulatory devices.",
            "Executing the two profiles separately requires more compute than a single shared pass; comparative deployment cost was not measured in the original evaluation.")
    replace("Fourth, runtime deployment currently maintains separate backbone parameter checkpoints for the rhythm and pathology specialist branches to preserve strict evaluation isolation during benchmarking.",
            "Fourth, the released rhythm and pathology profiles use separate backbone checkpoints, which does not itself establish evaluation isolation.")
    edit("This study establishes a modular", r"\supplementary", r"""
This study designed and evaluated a modular CNN--Transformer architecture with separate rhythm and pathology specialists. The historical selected development results support P6 top-1 accuracy of 95.19\% and mean binary F1 of 80.09\% on 1,643 ECGs, and P4 mean binary accuracy of 80.23\% and macro-F1 of 79.35\% on 962 ECG--label observations from 733 ECGs. These estimates do not measure end-to-end clinical performance. Subsequent bounded analyses demonstrate sensitivity to the evaluated population, limited benefit of the tested morphology addition, and the tradeoff between emitted errors and withheld opportunities. Released bytes and selected reported metrics can be checked independently. Complete training replay, historical patient/signal disjointness and historical clinical quarantine were not established. Independent external evaluation is ongoing.
""", "R1-1/R1-2/R1-4/R2-4k", "Release metrics and bounded post-study experiments")
    edit(r"\supplementary{", r"\authorcontributions", r"""
\supplementary{Appendix~\ref{appendix:supplement} includes verified development summaries, profile-specific tables and release hashes. The companion supplement contains aggregate recalculations and evidence references.}
""", "R1-4", "Shareable supplement inventory")
    edit(r"\dataavailability{", r"\acknowledgments", r"""
\dataavailability{Release v0.1.0 and the code and permitted derived evidence are available at \url{https://github.com/Mateo197802/titan-v45-ecg-multihead}. Table~\ref{tab:app_hashes} identifies the five verified model files. A checksum authenticates matching bytes only; it does not demonstrate training replay, patient-level separation, or authenticity of all historical artifacts. Source ECGs remain subject to source terms and restricted records are not redistributed.}
""", "R1-4", "Release asset manifest; source rights disposition")

    opt_rows = csv.DictReader((REPO / "tests/figure_evaluation/tables_snapshot/optuna_trials.csv").open())
    table_edit("tab:app_shared", table("Archived job 16768 summary (50 epochs). Internal development only.",
        "tab:app_shared", ["Recorded field","Value"], [["Training windows","9,021"], ["Validation windows","924"],
        ["Best composite","0.598418"], ["Reported P8 macro-F1","0.694886"], ["Reported P4 macro-F1","0.583806"],
        ["Reported global rhythm14 macro-F1","0.326219"], ["Reported global pathology7 macro-F1","0.532517"],
        ["Clinical-axis macro-F1","0.000000"]]) + r"""

\subsection{Historical optimization and run trajectory}
\label{sec:trajectory}
The 50 printed epochs in job 16768 are shown in Figure~\ref{fig:trajectory}. The trajectories describe this development run only; its logged composite is not interchangeable with the V3C stable-tail ranking or with P6/P4 release metrics. The run reported a manifest-based balanced sampler and maximum sample weight of 4. The archived report separates targeted P8/P4 from global 14/7 validation and clinical-axis scores. Clinical-axis validation macro-F1 was recorded as zero, so the existence of an axis loss does not establish useful prediction. The aggregate epoch log is supplied without record identifiers. The report's checkpoint path and the subsequent job's declared initialization support the sequence, but do not authenticate the bytes of the intermediate checkpoint.

\begin{figure}[htbp]
\centering
\includegraphics[width=.9\linewidth]{fig16768_internal_history}
\caption{Internal training and validation trajectories printed by job 16768. Values retain the precision of the epoch log; the final report retains more digits. These are not performance estimates for released specialists.\label{fig:trajectory}}
\end{figure}
""", "R1-4/R2-3a", "Archived 16768 report and complete printed trajectory")
    table_edit("tab:app_pathology_ft", table("Archived V3F internal summary. Values are from the last of eight epochs.",
        "tab:app_pathology_ft", ["Recorded field","Value"], [["Rhythm validation windows","144"],
        ["Pathology validation windows","776"], ["Rhythm macro-F1","0.751823"], ["Rhythm top-1","0.708333"],
        ["P4 macro-F1","0.518821"]]), "R1-4/R2-3a", "Historical SHA-matched V3F reports")
    table_edit("tab:app_path_spec", table("Archived internal P4 calibration observations and cutoffs.",
        "tab:app_path_spec", ["Panel","Windows","Cutoff","Internal accuracy","Internal F1"],
        [[a,b,c,d,e] for a,b,c,d,e in [("ASMI",432,.670,.7940,.7813),("LVH",374,.705,.7487,.7513),
                                     ("IMI",492,.635,.7927,.8075),(r"ISC\_",194,.595,.8814,.8856)]]),
        "R2-3a/R2-4e", "CEDIA 17296 calibration receipt")
    table_edit("tab:app_optuna_trials", table("Nine retained V3C candidates; selection by stable-tail rank, not peak.",
        "tab:app_optuna_trials", ["Trial","Ranking score","Peak composite"],
        [[r["trial"],r["ranking_score"],r["peak_composite_score"]] for r in opt_rows]), "R1-4", "V3C recovered trials CSV")
    table_edit("tab:app_source_primary6", r"\input{tables/p6_sources}", "R1-1/R2-3a", "P6 archived source groups")
    table_edit("tab:app_source_primary4", r"\input{tables/p4_sources}", "R1-1/R2-3a", "P4 archived source groups")
    table_edit("tab:app_quarantine_transitions", table("Scope of routing evidence. Historical June entries are not estimable.",
        "tab:app_quarantine_transitions", ["Analysis","Unit","Outcome"],
        [["June historical quarantine","ECG","Not estimable"], ["SPH later joint policy","ECG","2,478/12,869 withheld"],
         ["LUDB later P6 fallback","ECG","48/48 routed to P6"],
         ["LUDB unresolved after fallback","Known opportunities","77/924"]]), "R2-4k", "Later selective and fallback results")
    table_edit("tab:app_calibration_reference", r"\input{tables/classes_p8}", "R2-4e", "P8 release thresholds and saved fallback")
    table_edit("tab:app_record_schema", table("Minimum fields used to recalculate archived selected results.",
        "tab:app_record_schema", ["Field","Use"], [["ECG identifier","Links observations within the retained analysis"],
        ["Source alias","Defines a retained source stratum, not patient independence"], ["Reference and score","Defines binary ROC and decision comparison"],
        ["Top-1 and accepted set","Defines rhythm correctness"], ["Endpoint and binary decision","Defines pathology panel counts"]],
        "@{}p{.29\\linewidth}p{.64\\linewidth}@{}"), "R1-4/R2-4k", "Saved prediction schemas; no historical clinical referral flag")
    table_edit("tab:app_hashes", r"""
To verify a published file, download it from release v0.1.0 and run
\path{sha256sum FILE} or \path{Get-FileHash -Algorithm SHA256 FILE}. Compare the full digest and byte length in Table~\ref{tab:app_hashes}. V3F and V3AG are distinct waveform backbones; V3P and V3Q are P6 and P8 specialist weights; the remaining V3AG file is the P4 specialist. The unrecovered historical Optuna database and the generic predictions file formerly listed are not represented as verified release objects.
\input{tables/release_hashes}
""", "R1-4", "Five published release v0.1.0 digests")
    bib_start = re.search(r"\\begin\{thebibliography\}\{\d+\}", s).group()
    replace(bib_start, bib_start + r"""
\bibitem[Reyna et~al.(2022)]{Reyna2022Challenge}
Reyna, M.A.; et al. Issues in the automated classification of multilead ECGs using heterogeneous labels and populations. \emph{Physiol. Meas.} \textbf{2022}, 43, 084001. doi:10.1088/1361-6579/ac79fd.
\bibitem[Wagner et~al.(2020)]{Wagner2020PTBXL}
Wagner, P.; et al. PTB-XL, a large publicly available electrocardiography dataset. \emph{Sci. Data} \textbf{2020}, 7, 154. doi:10.1038/s41597-020-0495-6.
\bibitem[Rossi et~al.(2026)]{Rossi2026AF}
Rossi, M.; et al. Clinical characteristics and outcomes of first diagnosed atrial fibrillation: Insights from 2 prospective registries in Europe and Asia. \emph{Heart Rhythm} \textbf{2026}, 23, 356--367. doi:10.1016/j.hrthm.2025.08.007.""")
    bib_fixes = {
        "Vranken2021Uncertainty": r"Vranken, J.F.; van de Leur, R.R.; et al. Uncertainty estimation for deep learning-based automated analysis of 12-lead electrocardiograms. \emph{Eur. Heart J. Digit. Health} \textbf{2021}, 2, 401--415. doi:10.1093/ehjdh/ztab045.",
        "Mastoi2022DERMA": r"Mastoi, Q.; Wah, T.Y.; et al. Novel DERMA Fusion Technique for ECG Heartbeat Classification. \emph{Life} \textbf{2022}, 12, 842. doi:10.3390/life12060842.",
        "Herman2024": r"Herman, R.; Demolder, A.; et al. Validation of an automated artificial intelligence system for 12-lead ECG interpretation. \emph{J. Electrocardiol.} \textbf{2024}, 82, 147--154. doi:10.1016/j.jelectrocard.2023.12.009.",
        "Elsheikhy2025Lightweight": r"Elsheikhy, D.H.; Hassan, A.S.; Yhiea, N.M.; Fareed, A.M.; Rashed, E.A. Lightweight Deep Learning Architecture for Multi-Lead ECG Arrhythmia Detection. \emph{Sensors} \textbf{2025}, 25, 5542. doi:10.3390/s25175542.",
        "Zhou2025Classification": r"Zhou, F.; Fang, D. Classification of multi-lead ECG based on multiple scales and hierarchical feature convolutional neural networks. \emph{Sci. Rep.} \textbf{2025}, 15, 16418. doi:10.1038/s41598-025-94127-6.",
    }
    for key, entry in bib_fixes.items():
        pat = r"(\\bibitem\[[^\]]+\]\{"+key+r"\})\n.*?(?=\n\\bibitem)"
        s, changed = re.subn(pat, lambda m, entry=entry: m[1]+"\n"+entry+"\n\n", s, flags=re.S)
        assert changed == 1
    s = re.sub(r"\\bibitem\[[^\]]+\]\{(?:Bai2024hybrid|Huang2024Efficient)\}\n.*?(?=\n\\bibitem)", "", s, flags=re.S)
    replace(r"\bibitem[He et~al.(2016)]{He2016Deep}", r"""
\bibitem[Li et~al.(2024)]{Li2024DualView}
Li, H.; Han, J.; Zhang, H.; Zhang, X.; Si, Y.; Zhang, Y.; Liu, Y.; Yang, H.
Clinical knowledge-based ECG abnormalities detection using dual-view CNN-Transformer and external attention mechanism.
\emph{Comput. Biol. Med.} \textbf{2024}, 178, 108751. doi:10.1016/j.compbiomed.2024.108751.

\bibitem[He et~al.(2016)]{He2016Deep}""")
    s = s.replace(r"\begin{figure}[H]", r"\begin{figure}[htbp]").replace(r"\begin{table}[H]", r"\begin{table}[htbp]")
    s = s.replace(r"\FloatBarrier"+"\n", "")
    s = s.replace(r"\begin{document}", r"\setlength{\headheight}{20pt}"+"\n"+r"\begin{document}")
    s = re.sub(r"\\includegraphics\[[^]]*\]\{(fig[^}]+)\.png\}",
               lambda m: rf"\includegraphics[width=\linewidth,height=.58\textheight,keepaspectratio]{{{m[1]}}}", s)
    (LATEX / "manuscrito.tex").write_text(s, encoding="utf-8", newline="\n")
    log = ["# Manuscript change ledger", "", "Original anchors are line numbers in the preserved submitted TeX.", "",
           "| Reviewer | Original line | Intervention anchor | Evidence |", "|---|---:|---|---|"]
    log += [f"| {c} | {n or 'section'} | {a[:105]} | {e} |" for c,n,a,e in changes]
    (ROOT / "MANUSCRIPT_CHANGE_LEDGER.md").write_text("\n".join(log)+"\n", encoding="utf-8")


if __name__ == "__main__":
    build()
