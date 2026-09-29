"""Execute the single frozen additive-order probe on audited training artifacts."""
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import time
import traceback

from . import METHOD_VERSION
from .core import build_schedule, measure
from .report import summarize, markdown
from two_player.data import digest, code_commit
from two_player_v22.data import load_dataset, verify_bytes
from two_player_v22.model import Model
from two_player_v23_diagnostic.runtime import (
    ROOT, configurations, run_id, tensor_hashes, check_train, atomic_json,
    process_peak_rss, runtime_source as v23_source, DATA_FINGERPRINT)
from two_player_v23_diagnostic.report import summarize_grid

GRID_COMMIT='20f457c63bf07b2dd7f1a9eb9d5528d5d93cbc37'
AUDIT_PATH='docs/validation/V23_INDEPENDENT_AUDIT.json'
AUDIT_SHA='e5f7d6df255699ea0f5684f215546f72dd48368f70e6c4c2ad1c478199ce8ced'
SECONDS=600.
BYTES=200_000_000
RSS_BYTES=1_000_000_000


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'),
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def require(condition,message):
    if not condition: raise ValueError(message)


def source_identity():
    paths=set(v23_source())|{AUDIT_PATH,'docs/METHOD_V24_ORDER_PROBE.md'}
    paths|={p.relative_to(ROOT).as_posix() for p in Path(__file__).parent.glob('*.py')}
    return {p:hashlib.sha256((ROOT/p).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for p in sorted(paths)}


def output_bytes(path,exclude_journal=False):
    path=Path(path)
    return sum(p.stat().st_size for p in path.rglob('*') if p.is_file()
               and not (exclude_journal and p==path/'journal.json'))


def verify_prerequisite(grid,training):
    """No model construction/loading; only pinned receipts and manifest bytes."""
    audit=read(ROOT/AUDIT_PATH)
    require(sha(ROOT/AUDIT_PATH)==AUDIT_SHA,'Prerequisite independent-audit bytes changed')
    ledger=read(grid/'ledger.json')
    require(audit['status']=='verified' and audit['errors']==[] and ledger['status']=='complete'
            and ledger['failures']==[],'Incomplete/failed prerequisite diagnostic')
    require(sha(grid/'ledger.json')==audit['ledger_sha256'],'Prerequisite ledger changed')
    require(ledger['code_commit']==audit['source_verification']['commit']==GRID_COMMIT
            and ledger['source']==v23_source()
            and digest(ledger['source'])==audit['source_verification']['inventory_sha256'],
            'Prerequisite committed source identity differs')
    require(audit['counts']['cells']==18 and audit['counts']['snapshots_checked']==72
            and audit['counts']['historical_replays']==9,'Incomplete independent audit')
    manifest,_=verify_bytes(training)
    require(manifest==ledger['dataset_manifest']
            and manifest['dataset_fingerprint']==audit['training']['dataset_fingerprint']==DATA_FINGERPRINT
            and sha(training/'manifest.json')==audit['training']['manifest_sha256']
            and sha(training/'data.json')==audit['training']['payload_sha256'],
            'Standalone training does not match audited source/data')
    return ledger,manifest,audit


def run_probe(grid,training,output):
    require(os.environ.get('OPENBLAS_NUM_THREADS')==os.environ.get('OMP_NUM_THREADS')=='1',
            'Set BLAS and OMP threads to1 before Python startup')
    grid,training,output=(Path(p).resolve() for p in (grid,training,output))
    require(not output.is_relative_to(grid) and not output.is_relative_to(training),
            'Probe output must be separate from immutable input artifacts')
    output.mkdir(parents=True,exist_ok=False)
    started=time.perf_counter(); source=source_identity()
    journal={'version':METHOD_VERSION,'status':'active','code_commit':code_commit(),'source':source,
             'limits':{'seconds':SECONDS,'output_bytes':BYTES,'process_peak_rss_bytes':RSS_BYTES},
             'grid':str(grid),'training':str(training),'optimizer_updates':0,
             'development_predictions':0,'selection_predictions':0,'final_predictions':0,
             'new_search_decisions':0,'completed_cells':[],'errors':[],
             'seconds':None,'artifact_bytes_excluding_journal':None}
    atomic_json(output/'journal.json',journal)
    def guard():
        if time.perf_counter()-started>=SECONDS: raise TimeoutError('Frozen probe time limit exceeded')
        rss=process_peak_rss()
        if rss is None: raise RuntimeError('Peak RSS measurement unavailable on this runtime')
        if rss>=RSS_BYTES: raise MemoryError('Frozen probe peak-RSS limit exceeded')
        if output_bytes(output)>=BYTES: raise RuntimeError('Frozen probe output limit exceeded')
    try:
        guard(); ledger,manifest,audit=verify_prerequisite(grid,training); guard()
        journal.update(grid_ledger_sha256=audit['ledger_sha256'],dataset_fingerprint=DATA_FINGERPRINT,
                       prerequisite_audit_sha256=AUDIT_SHA)
        train=load_dataset(training,'train'); check_train(train); guard()
        train_digest=digest(train)
        schedule=build_schedule(train,guard); guard()
        schedule_digest=digest(schedule)
        atomic_json(output/'schedule.json',schedule); guard()
        journal['schedule_sha256']=sha(output/'schedule.json')
        atomic_json(output/'journal.json',journal); guard()
        require(source_identity()==source,'Probe source changed during packing')
        # This verifier loads snapshots: packing has already been saved above.
        verified=summarize_grid(grid); guard()
        require(verified['status']=='verified_diagnostic' and verified['verification_errors']==[],
                'Strict prerequisite verification failed: '+str(verified['verification_errors']))
        require(verified['ledger_sha256']==journal['grid_ledger_sha256']
                and verified['dataset_fingerprint']==DATA_FINGERPRINT,'Strict report identity mismatch')
        lookup={r['id']:r for r in ledger['runs']}
        require(len(lookup)==len(ledger['runs'])==18,'Prerequisite cell inventory mismatch')
        rows=[]
        for config in configurations():
            guard(); name=run_id(config); item=lookup[name]
            require(source_identity()==source,'Probe source changed before measurement')
            require(item['config']==asdict(config) and item['status']=='complete','Invalid final cell')
            receipt=read(grid/name/'receipt.json')
            require(sha(grid/name/'receipt.json')==item['receipt_sha256'],'Prerequisite receipt changed')
            snaps=[s for s in receipt['snapshots'] if s['epoch']==160]
            require(len(snaps)==1 and snaps[0]['checkpoint']=='checkpoint-e160.npz','Final snapshot mismatch')
            path=grid/name/'checkpoint-e160.npz'
            cp_sha=sha(path)
            require(cp_sha==snaps[0]['checkpoint_sha256'],'Final checkpoint bytes changed')
            model=Model.load(path,config,receipt['identity'])
            require((model.epoch,model.step)==(160,10560),'Final checkpoint counters differ')
            before=tensor_hashes(model); guard()
            print('MEASURE '+name,flush=True)
            result=measure(model,train,schedule,guard); guard()
            require(tensor_hashes(model)==before and (model.epoch,model.step)==(160,10560),
                    'Probe mutated model online/EMA/Adam state')
            require(digest(train)==train_digest and digest(schedule)==schedule_digest,'Probe mutated its data/schedule')
            require(sha(path)==cp_sha and sha(grid/'ledger.json')==journal['grid_ledger_sha256'],
                    'Input artifacts changed during probe')
            require(source_identity()==source,'Probe source changed during measurement')
            require(len(result['rows'])==4 and all(r['config']==asdict(config) for r in result['rows']),
                    'Incomplete/foreign measurement rows')
            result.update(config=asdict(config),checkpoint_sha256=cp_sha,checkpoint_tensor_sha256=digest(before))
            destination=output/(name+'.json'); atomic_json(destination,result); guard()
            rows.extend(result['rows'])
            journal['completed_cells'].append({'id':name,'config':asdict(config),
                'checkpoint_sha256':cp_sha,'measurement_file':destination.name,'measurement_sha256':sha(destination)})
            atomic_json(output/'journal.json',journal); guard()
        report=summarize(rows,schedule); guard()
        require(report['status']=='verified_probe' and report['verification_errors']==[],
                'Probe report verification failed: '+str(report['verification_errors']))
        report.update(method=METHOD_VERSION,code_commit=journal['code_commit'],source=source,
                      dataset_fingerprint=DATA_FINGERPRINT,grid_ledger_sha256=journal['grid_ledger_sha256'],
                      prerequisite_audit_sha256=AUDIT_SHA,schedule_file_sha256=journal['schedule_sha256'],
                      measurements=journal['completed_cells'])
        atomic_json(output/'report.json',report)
        (output/'report.md').write_text(markdown(report),encoding='utf-8'); guard()
        require(source_identity()==source,'Probe source changed at completion')
        final_manifest,_=verify_bytes(training)
        require(final_manifest==manifest and sha(grid/'ledger.json')==journal['grid_ledger_sha256'],
                'Probe input identity changed at completion')
        require(sha(output/'schedule.json')==journal['schedule_sha256'],
                'Saved schedule changed during probe')
        for cell in journal['completed_cells']:
            require(sha(output/cell['measurement_file'])==cell['measurement_sha256'],
                    'Saved measurement changed during probe')
            guard()
        guard()
        journal.update(status='complete',report_sha256=sha(output/'report.json'),
                       markdown_sha256=sha(output/'report.md'),seconds=time.perf_counter()-started,
                       process_peak_rss_bytes=process_peak_rss(),
                       artifact_bytes_excluding_journal=output_bytes(output,True))
        atomic_json(output/'journal.json',journal); guard()
    except BaseException as exc:
        # A provisional report must never survive a failed final guard as a success.
        if (output/'report.json').exists():
            provisional=read(output/'report.json')
            provisional['status']='inconclusive'
            provisional.setdefault('verification_errors',[]).append(f'Runtime failed: {type(exc).__name__}: {exc}')
            provisional['screens']=None
            atomic_json(output/'report.json',provisional)
            (output/'report.md').write_text(
                '# V2.4 order probe: inconclusive\n\nRuntime verification failed. See journal.json and retained measurements.\n',
                encoding='utf-8')
        journal.update(status='inconclusive',seconds=time.perf_counter()-started,
                       process_peak_rss_bytes=process_peak_rss(),
                       artifact_bytes_excluding_journal=output_bytes(output,True))
        journal['errors'].append(f'{type(exc).__name__}: {exc}')
        journal['traceback']=traceback.format_exc()
        atomic_json(output/'journal.json',journal)
    return journal


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('grid'); parser.add_argument('training'); parser.add_argument('output')
    args=parser.parse_args(); result=run_probe(args.grid,args.training,args.output)
    print(json.dumps({'status':result['status'],'cells':len(result['completed_cells']),'errors':result['errors']}))
    raise SystemExit(0 if result['status']=='complete' else 1)
