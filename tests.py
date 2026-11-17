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

if __name__=='__main__':unittest.main()
