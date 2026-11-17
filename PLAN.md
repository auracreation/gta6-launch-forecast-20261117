# Forecast engine implementation plan

Goal: satisfy DESIGN.md and the attached user objective through research, implementation, validation and official submission.
Architecture: one offline inference module, one research harness, one assertion suite; no inference dependencies.
Tech: Python3.13 standard library; local exploratory runtime3.9 until3.13 availability checked.
Spec: DESIGN.md and make.fun kit RULES.txt (download snapshot stored outside public repo).

Global constraints: exact ln pinball with factor2; strict positive quantiles<=1e9;23 horizons;8s per case; exclude target future and outcome notes.
Review focus: sparse prehistory; channels null; first print0; target accidentally present in analogs; malicious filename/id or nonfinite JSON.

- [ ] Task1: tests.py metric worked example and cutoff-safe pseudo-case fixtures; run red before implementation. main.py public interfaces score(actual,predictions), make_case(analog,comparables), forecast(case,config=None), run(). research harness imports the same predictor/metric.
- [ ] Task2: minimal candidate models and grouped experiment harness; verify all folds exclude the event; reserve2026 launches for chronological holdout. Record every configuration, per-event score, calibration and aggregate mean/median/worst/variance. Lock config by training folds; do not tune to official score.
- [ ] Task3: numerical, I/O, determinism and performance tests in actual3.13; independent review and fixes; document data provenance, ablations and limits. Commit frozen candidate.
- [ ] Task4: create public repository with required badges/About/owner claim, bundle native logs unchanged, check gates, submit once, poll official score. Record commit, config, id,timestamp,loss,valid,runtime,coverage,miss. Preserve rollback. Improve only when independent evidence supports it.

Ruling: user's comprehensive execute-and-submit request authorizes ordinary design choices and publication; no extra design approval gate. No existing project/callers to preserve. All callers are tests.py,research.py and the sandbox root entrypoint.
