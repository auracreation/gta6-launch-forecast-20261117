import importlib.util
import math
import pathlib
import os
import unittest

class ContractTests(unittest.TestCase):
    def test_engine_exists(self):
        self.assertIsNotNone(importlib.util.find_spec('main'), 'offline engine is missing')

    def test_official_metric_example(self):
        import main
        q = [[600000,800000,900000,1100000,1500000]] * 2
        m = main.score([1000000,700000], q)
        self.assertAlmostEqual(m['loss'], 0.112545, places=6)
        self.assertAlmostEqual(m['typical_miss_pct'], 19.52, places=2)
        self.assertEqual(m['coverage_90'],1)

    def test_score_omits_unprinted_hours(self):
        import main
        rows = [[40, 50, 60, 70, 80], [200] * 5]
        self.assertEqual(main.score([None, 100], rows), main.score([100], [rows[1]]))


class ForecastTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import json
        casepath=pathlib.Path(os.environ.get('MAKEFUN_TEST_CASE',str(pathlib.Path(__file__).resolve().parents[2]/'work/gta6-twitch-ccu-forecast-01-kit/input/p00.in')))
        if not casepath.exists():raise unittest.SkipTest('set MAKEFUN_TEST_CASE to kit input/p00.in')
        cls.case=json.loads(casepath.read_text())

    def test_cutoff_filters_target_future(self):
        import copy, main
        before=main.features(self.case)
        poisoned=copy.deepcopy(self.case)
        poisoned['history_hourly'].append({'from':self.case['checkpoint'],'viewers':1e100,'channels':1})
        self.assertEqual(before,main.features(poisoned))

    def test_future_analog_exclusion(self):
        import copy, main
        poisoned=copy.deepcopy(self.case)
        poisoned['comparables']=[dict(self.case['comparables'][0],day_start='2026-11-20T00:00:00Z')]
        self.assertEqual(main.training(poisoned),[])

    def test_exclude_same_launch_and_premiere(self):
        import copy, main
        a=self.case['comparables'][0]
        pseudo,actual=main.make_case(a,self.case['comparables'])
        self.assertNotIn(a['name'],[x['name'] for x in pseudo['comparables']])
        pseudo['comparables']=[dict(a,name=a['name'].upper()),self.case['comparables'][-1]]
        self.assertEqual(main.training(pseudo),[])
        self.assertEqual(len(actual),23)

    def test_zero_missing_history_and_channels(self):
        import copy,main
        c=copy.deepcopy(self.case)
        c['known'][0]['viewers']=0;c['known'][0]['channels']=None
        c['history_hourly']=[];c['history']=[];c['comparables']=[]
        result=main.forecast(c)
        self.assertEqual([r['hour'] for r in result['hours']],list(range(2,25)))
        for row in result['hours']:
            self.assertEqual(row['q'],sorted(row['q']))
            self.assertTrue(all(math.isfinite(q) and 0<q<=1e9 for q in row['q']))

    def test_nonfinite_first_print_rejected(self):
        import copy,main
        c=copy.deepcopy(self.case);c['known'][0]['viewers']=float('inf')
        with self.assertRaises(ValueError):main.forecast(c)

    def test_metric_equal_quantiles(self):
        import main
        self.assertAlmostEqual(main.score([100,1000],[[200]*5,[200]*5])['loss'],(math.log(2)+math.log(5))/2)

    def test_engine_deterministic_contract(self):
        import main,json
        a=main.forecast(self.case);b=main.forecast(self.case)
        self.assertEqual(a,b)
        self.assertEqual(set(a),{'hours'})
        self.assertLessEqual(len(json.dumps(a).encode()),65536)
        for row in a['hours']:
            self.assertEqual(set(row),{'hour','q'})
            self.assertEqual(len(row['q']),5)
            self.assertEqual(row['q'],sorted(row['q']))
            self.assertTrue(all(0<q<=1e9 and math.isfinite(q) for q in row['q']))

    def test_harness_matches_inference(self):
        import main,research
        path=os.environ.get('MAKEFUN_TEST_CASE',str(pathlib.Path(__file__).resolve().parents[2]/'work/gta6-twitch-ccu-forecast-01-kit/input/p00.in'))
        _,events=research.load(path)
        analog=self.case['comparables'][0]
        case,_=main.make_case(analog,self.case['comparables'])
        samples=[e['sample'] for e in events if e['name']!=analog['name']]
        self.assertEqual(main.training(case),samples)
        self.assertEqual(main.forecast(case),main.predict(samples,main.features(case),main.DEFAULT))

    def test_quantile_regression_constant_training(self):
        import main
        sample=([10.,4.,0.,0.,0.,0.,1.],[0.5]*23)
        logs=main.quantile_fit([sample]*5,sample[0],dict(main.DEFAULT,features=1,bandwidth=1.,ridge=1.))
        for row in logs:
            for q in row:self.assertAlmostEqual(q,0.5,places=5)

    def test_selected_history_feature_changes_forecast(self):
        import main
        samples=[([10.,4.,v,0.,0.,0.,1.],[v]*23) for v in (-1.,-.5,0.,.5,1.)]
        cfg={'family':'ridge','features':1,'indices':[0,2],'ridge':.3,'bandwidth':2.,'distribution':'empirical','spread':1.}
        a=main.predict(samples,[10.,4.,0.,0.,0.,0.,1.],cfg)['hours'][0]['q'][2]
        b=main.predict(samples,[10.,4.,1.,0.,0.,0.,1.],cfg)['hours'][0]['q'][2]
        self.assertGreater(b/a,1.5)

    def test_ensemble_blends_quantiles_on_log_scale(self):
        import main
        samples, features = main.training(self.case), main.features(self.case)
        members = main.DEFAULT['members']
        a, b = [main.predict(samples, features, member)['hours'] for member in members]
        result = main.forecast(self.case)['hours']
        for x, y, blend in zip(a, b, result):
            for u, v, q in zip(x['q'], y['q'], blend['q']):
                self.assertTrue(math.isclose(q, math.sqrt(u*v), abs_tol=0.00001))

    def test_research_grid_does_not_inherit_current_model_features(self):
        import research
        configs = research.configurations()
        self.assertEqual({c['features'] for c in configs}, {1, 2, 4})
        self.assertTrue(all('indices' not in c for c in configs))

if __name__=='__main__':unittest.main()
