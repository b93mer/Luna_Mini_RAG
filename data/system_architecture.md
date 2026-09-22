# System architecture (current state)

**Purpose:** Accurate map of what the system does and where each piece lives.  
**Authority for freeze:** the live paper path in `Launcher/run_live_paper_full.py` — not `Model_B/model_b.py`.  
**Related:** [`baseline_freeze.md`](baseline_freeze.md) · [`session_perf_diag.md`](session_perf_diag.md) · [`priority_queue.md`](priority_queue.md)

**As of:** 2026-08-18. **V2-EV path 2 chosen** (operator chat): live `ev_r` stays mashed; `honest_ev` is write-only observe. **Rank-1 stamps confirmed** on the 8/18 live session (`746d1f1` fill EV / G1 / `calendar_dte` / CC `atr_15m`). Phase B sign-fix **not** landed. Freeze **not** started. **2.37 deferred** with caveats. Direction / tenor / YAML-binding identity is locked in the tables below; do **not** treat replica EOD mom concordance (~83–91%) or mashed residual as forecast error.

---

## Top-level components

### Launcher / live paper runner

`Launcher/run_live_paper_full.py` is the session process: loads config, warms data, loops the universe, scores conviction + EV, fires paper intents, persists open positions, and runs the exit monitor. Entry point: `main()` at `:4673`; `__main__` at `:6346`.

Supporting: `Launcher/config_mb_v2.0.0.yaml`, `Launcher/notify.py` (push text only).

### Model B (legacy / divergent path)

`Model_B/model_b.py` can call `utils/ev_engine.compute_expected_value` (`Model_B/model_b.py:1728`), which implements proper signed E[R] with conviction-blended `p_win` (`utils/ev_engine.py:127`). **This is not what writes `Logs/paper_trades_*.jsonl` in the live paper sessions.** Freeze authority is the launcher formula in `_evaluate_conviction_and_ev`.

### Data adapters

`utils/data_adapter.py` — Alpaca stock quotes/bars and option quotes/chain. Config: `data.source: alpaca`, `broker.mode: alpaca_options_paper` (`config_mb_v2.0.0.yaml:16-21,36-38`). Paper runner constructs `DataAdapter` near `main` loop setup (`run_live_paper_full.py:4820`).

### Three EV objects / three regime objects / direction objects / tenor objects

Do not collapse these. Only the launcher mashed formula and the RegimeBoss **skip_reason** path are freeze-authoritative for paper logs. Direction and tenor are the same honesty class: several objects share a label. Live fire-path direction today is **4.8 TRENDING × MultiDTE only**. Tenor that 4.8 / MACRO_COMPRESS inherit is **`gate_tier`**, not OCC DTE.

**EV**

| Object | Where | On live paper path? |
|--------|-------|---------------------|
| Launcher `ev_real` → `log_record["ev_r"]` | `_evaluate_conviction_and_ev` `:2299-2311` | **Yes** — mashed `p·W + (1−p)·L − slip` with **positive** `r_loss` |
| `utils/ev_engine.compute_expected_value` | `Model_B/model_b.py` | **No** — not imported by the launcher |
| `Model_B/ev_execution_gate.compute_ev_real` | Dexter helper | **No** — not the call site |

**Regime**

| Object | What it is | Where it binds |
|--------|------------|----------------|
| `factors["regime"]` / `GATE:REGIME` | RegimeObserver VWAP-stability purity (`vwap_dist` → `regime_stability` on `state["regime"].score`). Hard-block if `< 0.70`. | Inside `_evaluate_conviction_and_ev` |
| RegimeBoss standdown | macro/ticker compress, multidTE, etc. Gate identity = `skip_reason` / `regime_boss_reason`, **not** `regime_boss_block_type` (2.30). | **After** conviction (`_apply_regime_boss_hard_block` `:1292`) |
| `GATE:REGIME_STALE` | RegimeObserver TTL (~15 min) | **After** conviction, before spike |

Disabled: legacy vol-mult block (`:5851-5853`). Conviction `factors["regime"]` is **not** RegimeBoss — see `docs/scoping/2026-08-10_regime_factor_composition_trace.md`.

**Direction**

| Object | What it is | On live fire path? |
|--------|------------|---------------------|
| 4.8 TRENDING × MultiDTE | `_apply_trending_direction_validity_block`; YAML `gate_tiers: ["MultiDTE"]` | **Yes** — near-no-op on SPY/QQQ (`gate_tier` is always `0DTE` for those names). ~0.1% NF overlap with G1. |
| G1 `direction_commit_g1` | `attach_g1_direction_state`; `mode: log_only` | **Observe only** — `action_taken=none`. Apply-scoping still open. Do **not** promote. |
| `setup_direction_validator` | log_only (6/13: do not promote) | **Observe only** |
| `policy.decide()` `direction` / `conv_threshold` / `size_cap_mult` | Returned by RegimeBoss policy (`utils/regime/policy.py`) | **Dead output** — launcher uses only `trade_allowed` + `skip_reason`. Qty hardcoded `1`. Adaptation is binary allow/block. |
| Model_B `direction_picker` | RSI/VWAP CALL/PUT | **Unused** on the live paper path |
| Research D4 macro-fallback | ticker mom when TRENDING else macro | **Rejected** for the precision goal |
| Replica EOD mom concordance ~83–91% | SPY/QQQ large-move, 5m replica vs session-return sign | **Not a fire KPI** — do not quote as live directional accuracy |
| CXD / C1 (strict NF Jun 16–Aug 7, +60m underlying) | Alignment stratum vs G1_strict counterfactual | Measurement: C1 **57.9%** vs misaligned **39.9%**; conviction anti-ranks inside C1; G1_strict **+8.8pp** on NF with ~42% regret. Live G1 fires: 8/10, 8/11, **8/18** pass; 8/13 QQQ PUT `would_block` and still **+0.83R**; **8/18 QQQ PUT pass and −1.02R hard_stop** — n=1 each, not promote or kill. Pre-8/10 NF `momentum_dir` is **not** the same object as schema 1.1. |

**Tenor**

| Object | How it is assigned | What it controls |
|--------|--------------------|------------------|
| Setup family (`*_0DTE` vs `*_MultiDTE`) | Same heuristic as `gate_tier`: ticker in {SPY,QQQ} **or** Friday. **Not** OCC DTE. | Conviction override keys, EV profile lookup, review labels |
| `gate_tier` (`0DTE` vs `MultiDTE`) | Same heuristic (`:5364-5369`) | MACRO_COMPRESS hard-block vs MultiDTE bypass; **4.8 scope** (`gate_tiers: ["MultiDTE"]`) |
| Contract DTE | Always `_next_friday_expiry()` (holiday-aware since `9b2fcde`). Timeout uses **actual** contract DTE (40 vs 90). | Picked expiry / OCC; `kill_after_minutes_0dte` only when snapshot `dte == 0` |

4.8 and compress inherit **`gate_tier`**, not OCC DTE. 4.14 only rolled phantom Fridays back; it did **not** add daily 0DTE selection. Window 2 `Breakout_0DTE` is a Friday-weekly book, not same-day 0DTE (e.g. 8/13 QQQ PUT expiry 8/14). Instance #24 is review hygiene (“don’t say 0DTE”); freeze identity is **who 4.8 / compress apply to**.

### Conviction composite

Computed in `_evaluate_conviction_and_ev` (`:2144+`). Factors and weights (`:2359-2376`):

| Factor | Weight | Source |
|--------|--------|--------|
| `regime` | 0.20 | RegimeObserver VWAP-stability purity (`state["regime"].score`) — **not** RegimeBoss |
| `signal` | 0.25 | `signal_strength` on log_record |
| `rr` | 0.20 | `rr_score` (ATR expansion vs baseline — **not** reward/risk). In-code comment at `:2181` (“RR > 3:1”) is stale; do not quote it. |
| `liquidity` | 0.20 | option spread/depth (injected) or stock fallback |
| `iv` | 0.10 | Realized-vol proxy (`_estimate_iv_from_bars` close-to-close), not implied vol — same honesty class as `rr_score` |
| `time_of_day` | 0.05 | default / stamped score |

Threshold: `conviction.standard` (default 0.7835) via `_get_min_conviction` (`:417-456`), with per-setup overrides in `setup_conviction_overrides`. Load-bearing overrides: `Pullback: 0.90` (63% of strict-NF this window; conv ≥ 0.83 still `low_conviction`), `Breakout_MultiDTE: 0.77`, `Momentum_0DTE: 0.80`. `Breakout_0DTE` is **not** in the override map (fallback 0.7835). Optional dual-RSI boost when named-trigger mode is `scoring`. Setup `*_0DTE` is the **setup-family** object, not contract DTE (tenor table above; Instance #24).

### EV filter

Live computation (`:2299-2311`): builds `ev_real`, hard-blocks when `ev_real <= 0` (`GATE:EV_NONPOSITIVE`). Return value is stored as `log_record["ev_r"]` (`:5780`). Identity locked 2026-08-14 (Q1 PASS at 1e-5; max \|err\| 4.79e-6 = spread round-trip, not a second formula).

**Current (live, mashed):**  
`p·(r_win − decay − fric) + (1−p)·(r_loss − fric)` with **positive** `r_loss` (`avg_loss_r`) from exit profiles. On the 20-session window `decay = fee = adv_sel = 0` and `fric = est_slip` (spread fraction), so stamped `ev_r = p·W + (1−p)·L − slip`. Mean stamped **+0.952R** vs mean realized **+0.167R**.

**Friction mismatch is live, not inert:** EV subtracts `est_slip`; `pnl_r` is mid-to-mid with **no** spread. Decay-only asymmetry is unused (defaults 0). Sign error and this slip mismatch are **two** defects; a sign flip that still subtracts slip is not the gross invariant in `baseline_freeze.md`.

**Skip identity:** `ev<=0` is appended after regime / liquidity / spread / event, so it is almost never `skip_reason` (`reasons[0]`). Window: 227 `GATE:EV_NONPOSITIVE` code stamps, **0** `skip_reason` hits. After a sign fix the same `<= 0` test starts seeing ~0.17–0.28 and becomes behavior-adjacent — approval-gated.

**Not current — path 2 chosen 2026-08-16 (queue V2-EV):**

| Path | Live scalar | Freeze consequence |
|------|-------------|--------------------|
| 1. Fix sign in place | — | Not chosen |
| **2. Dual-write `honest_ev` (CHOSEN)** | mashed `ev_r` stays the decision number; `honest_ev` write-only gross | Freeze mashed; observe honest |
| 3. Leave mashed | — | Not chosen |

Live mashed math is unchanged. `honest_ev = p·r_win − (1−p)·|r_loss|` (no slip). `ev_formula_path=2_dual_write_honest_observe`. Do **not** treat the gross honest stamp as an approved live-formula change. Friction strip remains a second, unchosen decision.

Priors: `Logs/exit_profiles_v2.json` injected at `:5700-5704`; fallback `ev_filter.default_exit_profile` in YAML (`:28-35`). Fill rows copy `p_win` / `r_win` / `r_loss` / profile source / `honest_ev` / `g1_direction_state` / `calendar_dte` onto pos/fill (**confirmed 2026-08-18** on QQQ `paper_fill`; historical 22 fills still need intent join). CC rows stamp `atr_15m` + baseline id (**195/195** on 8/18).

**Quirk:** YAML `ev_filter.min_ev_r: 0.25` is **not** enforced on the live launcher path; only `ev_real <= 0` is. `min_ev_r` is consumed on the legacy Model B / `ev_engine` path. Do not wire it onto mashed (cannot bind; fire-set 0.82–1.02) or honest (would touch the 7 Breakout_0DTE fills) without a separate approval.

### Exit rules

`utils/exit_rules.check_exit` (`:23-190`), driven by `config.exits`:

| Rule | Config | Return |
|------|--------|--------|
| Hard stop | `stop_rules.hard_drawdown_pct: -0.25` | `("stop", "hard_stop")` |
| Base take profit | `profit_targets.base_take: 0.20` | `("scale", "base_take_profit")` |
| Runner trail | `runner_trail_start: 1.0`, `trail_pct_from_peak: 0.5` | `("scale", "runner_trail")` |
| Timeout (flat/negative only) | `time_rules.kill_after_minutes: 90` / `kill_after_minutes_0dte: 40` — keyed off **contract** `snapshot.dte`, not `gate_tier` | `("stop", "timed_out")` |
| Deep ITM | `exits.deep_itm.*` | stop or scale variants |

Live `check_exit` is the rules above. YAML `scale_percents` / `iv_halt` / `force_flatten_by` are **dead**. On 1-lot paper (`qty: 1`), a `("scale", "base_take_profit")` cannot partial-close (`qty // 2` floors to 1) and becomes a **full close**. `tests/test_exit_rules.py` still describes `trailing_stop` / `iv_collapse` — test drift; do not “fix” tests in a docs pass.

Exit monitor: `_maybe_eval_exit_overlays` (`run_live_paper_full.py:4073`), throttled every `EXIT_MONITOR_EVERY_N_TICKS = 40` (`:52`, `:6267-6270`).

### Risk halts

`_update_risk_after_trade` (`:2474+`): increments `day_pnl_r`, `consec_losses`, `trade_count`; sets `trading_halted` on:

- `max_consec_losses` (config `risk.max_consec_losses: 3`)
- `day_pnl_r <= max_day_loss_r` (`risk.max_day_loss_r: -1.0`)
- `trade_count >= max_trades_per_day` — YAML `risk.max_trades_per_day: 3` is **not** the binding cap. Live sandbox `SANDBOX_DAILY_TRADE_CAP=2` (W2 max fills/session = 2). `violate_daily_risk` is called with the sandbox cap.

Also `utils/risk_guardrails.violate_daily_risk` cross-check against JSONL. Halt sets `halt_flatten_pending`; flatten via `_flatten_all_open_positions_on_halt` (`:3904+`).

### Logging surface

| File | Contents | Live vs diagnostic |
|------|----------|-------------------|
| `Logs/paper_trades_YYYY-MM-DD.jsonl` | Every eval + intents + fills. Path 2: CC stamps `atr_15m` / `atr_ratio` / baseline id; fills copy `p_win` / `r_win` / `r_loss` / `honest_ev` / `g1_direction_state` / `calendar_dte` (**confirmed 8/18**; pre-stamp fills still drop them). | **Live** (via `utils/trade_logger.log_trade`) |
| `state/open_positions.json` | Open paper positions | **Live** |
| `SlippageLogs/slippage_*.jsonl` | Entry mid snapshot / adverse flag (observe) | Diagnostic-ish |
| `Logs/near_fire_observations_*.jsonl` | Strict-NF (≥0.83) **skip-only** by design: `_finalize_near_fire_observation_if_pending` returns when `trade_entered=True`. `forward_outcome` rows are **separate** `underlying_price` checkpoints at 30/60/120 min — not option R, not inline on the observation row (schema 1.0 and 1.1). | Diagnostic |
| `Logs/in_trade_observations_*.jsonl` | In-trade marks (`current_pnl_pct`, `max_gain_pct`); MFE/MAE are **derivable**, not a fill stamp | Diagnostic |
| `Logs/session_stub_*.json` | Post-session stub from `session_close.py` | Diagnostic |
| `Logs/launcher_*.log` | Process log | Ops |
| `pretrade_log.jsonl` (repo root) | Operator morning journal — **no** `ev_r` | Operator / journal |
| `session_journal_log.jsonl` | Session journal | Operator / journal |
| `Logs/exit_profiles_v2.json` | Setup EV priors | Live input |

### Diagnostic surface

| Tool | Answers |
|------|---------|
| `Analysis/session_perf_diag.py` | Multi-session fill expectancy, exit class, hold cohorts. EV residual vs mashed `ev_r` is **not** forecast error until path 1 lands. |
| `Analysis/v2_diag_followon.py` | V2-DIAG follow-on (analysis-only): in-trade MFE/MAE × exit class; timeout 10-min grid; NF honest EV × setup × skip_reason (skip-only); `atr_15m` on fire-family NF; `iv_rank_used` histogram (rv_rank, tape key kept). Does **not** rank skips on option R. |
| `Analysis/session_summary.py` | Single-session skip/fire anatomy |
| `Analysis/conviction_slope_tracker.py` | Conviction trajectory / near-fire framing |
| `Analysis/rr_score_observer.py` | `rr_score` distribution / session class |
| Weekly aggregators under `Analysis/` | Cross-session §§ for reviews |
| `session_close.py` | Stub + terzetto export |

---

## Data flow / pipeline

### 1. Pre-market / startup

- `main()` loads config (`_load_config`), prints conviction threshold (`:4673-4692`).
- Smoke quote on QQQ (`:4839-4851`).
- Load exit profiles (`:4862-4875`).
- IV-rank warmup per ticker (`:4884-4890`).
- VIX regime refresh helper registered (`:4903+`).
- Near-fire trackers + spike gate init (`:4716-4759`).
- `DataAdapter` constructed (`:4820`).

**Key config keys read:** `conviction.*`, `universe`, `ev_filter.*`, `risk.*`, `exits.*`, `near_fire.threshold`, spike/named-trigger blocks.

### 2. Market open / eval loop

- Outer loop sleeps `LOOP_SLEEP_SECONDS = 0.25` (`:8`, `:6304`).
- Per ticker: stock quote (`data_adapter.get_stock_quote`) / manual context, reversal plan, RegimeBoss **stamp** (allow/reason on `log_record`), signal construction. Daily RSI is **score-only** (`CTX:DAILY_RSI_NOT_EXTREME` damps `signal_strength`; not a hard skip). Stub `non_decision_primary` may still name it “dominant skip” — label, not gate identity.
- RegimeBoss **does not** skip before conviction. Compress/standdown is applied **after** conviction so the observer can capture high-conv + RegimeBoss skips. `GATE:REGIME` (Observer purity `< 0.70`) is the only regime hard-block inside `_evaluate_conviction_and_ev`. Observer TTL stale-gate (`GATE:REGIME_STALE`) is also after conviction.

### 3. Signal → candidate

Setup classification `_classify_setup_type` (`:5649`). G1 attach (`log_only`). `_apply_trending_direction_validity_block` (4.8 TRENDING × MultiDTE, `:5680`). EV priors injected from setup profile (`:5700-5704`). Option liquidity injected (`:5706-5720`).

### 4. Intent evaluation

`_evaluate_conviction_and_ev` (`:5765`): hard blocks inside the function are `GATE:REGIME` (Observer purity), liquidity, spread, event, **EV≤0** (rarely `skip_reason`), VIX — then weighted conviction vs min threshold / setup override. `ev_r` stamped (`:5780`). RegimeBoss hard block **after** (`:5783`). Observer TTL stale-gate (`:5858-5865`). Spike gate (`:5896`). On pass: `status = paper_intent` (`:5923`). NF finalize on skip paths only (`trade_entered` drops pending observer rows).

### 5. Paper fill (entry)

`_build_contract_preview` (`:5988`) → mid as entry. Microstructure gates. Slippage logger snapshot (observe; mid as fill). `_build_pos_entry` with `entry_price = contract_preview.mid` (`:6147` / execute twin `:6198`). Persist `state/open_positions.json`. `log_trade` writes intent/eval rows throughout.

### 6. Position management

Every 40 ticks: `_maybe_eval_exit_overlays` (`:6267-6270`). Refresh option mid (`:4151-4170`); reject synthetic. Update peak. PM override check. Watchdog. Else `check_exit(snapshot, exits_cfg)`.

### 7. Exit

On decision:  
`pnl_pct = (exit_price − entry_price) / entry_price`  
`pnl_r = pnl_pct / _1r` with `_1r = |hard_drawdown_pct|` (`:4267-4268`).  
Exit price = accepted mid (or watchdog last real mid). **No spread/fee netting.**

### 8. Post-fill

`_update_risk_after_trade` stamps `pnl_r`, may halt, calls `log_trade` (`:2540`). Position removed from open list.

### 9. End of session

Operator/process: `session_close.py` builds stub + optional terzetto export. Diag scripts run offline. RegimeBoss state persisted near loop end (`:6342`).

---

## Hot path (signal → target → log)

Exact surface that must not change **once the freeze starts** (freeze has not started). A representative path: score → pass gates → paper intent → open position → target exit → fill log. Pre-freeze exceptions are only what `baseline_freeze.md` lists (chosen EV path + additive audit stamps). Dual-write of `honest_ev` is additive logging if mashed `ev_r` remains the live scalar.

1. `main` (`Launcher/run_live_paper_full.py:4673`) — process entry / loop owner  
2. `data_adapter.get_stock_quote` — underlier quote for the tick  
3. `_compute_manual_indicator_context` (`:3423`) — RSI/ATR/VWAP inputs  
4. `_build_reversal_plan` (`:3103`) — reversal readiness / direction override when plan_ready  
5. RegimeBoss `update_and_decide` / **stamp** allow+reason on `log_record` — not yet a skip  
6. Signal / `signal_strength` assembly on `log_record` (daily RSI score-only damp lives here)  
7. ATR → `rr_score` stamp — live mapping unchanged; CC rows now also copy `atr_15m` / `atr_ratio` / baseline id (write-only)  
8. `_classify_setup_type` — setup **family** (not calendar DTE; not `gate_tier`; not OCC DTE)  
9. G1 attach (`log_only`) — observe; `action_taken=none`  
10. `_apply_trending_direction_validity_block` (`:1228`) (4.8 TRENDING × MultiDTE) — live fire-path direction gate; near-no-op on SPY/QQQ because `gate_tier` is always `0DTE` for those names; can `continue` **before** conviction  
11. Exit-profile inject `p_win` / `r_win` / `r_loss`  
12. `_get_option_liq_snapshot` — option spread/depth into quotes  
13. `_evaluate_conviction_and_ev` — Observer `GATE:REGIME` + other hard blocks + conviction + mashed `ev_real`/`ev_r`; write-only `honest_ev` (path 2)  
14. `_apply_regime_boss_hard_block` (`:1292`) — post-conviction RegimeBoss stop (`skip_reason`)  
15. Observer TTL stale-gate (`GATE:REGIME_STALE`, `:5858-5865`)  
16. `SpikeGate.allow` (`:286`) — single-shot fire control  
17. `_build_contract_preview` (`:1850`) — OCC / mid / greeks  
18. `_evaluate_option_microstructure` (`:1956`) — contract quality gate  
19. `_finalize_near_fire_observation_if_pending` (`:1040`) — **skip-only**; `trade_entered=True` drops the pending row  
20. `_build_pos_entry` (`:907`) — open position record (entry mid; copies `p_win` / `r_win` / `r_loss` / `honest_ev` / `g1_direction_state` / `calendar_dte` onto the pos)  
21. Persist `open_positions.json`  
22. `log_trade` → `utils.trade_logger.log_trade` (`:624` / `utils/trade_logger.py:10`) — intent/eval write  
23. `_maybe_eval_exit_overlays` (`:4073`) — exit monitor tick  
24. `data.get_option_quote` — mark mid  
25. `check_exit` (`utils/exit_rules.py:23`) — target/stop/time decision  
26. P&L algebra (`:4267-4268`) — mid-to-mid `pnl_r` (no slip)  
27. `_update_risk_after_trade` (`:2474`) — risk state + `pnl_r` stamp  
28. `log_trade` again — `paper_fill` write (`:2540`)

Any edit to these functions that changes decision behavior is a freeze violation once freeze starts, unless it is the **operator-chosen** EV path (step 13 formula only, friction documented in the same commit) or an additive write-only stamp listed in `baseline_freeze.md`.

---

## Non-hot paths (safe to touch during freeze)

- `Analysis/session_perf_diag.py`, `session_summary.py`, `conviction_slope_tracker.py`, `rr_score_observer.py`, `v2_diag_followon.py`, weekly aggregators  
- `session_close.py` stub/export (unless it starts feeding live gates — it must not)  
- `utils/near_fire_observer.py` and in-trade observation emitters (observe-only)  
- `Launcher/notify.py` / wire notify (display)  
- `docsV2/**`, findings prose  
- Replay / calibration scripts under `Analysis/` that do not mutate live config  
- Tests that assert analysis predicates or an EV unit test for the **chosen** path (tests may tighten; live gate thresholds must not move via test backdoors)  
- `Model_B/model_b.py` / `utils/ev_engine.py` **if left unused by the paper runner** — still flag before “fixing” them into the live path

---

## Config surface (hot path)

Values as of `Launcher/config_mb_v2.0.0.yaml` (2026-08-15 read; YAML values unchanged since 8/12). Changing a **binding** key **during freeze** is a violation. Freeze has not started. YAML is **not** the live config for every row — architecture map Stage 7–12 already flagged DOC/CODE MISMATCH. Keep the YAML values; **binds?** is the identity column.

| Key path | YAML value | Binds? | Controls |
|----------|------------|--------|----------|
| `universe` | SPY,QQQ,AMD,AAPL,NVDA,APP,META,COIN,MSFT | **Yes** | Tickers evaluated |
| `trading_enabled` | `false` | **No** — code sets `trading_enabled = True` at `:4802` | Config flag only; failsafe / sandbox flags in code |
| `ev_filter.enabled` | `true` | **Yes** | EV block section active |
| `ev_filter.min_ev_r` | `0.25` | **No** | Legacy / unused on launcher hard-block (live uses `<= 0`) |
| `ev_filter.default_exit_profile.*` | wr 0.496 / win 1.207 / loss 0.788 | **Yes** (fallback) | Fallback EV priors |
| `conviction.standard` | `0.7835` | **Yes** | Base min conviction |
| `conviction.cannonball` | `0.820` | **Yes** (mode) | Cannonball mode |
| `conviction.session_override` | `null` | **Yes** if set | Session raise/lower |
| `setup_conviction_overrides.*` | Pullback `0.90`, Fade `0.88`, Breakout_MultiDTE `0.77`, Momentum_0DTE `0.80`, Momentum_MultiDTE `0.82`, Reversal_Approaching `0.82`, Reversal_0DTE `0.76`, Reversal_GapDown `0.86`. **Breakout_0DTE not listed** (fallback 0.7835) | **Yes** | Per-setup min conv |
| `near_fire.threshold` | `0.83` | **Yes** (observer) | Observer only |
| `risk.max_trades_per_day` | `3` | **No** | YAML halt threshold. Live cap is `SANDBOX_DAILY_TRADE_CAP=2` (W2 max fills/session = 2). |
| `risk.max_day_loss_r` | `-1.0` | **Yes** | Halt |
| `risk.max_consec_losses` | `3` | **Yes** | Halt |
| `risk.cool_down_minutes_after_loss` | `30` | **Yes** | Post-loss cooldown |
| `exits.stop_rules.hard_drawdown_pct` | `-0.25` | **Yes** | Stop + 1R definition |
| `exits.profit_targets.base_take` | `0.20` | **Yes** | Target (+20% premium). On 1-lot, `scale` is a **full close**. |
| `exits.profit_targets.runner_trail_start` | `1.0` | **Yes** | Trail arm |
| `exits.stop_rules.trail_pct_from_peak` | `0.5` | **Yes** | Trail giveback |
| `exits.time_rules.kill_after_minutes` | `90` | **Yes** | Timeout when contract `dte != 0` |
| `exits.time_rules.kill_after_minutes_0dte` | `40` | **Yes** | Timeout when contract `dte == 0` (not `gate_tier`) |
| `exits.scale_percents` / `iv_halt` / `time_rules.force_flatten_by` | present in YAML | **No** | Dead on live `check_exit` |
| `contracts.max_spread_pct` | `0.015` | **No** | Unused quality target. Live microstructure `MAX_OPTION_SPREAD_PCT=0.05`; conviction `spread_wide` > **0.08**. |
| `contracts.min_open_interest` | `750` | **No** | Unused on the live picker (`_pick_best_from_chain`) |
| `data.source` / `poll_interval` | `alpaca` / `5` | **Yes** | Feed |

Also loaded at runtime (not YAML): `Logs/exit_profiles_v2.json` per-setup `win_rate` / `avg_win_r` / `avg_loss_r`.

YAML `fills.slippage_bps` / `broker.slippage_bps` exist and are **not** on the paper-fill `pnl_r` path (mid-to-mid). Do not read them as live friction.

Code constants that behave like config: `LOOP_SLEEP_SECONDS`, `EXIT_MONITOR_EVERY_N_TICKS`, `ONE_R_PCT`, spike-gate module defaults, `SANDBOX_*` flags in `run_live_paper_full.py` (`SANDBOX_DAILY_TRADE_CAP=2` **binds**).

---

## Known divergences and quirks

1. **Model B / `ev_engine` vs launcher EV** — different formulas; launcher mashed path is freeze-authoritative for paper logs. Honest engines are not imported.  
2. **`min_ev_r: 0.25` unused on live hard-block** — live blocks only `ev_real <= 0`, which cannot bind on mashed 0.82–1.02.  
3. **`GATE:EV_NONPOSITIVE` is silent as skip identity** — 227 code stamps / 0 `skip_reason` in the 20-session window (append order).  
4. **`rr_score` misnamed** — ATR-expansion factor; rename deferred.  
5. **`pretrade_log.jsonl` ≠ trade log** — operator morning journal at repo root; `ev_r` lives on `paper_trades_*.jsonl`.  
6. **`session_perf_diag` does not join pretrade** — fills only (`docsV2/session_perf_diag.md`). Mashed residual is not forecast error.  
7. **`est_slip` on EV, not on `pnl_r`** — live mashed subtracts spread fraction; paper P&L is mid-to-mid. Decay/fee/adv_sel default 0 (inert). Two defects: sign + friction mismatch.  
8. **Targets can hold past timeout if green** — `timed_out` only when `pnl_percent <= 0` (`exit_rules.py:184-185`); explains long winning holds (e.g. NVDA 110m).  
9. **Paper entry uses mid; slippage logger records mid as fill** — observe-only; not in `pnl_r`.  
10. **Near-fire observer is skip-only** — fires that clear 0.83 do not write `near_fire_observation` rows.  
11. **`regime_boss_block_type` lies** — 2.30 classifier; use `skip_reason`.  
12. **2.15 unit trap** — `option_microstructure_spread_pct` fraction vs `option_liq_spread_pct` percent-points. NF stamped `ev` uses `option_spread_pct_at_signal` (percent-points) and is **not** that trap.  
13. **Stub “dominant skip” vs live gate** — `CTX:DAILY_RSI_NOT_EXTREME` is score-only.  
14. **`*_0DTE` setup label ≠ calendar DTE** — 8/13 `Breakout_0DTE` fire was 1 calendar DTE; **8/18 `Momentum_0DTE` fire was 3 calendar DTE** (`calendar_dte=3`, expiry 8/21). Friday-weekly / next-Friday book, not same-day 0DTE. Same honesty class as the tenor triple-split above.  
15. **YAML vs live binding** — `SANDBOX_DAILY_TRADE_CAP=2` binds (W2 max fills/session=2); YAML `max_trades_per_day=3` does not. `trading_enabled: false` vs code `True`. `contracts.max_spread_pct: 0.015` unused; live microstructure `MAX_OPTION_SPREAD_PCT=0.05`; conviction `spread_wide` >0.08. `contracts.min_open_interest: 750` unused on the picker.  
16. **Policy dead outputs** — `policy.decide()` `direction` / `conv_threshold` / `size_cap_mult` are never read; RegimeBoss adaptation is binary allow/block; qty hardcoded 1.  
17. **IV factor is realized-vol proxy** — weight 0.10; not implied vol. Same honesty class as `rr_score`.  
18. **1-lot “scale” collapse** — `base_take` returns `("scale", …)` but qty=1 cannot partial-close; YAML `scale_percents` / `iv_halt` / `force_flatten_by` are dead. `test_exit_rules.py` still describes `trailing_stop` / `iv_collapse` (test drift).  
19. **4.8 ≈ no-op on SPY/QQQ** — inherits `gate_tier`, which is always `0DTE` for those names; scope is `gate_tiers: ["MultiDTE"]`. ~0.1% NF overlap with G1.  
20. **G1-on-fill landed 8/16; confirmed 8/18** — ROI #7 copies `g1_direction_state` onto pos/fill. **8/18 `paper_fill` carries it.** Pre-8/16 historical fills still drop it (join from intent). Architecture previously said “not shipped”; that sentence is stale.

---

## What's NOT in the system

- No real broker execution on this paper path (`trading_enabled` YAML `false`; code failsafe `True`; paper mid marks).  
- No live slippage / fee netting in `pnl_r` (YAML `fills.slippage_bps` / `broker.slippage_bps` are unused here).  
- No dedicated MFE/MAE **fill stamp**. In-trade `max_gain_pct` / `current_pnl_pct` already support derived MFE/MAE (`Analysis/v2_diag_followon.py` panel 1; extraction Q1).  
- No time-exit term in the EV equation (win/loss legs only; timeouts are a third empirical bucket).  
- No option-premium `forward_outcome` — existing checkpoints are underlying price; do not synthesize option R. Observer `honest_ev` is still absent (8/18: 0/31); CC/fill stamps are a different object.  
- No fire rows in the near-fire observer file (skip-only write).  
- No G1 state on **pre-8/16** fill rows (ROI #7 confirmed on 8/18+).  
- No live consumption of `policy.decide()` `direction` / `conv_threshold` / `size_cap_mult`.  
- Replica EOD mom concordance (~83–91%) is **not** a fire directional-accuracy KPI.  
- No automatic unfreeze — freeze-break criteria only trigger review (`baseline_freeze.md`). Freeze has not started.  
- `BrokerAdapter` slippage simulation exists in `utils/broker_adapter.py` but is **not** the paper-fill P&L path used by the exit monitor.
