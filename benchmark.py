"""Cold isolated processes and warm component timings; asserts output determinism."""
import argparse
import json
import os
from pathlib import Path
import resource
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import main


def run(input_dir, output):
    rows=[]
    for path in sorted(Path(input_dir).glob('*.in')):
        cold=[]; signature=None
        with tempfile.TemporaryDirectory() as scratch:
            root=Path(scratch);source=root/'input';dest=root/'output';source.mkdir();dest.mkdir()
            shutil.copyfile(path,source/path.name)
            env=dict(os.environ,MAKEFUN_INPUT_DIR=str(source),MAKEFUN_OUTPUT_DIR=str(dest),PYTHONHASHSEED='0')
            for _ in range(3):
                before=time.perf_counter()
                subprocess.run([sys.executable,'-P','-s',str(Path(main.__file__).resolve())],env=env,check=True,capture_output=True)
                cold.append((time.perf_counter()-before)*1000)
                actual=(dest/(path.stem+'.out')).read_bytes()
                assert signature is None or signature==actual
                signature=actual
            case=json.loads(path.read_text());parts=[]
            for _ in range(5):
                t0=time.perf_counter();case=json.loads(path.read_text());t1=time.perf_counter()
                x=main.features(case);samples=main.training(case);t2=time.perf_counter()
                forecast=main.predict(samples,x,main.DEFAULT);t3=time.perf_counter()
                encoded=json.dumps(forecast,separators=(',',':'),allow_nan=False)+'\n';t4=time.perf_counter()
                assert encoded.encode()==signature
                parts.append([(t1-t0)*1000,(t2-t1)*1000,(t3-t2)*1000,(t4-t3)*1000])
        rows.append({'case':path.stem,'cold_ms':cold,'cold_median_ms':statistics.median(cold),
                     'warm_components_ms':dict(zip(('parse','features_and_training','prediction','serialize'),map(statistics.median,zip(*parts)))),
                     'output_bytes':len(signature)})
    rss=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    result={'runtime':sys.version,'platform':sys.platform,'rss_mib':rss/(1024**2 if sys.platform=='darwin' else 1024),
            'rss_note':'maximum child RSS in this benchmark process; local machine, not official sandbox',
            'rows':rows,'cold_sum_median_ms':sum(r['cold_median_ms'] for r in rows)}
    Path(output).write_text(json.dumps(result,separators=(',',':'))+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--out',default='runtime.json');a=p.parse_args();run(a.input,a.out)
