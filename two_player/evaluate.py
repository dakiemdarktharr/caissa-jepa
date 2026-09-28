"""Exploratory local-position diagnostics, never a confirmatory evaluator."""
import time
import numpy as np
from .games import GAMES, ACTION_SIZE, exact_value
from .model import state_from, batch_arrays
from .data import digest


def plan(game,state,model=None,track='exact',node_limit=1024,time_limit=1.):
    """Complete depth-two max-min; any incomplete decision is retained as censored."""
    if track not in ('exact','hybrid') or node_limit<1 or time_limit<=0:
        raise ValueError('Invalid search budget/track')
    started=time.perf_counter(); deadline=started+time_limit
    stats={'nodes':0,'transitions':0,'encoder_calls':0,'predictor_calls':0,'value_calls':0}
    def check():
        if time.perf_counter()>=deadline:
            raise TimeoutError('Search budget exhausted')
    def step(s,a):
        check()
        if stats['nodes']>=node_limit: raise TimeoutError('Node budget exhausted')
        stats['nodes']+=1; stats['transitions']+=1
        return game.transition(s,a)
    root_z=None
    legal=tuple(sorted(game.legal_actions(state)))
    if not legal:
        raise ValueError('Planner requires a nonterminal state')
    scores={}; action=legal[0]; status='complete'
    try:
        if model is not None and track=='hybrid' and model.horizons:
            check(); root_z=model.encode(game.features(state)[None,:]); stats['encoder_calls']+=1
        for a in legal:
            child=step(state,a); terminal=game.terminal(child)
            if terminal is not None:
                scores[a]=state.player*terminal
                continue
            replies=[]
            for b in sorted(game.legal_actions(child)):
                leaf=step(child,b); terminal=game.terminal(leaf)
                if terminal is not None:
                    value=state.player*terminal
                elif model is None:
                    value=0.
                else:
                    check()
                    if root_z is None:
                        z=model.encode(game.features(leaf)[None,:]); stats['encoder_calls']+=1
                    elif model.horizons==(1,):
                        # Recurrent H1 is a declared inference control, not an H2-trained predictor.
                        acts=np.zeros((1,2,ACTION_SIZE)); acts[0,0,a]=1
                        z=model.predict(root_z,acts,1); stats['predictor_calls']+=1
                        acts[:]=0; acts[0,0,b]=1
                        z=model.predict(z,acts,1); stats['predictor_calls']+=1
                    else:
                        acts=np.zeros((1,2,ACTION_SIZE)); acts[0,0,a]=1; acts[0,1,b]=1
                        z=model.predict(root_z,acts,2); stats['predictor_calls']+=1
                    value=float(model.value(z)[0,0]); stats['value_calls']+=1
                    if not np.isfinite(value): raise FloatingPointError('Nonfinite leaf value')
                replies.append(value)
            scores[a]=min(replies)
        if time.perf_counter()>=deadline: raise TimeoutError('Late search return')
        action=max(legal,key=lambda a:(scores[a],-a))
    except TimeoutError:
        status='censored_budget'
        # Full root alternatives were not compared: never score this fallback as successful.
    return {'action':action,'status':status,'seconds':time.perf_counter()-started,**stats}


def schedule(records):
    output=[]
    for name in GAMES:
        seen=set(); choices=[]
        for r in sorted((r for r in records if r['game']==name),key=digest):
            s=state_from(r['state']); game=GAMES[name]
            key=game.canonical_key(s)
            if s.board.count(0)<=4 and key not in seen:
                seen.add(key); choices.append(r)
        output+=choices[:24]
    return output


def representation(model,records):
    batch=batch_arrays(records); z=model.encode(batch['x'])
    logits=z@model.params['pw']+model.params['pb']
    logits=np.where(batch['legal'],logits,-np.inf)
    logits-=np.max(logits,axis=1,keepdims=True)
    probs=np.exp(logits); probs/=probs.sum(axis=1,keepdims=True)
    indices=np.arange(len(records)); labels=batch['policy']
    nll=-np.log(probs[indices,labels]); mse=(model.value(z)[:,0]-batch['value'][:,0])**2
    # Tied logits get average rank to avoid arbitrary action-index favoritism.
    ranks=1+(logits>logits[indices,labels,None]).sum(axis=1)+.5*((logits==logits[indices,labels,None]).sum(axis=1)-1)
    singular=np.linalg.svd(z-z.mean(axis=0),compute_uv=False)
    spectrum=singular**2; total=spectrum.sum()
    q=spectrum[spectrum>0]/total if total else np.array([])
    rank=float(np.exp(-np.sum(q*np.log(q)))) if total else 0.
    covariance=np.cov(z,rowvar=False,bias=True)
    offdiag=covariance-np.diag(np.diag(covariance))
    metrics={'count':len(records),'trajectories':len({r['trajectory'] for r in records}),
             'policy_nll':float(nll.mean()),'policy_mrr':float(np.mean(1/ranks)),
             'policy_top1':float(np.mean(np.argmax(probs,axis=1)==labels)),
             'value_mse':float(mse.mean()),'effective_rank':rank,
             'median_latent_std':float(np.median(z.std(axis=0))),
             'latent_norm':float(np.linalg.norm(z,axis=1).mean()),
             'off_diagonal_covariance_rms':float(np.sqrt(np.mean(offdiag**2))),
             'collapse_alert':bool(rank<2 or np.median(z.std(axis=0))<1e-3)}
    for h in (1,2):
        mask=batch['masks'][h]; count=int(mask.sum())
        metrics[f'h{h}_count']=count
        metrics[f'h{h}_latent_mse']=None
        if h in model.horizons and count:
            predicted=model.predict(z[mask],batch['actions'][mask],h)
            target=model.encode(batch['targets'][h][mask],target=True)
            metrics[f'h{h}_latent_mse']=float(np.mean((predicted-target)**2))
    # Cluster bootstrap is descriptive, conditional on this development dataset.
    groups={tid:np.array([i for i,r in enumerate(records) if r['trajectory']==tid])
            for tid in sorted({r['trajectory'] for r in records})}
    keys=list(groups); rng=np.random.default_rng(901)
    boot=[]
    for _ in range(500):
        ix=np.concatenate([groups[keys[i]] for i in rng.integers(len(keys),size=len(keys))])
        boot.append([nll[ix].mean(),mse[ix].mean()])
    bounds=np.quantile(boot,[.025,.975],axis=0)
    metrics['cluster_bootstrap_95']={'policy_nll':bounds[:,0].tolist(),'value_mse':bounds[:,1].tolist(),'replicates':500,'seed':901}
    return metrics


def evaluate(model,records,fixed_schedule):
    metrics={name:representation(model,[r for r in records if r['game']==name])
             for name in GAMES if any(r['game']==name for r in records)}
    if any(m['collapse_alert'] for m in metrics.values()):
        return {'representation':metrics,'decisions':[], 'planning_status':'blocked_collapse',
                'schedule_sha256':digest(fixed_schedule),'skipped_positions':len(fixed_schedule)}
    decisions=[]
    for record in fixed_schedule:
        game=GAMES[record['game']]; state=state_from(record['state']); cache={}
        values={a:-exact_value(game,game.transition(state,a),cache) for a in game.legal_actions(state)}
        for track in ('exact','hybrid'):
            result=plan(game,state,model,track)
            result.update(game=game.name,trajectory=record['trajectory'],position=digest(record),track=track,
                          oracle_action_gap=max(values.values())-min(values.values()),
                          regret=max(values.values())-values[result['action']] if result['status']=='complete' else None)
            decisions.append(result)
    return {'representation':metrics,'decisions':decisions,'planning_status':'evaluated',
            'skipped_positions':0,'schedule_sha256':digest(fixed_schedule)}
