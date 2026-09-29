"""Fresh, bounded and paired development grid from METHOD_V25."""
from collections import defaultdict
from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import time
import traceback

import numpy as np

from . import METHOD_VERSION
from .model import Model, Config, OBJECTIVE_VERSION
from .data import build_groups, epoch_plan, make_batch
from .metrics import diagnostics
from two_player.data import digest, code_commit
from two_player_v22.data import load_dataset, batch_arrays, verify_bytes
from two_player_v22.runtime import runtime_source as prior_source
from two_player_v23_diagnostic.runtime import atomic_json, process_peak_rss, tensor_hashes, check_train
from two_player_v2.evaluate import evaluate

ROOT = Path(__file__).resolve().parents[1]
TRAIN_FP = '73acd3d11c3a30fa56703d19768d899dff51c6af6ccf2afddc0f5f007d46cc18'
DEV_FP = 'bbfc41fc34e1e346a9dc5905f9f686bb61582e4a63f363d76ea2406088235617'
FAMILIES = ('direct','recurrent-pv','decoded-tail','scalar-tail','raw-mean','raw-tail','raw-scaled')
SEEDS = (17,29,43)
RATES = (.001,.0003)
EPOCHS = 160
CELL_LIMIT = 600.
TOTAL_LIMIT = 25200.
BYTE_LIMIT = 3_000_000_000
RSS_LIMIT = 1_000_000_000


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition: raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'),
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def configurations():
    return [Config(variant=v, learning_rate=rate, seed=seed)
            for v in FAMILIES for rate in RATES for seed in SEEDS]


def run_id(config):
    return f'{config.variant}-lr{config.learning_rate:g}-s{config.seed}'


def runtime_source():
    paths = set(prior_source()) | {'docs/METHOD_V25.md', 'two_player_v23_diagnostic/runtime.py',
                                  'two_player_v23_diagnostic/__init__.py', 'two_player_v23_diagnostic/metrics.py'}
    paths |= {p.relative_to(ROOT).as_posix() for p in Path(__file__).parent.glob('*.py')}
    return {p: hashlib.sha256((ROOT/p).read_bytes().replace(b'\r\n', b'\n')).hexdigest() for p in sorted(paths)}


def identity(config, manifest, group_sha256, source):
    return {'method': METHOD_VERSION, 'objective': OBJECTIVE_VERSION, 'source': source,
            'data': manifest['dataset_fingerprint'], 'group_sha256': group_sha256,
            'config_sha256': digest(asdict(config)), 'epochs': EPOCHS, 'group_draws_per_root': 4,
            'sampling_namespace': 2501, 'symmetry_namespace': 2511,
            'python': platform.python_version(), 'numpy': np.__version__}


def artifact_bytes(directory):
    return sum(p.stat().st_size for p in Path(directory).rglob('*') if p.is_file())


def check_development(dev):
    m = dev['manifest']
    require(m['dataset_fingerprint']==DEV_FP and m['split']=='development'
            and m['role']=='standalone-development' and m['fraction']==1.
            and m['audit']['status']=='PASSED' and m['parent_audit_status']=='PASSED'
            and len(dev['roots'])==209, 'Unfrozen standalone development input')
    require(all(r['split']=='development' for r in dev['roots'])
            and all(f['split']=='development' for f in dev['forks']), 'Foreign development records')
    require({g:sum(r['game']==g for r in dev['roots']) for g in ('connect4-4x5','reversi6')}
            == {'connect4-4x5':107,'reversi6':102}, 'Development game counts changed')


def fit_model(config, train, base, grouping, path, source, guard):
    """This optimizer boundary receives no development object or path."""
    check_train(train)
    require(config in configurations(), 'Unscheduled model configuration')
    expected = identity(config, train['manifest'], grouping['group_sha256'], source)
    guard(); require(runtime_source()==source, 'Source changed before model creation')
    model = Model(config); history = []
    group_identity = digest(grouping)
    for epoch in range(EPOCHS):
        started = time.perf_counter(); guard()
        indices, transforms, schedule = epoch_plan(grouping, config.seed, epoch)
        require(len(indices)==len(transforms)==2088 and schedule['group_draws']==2088,
                'Frozen grouped exposure changed')
        metrics, counts, sums = defaultdict(float), defaultdict(int), defaultdict(float)
        factor_min, factor_max = None, None
        steps = fork_rows = 0
        for start in range(0, len(indices), config.batch_groups):
            guard(); selected = indices[start:start+config.batch_groups]
            batch = make_batch(base, grouping, selected, transforms[start:start+len(selected)])
            require(len(np.unique(batch['group']))==len(selected), 'Partial/repeated draw groups conflated')
            report = model.update(batch); guard()
            steps += 1; fork_rows += len(batch['group'])
            for key, value in report.items():
                require(math.isfinite(float(value)), 'Nonfinite training receipt')
                metrics[key] += float(value)*len(selected)
                if key.endswith('_count'):
                    require(float(value).is_integer(), 'Fractional quantity labelled a count')
                    counts[key] += int(value)
                if key.endswith('_sum'): sums[key] += float(value)
            if report['h2_scaled_factor_count']:
                lo,hi=report['h2_scaled_factor_min'],report['h2_scaled_factor_max']
                factor_min=lo if factor_min is None else min(factor_min,lo)
                factor_max=hi if factor_max is None else max(factor_max,hi)
        model.epoch = epoch+1
        require(steps==66 and model.step==model.epoch*66 and fork_rows==schedule['fork_rows'],
                'Grouped training update/exposure mismatch')
        require(digest(grouping)==group_identity, 'Training mutated grouping metadata')
        require(runtime_source()==source, 'Source changed during fitting')
        history.append({'epoch':model.epoch,'step':model.step,'steps':steps,'schedule':schedule,
                        'fork_rows':fork_rows,'group_draws':len(indices),'count_totals':dict(counts),
                        'sum_totals':dict(sums),
                        'scaled_factors':{'count':counts['h2_scaled_factor_count'],
                            'min':factor_min,'max':factor_max,
                            'mean':sums['h2_scaled_factor_sum']/counts['h2_scaled_factor_count']
                                   if counts['h2_scaled_factor_count'] else None},
                        'metrics_group_weighted_batch_mean':{k:v/len(indices) for k,v in metrics.items()},
                        'seconds':time.perf_counter()-started})
        atomic_json(path/'history.json',history); guard(check_files=True)
    before = tensor_hashes(model)
    model.save(path/'checkpoint.npz', expected); guard(check_files=True)
    restored = Model.load(path/'checkpoint.npz',config,expected)
    require(tensor_hashes(restored)==before and (restored.epoch,restored.step)==(EPOCHS,EPOCHS*66),
            'Saved checkpoint differs from trained state')
    guard()
    return model, {'identity':expected,'epoch':model.epoch,'step':model.step,
                   'checkpoint_sha256':sha(path/'checkpoint.npz'),'tensor_sha256':digest(before),
                   'history_sha256':sha(path/'history.json'),'parameters':model.parameter_counts()}


def run_grid(training, development, output):
    require(os.environ.get('OPENBLAS_NUM_THREADS')==os.environ.get('OMP_NUM_THREADS')=='1',
            'Set both BLAS/OMP thread variables to1 before Python startup')
    training,development,output = (Path(p).resolve() for p in (training,development,output))
    require(not output.is_relative_to(training) and not output.is_relative_to(development),
            'Output must be outside immutable input directories')
    output.mkdir(parents=True,exist_ok=False)
    source = runtime_source(); started = time.perf_counter()
    ledger = {'version':'v25-grid04','method':METHOD_VERSION,'stage':'development','status':'active',
              'source':source,'code_commit':code_commit(),'epochs':EPOCHS,
              'limits':{'cell_seconds':CELL_LIMIT,'total_cell_seconds':TOTAL_LIMIT,'bytes':BYTE_LIMIT,'rss':RSS_LIMIT},
              'selection_predictions':0,'final_predictions':0,'development_decisions':0,
              'runs':[{'id':run_id(c),'config':asdict(c),'status':'planned'} for c in configurations()],
              'failures':[],'total_cell_seconds':0.,'preparation_seconds':None,
              'array_bytes':None,'process_peak_rss_bytes':None}
    atomic_json(output/'ledger.json',ledger)
    def resources(check_files=True):
        rss = process_peak_rss()
        require(rss is not None, 'Peak RSS measurement unavailable')
        if rss>=RSS_LIMIT: raise MemoryError('Frozen peak RSS limit exceeded')
        if check_files and artifact_bytes(output)>=BYTE_LIMIT: raise RuntimeError('Frozen output-byte limit exceeded')
        if ledger['total_cell_seconds']>=TOTAL_LIMIT: raise TimeoutError('Frozen cumulative cell limit exceeded')
    active = None; cell_started = None
    try:
        resources()
        tm,_ = verify_bytes(training); dm,_ = verify_bytes(development)
        require(tm['dataset_fingerprint']==TRAIN_FP and dm['dataset_fingerprint']==DEV_FP,
                'Only pinned standalone train/development artifacts are accepted')
        train = load_dataset(training,'train'); check_train(train)
        dev = load_dataset(development,'development'); check_development(dev)
        require(tm==train['manifest'] and dm==dev['manifest'] and
                tm['parent_dataset_fingerprint']==dm['parent_dataset_fingerprint'], 'Manifest provenance mismatch')
        groups = build_groups(train); dev_groups = build_groups(dev)
        require(len(groups['groups'])==2056, 'Training own-action inventory changed')
        base = batch_arrays(train,range(len(train['forks'])))
        dev_base = batch_arrays(dev,range(len(dev['forks'])))
        for arrays in (base,dev_base):
            for value in arrays.values(): value.setflags(write=False)
        schedule = [(r['game'],r['root_id'],r['trajectory']) for r in dev['roots']]
        truth = {'roots':[{k:r[k] for k in ('game','root_id','trajectory','actions','oracle_values','beyond_depth')}
                          for r in dev['roots']],
                 'unique_node_counts':{g:sum(n['game']==g for n in dev['nodes'].values())
                                       for g in ('connect4-4x5','reversi6')},
                 'development_fingerprint':DEV_FP}
        ledger.update(train_manifest=tm,development_manifest=dm,
                      train_group_sha256=groups['group_sha256'],development_group_sha256=dev_groups['group_sha256'],
                      development_schedule=schedule,development_schedule_sha256=digest(schedule),
                      development_truth=truth,development_truth_sha256=digest(truth),
                      array_bytes=sum(a.nbytes for b in (base,dev_base) for a in b.values()))
        atomic_json(output/'train-groups.json',groups); atomic_json(output/'development-groups.json',dev_groups)
        ledger['train_groups_file_sha256']=sha(output/'train-groups.json')
        ledger['development_groups_file_sha256']=sha(output/'development-groups.json')
        controls = {'zero':evaluate(dev['roots'],None,tracks=('exact',)),
                    'untrained':{str(seed):evaluate(dev['roots'],Model(Config(variant='direct',seed=seed)),tracks=('exact',)) for seed in SEEDS}}
        rows = controls['zero']+[row for values in controls['untrained'].values() for row in values]
        require(len(rows)==836 and all(r['status']=='complete' for r in rows),'Control decision failed/censored')
        atomic_json(output/'controls.json',controls); resources()
        ledger.update(controls_sha256=sha(output/'controls.json'),control_decisions=len(rows),
                      preparation_seconds=time.perf_counter()-started)
        require(runtime_source()==source,'Source changed during preparation')
        atomic_json(output/'ledger.json',ledger)
        for item,config in zip(ledger['runs'],configurations()):
            resources(); cell_started = time.perf_counter(); active = item
            path = output/active['id']; path.mkdir(exist_ok=False)
            active['status']='started'; atomic_json(output/'ledger.json',ledger)
            def guard(check_files=False):
                elapsed = time.perf_counter()-cell_started
                if elapsed>=CELL_LIMIT: raise TimeoutError('Frozen cell limit exceeded')
                if ledger['total_cell_seconds']+elapsed>=TOTAL_LIMIT: raise TimeoutError('Frozen cumulative cell limit exceeded')
                resources(check_files=check_files)
            expected = identity(config,tm,groups['group_sha256'],source)
            atomic_json(path/'budget.json',{'status':'active','identity':expected,'limit_seconds':CELL_LIMIT,'total_seconds':None})
            print('START '+active['id'],flush=True)
            guard()
            require(verify_bytes(training)[0]==tm and verify_bytes(development)[0]==dm,'Input bytes changed before cell')
            model,receipt = fit_model(config,train,base,groups,path,source,guard)
            before = tensor_hashes(model); counters = (model.epoch,model.step)
            guard(); scores = evaluate(dev['roots'],model); guard()
            require(len(scores)==418 and all(row['status']=='complete' for row in scores), 'Learned decision failed/censored')
            occurrence,details = diagnostics(model,dev,dev_base,dev_groups,guard)
            require(not details['collapse'], 'Collapsed unique-node representation; grid inconclusive')
            require(tensor_hashes(model)==before and (model.epoch,model.step)==counters,'Evaluation mutated model state')
            require(runtime_source()==source and verify_bytes(training)[0]==tm and verify_bytes(development)[0]==dm,
                    'Source/data changed during cell')
            guard()
            receipt.update(status='complete',config=asdict(config),scores=scores,representation=occurrence,
                           diagnostics=details,seconds=time.perf_counter()-cell_started)
            atomic_json(path/'receipt.json',receipt); guard(check_files=True)
            elapsed = time.perf_counter()-cell_started
            atomic_json(path/'budget.json',{'status':'complete','identity':expected,'limit_seconds':CELL_LIMIT,'total_seconds':elapsed})
            guard(check_files=True)
            elapsed = time.perf_counter()-cell_started
            active.update(status='complete',seconds=elapsed,receipt_sha256=sha(path/'receipt.json'),
                          checkpoint_sha256=receipt['checkpoint_sha256'])
            ledger['total_cell_seconds']+=elapsed
            ledger['development_decisions']+=len(scores)
            ledger['process_peak_rss_bytes']=process_peak_rss()
            atomic_json(output/'ledger.json',ledger); resources()
            # The final ledger write is still inside this cell's acceptance
            # envelope; cumulative cost already contains its recorded elapsed.
            final_elapsed=time.perf_counter()-cell_started
            if final_elapsed>=CELL_LIMIT or ledger['total_cell_seconds']+final_elapsed-elapsed>=TOTAL_LIMIT:
                raise TimeoutError('Final cell ledger write exceeded frozen acceptance limit')
            print('COMPLETE '+active['id']+' '+str(round(elapsed,3))+'s',flush=True)
            active=None; cell_started=None
        require(runtime_source()==source and verify_bytes(training)[0]==tm and verify_bytes(development)[0]==dm,
                'Final source/input verification failed')
        require(sha(output/'train-groups.json')==ledger['train_groups_file_sha256'] and
                sha(output/'development-groups.json')==ledger['development_groups_file_sha256'] and
                sha(output/'controls.json')==ledger['controls_sha256'],'Saved schedule/control bytes changed')
        for item in ledger['runs']:
            require(sha(output/item['id']/'receipt.json')==item['receipt_sha256'] and
                    sha(output/item['id']/'checkpoint.npz')==item['checkpoint_sha256'],'Saved cell bytes changed')
            resources()
        ledger.update(status='complete',total_wall_seconds=time.perf_counter()-started,
                      process_peak_rss_bytes=process_peak_rss())
        atomic_json(output/'ledger.json',ledger); resources()
    except BaseException as exc:
        error=f'{type(exc).__name__}: {exc}'
        if active is not None:
            elapsed = time.perf_counter()-cell_started
            # A completed cell may have failed on the final ledger/resource check.
            if active['status']=='complete': ledger['total_cell_seconds']-=active['seconds']
            active.update(status='failed',seconds=elapsed,error=error)
            ledger['total_cell_seconds']+=elapsed
            failure_path=output/active['id']; failure_path.mkdir(exist_ok=True)
            atomic_json(failure_path/'budget.json',{'status':'failed','limit_seconds':CELL_LIMIT,'total_seconds':elapsed,'error':error})
            if (failure_path/'receipt.json').exists():
                failed=read(failure_path/'receipt.json'); failed.update(status='failed',error=error)
                atomic_json(failure_path/'receipt.json',failed)
            ledger['failures'].append(active['id'])
        else:
            ledger['failures'].append('preparation_or_completion')
        ledger.update(status='inconclusive',error=error,traceback=traceback.format_exc(),
                      total_wall_seconds=time.perf_counter()-started,process_peak_rss_bytes=process_peak_rss())
        atomic_json(output/'ledger.json',ledger)
        print('FAILED '+error,flush=True)
    return ledger


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('training'); parser.add_argument('development'); parser.add_argument('output')
    args=parser.parse_args()
    result=run_grid(args.training,args.development,args.output)
    print(json.dumps({'status':result['status'],'complete':sum(r['status']=='complete' for r in result['runs']),'failures':result['failures']}))
    raise SystemExit(0 if result['status']=='complete' else 1)
