"""Run the public readback checks without unpacking private research inputs."""
import subprocess
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
RESULTS = "outputs/results"
REVIEW = f"{RESULTS}/reviewer_closure_experiments"
TWO = f"{RESULTS}/reviewer_two_comment_rigorous"
STAGE_A = f"{RESULTS}/specialist_heads/20261111-v2"
BM = f"{RESULTS}/benchmarkmax"


def run(*args):
    subprocess.run([sys.executable, *args], cwd=ROOT, check=True)


def main():
    run("docs/reproducibility/verify_reviewer_evidence_reconciliation.py", "--git-refs")
    run("scripts/evaluation/verify_reviewer_scientific_closure.py", "--public-dir", REVIEW,
        "--native-receipt", f"{REVIEW}/native_closure_verification.json")
    run("scripts/evaluation/build_reviewer_scientific_closure_zip.py", "verify",
        f"{REVIEW}/TITAN_V45_FOUR_REVIEWER_SCIENTIFIC_CLOSURE.zip")
    packet = ROOT / TWO / "TITAN_V45_TWO_COMMENT_SCIENTIFIC_EVIDENCE.zip"
    verifier = "scripts/evaluation/verify_reviewer_two_comment_rigorous.py"
    # The packet binds the exact original source bytes, not the integrated lint edits.
    with tempfile.TemporaryDirectory() as directory, ZipFile(packet) as archive:
        extracted = Path(directory)
        for name in archive.namelist():
            target = extracted / name
            if not target.resolve().is_relative_to(extracted.resolve()):
                raise ValueError("unsafe archive member")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(name))
        run(verifier, "--results", str(extracted / "results"), "--docs",
            str(extracted / "docs"), "--zip", str(packet), "--source-root", directory)
        for base, source in ((TWO, "results"), ("docs/reviewer_two_comment_rigorous", "docs")):
            for file in (extracted / source).iterdir():
                if file.read_bytes() != (ROOT / base / file.name).read_bytes():
                    raise ValueError(f"published evidence differs from packet: {file.name}")

    run("scripts/specialist_experiments/verify_aggregate_results.py",
        "--per-class", f"{STAGE_A}/SPECIALIST_PER_CLASS_RESULTS.csv",
        "--comparison", f"{STAGE_A}/SPECIALIST_MODEL_COMPARISON.csv")
    run("scripts/external_validation/validate_sph_aggregate.py",
        "--aggregate", f"{RESULTS}/external_sph/sph_aggregate_normalized_32669.json",
        "--protocol", "configs/external_validation/sph_frozen.json")
    run("scripts/benchmarkmax/verify_sph_b1_aggregate.py", "--report", f"{BM}/sph_b1_calibration_32758.json",
        "--config", "configs/benchmarkmax/sph_b1_calibration.json",
        "--calibrator", "scripts/benchmarkmax/calibrate_sph_frozen_scores.py", "--expected-job-id", "32758")
    run("scripts/benchmarkmax/verify_sph_scale_sensitivity.py", "--report",
        f"{BM}/sph_scale_sensitivity_32761.json", "--expected-job-id", "32761",
        "--expected-experiment-commit", "a2353f0863f05e4b1ea844f9b0c4dd4e270a6c85")
    run("scripts/benchmarkmax/verify_sph_prevalence_comparison.py", "--report",
        f"{BM}/sph_b1_prevalence_comparison_32763.json",
        "--config", "configs/benchmarkmax/sph_b1_prevalence_comparison.json",
        "--runner", "scripts/benchmarkmax/compare_sph_prevalence_baseline.py",
        "--registry", "docs/benchmarkmax/BENCHMARKMAX_EXPERIMENT_REGISTRY.json", "--expected-job-id", "32763")


if __name__ == "__main__":
    main()
