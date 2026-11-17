"""Event-level validation of short-history and prelaunch phase effects."""
import argparse
from datetime import date, timedelta
import itertools
import json
from pathlib import Path

import main
import research
from research_history import BASELINE


PRIOR = dict(BASELINE, indices=[0, 4], ridge=15.0, bandwidth=1.0)
SLOPE, MATURITY = main.DEFAULT['members']
ENSEMBLE = {'family': 'ensemble', 'members': [SLOPE, MATURITY]}


def summer_time(day):
    march = date(day.year, 3, 8)
    november = date(day.year, 11, 1)
    return (march + timedelta(days=(6 - march.weekday()) % 7)
            <= day < november + timedelta(days=(6 - november.weekday()) % 7))


def temporal_trials(case_path, events):
    """Shift the reference's complete past and future together around a new anchor."""
    analogs = json.loads(Path(case_path).read_text())['comparables']
    variants = {}
    for analog in analogs:
        if analog['name'] not in {e['name'] for e in events}:
            continue
        start = main.dt.datetime.fromisoformat(analog['day_start'].replace('Z', '+00:00'))
        for shift in (-1, 1):
            shifted = dict(analog, day_start=(start + timedelta(hours=shift)).isoformat())
            try:
                case, actual = main.make_case(shifted, [])
            except ValueError:
                continue
            x = main.features(case)
            variants[(analog['name'], shift)] = (x, [main.logcount(y) - x[0] for y in actual])
    flags = {e['name']: summer_time(date.fromisoformat(e['date'][:10])) for e in events}
    return flags, variants


def evaluate(events, targets, config, *, chronological=False, franchises=False, time_alignment=None):
    def group(name):
        return 'Ghost' if name.startswith('Ghost of ') else name

    rows = []
    for target in targets:
        train = [e for e in events if e['name'] != target['name']
                 and (not chronological or e['date'] < target['date'])
                 and (not franchises or group(e['name']) != group(target['name']))]
        if chronological and (len(train) < 6 or sum(e['x'][6] == target['x'][6] for e in train) < 2):
            continue
        if time_alignment:
            flags, shifts = time_alignment
            samples = [shifts.get((e['name'], int(flags[target['name']]) - int(flags[e['name']])), e['sample'])
                       for e in train]
        else:
            samples = [e['sample'] for e in train]
        forecast = main.predict(samples, target['x'], config)
        metrics = main.score(target['y'], [row['q'] for row in forecast['hours']])
        rows.append(dict(metrics, name=target['name'], training_events=len(train)))
    return {'summary': research.summarize(rows), 'rows': rows}


def run(case_path):
    _, events = research.load(case_path)
    console = [event for event in events if event['x'][6]]
    configs = {'original': BASELINE, 'prelaunch_level': PRIOR, 'recent_slope': SLOPE,
               'prelaunch_phase': MATURITY, 'equal_ensemble': ENSEMBLE,
               'no_platform_weight': {'family': 'ensemble', 'members': [dict(m, cross_platform=1.) for m in ENSEMBLE['members']]},
               'no_local_kernel': {'family': 'ensemble', 'members': [dict(m, bandwidth=100.) for m in ENSEMBLE['members']]},
               'normal_tails': {'family': 'ensemble', 'members': [dict(m, distribution='normal') for m in ENSEMBLE['members']]}}
    result = {
        'configs': configs,
        'console': {key: evaluate(events, console, cfg) for key, cfg in configs.items()},
        'chronological': {key: evaluate(events, console, cfg, chronological=True) for key, cfg in configs.items()},
        'all_launches': {key: evaluate(events, events, cfg) for key, cfg in configs.items()},
        'console_franchise_groups': evaluate(events, console, ENSEMBLE, franchises=True),
        'dst_alignment': evaluate(events, console, ENSEMBLE, time_alignment=temporal_trials(case_path, events)),
    }
    nested = []
    for held in console:
        inner = [event for event in events if event['name'] != held['name']]
        targets = [event for event in console if event['name'] != held['name']]
        selected = []
        for last in (7, 8):
            trials = [dict(main.PHASE_BASE, indices=indices + [last], ridge=ridge, bandwidth=bandwidth)
                      for indices, ridge, bandwidth in itertools.product(([0], [0,4]), (3.,15.), (.65,1.))]
            selected.append(min(trials, key=lambda cfg: evaluate(inner, targets, cfg)['summary']['mean_loss']))
        row = evaluate(inner, [held], {'family': 'ensemble', 'members': selected})['rows'][0]
        nested.append(dict(row, members=selected))
    result['nested'] = {'summary': research.summarize(nested), 'rows': nested}
    result['scope'] = 'Eight console events in a reused development library. Chronological folds test six events with at least two earlier console references. One franchise group contains both Ghost releases.'
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--case', required=True)
    parser.add_argument('--out', default='ensemble-results.json')
    args = parser.parse_args()
    report = run(args.case)
    Path(args.out).write_text(json.dumps(report, separators=(',', ':')) + '\n')
    for name in ('console', 'chronological', 'all_launches'):
        print(name, {model: round(metrics['summary']['mean_loss'], 6) for model, metrics in report[name].items()})
    print('nested', report['nested']['summary'])
    print('DST alignment', report['dst_alignment']['summary'])
