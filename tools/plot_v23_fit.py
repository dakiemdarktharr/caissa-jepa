"""Plot completed training-only diagnostic aggregates, without model scoring."""
import argparse
import hashlib
import json
import math
from pathlib import Path

FAMILIES=('direct','value-dynamics','raw-jepa')
GAMES=('connect4-4x5','reversi6')
EPOCHS=(0,40,80,160)
CAPACITIES=((64,32),(128,64))
SEEDS=(17,29,43)


def plot(source,output):
    source,output=Path(source),Path(output)
    report=json.loads(source.read_text(encoding='utf-8'))
    if (report.get('status')!='verified_diagnostic' or report.get('verification_errors')!=[]
            or report.get('stage')!='training-only diagnostic'
            or report['decisions']['candidate'] is not None):
        raise ValueError('Only a complete verified training diagnostic can be plotted')
    rows={(r['config']['variant'],r['config']['hidden'],r['config']['latent'],r['config']['seed']):r
          for r in report['runs']}
    if len(report['runs'])!=18 or set(rows)!={(f,h,z,s) for f in FAMILIES for h,z in CAPACITIES for s in SEEDS}:
        raise ValueError('Unexpected diagnostic grid inventory')
    paths=[output.with_suffix(ext) for ext in ('.png','.pdf')]
    if any(p.exists() for p in paths): raise FileExistsError('Plot outputs must be new')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
                         'axes.spines.right':False,'pdf.fonttype':42})
    fig,axes=plt.subplots(2,3,figsize=(11.6,7.4),sharex=True,sharey='row')
    colors=('#266b9a','#ce6d20')
    for row,game in enumerate(GAMES):
        for col,family in enumerate(FAMILIES):
            ax=axes[row,col]
            for (h,z),color in zip(CAPACITIES,colors):
                curves=[]
                for seed in SEEDS:
                    snapshots=rows[family,h,z,seed]['snapshots']
                    values=[sum(snapshots[str(e)]['components'][game][k] for k in ('1','2'))/2 for e in EPOCHS]
                    if any(not math.isfinite(v) or v<0 for v in values): raise ValueError('Invalid saved training MSE')
                    curves.append(values)
                    ax.plot(EPOCHS,values,color=color,alpha=.23,linewidth=1)
                means=[sum(c[i] for c in curves)/3 for i in range(4)]
                ax.plot(EPOCHS,means,'o-',color=color,linewidth=2,label=f'{h}/{z}')
            ax.grid(axis='y',alpha=.2)
            ax.set_ylim(bottom=0)
            ax.set_xticks(EPOCHS)
            if row==0: ax.set_title({'direct':'Direct policy/value','value-dynamics':'Value dynamics','raw-jepa':'Raw JEPA'}[family])
            if row==1: ax.set_xlabel('Training epoch')
            if col==0: ax.set_ylabel(('Connect4 4×5' if row==0 else 'Reversi 6×6')+'\nEncoded-value training MSE')
    handles,labels=axes[0,0].get_legend_handles_labels()
    fig.legend(handles,labels,title='Hidden / latent width',loc='upper center',ncol=2,bbox_to_anchor=(.5,.936),frameon=False)
    fig.suptitle('Training fit across budgets and capacities',fontsize=17,y=.987)
    fig.text(.06,.053,'509 training roots · equal-root nonterminal MSE, then equal H1/H2 · thin lines: 3 seeds; bold: mean',fontsize=9)
    fig.text(.06,.029,'Training diagnostics only. No development strength, JEPA superiority or convergence claim.',fontsize=9)
    fig.subplots_adjust(left=.09,right=.98,bottom=.135,top=.83,hspace=.23,wspace=.14)
    output.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(paths[0],dpi=180)
    fig.savefig(paths[1])
    plt.close(fig)
    return {'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'outputs':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report'); parser.add_argument('output')
    args=parser.parse_args(); print(json.dumps(plot(args.report,args.output),indent=2))
