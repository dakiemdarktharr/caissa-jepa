"""Finite training-only convergence/capacity diagnosis; fresh runs only."""
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
from . import METHOD_VERSION
from .metrics import snapshot_metrics
from two_player_v22.data import load_dataset, batch_arrays, verify_bytes, source_identity
from two_player_v22.model import Model, Config, OBJECTIVE_VERSION
from two_player_v21.augmentation import augmentation_plan, augment
from two_player.data import digest, code_commit

SEEDS=(17,29,43)
FAMILIES=('direct','value-dynamics','raw-jepa')
CAPACITIES=((64,32),(128,64))
SNAPSHOTS=(0,40,80,160)
EPOCHS=160
DRAWS=16
CELL_LIMIT=300.
TOTAL_LIMIT=5400.
BYTE_LIMIT=3_000_000_000
DATA_FINGERPRINT='73acd3d11c3a30fa56703d19768d899dff51c6af6ccf2afddc0f5f007d46cc18'
REFERENCE_PATH='docs/validation/V23_EPOCH40_REFERENCES.json'
ROOT=Path(__file__).resolve().parents[1]


def configurations():
    return [Config(variant=v,hidden=h,latent=l,learning_rate=.001,
                   jepa_weight=.1 if v=='raw-jepa' else 1.,seed=s)
            for h,l in CAPACITIES for v in FAMILIES for s in SEEDS]


def run_id(config):
    return f'{config.variant}-h{config.hidden}-z{config.latent}-s{config.seed}'


def runtime_source():
    paths=set(source_identity()) | {'two_player_v22/model.py',
          'two_player_v21/augmentation.py','tools/diagnose_v21_value_alignment.py',
          'docs/METHOD_V23_DIAGNOSTIC.md',REFERENCE_PATH}
    paths|={p.relative_to(ROOT).as_posix() for p in Path(__file__).parent.glob('*.py')}
    return {p:hashlib.sha256((ROOT/p).read_bytes().replace(b'\r\n',b'\n')).hexdigest()
            for p in sorted(paths)}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tensor_hashes(model):
    return {prefix+key:hashlib.sha256(array.tobytes()).hexdigest()
            for prefix,group in (('p_',model.params),('t_',model.target),('m_',model.m),('v_',model.v))
            for key,array in group.items()}


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
            'method':METHOD_VERSION,'objective':OBJECTIVE_VERSION,'epochs':EPOCHS,'draws':DRAWS,
            'python':platform.python_version(),'numpy':np.__version__}


def references():
    receipt=json.loads((ROOT/REFERENCE_PATH).read_text(encoding='utf-8'))
    rows=receipt['rows']
    expected={(v,s) for v in FAMILIES for s in SEEDS}
    if receipt['dataset_fingerprint']!=DATA_FINGERPRINT or len(rows)!=len(expected):
        raise ValueError('Invalid epoch40 reference inventory')
    result={}
    for row in rows:
        key=(row['variant'],row['seed'])
        config=Config(variant=key[0],seed=key[1],learning_rate=.001,
                      jepa_weight=.1 if key[0]=='raw-jepa' else 1.)
        if (key not in expected or key in result or row['config']!=asdict(config)
                or row['epoch']!=40 or row['step']!=2640
                or len(row['array_hashes'])!=59 or digest(row['array_hashes'])!=row['tensor_digest']):
            raise ValueError('Invalid epoch40 tensor reference')
        result[key]=row
    return result


def artifact_bytes(path,exclude_ledger=False):
    path=Path(path)
    return sum(p.stat().st_size for p in path.rglob('*') if p.is_file()
               and not (exclude_ledger and p==path/'ledger.json'))


def check_train(train):
    manifest=train['manifest']
    if (manifest['dataset_fingerprint']!=DATA_FINGERPRINT or manifest['split']!='train'
            or manifest['role']!='redacted-training' or manifest['fraction']!=1.
            or manifest['label_seed']!=271828 or manifest['audit']['status']!='PASSED'
            or manifest['parent_audit_status']!='PASSED'
            or [len(train[k]) for k in ('roots','nodes','forks')]!=[509,9237,6750]
            or [manifest[k] for k in ('root_count','node_count','fork_count')]!=[509,9237,6750]):
        raise ValueError('Training artifact does not match frozen diagnostic')
    if any(r['split']!='train' for r in train['roots']) or any(f['split']!='train' for f in train['forks']):
        raise ValueError('Nontraining record in diagnostic')
    if any(n['value_labelled'] is not True or n['policy_labelled'] is not (not n['terminal'])
           for n in train['nodes'].values()):
        raise ValueError('Diagnostic requires full oracle label access')


def train_run(config,train,batch,path,source,reference,output):
    """Fresh finite cell. Failure journal includes elapsed work; never resumes."""
    path=Path(path); path.mkdir(parents=True,exist_ok=False)
    started=time.perf_counter(); deadline=started+CELL_LIMIT
    expected=identity(config,train['manifest'],source)
    history=[]; snapshots=[]
    def guard(check_files=False):
        if time.perf_counter()>=deadline: raise TimeoutError('Diagnostic cell acceptance limit exceeded')
        if check_files and artifact_bytes(output)>=BYTE_LIMIT: raise RuntimeError('Diagnostic artifact limit exceeded')
    def take_snapshot(model):
        guard()
        if runtime_source()!=source: raise ValueError('Source changed during snapshot')
        epoch,step=model.epoch,model.step
        if epoch not in SNAPSHOTS or step!=epoch*66: raise ValueError('Snapshot counter mismatch')
        before=tensor_hashes(model)
        cp=path/f'checkpoint-e{epoch:03d}.npz'
        model.save(cp,expected)
        restored=Model.load(cp,config,expected)
        if tensor_hashes(restored)!=before or (restored.epoch,restored.step)!=(epoch,step):
            raise ValueError('Saved online/EMA/Adam state or counters differ')
        guard(check_files=True)
        match='not_applicable'
        if config.hidden==64 and epoch==40:
            row=reference[(config.variant,config.seed)]
            if (row['config']!=asdict(config) or row['array_hashes']!=before
                    or row['epoch']!=epoch or row['step']!=step):
                raise ValueError('Small-model epoch40 replay differs from frozen Grid03 tensors')
            match='verified'
        values=snapshot_metrics(model,train,deadline)
        if tensor_hashes(model)!=before or (model.epoch,model.step)!=(epoch,step):
            raise ValueError('Read-only diagnostics mutated model')
        mp=path/f'snapshot-e{epoch:03d}.json'; atomic_json(mp,values)
        guard(check_files=True)
        snapshots.append({'epoch':epoch,'step':step,'checkpoint':cp.name,'checkpoint_sha256':sha(cp),
                          'metrics':mp.name,'metrics_sha256':sha(mp),'S':values['S'],
                          'collapse':values['collapse'],'reference_match':match})
        if values['collapse']: raise ValueError('Collapsed representation; diagnostic inconclusive')
        if runtime_source()!=source: raise ValueError('Source changed during diagnostics')
        guard()
    atomic_json(path/'budget.json',{'status':'active','identity':expected,'limit_seconds':CELL_LIMIT,
                                  'total_seconds':None})
    try:
        check_train(train)
        if config not in configurations(): raise ValueError('Unscheduled diagnostic configuration')
        if runtime_source()!=source: raise ValueError('Source changed before fitting')
        model=Model(config); take_snapshot(model)
        for epoch in range(EPOCHS):
            epoch_start=time.perf_counter(); guard()
            indices,schedule=epoch_indices(train['forks'],config.seed,epoch)
            if len(indices)!=8352: raise ValueError('Frozen sampling exposure differs')
            transformations,augmentation=augmentation_plan(train['forks'],indices,config.seed,epoch)
            names=[train['forks'][int(i)]['game'] for i in indices]
            metrics=defaultdict(float); counts=defaultdict(int); steps=0
            for start in range(0,len(indices),config.batch_size):
                guard(); selected=indices[start:start+config.batch_size]
                augmented=augment(subset(batch,selected),names[start:start+len(selected)],
                                  transformations[start:start+len(selected)])
                report=model.update(augmented); steps+=1
                for key,value in report.items():
                    if not math.isfinite(float(value)): raise ValueError('Nonfinite training metric')
                    metrics[key]+=float(value)*len(selected)
                    if key.endswith('_count'): counts[key]+=int(value)
            model.epoch=epoch+1
            if steps!=66 or model.step!=model.epoch*66: raise ValueError('Training schedule counter mismatch')
            if runtime_source()!=source: raise ValueError('Source changed during fitting')
            history.append({'epoch':model.epoch,'step':model.step,'steps':steps,'schedule':schedule,
                            'augmentation':augmentation,'label_and_target_count_totals':dict(counts),
                            'metrics_sample_weighted':{k:v/len(indices) for k,v in metrics.items()},
                            'seconds':time.perf_counter()-epoch_start})
            atomic_json(path/'history.json',history); guard(check_files=True)
            if model.epoch in SNAPSHOTS: take_snapshot(model)
        guard()
        elapsed=time.perf_counter()-started
        atomic_json(path/'budget.json',{'status':'complete','identity':expected,'limit_seconds':CELL_LIMIT,
                                      'total_seconds':elapsed})
        guard(check_files=True)
        return {'config':asdict(config),'identity':expected,'seconds':elapsed,
                'parameters':model.parameter_counts(),'history_sha256':sha(path/'history.json'),
                'snapshots':snapshots}
    except BaseException as exc:
        atomic_json(path/'budget.json',{'status':'failed','identity':expected,'limit_seconds':CELL_LIMIT,
                                      'total_seconds':time.perf_counter()-started,
                                      'error':f'{type(exc).__name__}: {exc}'})
        raise


def run_grid(dataset,output):
    if os.environ.get('OPENBLAS_NUM_THREADS')!='1' or os.environ.get('OMP_NUM_THREADS')!='1':
        raise ValueError('Set BLAS and OMP thread counts to1 before Python startup')
    output=Path(output); output.mkdir(parents=True,exist_ok=False)
    prep=time.perf_counter(); source=runtime_source(); reference=references()
    # Inspect only the supplied standalone manifest before the full transition audit.
    manifest,_=verify_bytes(dataset)
    if manifest['dataset_fingerprint']!=DATA_FINGERPRINT or manifest['split']!='train':
        raise ValueError('Only the frozen standalone training artifact is accepted')
    train=load_dataset(dataset,'train'); check_train(train)
    batch=batch_arrays(train,range(len(train['forks'])))
    ledger={'version':'v23-training-diagnostic01','method':METHOD_VERSION,'stage':'training-only diagnostic',
            'source':source,'code_commit':code_commit(),'dataset_fingerprint':DATA_FINGERPRINT,
            'dataset_manifest':train['manifest'],'epochs':EPOCHS,'snapshots':list(SNAPSHOTS),
            'development_predictions':0,'selection_predictions':0,'final_predictions':0,'new_search_decisions':0,
            'runs':[{'id':run_id(c),'config':asdict(c),'status':'planned'} for c in configurations()],
            'status':'active','total_cell_seconds':0.,'preparation_seconds':time.perf_counter()-prep,
            'artifact_bytes':0,'artifact_bytes_scope':'All output files except ledger.json; cap includes ledger.json',
            'array_bytes':sum(a.nbytes for a in batch.values()),'process_peak_rss_bytes':process_peak_rss(),
            'resource_limits':{'cell_seconds':CELL_LIMIT,'total_cell_seconds':TOTAL_LIMIT,'artifact_bytes':BYTE_LIMIT},
            'failures':[]}
    atomic_json(output/'ledger.json',ledger)
    for item,config in zip(ledger['runs'],configurations()):
        started=time.perf_counter()
        item['status']='started'; atomic_json(output/'ledger.json',ledger)
        print('START '+item['id'],flush=True)
        try:
            if ledger['total_cell_seconds']+CELL_LIMIT>TOTAL_LIMIT:
                raise RuntimeError('Insufficient cumulative budget for a complete cell')
            current,_=verify_bytes(dataset)
            if current!=train['manifest']: raise ValueError('Training artifact changed')
            receipt=train_run(config,train,batch,output/item['id'],source,reference,output)
            atomic_json(output/item['id']/'receipt.json',receipt)
            elapsed=time.perf_counter()-started
            # Outer per-cell audit/bookkeeping is conservatively included in ledger time.
            if elapsed>=CELL_LIMIT: raise TimeoutError('Complete cell work exceeded acceptance limit')
            if artifact_bytes(output)>=BYTE_LIMIT: raise RuntimeError('Aggregate output limit exceeded')
            item.update(status='complete',seconds=elapsed,receipt_sha256=sha(output/item['id']/'receipt.json'))
            print('COMPLETE '+item['id']+' '+str(round(elapsed,3))+'s',flush=True)
        except BaseException as exc:
            item.update(status='failed',seconds=time.perf_counter()-started,error=f'{type(exc).__name__}: {exc}')
            ledger['failures'].append(item['id']); ledger['status']='inconclusive'
            atomic_json(output/(item['id']+'-failure.json'),{'error':item['error'],'traceback':traceback.format_exc()})
            print('FAILED '+item['id']+' '+item['error'],flush=True)
        ledger['total_cell_seconds']+=item['seconds']
        ledger['artifact_bytes']=artifact_bytes(output,exclude_ledger=True)
        ledger['process_peak_rss_bytes']=process_peak_rss()
        if ledger['total_cell_seconds']>=TOTAL_LIMIT: ledger['status']='inconclusive'
        atomic_json(output/'ledger.json',ledger)
        if item['status']!='complete' or ledger['status']=='inconclusive': break
    if all(item['status']=='complete' for item in ledger['runs']): ledger['status']='complete'
    if runtime_source()!=source: ledger['status']='inconclusive'; ledger['failures'].append('source changed')
    ledger['artifact_bytes']=artifact_bytes(output,exclude_ledger=True)
    atomic_json(output/'ledger.json',ledger)
    if artifact_bytes(output)>=BYTE_LIMIT:
        ledger['status']='inconclusive'
        ledger['failures'].append('final ledger exceeded aggregate artifact limit')
        atomic_json(output/'ledger.json',ledger)
    return ledger


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('training'); parser.add_argument('output')
    args=parser.parse_args(); result=run_grid(args.training,args.output)
    print(json.dumps({'status':result['status'],'runs':len(result['runs']),'failures':result['failures']}))
