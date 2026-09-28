"""Bounded, GUI-independent exploratory training with epoch-boundary resume."""
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import platform
import time
import tracemalloc
import traceback
import numpy as np
from .data import load_dataset, source_hash, code_commit, digest
from .model import Model, Config, VARIANTS, batch_arrays
from .evaluate import evaluate, schedule, plan
from .games import GAMES, exact_value
from .model import state_from


def train_epoch(model,records,deadline=None):
    # Epoch-addressed RNG has no hidden mutable state to reconstruct on resume.
    rng=np.random.default_rng(np.random.SeedSequence([model.config.seed,model.epoch]))
    indices=rng.permutation(len(records)); losses=[]
    for start in range(0,len(indices),model.config.batch_size):
        if deadline is not None and time.perf_counter()>=deadline:
            raise TimeoutError('Training budget exhausted between batches')
        batch=batch_arrays([records[i] for i in indices[start:start+model.config.batch_size]])
        losses.append(model.update(batch)['loss'])
    model.epoch+=1
    return {'epoch':model.epoch,'steps':model.step,'batch_mean_loss':float(np.mean(losses))}


def train(dataset,output,config,epochs=10,resume=False,max_seconds=180.,expected_identity=None):
    if epochs<1 or epochs>10 or max_seconds<=0 or max_seconds>180:
        raise ValueError('Pilot admission limits: 1..10 epochs, at most 180 seconds')
    output=Path(output)
    if not resume: output.mkdir(parents=True,exist_ok=False)
    elif not output.is_dir(): raise ValueError('Resume directory does not exist')
    started=time.perf_counter(); tracemalloc.start()
    try:
        records,fingerprint=load_dataset(dataset,'train')
        observed={'source_sha256':source_hash(),'dataset_fingerprint':fingerprint}
        if expected_identity is not None and observed!=expected_identity:
            raise ValueError('Dataset/source changed after pilot schedule freeze')
        identity={**observed,
                  'config_sha256':digest(asdict(config)), 'epochs':epochs,
                  'shuffle':'SeedSequence(seed,epoch); boundary-only resume',
                  'python':platform.python_version(),'numpy':np.__version__}
        checkpoint=output/'checkpoint.npz'
        model=Model.load(checkpoint,config,identity) if resume else Model(config)
        if model.epoch>epochs: raise ValueError('Checkpoint beyond planned epochs')
        history_path=output/'epochs.json'
        try:
            history=json.loads(history_path.read_text()) if resume and history_path.exists() else []
        except (json.JSONDecodeError,UnicodeDecodeError):
            history=[]  # Checkpoint is authoritative; missing history stays explicitly incomplete.
        # A crash between checkpoint/history writes must not replay committed epochs.
        history=[row for row in history if row['epoch']<=model.epoch]
        while model.epoch<epochs:
            if time.perf_counter()-started>=max_seconds: raise TimeoutError('Training admission time exhausted')
            history.append(train_epoch(model,records,started+max_seconds))
            model.save(checkpoint,identity)
            temporary=output/'epochs.json.tmp'
            with temporary.open('w',encoding='utf-8') as file:
                file.write(json.dumps(history,indent=2)); file.flush(); os.fsync(file.fileno())
            os.replace(temporary,history_path)
        if not model.step: raise ValueError('Zero-step training is invalid')
        if time.perf_counter()-started>max_seconds: raise TimeoutError('Training exceeded admission time')
        _,peak=tracemalloc.get_traced_memory()
        report={'status':'trained','identity':identity,'code_commit':code_commit(),
                'config':asdict(config),'epochs':model.epoch,'steps':model.step,
                'training_records':len(records),'parameters':model.parameter_counts(),
                'seconds':time.perf_counter()-started,'peak_tracemalloc_bytes':peak,
                'time_scope':'current attempt only; resumed attempts are not compute-comparable',
                'resumed':resume,'history_complete':len(history)==model.epoch,
                'memory_scope':'Python/NumPy traced allocations; not process RSS',
                'checkpoint_sha256':hashlib.sha256(checkpoint.read_bytes()).hexdigest()}
        (output/'training.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        return model,report
    except Exception:
        (output/'failure.txt').write_text('phase=training\n'+traceback.format_exc(),encoding='utf-8')
        raise
    finally:
        tracemalloc.stop()


def pilot(dataset,output):
    output=Path(output); output.mkdir(parents=True,exist_ok=False)
    validation,fingerprint=load_dataset(dataset,'validation')
    transfer,other=load_dataset(dataset,'transfer',exploratory_transfer=True)
    if other!=fingerprint: raise ValueError('Dataset changed between reads')
    expected={'source_sha256':source_hash(),'dataset_fingerprint':fingerprint}
    records=validation+transfer; positions=schedule(records)
    (output/'schedule.json').write_text(json.dumps(positions,indent=2),encoding='utf-8')
    baseline=[]
    for record in positions:
        game=GAMES[record['game']]; state=state_from(record['state']); cache={}
        values={a:-exact_value(game,game.transition(state,a),cache) for a in game.legal_actions(state)}
        result=plan(game,state)
        result.update(game=game.name,position=digest(record),trajectory=record['trajectory'],
                      regret=max(values.values())-values[result['action']] if result['status']=='complete' else None)
        baseline.append(result)
    results=[]
    for seed in (17,29,43):
        for variant in VARIANTS:
            if sum(p.stat().st_size for p in output.rglob('*') if p.is_file())>10**9:
                raise RuntimeError('Pilot artifact admission budget exceeded')
            folder=output/f'{variant}-{seed}'
            model,training=train(dataset,folder,Config(variant=variant,seed=seed),expected_identity=expected)
            began=time.perf_counter()
            evaluation=evaluate(model,records,positions)
            evaluation['seconds']=time.perf_counter()-began
            result={'training':training,'evaluation':evaluation}
            (folder/'evaluation.json').write_text(json.dumps(evaluation,indent=2,allow_nan=False),encoding='utf-8')
            results.append(result)
            (output/'partial-results.json').write_text(json.dumps(results,indent=2,allow_nan=False),encoding='utf-8')
            print(json.dumps({'variant':variant,'seed':seed,'train_seconds':training['seconds'],
                              'eval_seconds':evaluation['seconds'],'steps':model.step}),flush=True)
    receipt={'stage':'exploratory middle/late local-position pilot','source_sha256':source_hash(),
             'dataset_fingerprint':fingerprint,'code_commit':code_commit(),
             'schedule_sha256':digest(positions),'schedule_count':len(positions),
             'no_model_baseline':baseline,'runs':results,
             'selection_predictions':0,'final_predictions':0}
    _,final_fingerprint=load_dataset(dataset,'validation')
    if {'source_sha256':source_hash(),'dataset_fingerprint':final_fingerprint}!=expected:
        raise ValueError('Dataset/source changed before receipt publication')
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2,allow_nan=False),encoding='utf-8')
    return receipt


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dataset'); parser.add_argument('output')
    args=parser.parse_args()
    pilot(args.dataset,args.output)
