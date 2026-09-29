"""Plot a verified v2/v2.1/v2.2 report without fitting or model scoring.

Usage: python tools/plot_v2_development.py REPORT.json OUTPUT_BASENAME
Writes OUTPUT_BASENAME.png and OUTPUT_BASENAME.pdf; existing outputs are refused.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import textwrap


FAMILIES = ("direct", "value-dynamics", "decoded", "rjepa", "raw-jepa", "no-response")
CONTROLS = ("direct", "decoded", "value-dynamics")
V22_FAMILIES = ("direct", "value-dynamics", "decoded", "raw-jepa", "ema-value", "raw-no-response")
V22_CONTROLS = ("direct", "decoded", "value-dynamics", "ema-value")
LABELS = {"direct": "Direct policy/value", "value-dynamics": "Value dynamics",
          "decoded": "Decoded dynamics", "rjepa": "Projected JEPA",
          "raw-jepa": "Raw JEPA", "no-response": "No-response ablation",
          "ema-value": "EMA-value dynamics", "raw-no-response": "Raw no-response ablation"}
VERSIONS = {"v2-development-report01": "Development study (v2, grid 01)",
            "v21-development-report02": "Symmetry-augmented development (v2.1, grid 02)",
            "v22-development-report03": "Restricted-label development (v2.2, grid 03)"}
GAMES = {"connect4-4x5", "reversi6"}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _number(value, label, minimum=-2, maximum=2):
    _require(type(value) in (int, float) and math.isfinite(value)
             and minimum <= value <= maximum, "Invalid " + label)
    return float(value)


def extract(report):
    """Extract saved aggregates only, failing closed on incomplete evidence.

    This validates the report schema and completed-row status. Artifact hashes
    must already have been verified by the corresponding grid report generator;
    plotting does not re-run that verifier or recompute statistical intervals.
    """
    _require(report.get("version") in VERSIONS, "Unsupported report version")
    restricted = report["version"] == "v22-development-report03"
    families = V22_FAMILIES if restricted else FAMILIES
    controls = V22_CONTROLS if restricted else CONTROLS
    _require(report.get("stage") == "development", "Only development reports are supported")
    _require(report.get("verification_errors") == [], "Report has missing/failed verification")
    _require(report.get("status") in ("not_promoted", "development_screen_passed"),
             "Inconclusive or incomplete reports cannot be plotted as valid comparisons")
    commit = report.get("code_commit")
    _require(isinstance(commit, str) and re.fullmatch(r"[0-9a-f]{40}", commit),
             "Missing full source commit")
    runs = report.get("runs")
    expected_cells = {"v2-development-report01": 36, "v21-development-report02": 60,
                      "v22-development-report03": 72}[report["version"]]
    _require(isinstance(runs, list) and len(runs) == expected_cells, "Incomplete frozen run inventory")
    _require(len({run["id"] for run in runs}) == len(runs), "Duplicate run identifiers")
    seeds = sorted({run["config"]["seed"] for run in runs})
    _require(seeds == [17, 29, 43], "Unexpected training seed inventory")
    if restricted:
        expected = {(f, v, rate, seed) for f in (.25, 1.) for v in families
                    for rate in (.001, .0003) for seed in seeds}
        observed = {(r.get("fraction"), r["config"]["variant"], r["config"]["learning_rate"],
                     r["config"]["seed"]) for r in runs}
        _require(observed == expected, "Incomplete restricted-label cell inventory")
    cohort_counts = None
    for run in runs:
        _require(run.get("status") == "complete" and not run.get("verification_error"),
                 "A declared run failed or is unverified")
        counts = run.get("decision_status_counts", {})
        _require(type(counts.get("complete")) is int and counts["complete"] > 0
                 and counts.get("censored") == counts.get("error") == 0,
                 "Failed or censored decisions cannot be silently omitted")
        metrics = run.get("metrics", {})
        _require(set(metrics) == GAMES, "Missing game metrics")
        schedule = {}
        for game in sorted(GAMES):
            for track in ("exact", "hybrid"):
                row = metrics[game][track]
                _require(type(row.get("scheduled")) is int and row["scheduled"] > 0
                         and row.get("complete") == row["scheduled"]
                         and row.get("censored_or_error") == 0,
                         "Incomplete per-game decisions")
                schedule[game, track] = row["scheduled"]
        _require(sum(schedule.values()) == counts["complete"], "Decision counts disagree")
        if cohort_counts is None:
            cohort_counts = schedule
        _require(schedule == cohort_counts, "Run schedules differ")
    promotion = report.get("promotion")
    _require(isinstance(promotion, dict) and promotion.get("status") == report["status"],
             "Missing or inconsistent promotion report")
    if restricted:
        _require(promotion.get("primary_fraction") == .25, "Primary regime must select 25% of roots")
    selected = promotion.get("selected", {})
    _require(set(selected) == set(families), "Missing tuned family")
    candidate = promotion.get("candidate")
    eligible = ("raw-jepa",) if restricted else ("rjepa", "raw-jepa")
    _require(isinstance(candidate, dict) and candidate.get("variant") in eligible
             and candidate.get("collapse") == [], "No eligible JEPA candidate")
    bars = []
    for family in families:
        row = selected[family]
        _require(row.get("variant") == family, "Family identity mismatch")
        if restricted:
            _require(row.get("fraction") == .25, "A plotted family uses a nonprimary regime")
        value = _number(row["mean_regret"], "mean regret", 0, 2)
        rate = _number(row["learning_rate"], "learning rate", 1e-12, 1)
        weight = row.get("jepa_weight")
        if weight is not None:
            weight = _number(weight, "auxiliary weight", 0, 100)
        _require(isinstance(row.get("collapse"), list), "Missing collapse diagnostic")
        bars.append({"family": family, "regret": value, "learning_rate": rate,
                     "jepa_weight": weight, "collapsed": bool(row["collapse"])})
    candidate_family = candidate["variant"]
    for key in (("mean_regret", "learning_rate", "jepa_weight", "fraction") if restricted
                else ("mean_regret", "learning_rate", "jepa_weight")):
        _require(candidate.get(key) == selected[candidate_family].get(key), "Candidate differs from tuned family")
    comparisons = promotion.get("comparisons", {})
    _require(set(comparisons) == set(controls), "Missing paired control comparison")
    intervals = []
    for family in controls:
        row = comparisons[family]
        bootstrap = row.get("bootstrap", {})
        bounds = bootstrap.get("aggregate_ci95")
        _require(isinstance(bounds, list) and len(bounds) == 2, "Missing saved 95% interval")
        low, high = (_number(v, "interval endpoint") for v in bounds)
        _require(low <= high, "Reversed interval endpoints")
        improvement = _number(row["aggregate_improvement"], "paired improvement")
        _require(set(row.get("per_seed_improvement", {})) == set(map(str, seeds)),
                 "Missing paired seed effects")
        _require(bootstrap.get("replicates") == 2000 and bootstrap.get("seed") == 901,
                 "Unexpected bootstrap protocol")
        if restricted:
            _require(bootstrap.get("label_mask_scope") ==
                     "One fixed label mask; no resampling of label-selection seeds",
                     "Missing fixed-label-mask interval scope")
        intervals.append({"family": family, "improvement": improvement, "low": low, "high": high})
    return {"title": VERSIONS[report["version"]], "status": report["status"],
            "candidate": candidate_family, "bars": bars, "intervals": intervals,
            "restricted_labels": restricted,
            "seeds": seeds, "source_commit": commit,
            "game_counts": {game: cohort_counts[game, "exact"] for game in sorted(GAMES)}}


def render(report_path, output_basename):
    report_path = Path(report_path)
    raw = report_path.read_bytes()
    data = extract(json.loads(raw))
    base = Path(output_basename)
    png, pdf = Path(str(base)+".png"), Path(str(base)+".pdf")
    if png.exists() or pdf.exists():
        raise FileExistsError("Refusing to overwrite an existing figure")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.titleweight": "semibold", "pdf.fonttype": 42,
                         "ps.fonttype": 42, "figure.facecolor": "white"})
    figure, (left, right) = plt.subplots(1, 2, figsize=(12, 6.8),
                                       gridspec_kw={"width_ratios": (1.1, 1)})
    figure.subplots_adjust(left=.18, right=.98, top=.80, bottom=.25, wspace=.59)
    figure.suptitle("CAISSA-JEPA | " + data["title"], x=.055, y=.965, ha="left", fontsize=16, fontweight="semibold")
    status_label = "Development screen passed" if data["status"] == "development_screen_passed" else "Development screen not passed"
    figure.text(.055, .914, status_label + "  |  Candidate: " + LABELS[data["candidate"]], fontsize=11, color="#414B55")
    if data["restricted_labels"]:
        figure.text(.055, .874, "Primary: 25% of training roots selected | One fixed label mask",
                    fontsize=10, color="#414B55")

    bar_values = [row["regret"] for row in data["bars"]]
    colors = ["#176B87" if row["family"] == data["candidate"] else "#A9B5C1" for row in data["bars"]]
    artists = left.barh(range(len(bar_values)), bar_values, color=colors, height=.61)
    labels = []
    for row in data["bars"]:
        settings = "lr=" + format(row["learning_rate"], "g")
        if row["jepa_weight"] is not None and row["family"] not in ("direct", "value-dynamics", "ema-value"):
            settings += ", weight=" + format(row["jepa_weight"], "g")
        labels.append(LABELS[row["family"]]+(" [collapse]" if row["collapsed"] else "")+"\n"+settings)
    left.set_yticks(range(len(labels)), labels, fontsize=9)
    left.invert_yaxis()
    left.set_xlim(0, max(.05, max(bar_values)*1.27))
    for artist, row in zip(artists, data["bars"]):
        if row["collapsed"]:
            artist.set_hatch("///")
        left.text(row["regret"]+.006, artist.get_y()+artist.get_height()/2,
                  f"{row['regret']:.3f}", va="center", fontsize=10)
    left.set_title("A  Tuned family performance", loc="left", pad=13)
    left.set_xlabel("Equal-game exact-search regret (lower is better)", labelpad=10)
    left.grid(axis="x", color="#E9EDF0", linewidth=.7)
    left.set_axisbelow(True)

    right.axvline(0, color="#707C86", linestyle="--", linewidth=1)
    all_bounds = [0.0]
    for row_index, row in enumerate(data["intervals"]):
        right.hlines(row_index, row["low"], row["high"], color="#176B87", linewidth=2.2)
        right.plot([row["low"], row["high"]], [row_index]*2, "|", color="#176B87", markersize=9)
        right.scatter(row["improvement"], row_index, color="#176B87", s=42, zorder=3)
        all_bounds.extend((row["low"], row["high"], row["improvement"]))
    span = max(.04, max(all_bounds)-min(all_bounds))
    right.set_xlim(min(all_bounds)-.10*span, max(all_bounds)+.10*span)
    right.set_ylim(len(data["intervals"])-.4, -.6)
    right.set_yticks(range(len(data["intervals"])), ["vs "+LABELS[row["family"]] for row in data["intervals"]], fontsize=9)
    right.set_title("B  Paired effects (95% intervals)" if data["restricted_labels"]
                    else "B  Paired candidate improvements", loc="left", pad=13)
    right.set_xlabel("Control regret minus candidate regret\n(positive favors candidate)", labelpad=10)
    right.grid(axis="x", color="#E9EDF0", linewidth=.7)
    right.set_axisbelow(True)
    if data["restricted_labels"]:
        from matplotlib.ticker import MaxNLocator
        right.xaxis.set_major_locator(MaxNLocator(nbins=5))
    else:
        right.text(.5, -.21, "Saved hierarchical bootstrap 95% intervals", transform=right.transAxes,
                   ha="center", fontsize=9, color="#414B55")

    counts = data["game_counts"]
    caption = (f"Adaptive development; three training seeds ({', '.join(map(str, data['seeds']))}). "
               f"Fixed development roots: Connect4 {counts['connect4-4x5']}, Reversi {counts['reversi6']}. "
               "Intervals describe this development cohort, do not correct adaptive selection, and do not establish confirmation. "
               "All plotted estimates and intervals are read from the verified aggregate report.")
    if data["restricted_labels"]:
        caption += (" Primary regime selects 25% of roots, not 25% of state labels. Intervals condition on one fixed "
                    "label mask. Full-label sensitivity is not plotted. This simulates label access; no oracle-compute saving is established.")
    figure.text(.055, .155 if data["restricted_labels"] else .127, textwrap.fill(caption, width=153), ha="left", va="top", fontsize=8.4,
                color="#414B55", linespacing=1.55)
    figure.text(.055, .027, "Source commit: "+data["source_commit"], fontsize=8, family="monospace", color="#58646F")
    base.parent.mkdir(parents=True, exist_ok=True)
    source_sha = hashlib.sha256(raw).hexdigest()
    figure.savefig(png, dpi=220, facecolor="white", metadata={"Title": data["title"], "Description": caption,
                                                            "SourceCommit": data["source_commit"], "ReportSHA256": source_sha})
    figure.savefig(pdf, facecolor="white", metadata={"Title": data["title"], "Author": "CAISSA-JEPA",
                                                    "Subject": caption, "Keywords": "source="+data["source_commit"]+"; report_sha256="+source_sha})
    plt.close(figure)
    return {"png": str(png.resolve()), "pdf": str(pdf.resolve()), "report_sha256": source_sha,
            "source_commit": data["source_commit"], "status": data["status"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", help="Verified aggregate development report JSON")
    parser.add_argument("output_basename", help="New output basename, without PNG/PDF extension")
    args = parser.parse_args()
    print(json.dumps(render(args.report, args.output_basename), indent=2))


if __name__ == "__main__":
    main()
