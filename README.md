# QuantStrategy: MT5 Multi-Timeframe Trend Bot

Live MetaTrader 5 trading bot, 20-year backtester, walk-forward optimizer and ML filter pipeline for a SuperTrend + DEMA + ADX trend-following system on XAUUSD, EURUSD, GBPUSD and USDJPY.

> **Disclaimer:** Research and educational code. Not financial advice. Trading leveraged instruments can lose more than you deposit. Nothing here is a claim of future profitability.

## Honest status

- The strategy's early backtest results were **invalid**. Two bugs inflated them: a look-ahead leak in the higher-timeframe lookup, and a missing JPY-to-USD P&L conversion. Both are fixed and verified on real data.
- After the fixes, the blended multi-engine system has **no demonstrated edge**.
- The only configuration that survived out-of-sample validation is **XAUUSD, H1 engine (`PF_H1`), `adx_rising=True`**. It is rule-only, with no ML filter. Live-forward evidence is still thin, so treat it as a candidate, not a proven system.

## Validated candidate: XAUUSD / PF_H1 / `adx_rising=True`

Full M5-precision backtest, stock parameters otherwise, two independent train/test cuts:

| Split | Window | Trades | WR | PF | Net | Sharpe | Max DD |
|---|---|---|---|---|---|---|---|
| 2020 | train 2006-19 | 232 | 35.8% | 1.25 | +11.7% | 0.28 | -5.19% |
| 2020 | **test 2020-26** | 99 | 41.4% | **1.76** | +15.0% | 0.59 | -2.61% |
| 2015 | train 2006-14 | 147 | 34.7% | 1.18 | +5.2% | 0.21 | -5.19% |
| 2015 | **test 2015-26** | 183 | 38.8% | **1.58** | +21.3% | 0.51 | -4.30% |

Stock (`adx_rising=False`) out-of-sample PF on the same splits: 1.17 and 1.04.

Not yet validated or not working:

- **EURUSD, USDJPY `PF_H1`:** results flip sign between train and test periods.
- **GBPUSD:** weak in both periods; paused in live.
- **`PF_M30`, `PF_M15`, `Confluence`:** negative on all symbols in both periods.

## Repository layout

| File | Purpose |
|---|---|
| `live_bot_ml.py` | Live MT5 bot: 4 engines per symbol, optional ML filter, Telegram/WhatsApp alerts, trade journal, MFE and peak-profit recorders |
| `backtest_optimized.py` | Multi-asset M5-precision backtester with slippage, commission and `--engines` filter |
| `optimizer.py` | Grid search plus walk-forward validation (imports `backtest_optimized.py`) |
| `split_data.py` | Splits MT5 CSVs into `train_data/` and `test_data/` at a date |
| `mfe_analyser_v3.py` | MFE/MAE and give-back analysis of a trades CSV |
| `ml_pipeline_fixed.py`, `ml_score.py` | Train LR/RF/XGB/LGB trade filters and score trade files. `ml_score.py` imports from `ml_pipeline`, so keep both in one folder under that module name |

## Setup

```bash
pip install pandas numpy scikit-learn xgboost lightgbm joblib tabulate MetaTrader5
```

`MetaTrader5` needs Windows. On Linux, run the `mt5linux` proxy and pass `--mt5-host` and `--mt5-port`.

**Data:** MT5 exports (tab-separated, `<DATE> <TIME> <OPEN> <HIGH> <LOW> <CLOSE> ...`) named `{SYMBOL}_{TF}_data.csv`, with `TF` in `M5, M15, M30, H1`, for each symbol.

## Usage

**Backtest one engine:**
```bash
python backtest_optimized.py --data-dir . --risk 2.0 --no-session --no-chart --engines PF_H1
```

**Honest train/test check (no parameter search):**
```bash
python split_data.py --data-dir . --symbols XAUUSD --split-date 2020-01-01
python backtest_optimized.py --data-dir train_data --symbols XAUUSD --risk 2.0 --no-session --no-chart --engines PF_H1
python backtest_optimized.py --data-dir test_data  --symbols XAUUSD --risk 2.0 --no-session --no-chart --engines PF_H1
```

**Walk-forward optimizer** (the grid is deduplicated automatically when `--engines` isolates one engine):
```bash
python optimizer.py --data-dir . --symbol XAUUSD --wf --train-end 2020-01-01 --engines PF_H1 --fast --no-session --workers 4
```

**Live bot** (credentials from environment variables, never on the command line in shared logs):
```powershell
python live_bot_ml.py --login $env:MT5_LOGIN --password $env:MT5_PASSWORD --server $env:MT5_SERVER `
  --no-ml --symbols XAUUSD --no-session --poll 30 --dema custom `
  --max-daily-loss 2.0 --max-open-trades 4 --no-setup-alerts
```

Useful flags: `--dryrun` (no orders), `--check` (config check only), `--no-ml`, `--risk-conf`, `--risk-pf`, `--no-setup-alerts` (silence "setup forming" alerts only), `--no-alerts`, `--trail-sl` (off by default).

## Method notes

- Strategy parameters live in `BASE_TF` (shared) and `ASSET_PROFILES[symbol]["tf_overrides"]` (per symbol; overrides win). The XAUUSD `adx_rising=True` rule is an H1 override in both `backtest_optimized.py` and `live_bot_ml.py`.
- Signals use the last **closed** higher-timeframe bar only.
- Judge changes by out-of-sample behavior across several split points, not by the best in-sample grid result. A 486-combo search on EURUSD produced a combo that fell from Sharpe 0.34 to -0.58 out-of-sample.

## Known limitations

- Backtest compounds equity and has no ruin stop. A losing configuration can run on a negative balance.
- `ml_score.py` scores every row you give it. Pointing it at the file a model was trained on gives leaked, inflated metrics.
- The shipped ML models predate the bug fixes. Retrain on clean trades before using them.
- `live_bot_ml.py` has no per-engine selector yet, so all four engines run per symbol.
- M5 bars cannot resolve intrabar order, so same-bar TP/SL ties are an assumption.
- Live sample size is small, so no live statistic here is conclusive.

## Security

Never commit credentials, bot tokens, `journal/`, trade CSVs or `.joblib` models. Suggested `.gitignore`:

```
journal/
*.csv
*.joblib
*.log
train_data/
test_data/
```

If a credential has ever appeared in a chat, log or commit, rotate it.

## License

MIT. See [LICENSE](LICENSE). Copyright (c) 2026 Krunal Rahul Pilodekar.
