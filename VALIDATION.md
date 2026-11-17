# Validation and model selection

No local result is an official score. The official practice labels and scorer are server-side. No withheld practice outcomes were downloaded or embedded. All candidate results are preserved in compact JSON files.

## Data and splits

37 complete launch events,31 before2026 for development and6 in2026 initially reserved. An event’s23 target hours always stay together. Features use that event’s hour1 and earlier observations; all rows after its checkpoint are hidden. The same event is excluded from fitting. Every main.forecast result is checked for parity with the research predictor. Exchangeable event LOO is distinct from historical as-of testing.

The initial search tried96 configurations: empirical analog mixtures, lognormal and Student-t5 trajectory distributions, and ridge regression over1,2,4 or6 features, multiple kernel widths and penalties. Its selected development loss was0.339559, nested loss0.347248; the untouched2026 holdout scored0.607934. That weak result prompted a platform-aware experiment. The original2026 holdout has since been inspected and is now diagnostic only. No new experiment claims an untouched holdout.

The target is console-only, so a second selection used the7 pre2026 console launches, while fitting on all30 other development events with a learned cross-platform weight. It compared81 analog/ridge configurations plus4 direct regularized quantile regressions. This is domain-specific validation with high uncertainty, not7 new independent datasets. A pure-console-only fit is effectively a small-data hierarchical extreme; partial pooling retains related mixed-platform launches. A direct QR family did not beat the simpler selected model. Boosted models were not added: tiny event count, no installed inference dependencies, and simpler families already expose strong variation. All candidates, including worse ones, remain recorded.

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

Reviewer diagnostic: replacing nominal count with effective sample count in the residual variance correction worsened console LOO loss0.171132→0.173869. This unpromoted change is not in inference. Small weighted samples remain a calibration limitation.

## Second candidate: prelaunch adoption

After the first official practice result0.198801, the new hypothesis was tested only on supplied comparable events, without fetching or inspecting practice answers. The original2026 holdout was already known, so all37 events now form a developmental dataset. Eight console-only launches define the target domain. A37-configuration search compares the original model and four prehistory feature sets at three penalties and three bandwidths. research_history.py reproduces it.

Selected configuration uses log opening viewers and mean log audience48–24hours before UTC day start, relative to opening. It uses ridge15 and bandwidth1, retaining cross-platform weight0.2. This distinguishes already active categories from launches starting from sparse prehistory. No unlock outcome annotations are parsed. Console LOO mean improves0.237660→0.180922, worst event0.716169→0.210917, typical miss40.63%→30.37%; median loss worsens0.164473→0.182987. Across all37 mixed events, mean improves0.388566→0.371897 while median and typical miss worsen slightly. Nested console model-selection loss is0.249515, so optimism and a small sample remain material.

The prelaunch-level model stayed a local comparator. A fixed-design jackknife diagnostic increased console loss from 0.171132 to 0.172129. The effective sample size correction also increased loss.

## Release candidate with recent momentum and prelaunch activity

Both components fit weighted ridge regressions with the existing empirical residual distribution. Both use opening viewers, prelaunch levels from 48 to 24 hours before UTC day start, a Gaussian kernel with bandwidth 0.65 in standardized features, and 0.2 weight for cross-platform analogs. The momentum component compares the last two hours before UTC day start to the preceding three and uses ridge penalty 3. The other compares the 12-hour prelaunch peak with the earlier baseline and uses penalty 15. The ensemble averages equal-level quantiles in log space. All features are calculated before the observation cutoff. No outcome from one of the four make.fun practice targets was used.

| Configuration | Console event LOO | Chronological console | All 37 event LOO |
|---|---:|---:|---:|
| Official entry 1 configuration | 0.237660 | 0.281683 | 0.388566 |
| Prelaunch level | 0.180922 | 0.197760 | 0.371897 |
| Momentum only | 0.171288 | 0.180108 | 0.402722 |
| Prelaunch activity only | 0.168363 | 0.192548 | 0.388794 |
| Equal ensemble | 0.158624 | 0.175746 | 0.379388 |
| Remove platform weighting | 0.185751 | 0.195748 | 0.392536 |
| Broad kernel | 0.201587 | 0.224410 | 0.427394 |
| Normal residual tails | 0.171378 | 0.170361 | 0.371592 |

Chronological folds required at least two earlier console references and scored six launches. The ensemble scored 0.179248 in nested console validation when each outer fold selected both component configurations separately. Its worst console LOO event was 0.187943, with 0.961957 coverage and 27.25% typical miss across that cohort. Holding out both Ghost releases together raised mean console loss to 0.162238. A one-hour US daylight-saving alignment shifted both the reference history and reference outcomes around the anchor, producing 0.161576. We retained UTC alignment and empirical residuals since they had the lowest mean loss on the matched eight-event cohort. Normal tails performed better on the other two splits.

An independent audit tested a probability integral transform recalibration using only inner-fold held-out forecasts. Half-strength calibration decreased mean console LOO loss to 0.153047, but raised chronological loss to 0.182230 and increased worst-event loss. The submission uses the existing empirical quantiles. All eight console series were explored during development, so any generalization claim depends on the nested, chronological, and eventual official results.

`runtime-ensemble.json` records Python 3.13.14 measurements on macOS aarch64. Across three new processes per case, median cold starts ranged from 75.7 to 94.3 ms and peak child RSS was 24.84 MiB. The benchmark also checked byte identity and recorded separate parse, feature extraction, prediction and serialization times. The official grader measures its own runtime.
