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
    for family,dim,bw,platform in itertools.product(('analog','ridge'), (1,2,4), (0.5,1.0,2.0), (0.03,0.2,1.0)):
        for ridge in ((0.3,3.0) if family=='ridge' else (3.0,)):
            configs.append(dict(base,family=family,features=dim,bandwidth=bw,ridge=ridge,cross_platform=platform))
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
        if config.get('flat_time'):
            train=[(x,[statistics.mean(y)]*23) for x,y in train]
        forecast=main.predict(train,target['x'],config)
        metric=main.score(target['y'],[r['q'] for r in forecast['hours']])
        rows.append(dict(metric,name=target['name'],training_events=len(train)))
    return rows


def run():
    parser=argparse.ArgumentParser()
    parser.add_argument('--case',required=True)
    parser.add_argument('--out',default='results.json')
    parser.add_argument('--domain',action='store_true')
    parser.add_argument('--replay',help='reuse the candidate configurations in an earlier result JSON')
    args=parser.parse_args()
    original,events=load(args.case)
    dev=[e for e in events if e['date']<'2026-01-01']
    holdout=[e for e in events if e['date']>='2026-01-01']
    if args.domain:
        domain_run(dev, holdout, events, args.out)
        return
    candidates=[]
    configs = [c['config'] for c in json.loads(Path(args.replay).read_text())['candidates']] if args.replay else configurations()
    for i,cfg in enumerate(configs):
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
                       ('no_history',dict(selected,features=2)),('no_platform_weight',dict(selected,cross_platform=1.0)),('broad_kernel',dict(selected,bandwidth=100.0)),
                       ('normal_tails',dict(selected,distribution='normal')),('narrow_spread',dict(selected,spread=0.75)),
                       ('wide_spread',dict(selected,spread=1.25))]:
        ablations.append({'label':label,'config':cfg,'summary':summarize(evaluate(dev,cfg))})
    baseline=[]
    for e in events:
        rows=[[math.floor(math.exp(e['x'][0]+z*.15*math.sqrt(h))*100+.5)/100 for z in (-1.645,-0.674,0,.674,1.645)] for h in range(1,24)]
        baseline.append(dict(main.score(e['y'],rows),name=e['name']))
    result={'selected':selected,'selection':'pre2026 event LOO; 2026 chronological holdout never used for selection',
            'candidates':candidates,'nested_dev':{'summary':summarize(nested),'rows':nested},
            'holdout':{'summary':summarize(hold),'rows':hold},
            'chronological_holdout':{'summary':summarize(chronological),'rows':chronological},
            'all_loo':{'summary':summarize(all_loo),'rows':all_loo},
            'ablations':ablations,'baseline':{'summary':summarize(baseline),'rows':baseline},
            'holdout_warning':'2026 events previously inspected in initial search; this is a diagnostic reuse, not an untouched final holdout',
            'timestamp':dt.datetime.now(dt.timezone.utc).isoformat()}
    Path(args.out).write_text(json.dumps(result,separators=(',',':'))+'\n')
    print(json.dumps({k:result[k] for k in ('selected','nested_dev','holdout','all_loo')},indent=2))

def domain_run(dev, holdout, events, output):
    console=[e for e in dev if e['x'][6]]
    configs=configurations()
    configs += [dict(main.DEFAULT,family='qr',features=d,ridge=r,bandwidth=1.,cross_platform=.2)
                for d,r in itertools.product((1,2),(.3,3.))]
    candidates=[]
    for cfg in configs:
        rows=evaluate(dev,cfg,console)
        candidates.append({'config':cfg,'summary':summarize(rows),'rows':rows})
    candidates.sort(key=lambda c:c['summary']['mean_loss'])
    selected=candidates[0]['config']
    nested=[]
    for held in console:
        inner=[e for e in dev if e['name']!=held['name']]
        validation=[e for e in console if e['name']!=held['name']]
        best=min(configs,key=lambda c:summarize(evaluate(inner,c,validation))['mean_loss'])
        nested.extend(evaluate(inner,best,[held]))
    ablations=[]
    for label,cfg in [('selected',selected),('no_platform_weight',dict(selected,cross_platform=1.)),
                      ('no_history_or_channels',dict(selected,features=1)),('flat_time',dict(selected,flat_time=True)),
                      ('normal_tails',dict(selected,distribution='normal')),('wider_tails',dict(selected,spread=1.25))]:
        ablations.append({'label':label,'config':cfg,'summary':summarize(evaluate(dev,cfg,console))})
    result={'selected':selected,'target_domain':'console-only launches, metadata known before release',
            'candidates':candidates,'nested_domain':{'summary':summarize(nested),'rows':nested},
            'all_loo':{'summary':summarize(evaluate(events,selected))},
            'diagnostic_2026_console':{'summary':summarize(evaluate(dev,selected,[e for e in holdout if e['x'][6]]))},
            'ablations':ablations,'warning':'Only seven development console launches. 2026 holdout previously inspected; no longer untouched.',
            'timestamp':dt.datetime.now(dt.timezone.utc).isoformat()}
    Path(output).write_text(json.dumps(result,separators=(',',':'))+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='candidates'},indent=2))


if __name__=='__main__':run()
