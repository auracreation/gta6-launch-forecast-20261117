"""Grouped launch experiments. Factual input is supplied by the make.fun kit."""
import argparse
import datetime as dt
import itertools
import json
import math
from pathlib import Path
import statistics
import time
import main


def summarize(rows):
    losses = [x['loss'] for x in rows]
    return {'mean_loss':statistics.mean(losses),'median_loss':statistics.median(losses),
            'worst_loss':max(losses),'variance':statistics.pvariance(losses),
            'coverage_90':statistics.mean(x['coverage_90'] for x in rows),
            'typical_miss_pct':100*math.expm1(statistics.mean(math.log1p(x['typical_miss_pct']/100) for x in rows)),
            'events':len(rows)}


def configurations():
    base = main.DEFAULT
    configs = []
    for family,dim,bw in itertools.product(('analog','normal','student','ridge'), (1,2,4,6), (0.5,1.0,2.0,100.0)):
        for ridge in ((0.3,3.0,15.0) if family=='ridge' else (3.0,)):
            configs.append(dict(base,family=family,features=dim,bandwidth=bw,ridge=ridge))
    return configs


def load(path):
    original=json.loads(Path(path).read_text())
    events=[]
    for a in original['comparables']:
        try: case, actual=main.make_case(a,[])
        except ValueError: continue
        x=main.features(case)
        events.append({'name':a['name'],'date':a['day_start'],'x':x,'y':actual,
                       'sample':(x,[main.logcount(y)-x[0] for y in actual])})
    return original,events


def evaluate(events, config, targets=None, temporal=False):
    rows=[]
    for target in events if targets is None else targets:
        train=[e['sample'] for e in events if e['name']!=target['name'] and (not temporal or e['date']<target['date'])]
        forecast=main.predict(train,target['x'],config)
        metric=main.score(target['y'],[r['q'] for r in forecast['hours']])
        rows.append(dict(metric,name=target['name'],training_events=len(train)))
    return rows


def run():
    parser=argparse.ArgumentParser()
    parser.add_argument('--case',required=True)
    parser.add_argument('--out',default='results.json')
    args=parser.parse_args()
    original,events=load(args.case)
    dev=[e for e in events if e['date']<'2026-01-01']
    holdout=[e for e in events if e['date']>='2026-01-01']
    candidates=[]
    for i,cfg in enumerate(configurations()):
        rows=evaluate(dev,cfg)
        candidates.append({'config':cfg,'summary':summarize(rows),'rows':rows})
    candidates.sort(key=lambda x:x['summary']['mean_loss'])
    selected=candidates[0]['config']
    # Nested event validation selects each outer fold's config without its target.
    nested=[]
    for held in dev:
        inner=[e for e in dev if e['name']!=held['name']]
        best=min(candidates,key=lambda c:summarize(evaluate(inner,c['config']))['mean_loss'])['config']
        nested.extend(evaluate(inner,best,[held]))
    hold=evaluate(dev,selected,holdout)
    chronological=evaluate(events,selected,holdout,temporal=True)
    all_loo=evaluate(events,selected)
    ablations=[]
    for label,cfg in [('selected',selected),('no_channels_or_history',dict(selected,features=1)),
                       ('no_history',dict(selected,features=2)),('uniform_analogs',dict(selected,bandwidth=100.0)),
                       ('normal_tails',dict(selected,distribution='normal')),('narrow_spread',dict(selected,spread=0.75)),
                       ('wide_spread',dict(selected,spread=1.25))]:
        ablations.append({'label':label,'config':cfg,'summary':summarize(evaluate(dev,cfg))})
    baseline=[]
    for e in events:
        rows=[[math.exp(e['x'][0]+z*.15*math.sqrt(h)) for z in main.Z] for h in range(1,24)]
        baseline.append(dict(main.score(e['y'],rows),name=e['name']))
    result={'selected':selected,'selection':'pre2026 event LOO; 2026 chronological holdout never used for selection',
            'candidates':candidates,'nested_dev':{'summary':summarize(nested),'rows':nested},
            'holdout':{'summary':summarize(hold),'rows':hold},
            'chronological_holdout':{'summary':summarize(chronological),'rows':chronological},
            'all_loo':{'summary':summarize(all_loo),'rows':all_loo},
            'ablations':ablations,'baseline':{'summary':summarize(baseline),'rows':baseline},
            'timestamp':dt.datetime.now(dt.timezone.utc).isoformat()}
    Path(args.out).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('selected','nested_dev','holdout','all_loo')},indent=2))

if __name__=='__main__':run()
