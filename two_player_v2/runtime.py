"""Bounded, paired v2 development grid; selection/final remain inaccessible."""
from collections import defaultdict
from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import tempfile
import time
import traceback

import numpy as np
from .data import load_dataset, batch_arrays, verify_bytes, source_identity
from .model import Model, Config, VARIANTS, OBJECTIVE_VERSION
from .evaluate import evaluate, representation
from two_player.data import digest, code_commit

SEEDS=(17,29,43)
RATES=(.001,.0003)
EPOCHS=40
DRAWS=16


def process_peak_rss():
    """Windows process-lifetime peak, including data/preprocessing/earlier cells."""
    if os.name!='nt': return None
    import ctypes
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[(name,ctypes.c_size_t) for name in
            ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage',
             'QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
    kernel=ctypes.WinDLL('kernel32',use_last_error=True); psapi=ctypes.WinDLL('psapi',use_last_error=True)
    kernel.GetCurrentProcess.restype=wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes=[wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD]
    memory=Counters(); memory.cb=ctypes.sizeof(memory)
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(),ctypes.byref(memory),memory.cb):
        raise OSError(ctypes.get_last_error(),'GetProcessMemoryInfo failed')
    return int(memory.PeakWorkingSetSize)


def atomic_json(path, obj):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            json.dump(obj,stream,indent=2,allow_nan=False); stream.flush(); os.fsync(stream.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


def runtime_source():
    root=Path(__file__).resolve().parents[1]
    paths=sorted(set(source_identity()) | {p.relative_to(root).as_posix() for p in (root/'two_player_v2').glob('*.py')} | {'docs/METHOD_V2.md'})
    return {p:hashlib.sha256((root/p).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for p in paths}


def epoch_indices(forks,seed,epoch):
    """Equal games/roots; uniform complete forks within each sampled root.

    Hence actions with more replies have more fork mass. All controls share it.
    """
    if type(epoch) is not int or epoch<0: raise ValueError('Invalid epoch')
    groups=defaultdict(lambda:defaultdict(list))
    for i,fork in enumerate(forks):
        if fork['split']!='train': raise ValueError('Sampling nontraining fork')
        groups[fork['game']][fork['root_id']].append(i)
    if not groups: raise ValueError('No training roots')
    maximum=max(len(g) for g in groups.values())
    rng=np.random.default_rng(np.random.SeedSequence([seed,epoch,2201]))
    indices=[]; counts={}
    for name,group in sorted(groups.items()):
        roots=sorted(group); order=list(rng.permutation(len(roots)))
        if len(order)<maximum: order+=rng.integers(len(roots),size=maximum-len(order)).tolist()
        for index in order:
            indices.extend(rng.choice(group[roots[index]],size=DRAWS,replace=True).tolist())
        counts[name]={'unique_roots':len(roots),'root_draws':maximum,'repeated_root_draws':maximum-len(roots),'fork_draws':maximum*DRAWS}
    result=np.asarray(indices,dtype=np.int64); rng.shuffle(result)
    return result,{'games':counts,'samples':len(result),'unique_forks':len(np.unique(result)),
                   'index_sha256':hashlib.sha256(result.astype('<i8').tobytes()).hexdigest()}


def subset(batch,indices): return {key:array[indices] for key,array in batch.items()}


def identity(config,manifest,source):
    return {'source':source,'data':manifest['dataset_fingerprint'],'config_sha256':digest(asdict(config)),
            'method':OBJECTIVE_VERSION,'epochs':EPOCHS,'draws':DRAWS,
            'python':platform.python_version(),'numpy':np.__version__}


def verify_resume(model,forks):
    count=len(epoch_indices(forks,model.config.seed,0)[0])
    if model.epoch>EPOCHS or model.step!=model.epoch*math.ceil(count/model.config.batch_size):
        raise ValueError('Checkpoint epoch/step does not match frozen schedule')


def train_run(config,train,batch,path,source,*,max_seconds=180.,resume=False):
    if not np.isfinite(max_seconds) or max_seconds<=0: raise ValueError('Invalid time cap')
    path=Path(path); path.mkdir(parents=True,exist_ok=resume)
    expected=identity(config,train['manifest'],source)
    if runtime_source()!=source: raise ValueError('Source changed before training')
    if resume:
        model=Model.load(path/'checkpoint.npz',config,expected); verify_resume(model,train['forks'])
        history=json.loads((path/'history.json').read_text())
        if len(history)!=model.epoch: raise ValueError('Checkpoint/history mismatch; explicit recovery required')
        budget=json.loads((path/'budget.json').read_text())
        if budget['status']!='complete' or budget['identity']!=expected:
            raise ValueError('Interrupted attempt has unaccounted compute; frozen-grid resume refused')
        prior_seconds=float(budget['total_seconds'])
        if not np.isfinite(prior_seconds) or prior_seconds<0 or budget['limit_seconds']!=max_seconds:
            raise ValueError('Invalid prior elapsed time or changed time cap')
    else: model=Model(config); history=[]; prior_seconds=0.
    started=time.perf_counter()
    atomic_json(path/'budget.json',{'status':'active','identity':expected,'prior_seconds':prior_seconds,
                                  'limit_seconds':max_seconds})
    for epoch in range(model.epoch,EPOCHS):
        epoch_start=time.perf_counter(); indices,schedule=epoch_indices(train['forks'],config.seed,epoch)
        metrics=defaultdict(float); steps=0
        for start in range(0,len(indices),config.batch_size):
            if prior_seconds+time.perf_counter()-started>=max_seconds: raise TimeoutError('Frozen training time cap exceeded')
            selected=indices[start:start+config.batch_size]
            report=model.update(subset(batch,selected)); steps+=1
            for k,v in report.items(): metrics[k]+=float(v)*len(selected)
        model.epoch=epoch+1
        if runtime_source()!=source: raise ValueError('Source changed during training')
        history.append({'epoch':model.epoch,'step':model.step,'steps':steps,'schedule':schedule,
                        'metrics_sample_weighted':{k:v/len(indices) for k,v in metrics.items()},
                        'seconds':time.perf_counter()-epoch_start})
        model.save(path/'checkpoint.npz',expected); atomic_json(path/'history.json',history)
    elapsed=time.perf_counter()-started
    if prior_seconds+elapsed>=max_seconds: raise TimeoutError('Frozen training time cap exceeded at completion')
    verify_resume(model,train['forks'])
    restored=Model.load(path/'checkpoint.npz',config,expected)
    if any(not np.array_equal(restored.params[k],v) for k,v in model.params.items()):
        raise ValueError('Saved checkpoint differs from trained model')
    elapsed=time.perf_counter()-started
    if prior_seconds+elapsed>=max_seconds: raise TimeoutError('Training/checkpoint verification exceeded cap')
    atomic_json(path/'budget.json',{'status':'complete','identity':expected,'total_seconds':prior_seconds+elapsed,
                                  'limit_seconds':max_seconds})
    return model,{'seconds':elapsed,'prior_attempt_seconds':prior_seconds,'epoch':model.epoch,'steps':model.step,
                  'identity':expected,'parameters':model.parameter_counts(),
                  'checkpoint_sha256':hashlib.sha256((path/'checkpoint.npz').read_bytes()).hexdigest()}


def diagnostics(model,dev,batch):
    return {name:representation(model,subset(batch,[i for i,r in enumerate(dev['forks']) if r['game']==name]))
            for name in sorted({r['game'] for r in dev['roots']})}


def run_grid(dataset,output):
    if os.environ.get('OPENBLAS_NUM_THREADS')!='1' or os.environ.get('OMP_NUM_THREADS')!='1':
        raise ValueError('Set both BLAS/OMP thread variables to1 before Python startup')
    output=Path(output); output.mkdir(parents=True,exist_ok=False)
    source=runtime_source(); manifest,_=verify_bytes(dataset)
    train=load_dataset(dataset,'train'); dev=load_dataset(dataset,'development')
    train_batch=batch_arrays(train,range(len(train['forks'])))
    dev_batch=batch_arrays(dev,range(len(dev['forks'])))
    configs=[Config(variant=v,learning_rate=lr,seed=s) for v in VARIANTS for lr in RATES for s in SEEDS]
    ledger={'version':'v2-grid01','stage':'development','source':source,'code_commit':code_commit(),
            'dataset_fingerprint':manifest['dataset_fingerprint'],'epochs':EPOCHS,'draws':DRAWS,
            'train_roots':len(train['roots']),'development_roots':len(dev['roots']),
            'development_schedule_sha256':digest([(r['game'],r['root_id'],r['trajectory']) for r in dev['roots']]),
            'selection_predictions':0,'final_predictions':0,'runs':[
                {'id':f'{c.variant}-lr{c.learning_rate:g}-s{c.seed}','config':asdict(c),'status':'planned'} for c in configs],
            'array_bytes':sum(a.nbytes for b in (train_batch,dev_batch) for a in b.values()),
            'memory_scope':'array bytes plus process-lifetime peak RSS, including preprocessing and previous cells; not per-model peak',
            'process_peak_rss_bytes':process_peak_rss(),'failures':[]}
    atomic_json(output/'ledger.json',ledger)
    controls={'zero':evaluate(dev['roots'],None,tracks=('exact',)),
              'untrained':{str(s):evaluate(dev['roots'],Model(Config(variant='direct',seed=s)),tracks=('exact',)) for s in SEEDS}}
    atomic_json(output/'controls.json',controls)
    ledger['controls_sha256']=hashlib.sha256((output/'controls.json').read_bytes()).hexdigest()
    control_rows=controls['zero']+[r for rows in controls['untrained'].values() for r in rows]
    ledger['control_status_counts']={status:sum(r['status']==status for r in control_rows) for status in ('complete','censored','error')}
    atomic_json(output/'ledger.json',ledger)
    for item,config in zip(ledger['runs'],configs):
        item['status']='started'; atomic_json(output/'ledger.json',ledger)
        print('START '+item['id'],flush=True)
        try:
            current,_=verify_bytes(dataset)
            if current['dataset_fingerprint']!=manifest['dataset_fingerprint']: raise ValueError('Dataset changed')
            if sum(p.stat().st_size for p in output.rglob('*') if p.is_file())>=2_900_000_000:
                raise RuntimeError('Frozen aggregate artifact cap reached')
            model,receipt=train_run(config,train,train_batch,output/item['id'],source)
            scores=evaluate(dev['roots'],model)
            metrics=diagnostics(model,dev,dev_batch)
            receipt.update(config=asdict(config),scores=scores,representation=metrics)
            if runtime_source()!=source: raise ValueError('Source changed during evaluation')
            atomic_json(output/item['id']/'receipt.json',receipt)
            item.update(status='complete',seconds=receipt['seconds'],checkpoint_sha256=receipt['checkpoint_sha256'],
                        decision_status_counts={status:sum(r['status']==status for r in scores) for status in ('complete','censored','error')},
                        receipt_sha256=hashlib.sha256((output/item['id']/'receipt.json').read_bytes()).hexdigest())
            ledger['process_peak_rss_bytes']=process_peak_rss()
            if sum(p.stat().st_size for p in output.rglob('*') if p.is_file())>=3_000_000_000:
                raise RuntimeError('Aggregate artifact cap exceeded; stop remaining cells')
            print('COMPLETE '+item['id']+' '+str(round(receipt['seconds'],3))+'s',flush=True)
        except Exception as exc:
            item.update(status='failed',error=f'{type(exc).__name__}: {exc}')
            ledger['failures'].append(item['id'])
            atomic_json(output/(item['id']+'-failure.json'),{'error':item['error'],'traceback':traceback.format_exc()})
            print('FAILED '+item['id']+' '+item['error'],flush=True)
            # Source/data/resource changes make later cells unsafe; preserve planned entries.
            if not isinstance(exc,TimeoutError):
                atomic_json(output/'ledger.json',ledger); raise
        atomic_json(output/'ledger.json',ledger)
    decisions_ok=all(r.get('decision_status_counts',{}).get('complete')==2*len(dev['roots']) for r in ledger['runs'])
    controls_ok=ledger['control_status_counts']['complete']==4*len(dev['roots'])
    ledger['status']='complete' if all(r['status']=='complete' for r in ledger['runs']) and decisions_ok and controls_ok else 'inconclusive'
    atomic_json(output/'ledger.json',ledger)
    return ledger


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dataset'); parser.add_argument('output')
    args=parser.parse_args(); result=run_grid(args.dataset,args.output)
    print(json.dumps({'status':result['status'],'runs':len(result['runs']),'failures':result['failures']}))
