"""Immutable legal reply-fork datasets with independent oracle labels and closure audit."""
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from . import GAMES_V2, METHOD_VERSION
from two_player.games import State, GAMES as OLD_GAMES, FEATURE_SIZE, ACTION_SIZE
from two_player.data import digest, code_commit
from benchmarks.reference_rules import ReferenceGame, ReferenceSolver, ReferenceBudgetExceeded

SPLITS=('train','development','selection','final')
DATA_VERSION='reply-forks-v2.0'


def state_from(obj): return State(tuple(obj['board']),obj['player'])


def source_identity():
    root=Path(__file__).resolve().parents[1]
    paths=('two_player_v2/data.py','two_player_v2/__init__.py','two_player/games.py','two_player/data.py','benchmarks/reference_rules.py')
    return {p:hashlib.sha256((root/p).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for p in paths}


def ref_action(action,cols): return -1 if action==64 else action//8*cols+action%8


def node_id(name,state): return digest([name,asdict(state)])


def closure(name,state):
    game=GAMES_V2[name]; states={node_id(name,state):state}; forks=[]
    for a in game.legal_actions(state):
        child=game.transition(state,a); cid=node_id(name,child); states[cid]=child
        replies=game.legal_actions(child)
        if not replies: forks.append(([node_id(name,state),cid,None],[a,None]))
        for b in replies:
            leaf=game.transition(child,b); lid=node_id(name,leaf); states[lid]=leaf
            forks.append(([node_id(name,state),cid,lid],[a,b]))
    return states,forks,{game.canonical_key(s) for s in states.values()}


def assign_roots(roots,old_training_keys):
    prepared=[]; counts=Counter(); seen=set(); trajectories=set()
    for root in roots:
        name=root['game']; game=GAMES_V2[name]; state=state_from(root['state'])
        key=game.canonical_key(state); trajectory=root['trajectory']
        if key in seen or (name,trajectory) in trajectories:
            raise ValueError('Duplicate root orbit or source trajectory in survey bank')
        seen.add(key); trajectories.add((name,trajectory))
        if root['canonical_key']!=key or tuple(root['actions'])!=game.legal_actions(state):
            raise ValueError('Survey root identity/legal actions mismatch')
        states,forks,keys=closure(name,state)
        bucket=int(trajectory[:16],16)%100
        split='train' if bucket<50 else 'development' if bucket<70 else 'selection' if bucket<85 else 'final'
        prepared.append((root,states,forks,keys,split))
    owner={}; kept=[]; excluded=[]
    for split in reversed(SPLITS):
        for root,states,forks,keys,assigned in prepared:
            if assigned!=split: continue
            reason=None
            if split!='train' and keys & old_training_keys: reason='old_v1_training_overlap'
            elif any(k in owner and owner[k]!=split for k in keys): reason='cross_split_fork_closure_overlap'
            if reason:
                counts[root['game']+'/'+reason]+=1
                excluded.append({'root_id':digest(root),'game':root['game'],'split':split,'reason':reason})
                continue
            owner.update({k:split for k in keys})
            item={**root,'root_id':digest(root),'split':split}
            kept.append((item,states,forks))
            counts[root['game']+'/'+split]+=1
    errors=[]
    for name in GAMES_V2:
        for split,minimum in (('train',100),('development',50),('selection',40),('final',40)):
            if counts[name+'/'+split]<minimum: errors.append(name+'/'+split+': insufficient independent root support')
    orbit_sets={split:set() for split in SPLITS}; feature_sets={split:set() for split in SPLITS}
    for root,states,_ in kept:
        game=GAMES_V2[root['game']]; split=root['split']
        for state in states.values():
            orbit_sets[split].add(game.canonical_key(state))
            feature_sets[split].add(hashlib.sha256(game.features(state).tobytes()).hexdigest())
    intersections={}
    for i,left in enumerate(SPLITS):
        for right in SPLITS[i+1:]:
            intersections[left+'/'+right]={'canonical':len(orbit_sets[left]&orbit_sets[right]),
                                           'feature_bytes':len(feature_sets[left]&feature_sets[right])}
    overlap=sum(v['canonical']+v['feature_bytes'] for v in intersections.values())
    if overlap: errors.append('Cross-split canonical/feature overlap remains')
    return kept,{'counts':dict(counts),'excluded_roots':excluded,'errors':errors,
                 'status':'PASSED' if not errors else 'FAILED','cross_split_feature_overlap':overlap,
                 'pairwise_intersections':intersections}


def old_training_footprint(directory):
    root=Path(directory); manifest=json.loads((root/'manifest.json').read_text())
    raw=(root/'records.jsonl').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=manifest['artifacts']['records.jsonl']['sha256']:
        raise ValueError('Old training exclusion source changed')
    keys=set()
    for line in raw.decode().splitlines():
        row=json.loads(line)
        if row['split']=='train':
            for field in ('state','next','future2'):
                if row[field] is not None: keys.add(OLD_GAMES[row['game']].canonical_key(state_from(row[field])))
    return keys,manifest['audit']['dataset_fingerprint']


def label_node(name,state,reference,solver):
    game=GAMES_V2[name]; refstate=reference.from_board(state.board,state.player)
    legal=game.legal_actions(state); outcome=game.terminal(state)
    if outcome!=reference.terminal(refstate) or {ref_action(a,game.cols) for a in legal}!=set(reference.legal_actions(refstate)):
        raise ValueError('Independent node rules mismatch')
    if outcome is None:
        action_values=solver.action_values(refstate)
        values=[action_values[ref_action(a,game.cols)] for a in legal]; value=max(values)
        optimal=[a for a,v in zip(legal,values) if v==value]
    else:
        value=state.player*outcome; optimal=[]; values=[]
    return {'game':name,'state':asdict(state),'legal':list(legal),'optimal':optimal,
            'value':value,'action_values':values,'terminal':outcome is not None}


def build_dataset(survey_directory,old_directory,output):
    output=Path(output); output.mkdir(parents=True,exist_ok=False)
    started=time.perf_counter(); survey_root=Path(survey_directory)
    receipt=json.loads((survey_root/'receipt.json').read_text())
    if receipt['status']!='PASSED' or receipt['model_predictions']!=0:
        raise ValueError('Rule-only survey has not passed')
    roots=[]
    for name,game in GAMES_V2.items():
        rows=json.loads((survey_root/(name+'.json')).read_text())
        if digest(rows)!=receipt['games'][name]['records_sha256']:
            raise ValueError('Survey root bank changed')
        ref=ReferenceGame(game.rows,game.cols,game.k,game.gravity,game.reversi)
        if ref.identity()!=receipt['games'][name]['reference']:
            raise ValueError('Reference changed since survey')
        roots.extend(rows)
    old_keys,old_fingerprint=old_training_footprint(old_directory)
    kept,audit=assign_roots(roots,old_keys)
    if audit['status']!='PASSED':
        (output/'failed-audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
        raise ValueError('Root support/overlap audit failed: '+str(audit['errors']))
    nodes={}; forks=[]; root_rows=[]; oracle_stats={}
    try:
        for name,game in GAMES_V2.items():
            reference=ReferenceGame(game.rows,game.cols,game.k,game.gravity,game.reversi)
            solver=ReferenceSolver(reference,time_limit=10.); counters=Counter(); deadline=time.perf_counter()+120
            for root,states,branches in kept:
                if root['game']!=name: continue
                for nid,state in states.items():
                    if nid in nodes: continue
                    if time.perf_counter()>=deadline: raise TimeoutError('Oracle label-generation budget exhausted')
                    if len(solver.cache)>=400000: solver.cache.clear(); counters['cache_clears']+=1
                    solver.time_limit=min(10.,max(.001,deadline-time.perf_counter()))
                    nodes[nid]=label_node(name,state,reference,solver)
                    if not nodes[nid]['terminal']:
                        for k in ('nodes','transitions','cache_hits','seconds'): counters[k]+=solver.last_stats[k]
                    counters['labelled_states']+=1
                rootnode=nodes[node_id(name,state_from(root['state']))]
                if rootnode['action_values']!=root['oracle_values']:
                    raise ValueError('Survey/reference oracle label disagreement')
                for state_ids,actions in branches:
                    forks.append({'root_id':root['root_id'],'game':name,'split':root['split'],
                                  'node_ids':state_ids,'actions':actions})
                root_rows.append(root)
            oracle_stats[name]={'reference':reference.identity(),**dict(counters)}
        payload={'roots':root_rows,'nodes':nodes,'forks':forks}
        raw=json.dumps(payload,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
        (output/'forks.json').write_bytes(raw)
        manifest={'version':DATA_VERSION,'method':METHOD_VERSION,'code_commit':code_commit(),
                  'source_identity':source_identity(),'survey_fingerprint':receipt['survey_fingerprint'],
                  'old_training_exclusion_fingerprint':old_fingerprint,'audit':audit,'oracle':oracle_stats,
                  'artifacts':{'forks.json':{'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}},
                  'root_count':len(root_rows),'node_count':len(nodes),'fork_count':len(forks),
                  'seconds':time.perf_counter()-started,'labels':'independent same-project exact minimax',
                  'provenance':{'source':'project-owned legal counterfactual forks','public_data_license':'NOT_ASSIGNED',
                                'external_data':False,'local_research_authorized':True}}
        identity={k:v for k,v in manifest.items() if k not in ('code_commit','seconds','oracle')}
        manifest['dataset_fingerprint']=digest(identity)
        (output/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
        return manifest
    except Exception:
        import traceback
        (output/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8')
        raise


def verify_bytes(directory):
    root=Path(directory); manifest=json.loads((root/'manifest.json').read_text())
    if manifest['version']!=DATA_VERSION or manifest['source_identity']!=source_identity() or manifest['audit']['status']!='PASSED':
        raise ValueError('Dataset version/source/audit mismatch')
    identity={k:v for k,v in manifest.items() if k not in ('code_commit','seconds','oracle','dataset_fingerprint')}
    if digest(identity)!=manifest['dataset_fingerprint']: raise ValueError('Manifest fingerprint changed')
    raw=(root/'forks.json').read_bytes(); artifact=manifest['artifacts']['forks.json']
    if len(raw)!=artifact['bytes'] or hashlib.sha256(raw).hexdigest()!=artifact['sha256']:
        raise ValueError('Dataset bytes changed')
    return manifest,raw


def load_dataset(directory,split):
    if split not in ('train','development'):
        raise ValueError('Selection/final predictions require a separate frozen protocol')
    manifest,raw=verify_bytes(directory); payload=json.loads(raw)
    roots=[r for r in payload['roots'] if r['split']==split]
    forks=[r for r in payload['forks'] if r['split']==split]
    needed={nid for r in forks for nid in r['node_ids'] if nid is not None}
    nodes={nid:payload['nodes'][nid] for nid in needed}
    # Reconstruct every transition and cross-check node identity before encoding.
    for nid,node in nodes.items():
        game=GAMES_V2[node['game']]; state=state_from(node['state'])
        if node_id(node['game'],state)!=nid or tuple(node['legal'])!=game.legal_actions(state):
            raise ValueError('Node legality/identity mismatch')
        if not set(node['optimal'])<=set(node['legal']) or node['value'] not in (-1,0,1):
            raise ValueError('Invalid oracle target')
        terminal=game.terminal(state)
        if node['terminal']!=(terminal is not None): raise ValueError('Terminal label mismatch')
        if terminal is not None:
            if node['optimal'] or node['action_values'] or node['value']!=state.player*terminal:
                raise ValueError('Terminal oracle value mismatch')
        else:
            values=node['action_values']
            if len(values)!=len(node['legal']) or any(v not in (-1,0,1) for v in values) or max(values)!=node['value']:
                raise ValueError('Oracle action-value consistency mismatch')
            if node['optimal']!=[a for a,v in zip(node['legal'],values) if v==max(values)]:
                raise ValueError('Optimal policy target mismatch')
    for fork in forks:
        game=GAMES_V2[fork['game']]
        for h,action in enumerate(fork['actions']):
            if action is None:
                if fork['node_ids'][h+1] is not None or not nodes[fork['node_ids'][h]]['terminal']:
                    raise ValueError('Invalid missing horizon')
                continue
            previous=state_from(nodes[fork['node_ids'][h]]['state'])
            expected=game.transition(previous,action)
            if node_id(fork['game'],expected)!=fork['node_ids'][h+1]:
                raise ValueError('Fork transition mismatch')
    return {'roots':roots,'nodes':nodes,'forks':forks,'manifest':manifest}


def batch_arrays(dataset,indices):
    forks=[dataset['forks'][int(i)] for i in indices]; n=len(forks)
    if not n: raise ValueError('Empty batch')
    batch={'x':np.zeros((n,3,FEATURE_SIZE)), 'valid':np.zeros((n,3),bool),
           'legal':np.zeros((n,3,ACTION_SIZE),bool),'policy':np.zeros((n,3,ACTION_SIZE)),
           'value':np.zeros((n,3,1)),'actions':np.zeros((n,2,ACTION_SIZE))}
    for i,fork in enumerate(forks):
        for h,nid in enumerate(fork['node_ids']):
            if nid is None: continue
            node=dataset['nodes'][nid]; game=GAMES_V2[node['game']]
            batch['x'][i,h]=game.features(state_from(node['state'])); batch['valid'][i,h]=True
            batch['legal'][i,h,node['legal']]=True
            if node['optimal']: batch['policy'][i,h,node['optimal']]=1/len(node['optimal'])
            batch['value'][i,h,0]=node['value']
        for h,action in enumerate(fork['actions']):
            if action is not None: batch['actions'][i,h,action]=1
    return batch


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('survey'); parser.add_argument('old_dataset'); parser.add_argument('output')
    args=parser.parse_args(); print(json.dumps(build_dataset(args.survey,args.old_dataset,args.output),indent=2))
