"""Reproducible procedural self-play and strict trajectory/state audit.

Audit reads final identities/rules only; no final model predictions are made.
Artifacts stay in an explicitly selected ignored output directory.
"""
from collections import Counter, defaultdict
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import time
import numpy as np
from .games import GAMES, State, RULES_VERSION

DATA_VERSION='tiny-trajectories-v1'
SPLITS=('train','validation','selection','test')


def digest(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def source_hash():
    return digest({p.name:hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
                   for p in sorted(Path(__file__).parent.glob('*.py'))})


def code_commit():
    return subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()


def trajectory_id(game,states,actions):
    versions=[]
    for mapping in game.transforms():
        transformed=[game.transform(states[i],a,mapping)[1] for i,a in enumerate(actions)]
        initial,_=game.transform(states[0],64,mapping)
        versions.append((initial.board,tuple(transformed)))
    return digest([asdict(game),min(versions)])


def generate(games_per_game=200,seed=1701):
    if games_per_game < 1 or games_per_game > 10000:
        raise ValueError('Bounded pilot requires 1..10000 games per game')
    rng=np.random.default_rng(seed)
    rows=[]
    for name,game in GAMES.items():
        for index in range(games_per_game):
            state=game.initial()
            actions=[]
            policy='random' if index%2 or game.reversi else 'random-immediate-win'
            while game.terminal(state) is None:
                legal=game.legal_actions(state)
                winning=[] if policy=='random' else [a for a in legal if game.terminal(game.transition(state,a))==state.player]
                action=int(rng.choice(winning or legal))
                actions.append(action)
                state=game.transition(state,action)
                if len(actions)>2*game.rows*game.cols+2:
                    raise RuntimeError('Game failed finite-length invariant')
            rows.append({'game':name,'actions':actions,'outcome':game.terminal(state),
                         'generator_seed':seed,'episode':index,'policy':policy,
                         'source':'project-owned procedural self-play'})
    return rows


def replay(row):
    game=GAMES[row['game']]
    states=[game.initial()]
    for action in row['actions']:
        states.append(game.transition(states[-1],action))
    result=game.terminal(states[-1])
    if result is None or result != row['outcome']:
        raise ValueError('Unfinished or incorrect outcome')
    return states


def audit(rows,scope='whole-game'):
    if scope not in ('whole-game','middle-late'):
        raise ValueError('Unknown predeclared scope')
    seen=set()
    prepared=[]
    reasons=Counter()
    quarantine=[]
    raw_counts=Counter()
    for number,row in enumerate(rows):
        try:
            game=GAMES[row['game']]
            states=replay(row)
            tid=trajectory_id(game,states,row['actions'])
        except (KeyError,TypeError,ValueError) as error:
            reasons['illegal_or_malformed_trajectory']+=1
            quarantine.append({'row':number,'reason':'illegal_or_malformed_trajectory','detail':str(error)})
            continue
        if tid in seen:
            reasons['duplicate_symmetry_trajectory']+=1
            quarantine.append({'row':number,'reason':'duplicate_symmetry_trajectory'})
            continue
        seen.add(tid)
        bucket=int(tid[:16],16)%100
        split='train' if bucket<70 else 'validation' if bucket<80 else 'selection' if bucket<90 else 'test'
        if row['game']=='connect3-heldout':
            split='transfer'
        for ply,action in enumerate(row['actions']):
            if scope=='middle-late' and ply/(game.rows*game.cols)<1/3:
                reasons['outside_predeclared_middle_late_scope']+=1
                continue
            future=states[ply+2] if ply+2<len(states) else None
            record={'game':row['game'],'trajectory':tid,'source_row':number,'ply':ply,'split':split,
                    'state':asdict(states[ply]),'action':action,'next':asdict(states[ply+1]),
                    'reply':row['actions'][ply+1] if future else None,
                    'future2':asdict(future) if future else None,
                    'value':states[ply].player*row['outcome']}
            keys={game.canonical_key(s) for s in states[ply:min(ply+3,len(states))]}
            prepared.append((record,keys))
            raw_counts[(row['game'],split)]+=1
    owner={}
    records=[]
    retained=Counter()
    trajectory_support=defaultdict(set)
    h2=Counter()
    phases=defaultdict(Counter)
    for split in ('transfer',)+tuple(reversed(SPLITS)):
        for record,keys in prepared:
            if record['split']!=split:
                continue
            if any(k in owner and owner[k]!=split for k in keys):
                reasons['cross_split_context_or_target_overlap']+=1
                quarantine.append({'row':record['source_row'],'ply':record['ply'],'reason':'cross_split_context_or_target_overlap'})
                continue
            owner.update({k:split for k in keys})
            records.append(record)
            label=(record['game'],split)
            retained[label]+=1
            h2[label]+=record['future2'] is not None
            trajectory_support[label].add(record['trajectory'])
            game=GAMES[record['game']]
            fraction=record['ply']/(game.rows*game.cols)
            phases[label]['early' if fraction<1/3 else 'middle' if fraction<2/3 else 'late']+=1
    errors=[]
    support={}
    for name in GAMES:
        for split in (('transfer',) if name=='connect3-heldout' else SPLITS):
            key=(name,split)
            count=retained[key]
            nt=len(trajectory_support[key])
            support[name+'/'+split]={'raw_records':raw_counts[key],'retained_records':count,
                                    'trajectories':nt,'h2_records':h2[key],
                                    'retention_fraction':count/raw_counts[key] if raw_counts[key] else 0,
                                    'phases':dict(phases[key])}
            minimum=(64,16,16) if split=='train' else (16,8,8)
            if count<minimum[0] or nt<minimum[1] or h2[key]<minimum[2]:
                errors.append(name+'/'+split+': insufficient record/trajectory/H2 support')
            required_phases=('early','middle') if scope=='whole-game' else ('middle','late')
            if any(not phases[key][p] for p in required_phases):
                errors.append(name+'/'+split+': missing phase coverage for '+scope+' claims')
    if reasons['illegal_or_malformed_trajectory']:
        errors.append('Illegal trajectories must be corrected in a new dataset version')
    report={'schema_version':DATA_VERSION,'rules_version':RULES_VERSION,'scope':scope,
            'raw_trajectories':len(rows),'unique_trajectories':len(seen),
            'retained_records':len(records),'support':support,'exclusion_counts':dict(reasons),
            'quarantine':quarantine,'cross_split_overlap':0,
            'split_policy':'canonical trajectory hash 70/10/10/10; strict context/H1/H2 symmetry ownership; heldout size variant transfer only',
            'errors':errors,'status':'PASSED' if not errors else 'FAILED',
            'records_sha256':digest(records),'source_rows_sha256':digest(rows)}
    report['dataset_fingerprint']=digest(report)
    return records,report


def write_dataset(directory,games_per_game=200,seed=1701,scope='whole-game'):
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=False)
    started=time.perf_counter()
    rows=generate(games_per_game,seed)
    records,report=audit(rows,scope)
    artifacts={}
    for name,items in (('trajectories.jsonl',rows),('records.jsonl',records)):
        path=directory/name
        path.write_text(''.join(json.dumps(row,sort_keys=True)+'\n' for row in items),encoding='utf-8')
        artifacts[name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,'rows':len(items)}
    from . import METHOD_VERSION
    manifest={'method':METHOD_VERSION,'source_sha256':source_hash(),'code_commit':code_commit(),
              'generator':{'games_per_game':games_per_game,'seed':seed,'scope':scope},
              'provenance':{'owner':'project','source':'procedural self-play from project-owned rules',
                            'external_data':False,'local_research_authorized':True,
                            'public_artifact_license':'NOT_ASSIGNED; do not distribute generated artifacts'},
              'python':platform.python_version(),'numpy':np.__version__,
              'artifacts':artifacts,'audit':report,'seconds':time.perf_counter()-started,
              'production_training_allowed':report['status']=='PASSED'}
    (directory/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return manifest


def load_dataset(directory,split,*,exploratory_transfer=False):
    if split not in ('train','validation') and not (split=='transfer' and exploratory_transfer):
        raise ValueError('Training/development loader excludes selection, final and transfer')
    root=Path(directory)
    manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    if set(manifest['artifacts'])!={'trajectories.jsonl','records.jsonl'}:
        raise ValueError('Dataset artifact inventory mismatch')
    for name,item in manifest['artifacts'].items():
        if name not in ('trajectories.jsonl','records.jsonl'):
            raise ValueError('Unknown dataset artifact')
        raw=(root/name).read_bytes()
        if len(raw)!=item['bytes'] or hashlib.sha256(raw).hexdigest()!=item['sha256']:
            raise ValueError('Dataset bytes changed')
    rows=[json.loads(line) for line in (root/'trajectories.jsonl').read_text(encoding='utf-8').splitlines()]
    records,actual=audit(rows,manifest['generator']['scope'])
    disk_records=[json.loads(line) for line in (root/'records.jsonl').read_text(encoding='utf-8').splitlines()]
    if digest(records)!=digest(disk_records) or actual!=manifest['audit']:
        raise ValueError('Dataset replay/audit identity mismatch')
    if actual['status']!='PASSED':
        raise ValueError('Dataset audit failed; training blocked: '+'; '.join(actual['errors']))
    return [r for r in records if r['split']==split],actual['dataset_fingerprint']


def main():
    import argparse
    parser=argparse.ArgumentParser(description='Generate and audit a bounded procedural research dataset')
    parser.add_argument('output')
    parser.add_argument('--games',type=int,default=200)
    parser.add_argument('--seed',type=int,default=1701)
    parser.add_argument('--scope',choices=('whole-game','middle-late'),default='whole-game')
    args=parser.parse_args()
    manifest=write_dataset(args.output,args.games,args.seed,args.scope)
    print(json.dumps({k:v for k,v in manifest.items() if k!='audit'},indent=2))
    print(json.dumps({k:v for k,v in manifest['audit'].items() if k!='quarantine'},indent=2))
    return 0 if manifest['production_training_allowed'] else 2


if __name__=='__main__':
    raise SystemExit(main())
