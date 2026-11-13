"""Convert the same manuscript source to editable Word without MDPI class macros."""
import json
import re
import subprocess
import tempfile
from pathlib import Path
from zipfile import ZipFile

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

from reviewer_map import ROOT


def argument(source, start):
    depth = 1
    for i in range(start, len(source)):
        if source[i] in "{}" and (i == 0 or source[i-1] != "\\"):
            depth += 1 if source[i] == "{" else -1
        if depth == 0:
            return source[start:i], i+1
    raise ValueError("Unterminated LaTeX argument")


def get(source, command):
    return argument(source, source.index("\\"+command+"{")+len(command)+2)[0]


def make(output):
    latex = ROOT / "latex"
    source = (latex/"manuscrito.tex").read_text(encoding="utf-8")
    aux = (latex/"manuscrito.aux").read_text(encoding="utf-8")
    labels = dict(re.findall(r"\\newlabel\{([^{}@]+)\}\{\{([^{}]+)\}", aux))
    bib = dict(re.findall(r"\\bibcite\{([^{}]+)\}\{\{(\d+)\}", aux))
    macros = ("supplementary", "authorcontributions", "funding", "institutionalreview",
              "informedconsent", "dataavailability", "acknowledgments", "conflictsofinterest")
    authors = re.sub(r"\\orcid[A-G]\{\}", "", get(source, "Author"))
    title = get(source, "Title")
    affiliations = get(source, "address").lstrip("%\n").replace(r"\\", "\n\n")
    front = "\\title{"+title+"}\n\\author{"+authors+"}\n\\date{}\n\\begin{document}\n\\maketitle\n"
    front += affiliations+"\n\n"+get(source,"corres")+"\n\n"+get(source,"firstnote")+"\n"
    front += "\n\\section*{Abstract}\n"+get(source,"abstract")+"\n\n\\textbf{Keywords:} "+get(source,"keyword")+"\n\n"
    body = source.split(r"\begin{document}",1)[1].split(r"\end{document}",1)[0]
    body = re.sub(r"\\input\{(tables/[^{}]+)\}", lambda m: (latex/(m[1]+".tex")).read_text(), body)
    for macro in macros:
        start = body.index("\\"+macro+"{")
        value,end = argument(body,start+len(macro)+2)
        heading = {"authorcontributions": "Author contributions", "institutionalreview": "Institutional review board statement",
                   "informedconsent": "Informed consent statement", "dataavailability": "Data availability",
                   "conflictsofinterest": "Conflicts of interest"}.get(macro,macro.capitalize())
        body = body[:start] + r"\paragraph{"+heading+"}\n"+value+"\n"+body[end:]
    body = body.replace(r"\appendixtitles{yes}", "").replace(r"\appendixstart", "")
    body = body.replace(r"\abbreviations{Abbreviations}{%", r"\section*{Abbreviations}"+"\n")
    body = body.replace(r"\end{tabular}}",r"\end{tabular}", 1)
    body = re.sub(r"\\resizebox\{\\textwidth\}\{!\}\{%\s*(\\begin\{tabular\}.*?\\end\{tabular\})\s*\}", r"\1", body, flags=re.S)
    body = re.sub(r"\\includegraphics\[[^]]*\]\{(fig[^{}]+)\}",
                  lambda m: r"\includegraphics[width=.96\linewidth]{figures/"+m[1]+".png}", body)
    body = re.sub(r"(\\caption\{)([^\n]*?)(\\label\{((?:fig|tab):[^{}]+)\})",
                  lambda m: m[1]+("Figure " if m[4].startswith("fig:") else "Table ")+labels[m[4]]+". "+m[2],body)
    body = re.sub(r"\\(?:citep|cite)\{([^{}]+)\}",lambda m: "["+", ".join(bib[k] for k in m[1].split(","))+"]",body)
    body = re.sub(r"\\ref\{([^{}]+)\}",lambda m: labels[m[1]],body)
    body = re.sub(r"\\label\{[^{}]+\}", "", body)
    body = re.sub(r"\\path\{([^{}]+)\}", lambda m:r"\texttt{"+m[1].replace("_",r"\_")+"}", body)
    text, references = body.split(r"\begin{thebibliography}",1)
    refs = re.split(r"\\bibitem(?:\[[^\]]*\])?\{([^{}]+)\}", references.split(r"\end{thebibliography}",1)[0])
    body = text.replace(r"\reftitle{References}", "") + "\n\\section*{References}\n"
    for key, citation in zip(refs[1::2],refs[2::2],strict=True):
        body += f"\n[{bib[key]}] {citation.strip()}\n"
    with tempfile.TemporaryDirectory(prefix="life-docx-") as temp:
        tmp = Path(temp)
        draft = tmp/"article.tex"
        draft.write_text(front+body+"\n\\end{document}\n",encoding="utf-8")
        reference = tmp/"reference.docx"
        reference.write_bytes(subprocess.check_output(["pandoc", "--print-default-data-file", "reference.docx"]))
        style = Document(reference)
        normal = style.styles["Normal"]
        normal.font.name, normal.font.size = "Cambria", Pt(11)
        normal.paragraph_format.space_after = Pt(7)
        for name in ("Title","Heading 1","Heading 2","Heading 3"):
            style.styles[name].font.color.rgb = RGBColor(0,0,0)
        for name in ("Title","Subtitle"):
            ppr = style.styles[name]._element.get_or_add_pPr()
            for node in ppr.findall(qn("w:pBdr")):
                ppr.remove(node)
        section = style.sections[0]
        section.page_width, section.page_height = Inches(8.27), Inches(11.69)
        section.left_margin, section.right_margin = Inches(.75), Inches(.75)
        section.top_margin, section.bottom_margin = Inches(.72), Inches(.72)
        style.save(reference)
        target = output/"TITAN_V45_LIFE_4620846_REVISED.docx"
        subprocess.run(["pandoc",str(draft),"-f","latex","-t","docx","--reference-doc",str(reference),
                        "--resource-path",str(latex),"-o",str(target)],check=True,cwd=latex)
    doc = Document(target)
    width = doc.sections[0].page_width - doc.sections[0].left_margin - doc.sections[0].right_margin
    for tab in doc.tables:
        tab.autofit = False
        borders = OxmlElement("w:tblBorders")
        for edge in ("top","bottom","insideH"):
            line = OxmlElement("w:"+edge)
            line.set(qn("w:val"),"single")
            line.set(qn("w:sz"),"4")
            line.set(qn("w:color"),"ADB6BE")
            borders.append(line)
        tab._tbl.tblPr.append(borders)
        count = len(tab.columns)
        header = [c.text for c in tab.rows[0].cells]
        weights = {
            ("File","Bytes","SHA-256"): [.34,.15,.51],
            ("Descriptor","Computation and unit","Scale"): [.25,.63,.12],
            ("Source family","ECGs","Correct","Top-1","Wilson 95% CI"): [.36,.10,.12,.13,.29],
            ("Module","Description","Parameters","Scope"): [.17,.36,.17,.30],
        }.get(tuple(header), [1/count]*count)
        tw = tab._tbl.tblPr.find(qn("w:tblW"))
        tw.set(qn("w:type"),"dxa")
        tw.set(qn("w:w"),str(round(width/635)))
        for col, share in zip(tab.columns, weights, strict=True):
            col.width = round(width*share)
        for row in tab.rows:
            tr = row._tr.get_or_add_trPr()
            tr.append(OxmlElement("w:cantSplit"))
            for cell, share in zip(row.cells, weights, strict=True):
                cell.width = round(width*share)
                for p in cell.paragraphs:
                    p.paragraph_format.space_after = Pt(2)
                    p.paragraph_format.space_before = Pt(2)
                    for run in p.runs:
                        run.font.size = Pt(8.5 if count >= 7 or header[0] == "File" else 9.5)
    doc.save(target)
    with ZipFile(target) as result:
        xml = result.read("word/document.xml").decode()
        evidence = {"editable_math_objects": len(re.findall(r"<m:oMath[ >]",xml)),
                    "editable_tables": xml.count("<w:tbl>"), "embedded_images": xml.count("<w:drawing>"),
                    "format": "Editable equivalent; official Life .dot download returned HTTP 403."}
        assert evidence["editable_tables"] >= 20 and evidence["embedded_images"] == 16
        assert evidence["editable_math_objects"] >= 24
        for token in ("95.19%", "79.35%", "9,021", "2,478", "Rossi"):
            assert token in xml, token
    (output/"WORD_EDITABILITY_QA.json").write_text(json.dumps(evidence,indent=2)+"\n")


if __name__ == "__main__":
    import sys
    make(Path(sys.argv[1]).resolve())
