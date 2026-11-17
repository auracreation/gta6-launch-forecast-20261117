# Validation and model selection

No local result is an official score. The official practice labels and scorer are server-side. No withheld practice outcomes were downloaded or embedded. All candidate results are preserved in compact JSON files.

## Data and splits

37 complete launch events,31 before2026 for development and6 in2026 initially reserved. An event’s23 target hours always stay together. Features use that event’s hour1 and earlier observations; all rows after its checkpoint are hidden. The same event is excluded from fitting. Every main.forecast result is checked for parity with the research predictor. Exchangeable event LOO is distinct from historical as-of testing.

The initial search tried192 configurations: empirical analog mixtures, lognormal and Student-t5 trajectory distributions, and ridge regression over1,2,4 or6 features, multiple kernel widths and penalties. Its selected development loss was0.339559, nested loss0.347248; the untouched2026 holdout scored0.607934. That weak result prompted a platform-aware experiment. The original2026 holdout has since been inspected and is now diagnostic only. No new experiment claims an untouched holdout.

The target is console-only, so a second selection used the7 pre2026 console launches, while fitting on all30 other development events with a learned cross-platform weight. It compared162 analog/ridge configurations plus4 direct regularized quantile regressions. This is domain-specific validation with high uncertainty, not7 new independent datasets. A pure-console-only fit is effectively a small-data hierarchical extreme; partial pooling retains related mixed-platform launches. A direct QR family did not beat the simpler selected model. Boosted models were not added: tiny event count, no installed inference dependencies, and simpler families already expose strong variation. All candidates, including worse ones, remain recorded.

## Selected inference

{'family': 'ridge', 'features': 1, 'ridge': 0.3, 'bandwidth': 0.5, 'distribution': 'empirical', 'spread': 1.0, 'cross_platform': 0.2}

At each UTC horizon, fit the log ratio to hour1 as a regularized local linear function of log opening viewers. Reference similarity is a Gaussian kernel of standardized log opening size. Different launch-platform classes get weight0.2; same class gets1. The7-event validation selected these hyperparameters. Standardization is estimated within each fitting fold. Ridge leaves the intercept unpenalized. Weighted fitted residuals, with a degrees-of-freedom variance correction, form an empirical mixture shifted to the target’s fitted center. Weighted inverse-CDF interpolation gives the five quantiles. Clamp final predictions to(0,1e9] and serialize deterministically.

This is a mixture over observed trajectory scenarios; their weights come from similarity and grouped validation. No arbitrary probabilities were assigned to six named scenarios. UTC-hour curves carry observed daily shape; a flat-trajectory ablation removes it. Separate regional or weekend coefficients are not supported by enough matched events. Channels and short/long prehistory features were evaluated but did not improve the selected development criterion. Missing slope or acceleration is never manufactured.

| Evaluation | Mean loss | Median | Worst | Coverage90 | Typical miss |
|---|---:|---:|---:|---:|---:|
|Chosen config,console LOO|0.171132|0.150080|0.243100|0.900621|32.019975|
|Nested console selection|0.233045|0.203092|0.556639|0.813665|45.033376|
|2026 console diagnostic(Saros)|0.802354|0.802354|0.802354|0.695652|188.262963|
|All37 event LOO|0.388566|0.238037|1.545460|0.834313|73.669108|

Nested selection is materially worse than the chosen configuration’s reuse of the development folds. Treat0.171132 as selection performance, not an unbiased estimate. No evidence here supports a guaranteed0.145928 official score. Saros is a severe outlier; broad launch generalization remains weak.

## Ablations

| Change | Console LOO loss | Coverage90 |
|---|---:|---:|
|selected|0.171132|0.900621|
|no_platform_weight|0.191240|0.956522|
|no_history_or_channels|0.171132|0.900621|
|flat_time|0.296829|0.590062|
|normal_tails|0.172299|0.962733|
|wider_tails|0.180377|0.944099|

See initial-results.json for Gaussian/Student-t comparisons, results.json for full-platform partial pooling and channel/history ablations, domain-results.json for domain selection, nested folds and time-shape ablation. The broad-kernel ablation is approximately, not exactly, uniform.

## Runtime and checks

Python3.13.14 on local macOS aarch64. benchmark.py uses3 cold processes per case and5 warm component runs, asserting byte equality. Initial benchmark predates final chosen configuration; runtime.json is regenerated after freezing it. The local machine differs from the official1CPU Linux container; only official run_ms establishes competition speed. No Docker sandbox is installed.

Assertion suite covers the official worked loss, equal-quantile identity, future target exclusion, same-event exclusion, premiere exclusion, reference availability, null channels, missing history, zero/huge counts, finite boundaries, strict output size/schema, ordered quantiles and harness/inference parity. Read-only reviewers confirmed the scoring and found the availability mismatch before submission; the fix has a regression test.
