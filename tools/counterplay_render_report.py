"""Regenerate the scoped feasibility report from small published evidence.

Rendering uses the separate paper/requirements-render.txt environment. It
does not train, regenerate episodes, or access raw/locked data.
"""
from __future__ import annotations

import csv
import argparse
from datetime import datetime, timezone
import hashlib
import html
import importlib.metadata
import json
import os
from pathlib import Path
import re
import subprocess
import time

os.environ.setdefault("MPLCONFIGDIR", "/tmp/counterplay-matplotlib")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                               TableStyle, Image, Preformatted)
from pypdf import PdfReader
from research_ledger import Ledger

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def evidence():
    records = []
    inputs = {}
    for name in ("docs/validation/CP01_DATA_DIAGNOSIS_2026-10-25.json",
                 "docs/validation/CP01_FINAL_SCREEN_DISPOSITION_2026-10-25.json",
                 "docs/validation/CP01_GRADIENT_REPAIR_2026-10-25.json"):
        inputs[name] = sha(ROOT / name)
    for attempt in (1, 2):
        path = ROOT / f"docs/validation/CP01_DATA_ATTEMPT{attempt}_2026-10-25.json"
        receipt = json.loads(path.read_text())
        units = ROOT / f"research/results/cp01-attempt{attempt}-roots.csv"
        rows = list(csv.DictReader(units.open()))
        if receipt["phase"] != "development-data-feasibility" or receipt["status"] != "failed_feasibility_gate":
            raise ValueError("this report is limited to the two failed development screens")
        inputs[str(path.relative_to(ROOT))] = sha(path)
        inputs[str(units.relative_to(ROOT))] = sha(units)
        for game in ("connect4-6x7", "reversi6"):
            audit = receipt["audit"]["development:" + game]
            selected = [r for r in rows if r["game"] == game]
            complete = sum(r["status"] == "complete" for r in selected)
            pairable = sum(int(r["pairable"]) for r in selected if r["pairable"] != "")
            support = sum(int(r["potential_nonzero_signed_support"]) for r in selected
                          if r["potential_nonzero_signed_support"] != "")
            assert len(selected) == audit["attempted_unique_roots"]
            assert complete == audit["complete_references"]
            assert pairable == audit["reference_pairable_roots"]
            if attempt == 2:
                assert support == audit["potential_nonzero_signed_support_roots"]
            records.append({"attempt": attempt, "game": game, "episodes": audit["generated_episodes"],
                            "candidates": len(selected), "complete": complete, "pairable": pairable,
                            "potential_sign_support": support, "no_candidate": audit.get("no_candidate_root", 0)})
    return records, inputs


def make_tables(records):
    lines = ["Table 1. Finite development-screen counts; screens reuse the same episodes.", "",
             "| Screen | Game | Episodes | No candidate | Complete / attempted | Pairable | Potential nonzero support |",
             "| --- | --- | ---: | ---: | ---: | ---: | ---: |"]
    for r in records:
        lines.append(f"| {r['attempt']} | {r['game']} | {r['episodes']} | {r['no_candidate']} | {r['complete']} / {r['candidates']} | {r['pairable']} | {r['potential_sign_support']} |")
    lines += ["", "Potential support was diagnosed after screen 1 and frozen as a necessary gate before screen 2. It is not actual model matching.", "",
              "Table 2. Builder resources; excludes tests, agent work and rendering.", "",
              "| Screen | Wall seconds | CPU seconds | Peak RSS bytes | Windows train / development |",
              "| --- | ---: | ---: | ---: | ---: |"]
    for attempt in (1, 2):
        r = json.loads((ROOT / f"docs/validation/CP01_DATA_ATTEMPT{attempt}_2026-10-25.json").read_text())
        train = sum(a["selected_windows"] for k, a in r["audit"].items() if k.startswith("train:"))
        dev = sum(a["selected_windows"] for k, a in r["audit"].items() if k.startswith("development:"))
        lines.append(f"| {attempt} | {r['wall_seconds']:.3f} | {r['cpu_seconds']:.3f} | {r['peak_rss_bytes']:,} | {train} / {dev} |")
    return "\n".join(lines)


def make_figure(records):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "svg.hashsalt": "cp01-feasibility"})
    fig, ax = plt.subplots(figsize=(7.1, 3.7), layout="constrained")
    labels = ["Screen 1: C4 (<=8)", "Screen 1: Reversi (<=6)",
              "Screen 2: C4 (<=12)", "Screen 2: Reversi (<=6)"]
    x = list(range(4))
    specs = [("complete", -0.24, "#326b91", "Complete references"),
             ("pairable", 0, "#cb7b32", "Reference-pairable"),
             ("potential_sign_support", 0.24, "#438777", "Possible nonzero signed support")]
    for key, offset, color, label in specs:
        bars = ax.bar([i + offset for i in x], [r[key] for r in records], width=0.22, color=color, label=label)
        ax.bar_label(bars, padding=3, fontsize=8)
    ax.set_xticks(x, labels, rotation=10, ha="right")
    ax.set_ylim(0, 59)
    ax.set_ylabel("Root count (50 development episodes/game)")
    ax.set_title("Reference eligibility failed in both Connect Four screens", loc="left", fontsize=12, pad=12)
    ax.legend(loc="upper center", frameon=False, fontsize=7.5, ncol=3)
    ax.spines[["top", "right"]].set_visible(False)
    ax.yaxis.grid(True, alpha=0.15); ax.set_axisbelow(True)
    dest = ROOT / "paper/figures"
    dest.mkdir(parents=True, exist_ok=True)
    fig.savefig(dest / "feasibility.png", dpi=220)
    fig.savefig(dest / "feasibility.svg", metadata={"Date": None})
    plt.close(fig)


def inline(text):
    text = html.escape(text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" color="#245578">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', text)
    return text


def render_pdf(markdown, output):
    for family, filename in (("Research", "DejaVuSerif.ttf"), ("ResearchBold", "DejaVuSerif-Bold.ttf")):
        directory = Path(font_manager.findfont("DejaVu Serif")).parent
        pdfmetrics.registerFont(TTFont(family, str(directory / filename)))
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ResearchBody", fontName="Research", fontSize=9.3, leading=13.6,
                              spaceAfter=7, alignment=TA_LEFT))
    styles.add(ParagraphStyle(name="ResearchTitle", fontName="ResearchBold", fontSize=20, leading=25, spaceAfter=16))
    styles.add(ParagraphStyle(name="ResearchH2", fontName="ResearchBold", fontSize=12.5, leading=16, spaceBefore=14, spaceAfter=8, keepWithNext=True))
    styles.add(ParagraphStyle(name="ResearchH3", fontName="ResearchBold", fontSize=10, leading=14, spaceBefore=10, spaceAfter=6, keepWithNext=True))
    styles.add(ParagraphStyle(name="ResearchCell", fontName="Research", fontSize=6.6, leading=8.4))
    story = []
    lines = markdown.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if not line:
            index += 1; continue
        if line.startswith("# "):
            story.append(Paragraph(inline(line[2:]), styles["ResearchTitle"]))
        elif line.startswith("### "):
            story.append(Paragraph(inline(line[4:]), styles["ResearchH3"]))
        elif line.startswith("## "):
            story.append(Paragraph(inline(line[3:]), styles["ResearchH2"]))
        elif line.startswith("!["):
            story.append(Image(str(ROOT / "paper/figures/feasibility.png"), width=170*mm, height=88.6*mm))
            caption = line.split("](", 1)[0][2:]
            story.append(Paragraph(inline(caption), styles["ResearchCell"]))
        elif line.startswith("|"):
            rows = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                cells = [c.strip() for c in lines[index].strip().strip("|").split("|")]
                if not all(re.fullmatch(r"[-: ]+", c) for c in cells):
                    rows.append([Paragraph(inline(c), styles["ResearchCell"]) for c in cells])
                index += 1
            widths = ([14, 31, 16, 19, 27, 20, 43] if len(rows[0]) == 7 else [17, 31, 31, 40, 51])
            table = Table(rows, colWidths=[x*mm for x in widths], repeatRows=1, hAlign="LEFT")
            table.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#e9eff2")),
                                       ("LINEBELOW", (0,0), (-1,0), 0.5, colors.HexColor("#647786")),
                                       ("VALIGN", (0,0), (-1,-1), "TOP"),
                                       ("TOPPADDING", (0,0), (-1,-1), 5),
                                       ("BOTTOMPADDING", (0,0), (-1,-1), 5)]))
            story.extend([table, Spacer(1, 9)]); continue
        elif re.match(r"^\d+\. ", line):
            story.append(Paragraph(inline(line), styles["ResearchBody"]))
        else:
            paragraph = [line]
            index += 1
            while index < len(lines) and lines[index].strip() and not lines[index].startswith(("#", "|", "![")):
                paragraph.append(lines[index].strip()); index += 1
            story.append(Paragraph(inline(" ".join(paragraph)), styles["ResearchBody"])); continue
        index += 1
    def footer(canvas, doc):
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#56636e"))
        canvas.drawString(20*mm, 13*mm, "Counterplay CP-01 | Scoped feasibility technical report | 25 October 2026")
        canvas.drawRightString(A4[0]-20*mm, 13*mm, str(doc.page))
    output.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(output), pagesize=A4, leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=19*mm, bottomMargin=22*mm, title="Counterplay CP-01: Feasibility report",
                            author="Counterplay project", pageCompression=1, invariant=1)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def build_report(commit):
    records, inputs = evidence()
    tables = make_tables(records)
    (ROOT / "paper/tables.md").write_text(tables + "\n")
    (ROOT / "paper/table-data.json").write_text(json.dumps(records, indent=2) + "\n")
    make_figure(records)
    source = ROOT / "paper/manuscript-source.md"
    text = source.read_text().replace("{{GENERATED_TABLES}}", tables)
    assert "{{" not in text and "TODO" not in text
    manuscript = ROOT / "paper/counterplay-feasibility.md"
    manuscript.write_text(text)
    pdf = ROOT / "output/pdf/counterplay-feasibility.pdf"
    render_pdf(text, pdf)
    pages = PdfReader(str(pdf)).pages
    extracted = "\n".join(p.extract_text() or "" for p in pages)
    assert len(pages) >= 4 and "31.534" in extracted and "59" in extracted
    assert "{{" not in extracted
    outputs = [manuscript, pdf, ROOT / "paper/tables.md", ROOT / "paper/table-data.json",
               ROOT / "paper/figures/feasibility.png", ROOT / "paper/figures/feasibility.svg"]
    manifest = {"schema": "counterplay.scoped-report.v1", "phase": "descriptive-feasibility-report",
                "analysis_commit": commit, "source_clean_at_start": True,
                "inputs": inputs | {"paper/manuscript-source.md": sha(source), "tools/counterplay_render_report.py": sha(__file__)},
                "outputs": {str(p.relative_to(ROOT)): sha(p) for p in outputs}, "pdf_pages": len(pages),
                "analysis_rows": len(records), "per_root_rows": sum(r["candidates"] for r in records), "model_fits": 0,
                "environment": {p: importlib.metadata.version(p) for p in ("reportlab", "matplotlib", "pypdf")},
                "verification": "receipt/CSV counts reconcile; PDF text extracted; visual page inspection still required"}
    (ROOT / "paper/artifact-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"pdf": str(pdf), "pages": len(pages), "count_rows": len(records),
                      "per_root_rows": sum(r["candidates"] for r in records)}))
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default="cp01-report-render-20261025-attempt1")
    args = parser.parse_args()
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True):
        raise ValueError("report generation requires clean pinned source")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    _, inputs = evidence()
    inputs["manuscript_source"] = sha(ROOT / "paper/manuscript-source.md")
    with Ledger(ROOT / "chess_data/research_metrics.sqlite") as ledger:
        # Input names are stable identifiers rather than path strings.
        ledger.create_run({"run_id": args.run_id, "phase": "workflow", "protocol_id": "counterplay-feasibility-report-v1",
                           "code_commit": commit, "config": {"source_inputs": inputs},
                           "inputs": {"render_source": sha(__file__), "source_text": inputs["manuscript_source"]},
                           "environment": {"python": __import__("sys").version,
                                           "reportlab": importlib.metadata.version("reportlab"),
                                           "matplotlib": importlib.metadata.version("matplotlib")}})
        started = time.perf_counter()
        try:
            manifest = build_report(commit)
            ledger.record(args.run_id, "generated", "paper_artifact", metrics={"pdf_pages": manifest["pdf_pages"],
                          "count_rows": manifest["analysis_rows"], "root_unit_rows": manifest["per_root_rows"],
                          "wall_seconds": time.perf_counter() - started},
                          dimensions={"artifact_manifest_sha256": sha(ROOT / "paper/artifact-manifest.json")},
                          note="Text and count checks pass; separate visual and independent claims review still required")
        except BaseException as error:
            ledger.record(args.run_id, "failure", "failure", metrics={"wall_seconds": time.perf_counter()-started},
                          dimensions={"exception": type(error).__name__}, note=str(error))
            raise


if __name__ == "__main__":
    main()
