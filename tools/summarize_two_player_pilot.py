"""Publish aggregate exploratory evidence without publishing trajectories/weights."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from two_player.data import digest, source_hash
from two_player.model import VARIANTS
from two_player.games import GAMES


def summarize(run_directory,dataset_directory,output):
    run_directory=Path(run_directory); output=Path(output)
    raw=(run_directory/'receipt.json').read_bytes(); receipt=json.loads(raw)
    manifest=json.loads((Path(dataset_directory)/'manifest.json').read_text())
    schedule=json.loads((run_directory/'schedule.json').read_text())
    if digest(schedule)!=receipt['schedule_sha256'] or source_hash()!=receipt['source_sha256']:
        raise ValueError('Schedule/source mismatch')
    if receipt['dataset_fingerprint']!=manifest['audit']['dataset_fingerprint']:
        raise ValueError('Dataset mismatch')
    runs=receipt['runs']
    if len(runs)!=21 or {(r['training']['config']['variant'],r['training']['config']['seed']) for r in runs}!={(v,s) for v in VARIANTS for s in (17,29,43)}:
        raise ValueError('Missing or duplicate predeclared runs')
    aggregate=[]; checkpoints=[]
    for run in runs:
        training=run['training']; evaluation=run['evaluation']; config=training['config']
        if training['identity']['source_sha256']!=receipt['source_sha256'] or training['identity']['dataset_fingerprint']!=receipt['dataset_fingerprint'] or evaluation['schedule_sha256']!=receipt['schedule_sha256']:
            raise ValueError('Run identity mismatch')
        checkpoint=run_directory/f"{config['variant']}-{config['seed']}"/'checkpoint.npz'
        if hashlib.sha256(checkpoint.read_bytes()).hexdigest()!=training['checkpoint_sha256']:
            raise ValueError('Checkpoint checksum mismatch')
        checkpoints.append(training)
        for name,representation in evaluation['representation'].items():
            row={'variant':config['variant'],'seed':config['seed'],'game':name,'representation':representation}
            for track in ('exact','hybrid'):
                records=[r for r in evaluation['decisions'] if r['game']==name and r['track']==track]
                complete=[r for r in records if r['status']=='complete']
                row[track]={'scheduled':sum(r['game']==name for r in schedule),'completed':len(complete),
                            'censored':len(records)-len(complete),'blocked':evaluation['planning_status']=='blocked_collapse',
                            'mean_regret':float(np.mean([r['regret'] for r in complete])) if complete else None,
                            'nonzero_regret':sum(r['regret']>0 for r in complete),
                            'neural_positions':sum(r['value_calls']>0 for r in complete),
                            'oracle_action_gap_positions':sum(r['oracle_action_gap']>0 for r in complete),
                            'seconds_total':sum(r['seconds'] for r in records),
                            'nodes_total':sum(r['nodes'] for r in records),
                            'value_calls_total':sum(r['value_calls'] for r in records)}
            aggregate.append(row)
    baselines={}
    for name in GAMES:
        rows=[r for r in receipt['no_model_baseline'] if r['game']==name]
        complete=[r for r in rows if r['status']=='complete']
        baselines[name]={'scheduled':len(rows),'completed':len(complete),'censored':len(rows)-len(complete),
                         'mean_regret':float(np.mean([r['regret'] for r in complete])) if complete else None}
    result={'stage':receipt['stage'],'code_commit':receipt['code_commit'],'source_sha256':receipt['source_sha256'],
            'raw_receipt_sha256':hashlib.sha256(raw).hexdigest(),'schedule_sha256':receipt['schedule_sha256'],
            'dataset_fingerprint':receipt['dataset_fingerprint'],
            'dataset':{k:v for k,v in manifest.items() if k!='audit'},
            'audit':{k:v for k,v in manifest['audit'].items() if k!='quarantine'},
            'hardware':{'cpu':'AMD Ryzen AI 5 340 w/ Radeon 840M','physical_cores':6,'logical_cores':12,
                        'physical_memory_bytes':16418648064,'blas_threads':1},
            'timing_limitations':'tracemalloc enabled; early runs overlapped regression tests; not an isolated efficiency benchmark',
            'uncertainty':'Three seed values retained; conditional trajectory bootstrap for NLL/value MSE only. Seed ranges are descriptive. Zero-regret ceiling is not equivalence. No confirmatory p-values.',
            'selection_predictions':0,'final_predictions':0,
            'no_model_baseline':baselines,'checkpoints':checkpoints,'metrics':aggregate}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
    print('variant | game | exact regret seeds | hybrid regret seeds')
    for variant in VARIANTS:
        for name in GAMES:
            rows=[r for r in aggregate if r['variant']==variant and r['game']==name]
            print(variant,name,[r['exact']['mean_regret'] for r in rows],[r['hybrid']['mean_regret'] for r in rows])
    return result


if __name__=='__main__': summarize(*sys.argv[1:])
