"""Small NumPy JEPA and matched-input controls; no paper-faithfulness claim."""
from dataclasses import dataclass, asdict
import hashlib
import json
import os
from pathlib import Path
import tempfile
import numpy as np
from .games import GAMES, State, FEATURE_SIZE, ACTION_SIZE
from . import METHOD_VERSION
from .data import digest

VARIANTS=('full','h1','no-response','no-var','direct','decoded','value-dynamics')


@dataclass(frozen=True)
class Config:
    variant: str = 'full'
    seed: int = 17
    latent: int = 32
    learning_rate: float = .001
    ema: float = .99
    batch_size: int = 64

    def __post_init__(self):
        if self.variant not in VARIANTS or self.latent<2 or self.batch_size<2:
            raise ValueError('Invalid model configuration')
        if not np.isfinite(self.learning_rate) or self.learning_rate<=0 or not 0<=self.ema<1:
            raise ValueError('Invalid optimizer/EMA configuration')


def state_from(data):
    return State(tuple(data['board']),data['player'])


def batch_arrays(records):
    if not records:
        raise ValueError('Empty batch')
    features=[]; legal=[]; targets={1:[],2:[]}; masks=[]
    for record in records:
        game=GAMES[record['game']]
        state=state_from(record['state'])
        actions=game.legal_actions(state)
        if record['action'] not in actions:
            raise ValueError('Illegal policy target')
        if not np.isfinite(record['value']) or record['value'] not in (-1,0,1):
            raise ValueError('Invalid outcome target')
        features.append(game.features(state))
        legal.append([a in actions for a in range(ACTION_SIZE)])
        next_state=state_from(record['next'])
        if game.transition(state,record['action'])!=next_state:
            raise ValueError('Incorrect H1 target')
        targets[1].append(game.features(next_state))
        future=record['future2']
        if future is not None:
            future_state=state_from(future)
            if game.transition(next_state,record['reply'])!=future_state:
                raise ValueError('Incorrect H2 target')
            targets[2].append(game.features(future_state))
        else:
            if record['reply'] is not None:
                raise ValueError('Reply without H2 target')
            targets[2].append(np.zeros(FEATURE_SIZE))
        masks.append(future is not None)
    actions=np.zeros((len(records),2,ACTION_SIZE))
    for i,r in enumerate(records):
        actions[i,0,r['action']]=1
        if r['reply'] is not None: actions[i,1,r['reply']]=1
    return {'x':np.array(features),'legal':np.array(legal,dtype=bool),'actions':actions,
            'policy':np.array([r['action'] for r in records]),
            'value':np.array([r['value'] for r in records],dtype=float)[:,None],
            'targets':{h:np.array(x) for h,x in targets.items()},
            'masks':{1:np.ones(len(records),bool),2:np.array(masks,dtype=bool)}}


class Model:
    def __init__(self,config=Config()):
        self.config=config
        self.step=0
        self.epoch=0
        rng=np.random.default_rng(config.seed)
        d=config.latent
        def weight(n,m): return rng.normal(0,np.sqrt(1/n),(n,m))
        self.params={'ew':weight(FEATURE_SIZE,d),'eb':np.zeros(d),'pw':weight(d,ACTION_SIZE),
                     'pb':np.zeros(ACTION_SIZE),'vw':weight(d,1),'vb':np.zeros(1),
                     'gw':weight(d+2*ACTION_SIZE+2,d),'gb':np.zeros(d),
                     'dw':weight(d,FEATURE_SIZE),'db':np.zeros(FEATURE_SIZE)}
        self.target={k:self.params[k].copy() for k in ('ew','eb')}
        self.m={k:np.zeros_like(v) for k,v in self.params.items()}
        self.v={k:np.zeros_like(v) for k,v in self.params.items()}

    @property
    def horizons(self):
        return () if self.config.variant=='direct' else (1,) if self.config.variant=='h1' else (1,2)

    def encode(self,x,target=False):
        p=self.target if target else self.params
        return np.tanh(x@p['ew']+p['eb'])

    def value(self,z):
        return np.tanh(z@self.params['vw']+self.params['vb'])

    def predictor_input(self,z,actions,h):
        actions=actions.copy()
        if h==1 or self.config.variant=='no-response': actions[:,1,:]=0
        indicator=np.zeros((len(z),2)); indicator[:,h-1]=1
        return np.concatenate((z,actions.reshape(len(z),-1),indicator),axis=1)

    def predict(self,z,actions,h):
        return np.tanh(self.predictor_input(z,actions,h)@self.params['gw']+self.params['gb'])

    def loss_grad(self,batch):
        p=self.params
        x=batch['x']; n=len(x); d=self.config.latent
        z=self.encode(x)
        grad={k:np.zeros_like(v) for k,v in p.items()}
        dz=np.zeros_like(z)
        logits=z@p['pw']+p['pb']
        logits=np.where(batch['legal'],logits,-np.inf)
        shifted=logits-np.max(logits,axis=1,keepdims=True)
        lognorm=np.log(np.exp(shifted).sum(axis=1,keepdims=True))
        probs=np.exp(shifted-lognorm)
        policy=float(np.mean(lognorm[:,0]-shifted[np.arange(n),batch['policy']]))
        dl=probs.copy(); dl[np.arange(n),batch['policy']]-=1; dl/=n
        grad['pw']+=z.T@dl; grad['pb']+=dl.sum(axis=0); dz+=dl@p['pw'].T
        value=self.value(z); delta=value-batch['value']
        value_loss=float(np.mean(delta**2))
        dv=2*delta/n*(1-value**2)
        grad['vw']+=z.T@dv; grad['vb']+=dv.sum(axis=0); dz+=dv@p['vw'].T
        total=policy+value_loss
        metrics={'policy_nll':policy,'value_mse':value_loss,'samples':n}
        for h in self.horizons:
            mask=batch['masks'][h]
            count=int(mask.sum()); metrics[f'h{h}_count']=count
            if not count:
                metrics[f'h{h}_loss']=0.
                continue
            inputs=self.predictor_input(z[mask],batch['actions'][mask],h)
            predicted=np.tanh(inputs@p['gw']+p['gb'])
            dp=np.zeros_like(predicted)
            target_x=batch['targets'][h][mask]
            if self.config.variant=='decoded':
                decoded=predicted@p['dw']+p['db']
                delta=decoded-target_x
                loss=float(np.mean(delta**2))
                dd=2*delta/(count*FEATURE_SIZE)
                grad['dw']+=predicted.T@dd; grad['db']+=dd.sum(axis=0)
                dp+=dd@p['dw'].T
            elif self.config.variant=='value-dynamics':
                loss=0.
            else:
                target=self.encode(target_x,target=True)
                delta=predicted-target
                loss=float(np.mean(delta**2))
                dp+=2*delta/(count*d)
            metrics[f'h{h}_loss']=loss; total+=loss
            predicted_v=self.value(predicted)
            delta=predicted_v-batch['value'][mask]*((-1)**h)
            auxiliary=.25*float(np.mean(delta**2))
            total+=auxiliary; metrics[f'h{h}_value_loss']=auxiliary
            dv=.5*delta/count*(1-predicted_v**2)
            grad['vw']+=predicted.T@dv; grad['vb']+=dv.sum(axis=0)
            dp+=dv@p['vw'].T
            dg=dp*(1-predicted**2)
            grad['gw']+=inputs.T@dg; grad['gb']+=dg.sum(axis=0)
            dz[mask]+=dg@p['gw'][:d].T
        centered=z-z.mean(axis=0)
        std=np.sqrt(np.mean(centered**2,axis=0)+1e-4)
        shortfall=np.maximum(0,.1-std)
        coefficient=0. if self.config.variant in ('direct','no-var') else .1
        variance=coefficient*float(np.mean(shortfall**2))
        total+=variance
        dz+=-2*coefficient*shortfall[None,:]*centered/(d*n*std[None,:])
        de=dz*(1-z**2)
        grad['ew']+=x.T@de; grad['eb']+=de.sum(axis=0)
        metrics.update(loss=total,variance_loss=variance,latent_std=float(np.std(z,axis=0).mean()))
        if not np.isfinite(total) or any(not np.all(np.isfinite(g)) for g in grad.values()):
            raise FloatingPointError('Nonfinite loss or gradient')
        return metrics,grad

    def update(self,batch):
        metrics,grad=self.loss_grad(batch)
        norm=np.sqrt(sum(np.sum(g*g) for g in grad.values()))
        scale=min(1.,5/max(norm,1e-12))
        self.step+=1
        for key in self.params:
            g=grad[key]*scale
            self.m[key]=.9*self.m[key]+.1*g
            self.v[key]=.999*self.v[key]+.001*g*g
            self.params[key]-=self.config.learning_rate*(self.m[key]/(1-.9**self.step))/(np.sqrt(self.v[key]/(1-.999**self.step))+1e-8)
        for key in self.target:
            self.target[key]=self.config.ema*self.target[key]+(1-self.config.ema)*self.params[key]
        metrics['gradient_norm']=float(norm)
        return metrics

    def parameter_counts(self):
        keys=['ew','eb','pw','pb','vw','vb']
        if self.horizons: keys+=['gw','gb']
        if self.config.variant=='decoded': keys+=['dw','db']
        return {'allocated':sum(a.size for a in self.params.values()),
                'active':sum(self.params[k].size for k in keys)}

    def save(self,path,identity):
        path=Path(path)
        arrays={prefix+k:v for prefix,group in (('p_',self.params),('t_',self.target),('m_',self.m),('v_',self.v)) for k,v in group.items()}
        hashes={k:hashlib.sha256(v.tobytes()).hexdigest() for k,v in arrays.items()}
        metadata={'method':METHOD_VERSION,'config':asdict(self.config),'identity':identity,
                  'step':self.step,'epoch':self.epoch,'array_hashes':hashes}
        arrays['metadata']=np.array(json.dumps(metadata,sort_keys=True,allow_nan=False))
        path.parent.mkdir(parents=True,exist_ok=True)
        fd,temporary=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent)
        try:
            with os.fdopen(fd,'wb') as file:
                np.savez_compressed(file,**arrays); file.flush(); os.fsync(file.fileno())
            os.replace(temporary,path)
        finally:
            if os.path.exists(temporary): os.unlink(temporary)

    @classmethod
    def load(cls,path,config,identity):
        with np.load(path,allow_pickle=False) as file:
            metadata=json.loads(str(file['metadata']))
            if metadata['method']!=METHOD_VERSION or metadata['config']!=asdict(config) or metadata['identity']!=identity:
                raise ValueError('Checkpoint code/config/data/objective identity mismatch')
            model=cls(config)
            expected={prefix+k for prefix,group in (('p_',model.params),('t_',model.target),('m_',model.m),('v_',model.v)) for k in group}
            if set(file.files)!=expected|{'metadata'} or set(metadata['array_hashes'])!=expected:
                raise ValueError('Checkpoint tensor inventory mismatch')
            for prefix,group in (('p_',model.params),('t_',model.target),('m_',model.m),('v_',model.v)):
                for key in group:
                    array=file[prefix+key]
                    if array.shape!=group[key].shape or array.dtype!=np.float64 or not np.all(np.isfinite(array)):
                        raise ValueError('Invalid checkpoint tensor')
                    if hashlib.sha256(array.tobytes()).hexdigest()!=metadata['array_hashes'][prefix+key]:
                        raise ValueError('Checkpoint tensor checksum mismatch')
                    group[key]=array.copy()
            if type(metadata['step']) is not int or type(metadata['epoch']) is not int or min(metadata['step'],metadata['epoch'])<0:
                raise ValueError('Invalid checkpoint counters')
            model.step=metadata['step']; model.epoch=metadata['epoch']
            return model
