"""Reproducible portfolio adaptation of Michele Chen's customer analytics work."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent

def analyze(seed=2026, draws=100_000):
    rng = np.random.default_rng(seed)
    # Entirely synthetic demonstration data; not the course datasets.
    names = [f'Campaign {i}' for i in range(1, 6)]
    exposures = np.repeat(1000, 5)
    clicks = np.array([105, 82, 103, 92, 60])
    means = [2.4, 3.2, 2.7, 3.5, 6.0]
    observations = [rng.lognormal(np.log(m)-0.5*0.65**2, 0.65, int(n)) for m,n in zip(means,clicks)]
    ctr = rng.beta(clicks+1, exposures-clicks+1, size=(draws,5))
    volume = np.column_stack([x.mean() + x.std(ddof=1)/np.sqrt(len(x)) * rng.standard_t(len(x)-1, size=draws) for x in observations])
    metrics = {'CTR':ctr, 'Post-click volume':volume, 'Value per impression':ctr*volume}
    rows=[]
    for metric, samples in metrics.items():
        winners=np.argmax(samples,axis=1)
        for i,name in enumerate(names):
            lo,hi=np.quantile(samples[:,i],[0.025,0.975])
            rows.append(dict(campaign=name,metric=metric,posterior_mean=samples[:,i].mean(),lower_95=lo,upper_95=hi,probability_best=np.mean(winners==i)))
    results=pd.DataFrame(rows)
    assert np.isfinite(results.select_dtypes('number')).all().all()
    assert np.allclose(results.groupby('metric').probability_best.sum(),1)
    return results, pd.DataFrame({'campaign':names,'exposures':exposures,'clicks':clicks,'observed_mean_volume':[x.mean() for x in observations]})

def main():
    results, inputs=analyze()
    out=ROOT/'results'; out.mkdir(exist_ok=True)
    results.to_csv(out/'posterior_summary.csv',index=False)
    inputs.to_csv(out/'synthetic_input_summary.csv',index=False)
    fig,axes=plt.subplots(1,3,figsize=(13,4),sharey=True)
    for ax,metric in zip(axes,['CTR','Post-click volume','Value per impression']):
        part=results[results.metric==metric]
        ax.barh(part.campaign,part.probability_best,color='#3977a8')
        ax.set_title(metric); ax.set_xlim(0,1); ax.set_xlabel('Posterior probability of being best')
    fig.suptitle('Campaign rankings depend on the metric — synthetic demonstration')
    fig.tight_layout();fig.savefig(out/'campaign_comparison.png',dpi=180);plt.close(fig)
    print(results.pivot(index='campaign',columns='metric',values='probability_best').round(3).to_string())

if __name__=='__main__': main()
