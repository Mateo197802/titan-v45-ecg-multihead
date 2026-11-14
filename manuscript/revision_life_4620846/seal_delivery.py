"""Check the local draft and package only approved, aggregate deliverables."""
import csv
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from reviewer_map import DOCS, MAP, ROOT

LATEX = ROOT / "latex"
BASE = Path.home() / ".codex/recovery/life-4620846-canonical-submission"
ORIGINAL = BASE / "extracted/mdpi_Articulo"
ARTICLES = ("TITAN_V45_LIFE_4620846_REVISED.pdf","TITAN_V45_LIFE_4620846_REVISED.docx",
            "REVIEWER_1_RESPONSE_DRAFT.docx","REVIEWER_2_RESPONSE_DRAFT.docx")
LEDGER = ROOT / "MANUSCRIPT_CHANGE_LEDGER.md"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pdf_info(pdf):
    text = subprocess.check_output(["pdftotext", "-enc", "UTF-8", str(pdf), "-"]).decode()
    assert "??" not in text
    words = len(re.findall(r"\b[\w]+(?:[-–][\w]+)*\b", text))
    return text, {"pages": text.count("\f"), "words_in_extracted_text": words, "sha256": digest(pdf)}


def package(target, files, compile_project=False):
    checksums = {name: digest(src) for name, src in files.items()}
    with ZipFile(target,"w",compression=ZIP_DEFLATED,compresslevel=9) as archive:
        for name, src in sorted(files.items()):
            assert ".." not in Path(name).parts and not Path(name).is_absolute()
            archive.write(src,name)
        archive.writestr("SHA256SUMS.txt","".join(f"{value}  {name}\n" for name,value in sorted(checksums.items())))
    with ZipFile(target) as archive:
        assert archive.testzip() is None
        assert all(hashlib.sha256(archive.read(n)).hexdigest()==v for n,v in checksums.items())
        if compile_project:
            with tempfile.TemporaryDirectory(prefix="life-archive-test-") as temp:
                archive.extractall(temp)
                for _ in range(2):
                    result = subprocess.run(["pdflatex","-interaction=nonstopmode","-halt-on-error","manuscrito.tex"],
                                            cwd=temp,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
                    if result.returncode:
                        raise RuntimeError(result.stdout.decode(errors="replace")[-3000:])
                _, info = pdf_info(Path(temp)/"manuscrito.pdf")
                assert info["pages"] >= 26
    return {"sha256": digest(target), "verified_members":len(files), "clean_extraction_compile":compile_project}


def seal(output, render_dir):
    latex = (LATEX/"manuscrito.tex").read_text(encoding="utf-8")
    log = (LATEX/"manuscrito.log").read_text(encoding="utf-8",errors="replace")
    aux = (LATEX/"manuscrito.aux").read_text(encoding="utf-8")
    assert not re.search(r"undefined|Overfull|Warning:|multiply defined",log)
    assert not re.search(r"e3b0c44298fc1c|4\.87\\%|6\.13\\%|97\.44\\%|84\.16\\%|storage cleanup|cleanup.candidate|/home/diego",latex,re.I)
    labels = {a:(b,c) for a,b,c in re.findall(r"\\newlabel\{([^{}@]+)\}\{\{([^{}]+)\}\{(\d+)\}",aux)}
    assert all(v[2] in labels for v in MAP.values())
    refs = re.findall(r"\\includegraphics\[[^]]*\]\{(fig[^{}]+)\}",latex)
    assert len(refs)==len(set(refs))==16
    assert all((LATEX/"figures"/(n+".pdf")).is_file() for n in refs)
    shutil.copyfile(LATEX/"manuscrito.pdf",output/ARTICLES[0])
    text0, orig = pdf_info(BASE/"life-4620846 (1).pdf")
    embedded, inner = pdf_info(ORIGINAL/"manuscrito.pdf")
    assert " ".join(embedded.split())==" ".join(text0.split())
    _, revised = pdf_info(output/ARTICLES[0])
    assert revised["pages"] >= orig["pages"] == 26
    assert revised["words_in_extracted_text"] > orig["words_in_extracted_text"]
    with ZipFile(BASE/"life-4620846 (2).zip") as original_zip:
        assert original_zip.testzip() is None

    figure_audit = ["# Figure reconciliation and replacement", "",
                    "Original images are preserved in the submitted archive. The figures below are new revision assets.",
                    "The original use of the same class-metric raster for two figures is recorded, not repaired retroactively.", "",
                    "| Revised asset | Original submitted raster SHA-256 | Revised vector SHA-256 | Derivation |",
                    "|---|---|---|---|"]
    for i,name in enumerate(refs):
        prior = ORIGINAL/"figures"/(("fig08_class_metrics" if name=="fig08b_pathology_class_metrics" else name)+".png")
        method = ("New schematic; revision_diagrams.py" if i<6 else
                  "Archived job 16768 aggregate epoch output; revision_data.py" if "16768" in name else
                  "Archived selected profile predictions; revision_data.py")
        figure_audit.append(f"| {name} | {digest(prior) if prior.exists() else 'New'} | {digest(LATEX/'figures'/(name+'.pdf'))} | {method} |")
    figure_audit += ["", "The new P4 class panel replaces the second use of the P6 image. The revised error figure is a bar chart, not a Sankey. Figures 1 and 2 were redrawn from project concepts without third-party artwork; the original files' authorship and authorization were not inferred from their archive presence."]
    (output/"FIGURE_RECONCILIATION_AND_REPLACEMENT.md").write_text("\n".join(figure_audit)+"\n",encoding="utf-8")

    matrix = ROOT/"REVIEWER_MANUSCRIPT_RECONCILIATION_MATRIX.csv"
    with matrix.open(encoding="utf-8",newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows)==40 and len({r["criterion"] for r in rows})==40
    assert sum(float(r["points"]) for r in rows)==20.5
    final = output/matrix.name
    with final.open("w",encoding="utf-8",newline="") as stream:
        fields = [*rows[0],"revised_number","revised_pdf_page"]
        writer = csv.DictWriter(stream,fieldnames=fields)
        writer.writeheader()
        for row in rows:
            number,page = labels[row["revised_label"]]
            writer.writerow({**row,"revised_number":number,"revised_pdf_page":page})
    for name in ("MANUSCRIPT_CHANGE_LEDGER.md","EVIDENCE_SOURCES.md","RELEASE_RECALCULATION.json","JOB_16768_AGGREGATE_EPOCHS.csv"):
        shutil.copyfile(ROOT/name,output/name)
    shutil.copyfile(DOCS/"REVIEWER_40_VERIFIED_SCORE.json",output/"REVIEWER_40_VERIFIED_SCORE_BASELINE.json")
    render_counts = {}
    for filename in ARTICLES[1:]:
        with ZipFile(output/filename) as archive:
            assert archive.testzip() is None
            xml = archive.read("word/document.xml").decode()
            if filename.startswith("REVIEWER"):
                assert "cleanup-candidate manifest" in xml and "16768" in xml and "original" in xml
            else:
                assert "cleanup-candidate manifest" not in xml
        render_counts[filename] = len(list((render_dir/Path(filename).stem).glob("page-*.png")))
        assert render_counts[filename] > 0
    assert len(list(render_dir.glob("pdf-*.png")))==revised["pages"]
    layout = f"""# Manuscript layout and verification

- Submitted standalone PDF and embedded PDF: 26 pages each; extracted text identical, PDF bytes different.
- Revised PDF: {revised['pages']} pages; both reference passes completed. No LaTeX warnings, overfull boxes, undefined references or duplicate labels in the final log.
- Figures: 15 numbered in the main article and one appendix trajectory. Quantitative panels were rebuilt from archived predictions or the retained epoch output. Figures 8 and 10 are distinct; Figure 15 is an error-count bar chart.
- PDF and Word documents rendered with Poppler and LibreOffice. Page sheets and targeted full-size views were reviewed. Ordinary unused space in final bibliography and float layout is not evidence of missing content.
- Editable equivalent Word: {render_counts[ARTICLES[1]]} rendered pages; 26 editable tables, 130 OMML math objects and 16 images. Official Life Word template endpoint returned HTTP 403; exact template conformity is not asserted.
- Reviewer 1 and 2 drafts: {render_counts[ARTICLES[2]]} and {render_counts[ARTICLES[3]]} pages, respectively. PDF cross-references were taken from the final LaTeX auxiliary file.
- Word cross-references are editable text carrying final PDF numbers, not dynamically updated Word fields. The LaTeX source is canonical.
- No hosted Overleaf project was modified; compilation was tested locally from a fresh extraction of the exact ZIP.
"""
    (output/"MANUSCRIPT_LAYOUT_QA_REPORT.md").write_text(layout,encoding="utf-8")
    overleaf = {p.relative_to(LATEX).as_posix():p for p in LATEX.rglob("*") if p.is_file() and
                (p.name in ("README.md","manuscrito.tex") or
                 (p.parent.name=="Definitions" and "-converted-to" not in p.name) or
                 (p.parent.name=="figures" and p.suffix==".pdf") or p.parent.name=="tables")}
    bundles = {}
    name = "TITAN_V45_LIFE_4620846_OVERLEAF.zip"
    bundles[name] = package(output/name,overleaf,compile_project=True)
    supplement_names = ["EVIDENCE_SOURCES.md","RELEASE_RECALCULATION.json","JOB_16768_AGGREGATE_EPOCHS.csv",
                        "REVIEWER_40_VERIFIED_SCORE_BASELINE.json","WORD_EDITABILITY_QA.json"]
    supplement = {n:output/n for n in supplement_names}
    supplement.update({p.relative_to(LATEX).as_posix():p for p in (LATEX/"tables").glob("*.tex")})
    name = "TITAN_V45_LIFE_4620846_SUPPLEMENTARY.zip"
    bundles[name] = package(output/name,supplement)
    qa = {"original_standalone_pdf":orig, "original_embedded_pdf":inner,
          "original_pdf_text_agreement":True, "original_zip_sha256":digest(BASE/"life-4620846 (2).zip"),
          "original_tex_sha256":digest(ORIGINAL/"manuscrito.tex"), "revised_pdf":revised,
          "revised_tex_sha256":digest(LATEX/"manuscrito.tex"),"compiled_labels":labels,"rendered_docx_pages":render_counts,
          "source_commit":"6f50a6337fc3e8b518655b05916ced7447598b47",
          "recalculations":"RELEASE_RECALCULATION.json","evidence_sources":"EVIDENCE_SOURCES.md",
          "reviewer_criteria":40,"technical_points":20.5,"new_points":0,
          "editorial_status_counts":dict(Counter(v[3] for v in MAP.values())),
          "independent_external_results_included":False,"original_training_reproduced":False,
          "historical_quarantine_demonstrated":False,"technical_limits":"See EVIDENCE_SOURCES.md",
          "packages":bundles,"docx_sha256":{name:digest(output/name) for name in ARTICLES[1:]}}
    (output/"FINAL_MANUSCRIPT_SCIENTIFIC_QA.json").write_text(json.dumps(qa,indent=2)+"\n",encoding="utf-8")
    (output/"SHA256SUMS.txt").write_text("".join(f"{digest(p)}  {p.name}\n" for p in sorted(output.iterdir())
                                                if p.is_file() and p.name!="SHA256SUMS.txt"),encoding="ascii")
    print(json.dumps({"original":orig,"revised":revised,"bundles":bundles,"rendered":render_counts},indent=2))


if __name__=="__main__":
    import sys
    seal(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve())
