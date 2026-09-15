"""English-only, bounded-cost painter views for the research monitor."""
from datetime import datetime
import math

from PySide6.QtCore import QRectF, Qt, QPointF
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPainterPath

from model_registry import training_model_specs
from arena_research import evaluation_display, matchup_statistics


def text(p, rect, value, color="#B7FFAE", size=10, bold=False):
    p.setPen(QColor(color))
    p.setFont(QFont("Consolas", size, QFont.Bold if bold else QFont.Normal))
    p.drawText(rect, Qt.AlignLeft | Qt.AlignVCenter | Qt.TextWordWrap, str(value))


def panel(p, rect):
    p.setPen(QPen(QColor("#117A2B"), 1))
    p.setBrush(QColor("#030A07"))
    p.drawRoundedRect(rect, 5, 5)


def duration(seconds):
    if seconds is None:
        return "--"
    seconds = max(0, int(seconds))
    return f"{seconds // 3600:02d}:{seconds // 60 % 60:02d}:{seconds % 60:02d}"


def plot(p, rect, history):
    panel(p, rect)
    points = [h for h in history if isinstance(h.get("loss"), (int, float)) and math.isfinite(h["loss"])]
    points = points[::max(1, len(points) // 400)]
    if not points:
        text(p, rect.adjusted(12, 0, -10, 0), "Waiting for measured train / validation loss", "#63A86C", 9)
        return
    lo, hi = min(h["loss"] for h in points), max(h["loss"] for h in points)
    hi = max(hi, lo + 0.001)
    area = rect.adjusted(54, 10, -10, -24)
    text(p, QRectF(rect.x()+4, area.y()-6, 49, 17), f"{hi:.3f}", size=8)
    text(p, QRectF(rect.x()+4, area.bottom()-12, 49, 17), f"{lo:.3f}", size=8)
    for phase, color in (("train", "#39FF14"), ("validation", "#00E5FF")):
        path = QPainterPath()
        previous = False
        for index, point in enumerate(points):
            if point.get("phase", "train") != phase:
                continue
            first_step = min(h.get("step", 0) for h in points)
            last_step = max(h.get("step", 0) for h in points)
            x = area.x() + area.width() * (point.get("step", 0)-first_step) / max(1, last_step-first_step)
            y = area.bottom() - area.height() * (point["loss"]-lo)/(hi-lo)
            if previous:
                path.lineTo(x, y)
            else:
                path.moveTo(x, y)
            previous = True
            p.setPen(QPen(QColor(color), 3))
            p.drawPoint(QPointF(x, y))
        p.setPen(QPen(QColor(color), 1.5))
        p.setBrush(Qt.NoBrush)
        p.drawPath(path)
    text(p, QRectF(area.x(), rect.bottom()-22, area.width(), 20),
         f"Step {points[0].get('step', 0)} -> {points[-1].get('step', 0)} | green train / cyan validation", size=8)


def paint_training(widget):
    p = QPainter(widget)
    p.setRenderHint(QPainter.Antialiasing)
    p.fillRect(widget.rect(), QColor("#000000"))
    text(p, QRectF(18, 8, widget.width()-36, 32), "MARS-JEPA Chess // ALL-MODEL TRAINING MONITOR", "#39FF14", 16, True)
    text(p, QRectF(18, 40, widget.width()-36, 25), "Equal share of 8 training hours | queue/cache time excluded | one trainer at a time", size=9)
    specs = training_model_specs(widget.board_widget.project_dir)
    width = (widget.width()-48)/2
    height = (widget.height()-92)/math.ceil((len(specs)+1)/2)
    for index, spec in enumerate(specs):
        x, y = 16 + (index % 2)*(width+16), 76 + (index//2)*(height+8)
        rect = QRectF(x, y, width, height)
        panel(p, rect)
        run = widget.training_runs.get(spec["id"], {})
        latest = run.get("latest", run.get("report", run))
        status = run.get("status", "NOT STARTED")
        active = status in ("RUNNING", "STARTING")
        percent = min(100, max(0, float(latest.get("progress_percent", 0))))
        text(p, QRectF(x+12,y+5,width-24,23), spec["label"], "#39FF14", 11, True)
        text(p, QRectF(x+12,y+30,width-24,20), f"{status} | {latest.get('phase', '--')} | {percent:.2f}% | step {run.get('trained_steps', 0):,}", size=9)
        p.fillRect(QRectF(x+12,y+53,width-24,4), QColor("#163720"))
        p.fillRect(QRectF(x+12,y+53,(width-24)*percent/100,4), QColor("#39FF14"))
        finish = latest.get("estimated_finish_timestamp") if active else None
        finish_text = datetime.fromtimestamp(finish).strftime("%d %b %H:%M:%S") if finish else "--"
        eta = duration(latest.get("eta_seconds")) if active else "--"
        text(p, QRectF(x+12,y+61,width-24,20), f"ETA {eta} | finish {finish_text} | {latest.get('eta_status', '--') if active else status}", size=8)
        spread = latest.get("eta_range_seconds") if active else None
        extra = f"range {duration(spread[0])} - {duration(spread[1])}" if spread else f"cache {latest.get('cache_shards_completed', 0)}/{latest.get('cache_shards_total', 0)} shards | {latest.get('prepared_positions', 0):,} positions"
        text(p, QRectF(x+12,y+81,width-24,20), f"{extra} | {latest.get('rows_per_second') or latest.get('cache_rows_per_second') or 0:,.1f} positions/s", "#63A86C", 8)
        plot(p, QRectF(x+12,y+105,width-24,max(15,height-116)), run.get("history", []))
    rect = QRectF(16+(len(specs)%2)*(width+16), 76+(len(specs)//2)*(height+8), width, height)
    panel(p, rect)
    text(p, rect.adjusted(12,8,-12,-height+35), "EXPERIMENT NOTES", "#39FF14", 11, True)
    text(p, rect.adjusted(12,40,-12,-12),
         "Compare validation within each objective, not raw loss across architectures.\n"
         "Ranking accuracy is margin success against a sampled legal negative; it is NOT all-legal top-1 accuracy.\n"
         "Cache preparation is shared. ETA calibrates from observed train/validation batches.\n"
         + "\n".join(widget.log_lines[-3:]), size=9)
    p.end()


def paint_arena(w):
    p = QPainter(w)
    p.setRenderHint(QPainter.Antialiasing)
    p.fillRect(w.rect(), QColor("#000000"))
    top = max(160, w.stats_label.geometry().bottom()+48)
    size = max(256, int(min(w.height()-top-64, w.width()*0.47))//8*8)
    left, square = 30, size/8
    evaluation = getattr(w, "evaluation", {})
    fill, value_text = evaluation_display(evaluation)
    bar_x = left+size+14
    text(p, QRectF(left,top-35,size,28), "MODEL VS MODEL // READ-ONLY", "#39FF14", 12, True)
    for row in range(8):
        for col in range(8):
            cell = QRectF(left+col*square,top+row*square,square,square)
            p.fillRect(cell, QColor("#B58863" if (row+col)%2 else "#F0D9B5"))
            if row*8+col in (getattr(w,"last_move",None) or [])[:2]:
                p.fillRect(cell, QColor(80,200,40,95))
            piece = w.board[row*8+col]
            if piece == ".":
                continue
            target = cell.adjusted(square*.06,square*.06,-square*.06,-square*.06)
            renderer = w.board_widget.piece_renderers.get(piece)
            if renderer and renderer.isValid():
                renderer.render(p, target)
            else:
                p.setFont(QFont("Segoe UI Symbol", int(square*.6)))
                p.setPen(QColor("#111111"))
                p.drawText(target, Qt.AlignCenter, w.board_widget.piece_symbols.get(piece,piece))
    p.fillRect(QRectF(bar_x,top,26,size), QColor("#20262A"))
    p.fillRect(QRectF(bar_x,top+size*(1-fill),26,size*fill), QColor("#F3F4ED"))
    for yy, label in ((top-34,"BLACK: "+w.model_label(w.black_model_id)),
                      (top+size+24,"WHITE: "+w.model_label(w.white_model_id))):
        tag = QRectF(bar_x-210,yy,250,28)
        panel(p,tag)
        text(p,tag.adjusted(7,0,-5,0),label,size=8,bold=True)
    for i, letter in enumerate("abcdefgh"):
        text(p,QRectF(left+i*square+square*.43,top+size+2,square,19),letter,size=8)
        text(p,QRectF(10,top+i*square+square*.3,18,20),8-i,size=8)
    side = bar_x+42
    width = w.width()-side-20
    panel(p,QRectF(side,top-34,width,size+70))
    records = getattr(w,"move_records",[])
    search = getattr(w,"live_search",{})
    stats = matchup_statistics([r for r in w.arena_history if not w.series_id or r.get("series_id")==w.series_id], w.white_model_id,w.black_model_id)
    ci = stats["score_ci95"]
    ci_text = f"[{ci[0]:.1%}, {ci[1]:.1%}]" if ci else "insufficient paired games"
    score = f"{stats['score']:.1%}" if stats["score"] is not None else "--"
    elo = f"{stats['elo']:+.1f}" if stats["elo"] is not None else "not finite / insufficient"
    last = records[-1] if records else {}
    rows = [
        f"Match {w.current_match_number} | round {w.series_round} | ply {w.current_ply} | {w.current_turn.upper()} to move",
        f"Last: {w.current_move} ({last.get('uci','--')}) | {w.current_source}",
        f"Search: depth {search.get('depth','--')} | nodes {search.get('nodes','--')} | NPS {search.get('nps','--')} | sims {search.get('simulations','--')}",
        f"Search time {search.get('time','--')}s | last move {last.get('move_seconds',0):.3f}s | budget {getattr(w,'move_time_seconds',.35):.2f}s",
        f"Referee: {evaluation.get('source','Pending')} | {value_text}",
        f"Ref depth {evaluation.get('depth','--')} | W/D/L {evaluation.get('wdl_white','unavailable')} | cp {evaluation.get('cp_white','--')} | mate {evaluation.get('mate_white','--')}",
        f"Reference ply {evaluation.get('ply','--')} | {evaluation.get('bound','--')} | cp visual only; WDL score = W + D/2",
        f"Current series / White model: {stats['wins']}W {stats['draws']}D {stats['losses']}L | score {score}",
        f"Paired games {stats['pairs']} | relative Elo {elo}",
        f"95% score bound {ci_text} (fixed-sample; NOT sequential proof)",
        f"Censored {stats['censored']} | errors {stats['failures']} | exploratory results only",
        f"Seed {w.match_seed} | randomized first color + reversed-color leg",
    ]
    if evaluation.get('reference_error'):
        rows.append("REFEREE FALLBACK: " + str(evaluation['reference_error'])[:100])
    from main import move_thanh_text
    pv = search.get('pv', [])
    if pv:
        rows.append("PV (UCI): " + " ".join(move_thanh_text(m) if isinstance(m,(list,tuple)) else str(m) for m in pv[:8]))
    elif search.get('moves'):
        rows.append("MCTS root visits: " + " / ".join(f"{move_thanh_text(m['move'])}: {m['visits']}" for m in search['moves'][:3]))
    for side_name, model_id in (("White",w.white_model_id),("Black",w.black_model_id)):
        metrics = getattr(w,'heldout_metrics',{}).get(model_id,{})
        if metrics.get('top1_accuracy') is not None:
            rows.append(f"{side_name} validation: top1 {metrics['top1_accuracy']:.1%} / top5 {metrics['top5_accuracy']:.1%} / NLL {metrics['mean_nll']:.3f} / n={metrics['positions']}")
        else:
            rows.append(f"{side_name} validation top1/top5/NLL: not measured for this checkpoint")
    yy = top-28
    for row in rows:
        text(p,QRectF(side+10,yy,width-20,25),row,size=8)
        yy += 25
    if w.match_result:
        text(p,QRectF(side+10,yy,width-20,23),f"RESULT: {w.match_result.get('result')} / {w.match_result.get('reason')}","#FFB000",10,True)
        yy += 24
    text(p,QRectF(side+10,yy,width-20,22),"MOVES (SAN) // full FEN, search and reference telemetry saved to JSONL", "#00E5FF",8)
    yy += 24
    slots = max(1,int((top+size+28-yy)//22))
    pairs = [(i,records[i:i+2]) for i in range(0,len(records),2)]
    for i, pair in pairs[-slots:]:
        text(p,QRectF(side+10,yy,width-20,21),f"{i//2+1:3d}. " + "   ".join(r.get('san',r.get('move_text','?')) for r in pair),size=10)
        yy += 22
    p.end()
