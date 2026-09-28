"""Rule-only v2 situation feasibility; never reads model weights or predictions."""
from collections import Counter
from dataclasses import asdict
import json
import hashlib
from pathlib import Path
import time
import numpy as np
from two_player.games import GAMES, BoardGame
from two_player.data import digest, code_commit, source_hash
from benchmarks.reference_rules import ReferenceGame, ReferenceSolver, ReferenceBudgetExceeded


def reference_action(action,cols):
    return -1 if action==64 else (action//8)*cols+action%8


def shallow_values(game,state):
    values={}; nonterminal=0
    for action in game.legal_actions(state):
        child=game.transition(state,action); terminal=game.terminal(child)
        if terminal is not None: values[action]=state.player*terminal; continue
        replies=[]
        for reply in game.legal_actions(child):
            leaf=game.transition(child,reply); terminal=game.terminal(leaf)
            if terminal is None: nonterminal+=1
            replies.append(0 if terminal is None else state.player*terminal)
        values[action]=min(replies)
    return values,nonterminal


def survey(output,games_per_game=2000,seed=98371,time_limit=120.,admitted_limit=500,expanded=False):
    output=Path(output); output.mkdir(parents=True,exist_ok=False)
    if not 1<=games_per_game<=2000 or not 0<time_limit<=120 or not 1<=admitted_limit<=500:
        raise ValueError('Survey budget exceeds frozen limits')
    result={'stage':'rule-only development feasibility','seed':seed,'games_per_game':games_per_game,
            'code_commit':code_commit(),'model_predictions':0,'games':{},'expanded':expanded,
            'survey_sha256':hashlib.sha256(Path(__file__).read_bytes().replace(b'\r\n',b'\n')).hexdigest(),
            'adapter_package_sha256':source_hash()}
    games={'connect4-4x5':BoardGame('connect4-4x5',4,5,4,gravity=True),'reversi4':GAMES['reversi4']} if expanded else {name:GAMES[name] for name in ('connect3','reversi4')}
    for offset,(name,game) in enumerate(games.items()):
        started=time.perf_counter(); deadline=started+time_limit
        ref=ReferenceGame(game.rows,game.cols,game.k,game.gravity,game.reversi)
        solver=ReferenceSolver(ref,time_limit=10.)
        rng=np.random.default_rng(np.random.SeedSequence([seed,offset]))
        records=[]; seen=set(); admitted_trajectories=set(); rejected=Counter(); solve_stats=Counter(); sampled=0
        stop='trajectory_limit'
        for episode in range(games_per_game):
            if time.perf_counter()>=deadline: stop='time_limit'; break
            if len(solver.cache)>=500000: stop='cache_limit'; break
            if len(records)>=admitted_limit: stop='admitted_limit'; break
            state=game.initial(); candidates=[]; actions=[]
            while game.terminal(state) is None:
                legal=game.legal_actions(state)
                if 5<=state.board.count(0)<=8 and len(legal)>=2:
                    candidates.append(state)
                winning=[] if episode%2 or game.reversi else [a for a in legal if game.terminal(game.transition(state,a))==state.player]
                action=int(rng.choice(winning or legal)); actions.append(action)
                state=game.transition(state,action)
            sampled+=1
            trajectory=digest([name,actions])
            if trajectory in admitted_trajectories:
                rejected['duplicate_admitted_trajectory']+=1
                continue
            for state in sorted(candidates,key=lambda s:digest(asdict(s))):
                if time.perf_counter()>=deadline: stop='time_limit'; break
                key=game.canonical_key(state)
                if key in seen: rejected['duplicate_canonical_root']+=1; continue
                seen.add(key)
                shallow,leaves=shallow_values(game,state)
                if not leaves: rejected['no_nonterminal_depth2_leaf']+=1; continue
                refstate=ref.from_board(state.board,state.player)
                legal=game.legal_actions(state)
                if set(ref.legal_actions(refstate))!={reference_action(a,game.cols) for a in legal}:
                    raise ValueError('Independent legal action disagreement')
                solver.time_limit=min(10.,max(.001,deadline-time.perf_counter()))
                try:
                    oracle=solver.action_values(refstate)
                except ReferenceBudgetExceeded:
                    rejected['oracle_budget_unresolved']+=1
                    continue
                finally:
                    for metric in ('nodes','cache_hits','transitions','terminal_nodes','seconds'):
                        solve_stats[metric]+=solver.last_stats[metric]
                if max(oracle.values())==min(oracle.values()):
                    rejected['all_exact_action_values_equal']+=1; continue
                for a in legal:
                    child=game.transition(state,a)
                    refchild=ref.transition(refstate,reference_action(a,game.cols))
                    if ref.board(refchild)!=child.board or refchild.player!=child.player or ref.terminal(refchild)!=game.terminal(child):
                        raise ValueError('Independent transition/outcome disagreement')
                    replies=game.legal_actions(child)
                    if set(ref.legal_actions(refchild))!={reference_action(b,game.cols) for b in replies}:
                        raise ValueError('Independent reply legality disagreement')
                    for b in replies:
                        leaf=game.transition(child,b)
                        refleaf=ref.transition(refchild,reference_action(b,game.cols))
                        if ref.board(refleaf)!=leaf.board or refleaf.player!=leaf.player or ref.terminal(refleaf)!=game.terminal(leaf):
                            raise ValueError('Independent depth2 transition/outcome disagreement')
                records.append({'game':name,'trajectory':trajectory,'episode':episode,'state':asdict(state),
                                'canonical_key':key,'actions':list(legal),
                                'oracle_values':[oracle[reference_action(a,game.cols)] for a in legal],
                                'depth2_zero_values':[shallow[a] for a in legal],
                                'nonterminal_depth2_leaves':leaves,
                                'beyond_depth':len(set(shallow.values()))==1})
                admitted_trajectories.add(trajectory)
                if len(records)%50==0: print(json.dumps({'game':name,'admitted':len(records),'seconds':time.perf_counter()-started}),flush=True)
                break  # One admitted root per source trajectory.
        beyond=sum(r['beyond_depth'] for r in records)
        report={'sampled_trajectories':sampled,'admitted':len(records),'beyond_depth':beyond,
                'unique_admitted_trajectories':len(admitted_trajectories),
                'unique_canonical_roots_examined':len(seen),'exclusions':dict(rejected),
                'oracle_stats':dict(solve_stats),'oracle_cache_entries':len(solver.cache),
                'seconds':time.perf_counter()-started,'stopped_by':stop,
                'reference':ref.identity(),'records_sha256':digest(records),
                'status':'PASSED_SUPPORT' if len(records)>=100 and beyond>=50 else 'FAILED_SUPPORT'}
        (output/f'{name}.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
        result['games'][name]=report
        (output/'receipt.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(json.dumps({'game':name,**report}),flush=True)
    result['status']='PASSED' if all(r['status']=='PASSED_SUPPORT' for r in result['games'].values()) else 'FAILED'
    result['survey_fingerprint']=digest(result)
    (output/'receipt.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('output')
    parser.add_argument('--expanded',action='store_true')
    args=parser.parse_args()
    raise SystemExit(0 if survey(args.output,seed=98372 if args.expanded else 98371,expanded=args.expanded)['status']=='PASSED' else 2)
