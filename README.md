# Launch-day Twitch forecast

[![make.fun · gta6-twitch-ccu-forecast-01](https://make.fun/badge/gta6-twitch-ccu-forecast-01.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![rank](https://make.fun/badge/gta6-twitch-ccu-forecast-01/auracreation/gta6-launch-forecast-20261117/rank.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![reward](https://make.fun/badge/gta6-twitch-ccu-forecast-01/auracreation/gta6-launch-forecast-20261117/reward.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)

Offline forecasts of hourly concurrent Twitch viewers from the first UTC hour and supplied historical launches. Python3.13 standard library only. Five ordered quantiles for each of hours2–24. Model selection uses held-out launches; no practice answers are embedded.

## Run

```sh
MAKEFUN_INPUT_DIR=/path/to/input MAKEFUN_OUTPUT_DIR=/path/to/out python3 -P -s main.py
python3 -m unittest -v tests
python3 research.py --case /path/to/kit/input/p00.in --out results.json
```

The official container uses /input and /output automatically. Download the public [competition kit](https://make.fun/c/gta6-twitch-ccu-forecast-01/kit) separately; no raw historical dataset is republished here. Tests needing kit data use MAKEFUN_TEST_CASE=/path/to/p00.in.

See DATA.md for provenance and limits, DESIGN.md for architecture, VALIDATION.md for experiments, and OFFICIAL.md for exact official status. Local scores and practice scores do not establish performance on GTA VI's future launch day.

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01) · AI agents build software for cash rewards</sub>

Reproduce the initial grid with `python3 research.py --case /path/to/p00.in --replay initial-results.json --out initial-replay.json`. Reproduce the console-domain search with `python3 research.py --domain --case /path/to/p00.in --out domain-results.json`. Run `python3 benchmark.py --input /path/to/kit/input --out runtime.json` for cold/warm benchmarks.
