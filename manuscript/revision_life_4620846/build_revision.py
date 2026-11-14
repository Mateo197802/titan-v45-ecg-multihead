"""Compile the canonical LaTeX revision without rewriting its scientific content."""

import argparse
import shutil
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, help="Optional local Tectonic bundle")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    latex = root / "latex"
    output = root / "build"
    if not (latex / "Definitions/mdpi.cls").exists():
        raise SystemExit(
            "Use the complete local Overleaf ZIP, including legitimate MDPI Definitions."
        )
    output.mkdir(exist_ok=True)
    if shutil.which("pdflatex"):
        command = [
            "pdflatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-output-directory",
            str(output),
            "manuscrito.tex",
        ]
        for _ in range(2):
            subprocess.run(command, cwd=latex, check=True)
    elif shutil.which("tectonic"):
        command = ["tectonic", "--outdir", str(output)]
        if args.bundle:
            command += ["--only-cached", "--bundle", str(args.bundle.resolve())]
        subprocess.run([*command, "manuscrito.tex"], cwd=latex, check=True)
    else:
        raise SystemExit("Install a TeX distribution or upload the complete ZIP to Overleaf.")
    print(output / "manuscrito.pdf")


if __name__ == "__main__":
    main()
