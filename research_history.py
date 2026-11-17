"""Expanded console validation, using prelaunch activity instead of channel counts."""
import argparse
import itertools
import json
from pathlib import Path
import main
import research

BASELINE={'family':'ridge','features':1,'ridge':.3,'bandwidth':.5,'distribution':'empirical','spread':1.,'cross_platform':.2}


def run(case_path, output):
    _,events=research.load(case_path)
    domain=[e for e in events if e['x'][6]]
    configs=[BASELINE]+[dict(BASELINE,indices=idx,ridge=reg,bandwidth=bw) for idx,reg,bw in itertools.product(([0,2],[0,4],[0,2,4],[0,2,3,4,5]),(.3,3.,15.),(.5,1.,2.))]
    results=[]
    for cfg in configs:
        rows=research.evaluate(events,cfg,domain)
        results.append({'config':cfg,'summary':research.summarize(rows),'rows':rows})
    results.sort(key=lambda c:c['summary']['mean_loss'])
    nested=[]
    for held in domain:
        train=[e for e in events if e['name']!=held['name']]
        inner=[e for e in domain if e['name']!=held['name']]
        best=min(configs,key=lambda c:research.summarize(research.evaluate(train,c,inner))['mean_loss'])
        row=research.evaluate(train,best,[held])[0];row['selected']=best;nested.append(row)
    report={'configs':results,'nested':{'summary':research.summarize(nested),'rows':nested},
            'baseline':research.summarize(research.evaluate(events,BASELINE,domain)),
            'warning':'2026 outcomes previously inspected. Expanded developmental search; nested event estimates provided.'}
    Path(output).write_text(json.dumps(report,separators=(',',':'))+'\n')
    print(json.dumps({'selected':results[0],'nested':report['nested']['summary'],'baseline':report['baseline']},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--case',required=True);p.add_argument('--out',default='history-results.json');a=p.parse_args();run(a.case,a.out)
