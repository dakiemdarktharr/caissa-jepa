"""Plot a completed V2.5 strict report or its aggregate-only public derivative.

Usage: python tools/plot_v25_grid.py FINAL_REPORT.json NEW_OUTPUT_BASENAME
Writes .png, _all_cells.png, and a two-page .pdf. Existing outputs are refused.
Reads saved aggregates/intervals only; no models, datasets or grid directories.
"""
import json
from pathlib import Path
import textwrap

try:
    from .compact_v25_report import (validate, read, compact, VERSION, FAMILIES,
                                    CONTROLS, GAMES, TRACKS, RATES, SEEDS)
except ImportError:
    from compact_v25_report import (validate, read, compact, VERSION, FAMILIES,
                                   CONTROLS, GAMES, TRACKS, RATES, SEEDS)

LABELS = {'direct': 'Direct policy/value', 'recurrent-pv': 'Recurrent policy/value',
          'decoded-tail': 'Reconstruction tail', 'scalar-tail': 'Scalar consistency tail',
          'raw-mean': 'JEPA mean', 'raw-tail': 'JEPA tail [candidate]',
          'raw-scaled': 'JEPA scaled-uniform'}
COLORS = ('#176B87', '#C06A24', '#6856A5')
GAME_LABELS = ('Connect4 4x5', 'Reversi 6x6')


def extract(report):
    """Pure extraction, preserving the exact-selected family and full grid."""
    validate(report)
    cells = {(r['config']['variant'], r['config']['learning_rate'], r['config']['seed']): r
             for r in report['runs']}
    chosen = report['selected']
    tracks = {}
    for track in TRACKS:
        tracks[track] = {
            'families': [{'family': v, 'rate': chosen[v]['learning_rate'],
                          'mean': chosen[v]['tracks'][track]['mean_regret'],
                          'games': [chosen[v]['tracks'][track]['per_game_regret'][g] for g in GAMES],
                          'seeds': [chosen[v]['tracks'][track]['per_seed_regret'][str(s)] for s in SEEDS]}
                         for v in FAMILIES],
            'comparisons': [{'control': v,
                             'means': [row['aggregate_improvement']]+[row['per_game_improvement'][g] for g in GAMES],
                             'intervals': [row['bootstrap']['aggregate_ci95']]+[row['bootstrap']['per_game_ci95'][g] for g in GAMES]}
                            for v, row in ((v, report['tracks'][track]['comparisons'][v]) for v in CONTROLS)],
            'gate': report['tracks'][track]['passed']}
    full = {}
    for track in TRACKS:
        matrix = []
        for variant in FAMILIES:
            for rate in RATES:
                row = []
                for scope in ('equal-game', *GAMES):
                    for seed in SEEDS:
                        metrics = cells[variant, rate, seed]['metrics']
                        value = (sum(metrics[g][track]['mean_regret'] for g in GAMES)/2
                                 if scope == 'equal-game' else metrics[scope][track]['mean_regret'])
                        row.append(value)
                matrix.append(row)
        full[track] = matrix
    return {'tracks': tracks, 'full': full, 'selected': {v: chosen[v]['learning_rate'] for v in FAMILIES},
            'status': report['status'], 'mechanism_passed': report['mechanism']['passed'],
            'source_commit': report['code_commit'], 'ledger_sha256': report['ledger_sha256']}


def render(report_path, output_basename):
    raw, input_sha = read(report_path)
    public = raw if raw.get('version') == VERSION else compact(raw, input_sha)
    data = extract(public)
    report_sha = public['source_report_sha256']
    base = Path(output_basename)
    png, appendix, pdf = Path(str(base)+'.png'), Path(str(base)+'_all_cells.png'), Path(str(base)+'.pdf')
    if any(p.exists() for p in (png, appendix, pdf)):
        raise FileExistsError('Refusing to overwrite an existing figure')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    from matplotlib.lines import Line2D
    import numpy as np

    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.titleweight': 'semibold', 'pdf.fonttype': 42,
                         'ps.fonttype': 42, 'figure.facecolor': 'white'})
    fig, axes = plt.subplots(2, 3, figsize=(18, 10),
                             gridspec_kw={'width_ratios': (1, .82, 1.15)})
    fig.subplots_adjust(left=.15, right=.98, bottom=.20, top=.85, hspace=.49, wspace=.55)
    fig.suptitle('CAISSA-JEPA | Complete legal-reply development study',
                 x=.035, y=.973, ha='left', fontsize=19, fontweight='semibold')
    status = {'not_promoted': 'Development screen not passed',
              'exploratory_hybrid_only': 'Exploratory hybrid mechanism only; exact project gate failed',
              'development_screen_passed': 'Development screen passed; independent selection still required'}[data['status']]
    fig.text(.035, .929, status+'  |  Prespecified candidate: JEPA tail', fontsize=12, color='#38434C')
    fig.text(.035, .895, 'One global rate per family selected on EXACT regret; unchanged for HYBRID. Full labels, three paired training seeds.',
             fontsize=10, color='#52606B')
    regret_limit = max(.05, max(row['mean'] for ts in data['tracks'].values() for row in ts['families']),
                       max(value for ts in data['tracks'].values() for row in ts['families']
                           for value in row['games']+row['seeds']))*1.2
    for ti, track in enumerate(TRACKS):
        families = data['tracks'][track]['families']
        mean_ax, game_ax, ci_ax = axes[ti]
        for i, row in enumerate(families):
            color = COLORS[0] if row['family'] == 'raw-tail' else '#BCC7D0'
            mean_ax.barh(i, row['mean'], color=color, height=.58)
            mean_ax.scatter(row['seeds'], [i]*3, marker='|', s=36, color='#263640', zorder=3)
            mean_ax.text(row['mean']+.012*regret_limit, i, f"{row['mean']:.3f}", va='center', fontsize=8)
            for gi, value in enumerate(row['games']):
                game_ax.scatter(value, i+(-.13 if gi == 0 else .13), color=COLORS[gi+1],
                                marker=('o', 's')[gi], s=37 if row['family'] == 'raw-tail' else 25, zorder=3)
        labels = [LABELS[r['family']]+f"  (lr {r['rate']:g})" for r in families]
        mean_ax.set_yticks(range(7), labels, fontsize=9)
        game_ax.set_yticks(range(7), ['']*7)
        for ax in (mean_ax, game_ax):
            ax.set_ylim(6.6, -.6); ax.set_xlim(0, regret_limit)
            ax.grid(axis='x', color='#E9EDF0'); ax.set_axisbelow(True)
            ax.set_xlabel('Action regret (lower is better)', fontsize=9)
        mean_ax.set_title(f"{'A' if ti == 0 else 'D'}  {track.upper()}: equal-game mean", loc='left', fontsize=11, pad=12)
        game_ax.set_title(f"{'B' if ti == 0 else 'E'}  {track.upper()}: per game", loc='left', fontsize=11, pad=12)
        ci_ax.axvline(0, color='#67737D', linestyle='--', linewidth=1)
        endpoints = [0.]
        for i, row in enumerate(data['tracks'][track]['comparisons']):
            for scope, (estimate, bounds) in enumerate(zip(row['means'], row['intervals'])):
                y = i+(-.20, 0., .20)[scope]
                ci_ax.hlines(y, *bounds, color=COLORS[scope], linewidth=2.0 if scope == 0 else 1.1)
                ci_ax.scatter(estimate, y, s=32 if scope == 0 else 20, color=COLORS[scope],
                              marker=('D', 'o', 's')[scope], zorder=3)
                endpoints.extend([estimate, *bounds])
        span = max(.04, max(endpoints)-min(endpoints))
        ci_ax.set_xlim(min(endpoints)-.1*span, max(endpoints)+.1*span)
        ci_ax.set_ylim(3.55, -.65)
        ci_ax.set_yticks(range(4), ['vs '+LABELS[v] for v in CONTROLS], fontsize=9)
        ci_ax.grid(axis='x', color='#E9EDF0'); ci_ax.set_axisbelow(True)
        ci_ax.set_title(f"{'C' if ti == 0 else 'F'}  Raw-tail effects; saved 95% intervals", loc='left', fontsize=11, pad=12)
        ci_ax.set_xlabel('Control regret minus candidate regret\n(positive favors candidate)', fontsize=9)
    fig.legend(handles=[Line2D([], [], marker=m, color=c, label=label, linewidth=1.5)
                        for m, c, label in zip(('D', 'o', 's'), COLORS, ('Equal-game', *GAME_LABELS))],
               loc='lower right', bbox_to_anchor=(.975, .135), ncol=3, frameon=False, fontsize=9)
    caption = ('Adaptive DEVELOPMENT on 209 reused roots (107 Connect4, 102 Reversi), with seeds 17/29/43. '
               'Bars are three-seed means; ticks show those seeds. Paired root-bootstrap intervals use 10,000 draws, '
               'shared across the fixed seeds and stratified by game. Intervals do not correct adaptive model selection '
               'and are not confirmation. Same legal tree does not imply equal wall time or active compute. '
               'All 42 cells and both rates appear on the appendix page; no model scoring is performed by this plotter.')
    fig.text(.035, .123, textwrap.fill(caption, 205), va='top', fontsize=8.6, color='#52606B', linespacing=1.5)
    fig.text(.035, .032, 'Source '+data['source_commit']+'  |  Strict report SHA-256 '+report_sha,
             fontsize=7.5, family='monospace', color='#58646F')

    full, panels = plt.subplots(1, 2, figsize=(18, 10))
    full.subplots_adjust(left=.20, right=.95, bottom=.20, top=.84, wspace=.15)
    full.suptitle('CAISSA-JEPA | Complete 42-cell development inventory',
                  x=.035, y=.973, ha='left', fontsize=19, fontweight='semibold')
    full.text(.035, .924, 'Every family x both rates x seeds 17/29/43; no cell omitted. Each entry is saved per-cell action regret.',
              fontsize=11, color='#38434C')
    full.text(.035, .888, 'Asterisk marks the EXACT-selected rate used unchanged in both tracks. Candidate rows are explicitly labeled.',
              fontsize=10, color='#52606B')
    for ti, track in enumerate(TRACKS):
        matrix = np.asarray(data['full'][track])
        ax = panels[ti]
        image = ax.imshow(matrix, cmap='YlGnBu', vmin=0, vmax=2, aspect='auto')
        for r in range(14):
            for c in range(9):
                ax.text(c, r, f'{matrix[r,c]:.3f}', ha='center', va='center', fontsize=8,
                        color='white' if matrix[r,c] > 1.05 else '#163040')
        labels = [LABELS[v]+f' | {rate:g}'+(' *' if data['selected'][v] == rate else '') for v in FAMILIES for rate in RATES]
        ax.set_yticks(range(14), labels if ti == 0 else ['']*14, fontsize=9)
        ax.set_xticks(range(9), [str(s) for _ in range(3) for s in SEEDS], fontsize=9)
        ax.set_xlabel('Equal-game                 Connect4 4x5                 Reversi 6x6', fontsize=9, labelpad=10)
        ax.set_title(track.upper()+' regret (lower is better)', loc='left', fontsize=12, pad=12)
        for boundary in (2.5, 5.5): ax.axvline(boundary, color='white', linewidth=2)
        for boundary in np.arange(1.5, 14, 2): ax.axhline(boundary, color='white', linewidth=1.6)
        for spine in ax.spines.values(): spine.set_visible(False)
    full.colorbar(image, ax=panels, fraction=.025, pad=.03, label='Action regret; fixed range [0, 2]')
    full.text(.035, .115, textwrap.fill('Adaptive development, not confirmatory evidence. '
              'The fixed color scale spans the full zero-sum action-regret range. '
              'Equal-game cells average the two saved game means, so unequal game counts do not change their weight. '
              'No confidence interval is inferred for an individual cell. All cells are complete and uncollapsed under the strict report.', 205),
              va='top', fontsize=8.6, color='#52606B', linespacing=1.5)
    full.text(.035, .032, 'Source '+data['source_commit']+'  |  Strict report SHA-256 '+report_sha,
              fontsize=7.5, family='monospace', color='#58646F')
    base.parent.mkdir(parents=True, exist_ok=True)
    metadata = {'Title': 'CAISSA-JEPA V2.5 adaptive development', 'Description': caption,
                'SourceCommit': data['source_commit'], 'ReportSHA256': report_sha}
    fig.savefig(png, dpi=220, facecolor='white', metadata=metadata)
    full.savefig(appendix, dpi=220, facecolor='white', metadata=metadata)
    with PdfPages(pdf, metadata={'Title': metadata['Title'], 'Author': 'CAISSA-JEPA', 'Subject': caption,
                                'Keywords': 'source='+data['source_commit']+'; report_sha256='+report_sha}) as pages:
        pages.savefig(fig, facecolor='white'); pages.savefig(full, facecolor='white')
    plt.close(fig); plt.close(full)
    return {'png': str(png.resolve()), 'all_cells_png': str(appendix.resolve()), 'pdf': str(pdf.resolve()),
            'status': data['status'], 'input_sha256': input_sha, 'strict_report_sha256': report_sha,
            'source_commit': data['source_commit']}


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report'); parser.add_argument('output_basename')
    args = parser.parse_args()
    print(json.dumps(render(args.report, args.output_basename), indent=2))


if __name__ == '__main__': main()
