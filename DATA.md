# Historical evidence

Source: make.fun public gta6-twitch-ccu-forecast-01 kit, retrieved2026-11-17. Its NOTICE attributes the supplied counts to [SullyGnome](https://sullygnome.com), collected2026-11-17; exact original collection timestamps are unavailable. The kit contains38 comparables,37 complete launch UTC days and GTA VI prelaunch history. See data-catalog.csv for every source, event date, point count, opening/peak and source irregularities. Raw hourly series remain in the downloadable kit. Missing hours are missing observations, never interpolated or zeros. Peaks in the catalog describe labels; the predictor never reads the catalog or outcome-bearing annotations.

SullyGnome supplies hourly average concurrent viewers and channels, not cumulative views, trailer video views or concurrent players. Its data has no stated open licence and its notice requests no bulk scraping. No additional scraping was performed and no raw curves are republished. The public software licence applies to our code, not third-party data. Numerical counts were not independently reconstructed from the historical provider.

The GTA VI premiere history is excluded from launch fitting. Early-access events include Hogwarts Legacy,007 First Light,Forza Horizon6,Starfield,DiabloIV,Assassin’s Creed Shadows,DOOM:The Dark Ages,Death Stranding2 and Forza Horizon5. Other unlock annotations are partly unverified and some use hindsight. We do not parse those annotations as target features. Platform and genre differences remain an analog-selection risk. GTA V launch hourly CCU is missing in the supplied data; no curve was fabricated. RDR2 is an official withheld practice event, so its post-cutoff observations were not fetched.

[Rockstar’s game page](https://www.rockstargames.com/VI) and [regional support notice](https://support.rockstargames.com/articles/29jV3Cv2cCgvwM1XgtMO5o/grand-theft-auto-vi-regional-pre-load-and-release-times-on-playstation-5-and-xbox-series-x-or-s?pubDate=20261107) confirm19November2026 and midnight local release on consoles, checked2026-11-17. The forecast measures hours of the UTC date, which differs from elapsed hours since the earliest regional unlock.

Target features use only input rows strictly before its own checkpoint. The kit explicitly provides the same2026 comparison library even for its2018 practice case. Accordingly exchangeable-event tests use the supplied reference library without claiming it existed at each historical launch; separately labelled chronological tests train only on earlier dates. All final inference references must finish before2026-11-19T01:00Z. No future GTA outcome is used.

I checked the [Twitch game analytics documentation](https://dev.twitch.tv/docs/insights) and [Streams Charts game endpoint](https://streamscharts.com/api/docs/games) on 2026-11-17. Both document game-level aggregates by calendar day, so neither supplies the hourly labels needed here. The [Tang and Huang research archive](https://github.com/mingt2019/Twitch-Dataset) describes real-time stream samples for 5–21 October 2017 UTC. Its linked full archive returned a sign-in page. No hourly series were added for Gran Turismo Sport, South Park, or The Evil Within 2. An event with a single reported peak still lacks an hourly curve. The supplied kit remains the source for all fitted series, including mixed-platform and multiplayer launches.

## Input integrity

- p00.in: SHA256 `e9411e07f804e71a16af1703e741239b2c7a7a1105314ea5b0c8cb57a2745319`
- p01.in: SHA256 `2274f00b9b24ab8d29f3ea793d58391b900fd271f4098b83f6483e47356cc890`
- p02.in: SHA256 `88c777fa061c646db6810e9b961ecfd055addf6f9783954445e92e908cf3552c`
- p03.in: SHA256 `54ff087be214580d8b90a8bba4cd14fa3d977d81ea1c1f670e9dca30ea6ba3a6`
