# Research

**Status: DRAFT.** The bar below takes effect at the commit that changes this line to "IN FORCE". After that commit, changing the bar or the model starts a new attempt.

## What this repo is

A public record of one question: can a model built on public chart data forecast the Billboard Hot 100 better than the free alternatives?

The repo holds the rules, the bar, a manifest of the weekly log, and the model's frozen predictions. It holds no API keys, no trading code and no market data.

## Rules

1. No prediction-market account and no prediction-market data until the bar is met.
2. Chart data can show forecasting skill. Nothing in this repo is called alpha.
3. Meeting the bar unlocks one thing: comparing the model's probabilities with public price history, read-only. An account is a separate, later decision.
4. A pump flag means stay away from that song. It is never a reason to bet.
5. A changed model is a new attempt with a new 13-week test. Every attempt is written in `ATTEMPTS.md` before its test starts.

## The model

- **Layer 1** finishes a song's Friday-to-Thursday Spotify US total from its first three days. It is built on 2017-2021 daily chart data: fit on 2017-2019, tuned on 2020, tested once on 2021. It is also the "normal growth" model for the class project, where its large positive misses are the pump flags.
- **Layer 2** maps those totals to Hot 100 ranks. Its inputs are Spotify US daily streams and last week's Hot 100. Radio and sales are absorbed into a per-song residual. It is trained on 2026 chart weeks only, because the chart's formula changed in January 2026.

## Chart weeks

A chart week is one Hot 100, named by its chart date, which is a Saturday. Its tracking week runs Friday to Thursday and ends nine days before the chart date. Example: the chart dated 2026-11-21 covers 2026-11-06 to 2026-11-12.

## Weekly questions

**Candidates.** Each week's candidate songs are the union of:

- last week's Hot 100 top 20, and
- every song in the Spotify US daily top 20 on the first three days of the tracking week (Friday, Saturday, Sunday).

**Questions.** Two per candidate:

1. Is it in this week's Hot 100 top 10?
2. Which band is it in: 1-2, 3-5, 6-10, 11-20, or 21 and below?

**Forecasters.** Four sets of answers per week:

| Forecaster | When it answers | What it knows |
|---|---|---|
| Model, Monday | Monday of the tracking week | Spotify data for Friday to Sunday |
| Model, Friday | The Friday after the tracking week, before the public forecast is opened | Spotify data for all seven days |
| Repeat | Any time | Last week's Hot 100. A song not on it is answered "not top 10" and "21 and below" |
| Public forecast | When posted | Whatever its authors use. A candidate it does not list is answered "not top 10" and "21 and below" |

**Score.** A forecaster's weekly score is the share of that week's questions it answers correctly. The model's answer to a question is its most probable option.

## The bar

The test is 13 consecutive chart weeks, starting with the first tracking week after the model is frozen. Both conditions must hold:

1. **Monday.** The Monday model scores strictly higher than Repeat in at least 10 of the 13 weeks. Ties count against the model.
2. **Friday.** Over the 13 weeks together, the Friday model answers at least 95% as many questions correctly as the public forecast.

Condition 1 asks whether the model adds anything during the week, when Repeat is the only free forecast. Condition 2 asks whether the model reads a finished week about as well as the people who do this in public. Ten of 13 happens by luck under 5% of the time.

The Monday and Friday predictions are committed to `predictions/` before the chart posts. A prediction committed late does not count, and the week is scored as a loss.

## Headroom check

Headroom is the public forecast's weekly score minus Repeat's. It measures how much there is to forecast.

- It is computed on the first six logged weeks and reported. Those weeks fall in the holiday season, when the chart behaves unlike the rest of the year, so this reading does not decide anything.
- It is computed again on every week logged by the freeze date. If it averages under 5 percentage points, layer 2 is not built.

## Weekly log

Raw files stay on the local machine in `data/`, which git ignores. They are other people's published work, so the repo records only their SHA-256 hashes, which prove the files existed when logged.

Each week, save into `data/<chart date>/`:

| File | Contents | Minimum |
|---|---|---|
| `hot100.csv` | The Hot 100 as posted: `rank,title,artist` | Top 40 |
| `public_forecast.csv` | The public forecast as posted: `predicted_rank,title,artist,source,posted_at,url` | Top 20 |
| `spotify_us/<YYYY-MM-DD>.csv` | The Spotify US daily chart, one file per tracking day, with rank, track, artist and streams columns | 7 files, 150 rows each |

Then run:

```
python tools/log_week.py 2026-11-21
git add log/manifest.csv && git commit -m "log 2026-11-21"
```

The script checks the files and appends their hashes to `log/manifest.csv`.

## Timeline

| When | What |
|---|---|
| Chart dated 2026-11-21 | Weekly log starts |
| Late December 2026 | First headroom reading, on six holiday-season weeks |
| January 2027 | Class project submitted |
| Late January 2027 | Decisive headroom reading. If it passes, layer 2 is frozen and written into `ATTEMPTS.md` |
| February to April 2027 | 13 test weeks |
| Late April or early May 2027 | Result |

## Layout

```
README.md          rules, the bar, timeline
ATTEMPTS.md        one entry per frozen model, written before its test
log/manifest.csv   hashes of each week's saved files
predictions/       the model's Monday and Friday answers, committed before each chart posts
templates/         column headers for the weekly files
tools/log_week.py  checks a week's files and records their hashes
data/              raw weekly files, local only
```
