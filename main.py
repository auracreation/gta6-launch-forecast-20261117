"""Deterministic launch trajectories, using only Python's standard library."""
import datetime as dt
import json
import math
import os
from pathlib import Path

LEVELS = (0.05, 0.25, 0.5, 0.75, 0.95)
Z = (-1.644853626951, -0.674489750196, 0.0, 0.674489750196, 1.644853626951)
DEFAULT = {'family': 'ridge', 'features': 1, 'ridge': 0.3, 'bandwidth': 0.5, 'distribution': 'empirical', 'spread': 1.0, 'cross_platform': 0.2}


def logcount(x):
    value = float(x)
    if not math.isfinite(value):
        raise ValueError('count must be finite')
    return math.log(max(1.0, value))


def instant(s):
    return dt.datetime.fromisoformat(s.replace('Z', '+00:00')).timestamp()


def score(actual, predicted):
    if not actual or len(actual) != len(predicted):
        raise ValueError('score requires matching nonempty hours')
    loss, miss, covered = 0.0, 0.0, 0
    for y, row in zip(actual, predicted):
        ly = logcount(y)
        for tau, q in zip(LEVELS, row):
            d = ly - math.log(q)
            loss += 2 * max(tau * d, (tau - 1) * d)
        miss += abs(ly - math.log(row[2]))
        covered += row[0] <= max(1, y) <= row[4]
    n = len(actual)
    return {'loss': loss / (5 * n), 'typical_miss_pct': 100 * math.expm1(miss / n), 'coverage_90': covered / n}


def features(case):
    first = next(x for x in case['known'] if x['hour'] == 1)
    p = logcount(first['viewers'])
    start, cutoff = instant(case['day_start']), instant(case['checkpoint'])
    rows = case.get('history_hourly') or case.get('history') or []
    history = [(instant(x.get('from', x.get('at'))), x) for x in rows]
    history = [(t, x) for t, x in history if t < cutoff and math.isfinite(float(x['viewers']))]
    channels = first.get('channels')
    # A missing channel count contributes a neutral ratio, not an invented observation.
    ratio = p - logcount(channels) if channels is not None else 4.0
    def previous(lo, hi):
        values = [logcount(x['viewers']) for t, x in history if start + lo * 3600 <= t < start + hi * 3600]
        return sum(values) / len(values) - p if values else 0.0
    platforms = case['game'].get('platforms')
    if platforms is None:
        prefix = case.get('notes','').split('real unlock:')[0].lower()
        console = 'pc' not in prefix or 'console only' in prefix
    else:
        console = 'pc' not in platforms.lower()
    return [p, ratio, previous(-3, 0), previous(-12, -6), previous(-48, -24), previous(-168, -48), float(console)]


def make_case(analog, comparables):
    start = instant(analog['day_start'])
    rows = sorted(analog['hourly'], key=lambda r: r['from'])
    day = {int((instant(x['from']) - start) / 3600): x for x in rows if 0 <= instant(x['from']) - start < 86400}
    if set(day) != set(range(24)):
        raise ValueError('launch lacks a complete UTC day')
    checkpoint = dt.datetime.fromtimestamp(start + 3600, dt.timezone.utc).isoformat()
    case = {'schema': 'makefun/twitch-ccu-case/v1', 'id': 'validation', 'game': {'name': analog['name'], 'platforms': analog.get('platforms','unknown PC')},
            'day_start': analog['day_start'], 'checkpoint': checkpoint, 'levels': list(LEVELS),
            'known': [dict(day[0], hour=1)], 'forecast': [{'hour': h} for h in range(2,25)],
            'history_hourly': [x for x in rows if instant(x['from']) < start + 3600],
            'comparables': [x for x in comparables if x['name'] != analog['name']]}
    return case, [day[h]['viewers'] for h in range(1,24)]


def training(case):
    samples = []
    target = case['game']['name'].casefold()
    for analog in case.get('comparables', []):
        if analog['name'].casefold() == target or 'category before release' in analog['name'].casefold():
            continue
        # The kit deliberately supplies later analogs to its historical practice cases.
        if instant(analog['day_start']) + 86400 > instant('2026-11-19T01:00:00Z'):
            continue
        try:
            pseudo, actual = make_case(analog, [])
        except ValueError:
            continue
        x = features(pseudo)
        samples.append((x, [logcount(y) - x[0] for y in actual]))
    return samples


def quantile(values, weights, q):
    pairs = sorted(zip(values, weights))
    total = sum(weights)
    knots, cumulative = [], 0.0
    for value, weight in pairs:
        knots.append(((cumulative + weight / 2) / total, value))
        cumulative += weight
    if q <= knots[0][0]:
        return knots[0][1]
    for (a, x), (b, y) in zip(knots, knots[1:]):
        if q <= b:
            return x + (y - x) * (q - a) / (b - a)
    return knots[-1][1]


def solve(matrix, rhs):
    a = [list(row) + list(b) for row, b in zip(matrix, rhs)]
    n = len(a)
    for j in range(n):
        pivot = max(range(j,n), key=lambda i: abs(a[i][j]))
        a[j], a[pivot] = a[pivot], a[j]
        if abs(a[j][j]) < 1e-12:
            raise ValueError('singular fit')
        z = a[j][j]
        a[j] = [v / z for v in a[j]]
        for i in range(n):
            if i != j:
                z = a[i][j]
                a[i] = [v - z * w for v, w in zip(a[i], a[j])]
    return [row[n:] for row in a]


def predict_logs(samples, target, cfg):
    n, dim = len(samples), cfg['features']
    xs = [x[:dim] for x, _ in samples]
    mean = [sum(x[j] for x in xs) / n for j in range(dim)]
    sd = [max(0.5, math.sqrt(sum((x[j]-mean[j])**2 for x in xs)/n)) for j in range(dim)]
    xs = [[(x[j] - mean[j]) / sd[j] for j in range(dim)] for x in xs]
    xt = [(target[j]-mean[j])/sd[j] for j in range(dim)]
    bw = cfg['bandwidth']
    weights = [math.exp(-min(100, sum((a-b)**2 for a,b in zip(x,xt)) / (2*bw*bw))) + 1e-8 for x in xs]
    weights = [w * (1.0 if x[6] == target[6] else cfg.get('cross_platform',1.0)) for w,(x,_) in zip(weights,samples)]
    total = sum(weights)
    weights = [w*n/total for w in weights]
    if cfg['family'] in ('analog', 'normal', 'student'):
        return [[y[h] for _, y in samples] for h in range(23)], weights
    design = [[1.0]+x for x in xs]
    a = [[sum(w*x[i]*x[j] for w,x in zip(weights,design)) + (cfg['ridge'] if i==j and i>0 else 0) for j in range(dim+1)] for i in range(dim+1)]
    b = [[sum(w*x[i]*y[h] for w,x,(_,y) in zip(weights,design,samples)) for h in range(23)] for i in range(dim+1)]
    beta = solve(a,b)
    centers = [sum(v*coef[h] for v,coef in zip([1.0]+xt,beta)) for h in range(23)]
    fitted = [[sum(v*coef[h] for v,coef in zip(x,beta)) for h in range(23)] for x in design]
    correction = math.sqrt(1 + (dim+1)/max(2,n-dim-1))
    return [[centers[h]+(y[h]-fit[h])*correction for (_,y),fit in zip(samples,fitted)] for h in range(23)], weights


def forecast(case, config=None):
    cfg = DEFAULT if config is None else config
    if case['levels'] != list(LEVELS):
        raise ValueError('unsupported quantile levels')
    if sorted(x['hour'] for x in case['forecast']) != list(range(2,25)):
        raise ValueError('expected hours 2 through24')
    x = features(case)
    samples = training(case)
    return predict(samples, x, cfg)


def predict(samples, x, cfg):
    if len(samples) < 4:
        logs = [[z*0.15*math.sqrt(h) for z in Z] for h in range(1,24)]
    elif cfg['family'] == 'qr':
        logs = quantile_fit(samples, x, cfg)
    else:
        distributions, weights = predict_logs(samples,x,cfg)
        logs = []
        for values in distributions:
            if cfg['family'] in ('normal','student') or cfg['distribution'] == 'normal':
                m = sum(v*w for v,w in zip(values,weights))/sum(weights)
                sd = math.sqrt(sum(w*(v-m)**2 for v,w in zip(values,weights))/sum(weights))
                zvals = Z if cfg['family'] != 'student' else (-2.015048,-0.726687,0,0.726687,2.015048)
                row = [m + z*sd*cfg['spread'] for z in zvals]
            else:
                row = [quantile(values,weights,t) for t in LEVELS]
                center = row[2]
                row = [center+(v-center)*cfg['spread'] for v in row]
            logs.append(row)
    result = []
    for h,row in enumerate(logs,2):
        q = [round(math.exp(max(-13.815510557964, min(math.log(1e9), x[0]+v))),6) for v in row]
        q = [min(1e9,max(0.000001,v)) for v in q]
        result.append({'hour':h,'q':q})
    return {'hours':result}


def quantile_fit(samples, target, cfg):
    dim = cfg['features']
    n = len(samples)
    center = [sum(x[j] for x,_ in samples)/n for j in range(dim)]
    scales = [max(.5,math.sqrt(sum((x[j]-center[j])**2 for x,_ in samples)/n)) for j in range(dim)]
    design = [[1.]+[(x[j]-center[j])/scales[j] for j in range(dim)] for x,_ in samples]
    xt = [1.]+[(target[j]-center[j])/scales[j] for j in range(dim)]
    weights = [math.exp(-min(100,sum((a-b)**2 for a,b in zip(x,xt))/(2*cfg['bandwidth']**2))) *
               (1 if original[6]==target[6] else cfg.get('cross_platform',1)) + 1e-8
               for x,(original,_) in zip(design,samples)]
    rows = [[] for _ in range(23)]
    for h in range(23):
        labels = [y[h] for _,y in samples]
        for tau in LEVELS:
            beta = [quantile(labels,weights,tau)]+[0.]*dim
            for _ in range(30):
                residuals = [y-sum(a*b for a,b in zip(x,beta)) for x,y in zip(design,labels)]
                w = [base*(tau if r>=0 else 1-tau)/max(.01,abs(r)) for base,r in zip(weights,residuals)]
                a = [[sum(v*x[i]*x[j] for v,x in zip(w,design))+(cfg['ridge'] if i==j and i>0 else 0) for j in range(dim+1)] for i in range(dim+1)]
                b = [[sum(v*x[i]*y for v,x,y in zip(w,design,labels))] for i in range(dim+1)]
                beta = [v[0] for v in solve(a,b)]
            rows[h].append(sum(a*b for a,b in zip(xt,beta)))
    return [sorted(row) for row in rows]


def run():
    source = Path(os.environ.get('MAKEFUN_INPUT_DIR','/input'))
    dest = Path(os.environ.get('MAKEFUN_OUTPUT_DIR','/output'))
    dest.mkdir(parents=True,exist_ok=True)
    for path in sorted(source.glob('*.in')):
        case = json.loads(path.read_text(), parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))
        output = json.dumps(forecast(case),separators=(',',':'),allow_nan=False)+'\n'
        if len(output.encode()) > 65536:
            raise ValueError('forecast exceeds size cap')
        (dest / (path.stem+'.out')).write_text(output)


if __name__ == '__main__':
    run()
