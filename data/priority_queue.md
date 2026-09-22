# model_suite — Priority Queue (docsV2)

**Queue of record for the new schema / diagnostic era.**  
Legacy archive: [`docs/priority_queue.md`](../docs/priority_queue.md) (do not extend; provenance only).  
Findings home: [`findingsV2/`](findingsV2/) — session reviews from **2026-08-10** onward.

**Last updated:** 2026-08-25 (session review: convergent no-fire; peak AMD Pullback 0.8926 below 0.90 / above operator 0.86; bind `ticker_compress`. A-IV **reconfirmed** 456/456 CC, fill still N/A. Identity work stays stopped. Formula consult still C. Freeze not started.)

---

## Status legend

| Status | Meaning |
|--------|---------|
| `queued` | Not started / ready when scheduled |
| `in-progress` | Actively being worked |
| `logging` | Log-only / observe mode; accumulating evidence |
| `partially shipped` | Some scope landed; remainder explicit |
| `actionable` | Scope clear; ready for a dedicated Cursor task |
| `blocked` | Waiting on data, decision, or upstream |
| `HOLD` | Intentionally paused with stated reason |
| `approval-gated` | Needs explicit operator chat approval before behavior change |
| `watch` | Passive only; no fix until n/evidence threshold |
| `shipped` | Done — keep only if still load-bearing for a follow-on |

---

## Cutover note (why V2)

Legacy queue mixed shipped archaeology, forever-deferred “next weekend” items, and June observation summaries into one 500+ line living doc. Measurement surface changed ~2026-08-08:

1. NF observer **1.1** + G1 `log_only`
2. Diagnostic predicate honesty (rr / slope / session_summary)
3. Regime block_type **read-side** honesty (write-path still gated)

V2 keeps **active leverage** only. Pruned IDs are listed at the bottom — full notes remain in the legacy file.

---

## Now — active focus

Ordered for operator attention. Identity/honesty absorption sits **ahead** of G1 mining as freeze gates. Detail tables below. Docs absorption is **not** approval to change the picker or `gate_tier`.

1. **V2-EV** — **Path 2 chosen 2026-08-16.** Live `ev_r` stays mashed (`p·W + (1−p)·L − slip`). `honest_ev` is write-only. No profile retune, no `min_ev_r`, no sign-fix. Friction strip not implied. Prefer stamped `honest_ev` on **8/18+** fills (first live print: mashed 1.016 / honest 0.275 / realized −1.023).
2. **V2-EV-AUDIT** — Fill EV-component stamps + CC `atr_15m` + unrounded `est_slip`. **Confirmed 2026-08-18** (QQQ fill + 195/195 CC). Historical 22 / W2-32 fills still need intent join. Stamp task closed; freeze still waits on operator “freeze starts here” + formula consult.
3. **V2-G1-FILL** — Copy G1 onto fills (ROI #7). **Confirmed 2026-08-18** on `paper_fill`. Does not promote enforce. Pre-8/16 fills still drop it.
4. **2.1 / 5.7 tenor identity** — Docs identity stands. Additive `calendar_dte` stamped from `expiry` on intent/fill — **confirmed 8/18 (`3`)**. No picker change. `Momentum_0DTE` fire was 3 calendar DTE.
5. **V2-BIND** — Binding-config / dead-output inventory **landed in architecture**. YAML is not the live config. Do not reopen as a YAML-wiring task.
6. **V2-R1 / 2.30** — RegimeBoss `block_type` honesty (classifier fix still open; read-side evidence live). Gate identity = `skip_reason`. Freeze does **not** wait on the classifier rewrite.
7. **2.37** — **Deferred 2026-08-16** with caveats (see row). Not closed. Phase 3 out.
8. **V2-G1** stays `logging` (no enforce). **V2-CXD** stays in-progress measurement on **8/10+ schema 1.1 only** — do not pool pre/post-8/10 NF `momentum_dir`.
9. **V2-VOL / Finding 3.5** — RegimeBoss substrate HOLD (vol episode evidence); do not conflate with conviction `factors["regime"]`
10. **1.12(b) / 2.40 Ph2** — Halt flatten enforce + risk_guardrails PnL switch (approval-gated)
11. **V2-ID** — Identity / alias ledger is the tracking surface for misnamed tape keys (iv=rv_rank, rr=ATR expansion, mashed `ev_r`, three regime objects, tenor triple-split). Reviews use it; do not rename JSONL keys. [`2026-08-17_identity_blocking_ledger.md`](2026-08-17_identity_blocking_ledger.md)
12. **Two-book / timeout overlay (8/23)** — measurement landed; **operator locked**. Goal book = `index_weekly` (eval/product; **not** a live-path / fire-set edit). `time` is an allowed class — keep `timed_out`; do **not** retune `kill_after_minutes` from n=8. W2: `index_weekly` n=13 WR 61.5% +0.20 R (8/4/1) vs `name_multidte` n=18 WR 33.3% −0.10 R (6/5/7). Overlay n=8, A-TO 8/8, 7/8 in name MultiDTE. Ref: [`findingsV2/2026-08-23_two_book_timeout_census.md`](findingsV2/2026-08-23_two_book_timeout_census.md). Handoff: [`2026-08-23_operator_path_handoff.md`](2026-08-23_operator_path_handoff.md).
13. **8/24 A-IV confirm** — **PASS 2026-08-24.** CC `iv_factor_source` + `iv_rank` 459/459; `factors["iv"]` unchanged; source `realized_vol` 459/459; fill copy N/A; G1 `action_taken=none`. Zero-fill → no G1 census row. Identity work on this sibling **stops**. 8/25 reconfirm 456/456 CC, fill still N/A. Do **not** pass `current_chain_iv`. Do **not** start formula consult. Optional bookmark e.g. `pre-2026-08-24-iv-stamp`. Reviews: [`findingsV2/2026-08-24_session_review.md`](findingsV2/2026-08-24_session_review.md) §8.4, [`findingsV2/2026-08-25_session_review.md`](findingsV2/2026-08-25_session_review.md) §8.4.

---

## Tier A — Honesty & observability (load-bearing)

| ID | Item | Status | Queued | Notes / refs |
|----|------|--------|-------|--------------|
| **V2-R1** / **2.30** | Stale `regime_boss_block_type` classifier | `actionable` (fix) / read-side `shipped` | 2026-06-17 / research 2026-08-08 | Root cause locked: `"compress" in reason` wins before ticker check; multidTE→`ticker_disagreement` mis-map. **Read-side shipped** (`utils/regime_honesty.py` → session_summary S5b + stub). **Do not** treat `block_type` as gate identity until classifier ships. Launcher write-path honesty stamps remain **approval-gated**. Freeze does **not** wait on the classifier rewrite — `skip_reason` is freeze gate identity. Refs: `docs/research/2026-08-08_2_30_block_type_root_cause.md`, `docs/research/2026-08-10_regime_honesty_evidence_scoping.md`. |
| **V2-G1** | G1 hard-gate as observability (log_only) | `logging` | 2026-08-09 | Shipped: NF mom parity + `g1_direction_state` on NF + paper_trades; summary/stub rollups. **Enforce = out of scope.** **8/10–8/21 fire census (D):** n=5, all PUT, 5/5 intent G1, `action_taken=none`. Buckets: pass_won 3 / block_won 1 (8/13 QQQ misaligned TP +0.83) / pass_lost 1 (8/18 QQQ stop −1.02). Enforce-strict would **drop the winner and keep the loser** (live +2.355 R vs +1.526 R). The two messy cells are `gate_tier=0DTE` QQQ — 4.8 does not see them. n=5 descriptive; not a promote. Ref: [`findingsV2/2026-08-22_g1_direction_census.md`](findingsV2/2026-08-22_g1_direction_census.md). Fill copy **confirmed 8/18** — see **V2-G1-FILL**. |
| **V2-G1-FILL** | Copy G1 onto fills (ROI #7) | `shipped` (confirmed 8/18) | 2026-08-09 / land 2026-08-16 / confirm 2026-08-18 | Write-only copy of `g1_direction_state` onto pos/fill. **8/18 `paper_fill` carries full G1** (`would_pass_strict=true`, `action_taken=none`). No `skip_reason` / enforce. Historical pre-8/16 fills still drop it. Do not bundle with apply-scoping or G1 enforce. |
| **V2-CXD** | Conviction precision × direction commit | `in-progress` | 2026-08-09 | Live-evidence question: when mom≠0, does high conviction rank direction-correct setups? Precision > coverage. NF frame (Jun 16–Aug 7, +60m underlying): C1 **57.9%** vs misaligned **39.9%**. **8/10–8/21 fires do not answer it:** only 8/10 NVDA conv 0.8486 is ≥0.83; the other four fires are 0.79–0.81. Keep mining strict-NF × G1 on **schema 1.1 (8/10+) only**. Do **not** pool pre/post-8/10 NF `momentum_dir`. Replica EOD mom ~83–91% is **not** a fire KPI. Fire-set census: [`findingsV2/2026-08-22_g1_direction_census.md`](findingsV2/2026-08-22_g1_direction_census.md). |
| **2.37** | Gate-correctness (multidTE / ticker_compress) Phase 2 | `deferred` (caveats) | 2026-06-23 / defer 2026-08-16 | **Not closed.** Operator deferred 2026-08-16. Unlocked: direction tables / shock bins / composition end-date. Phase 3 / gate behavior **out**. Do **not** claim gate-correctness finished. Reopen only on Window 2 **7/02–8/14** (or frozen 7/02+ tape). 8/14 extraction stands as characterization: n=678 skip-only observer; honest-EV>0 excluding Pullback n=250; RegimeBoss **172 (68.8%)**. Pullback 428/678 at honest **−0.27**. No gate change. Ref: `docs/research/2026-08-08_gate_correctness_measurement_brief.md`. Couples **4.13**. |
| **V2-BIND** | Binding-config / dead-output inventory | `shipped` (docs 2026-08-15) | 2026-08-15 | YAML is not the live config (architecture map Stage 7–12 DOC/CODE MISMATCH). Binding: `SANDBOX_DAILY_TRADE_CAP=2` (W2 max fills/session=2); live spread `MAX_OPTION_SPREAD_PCT=0.05` + conviction `spread_wide` >0.08. Unused YAML: `max_trades_per_day=3`, `trading_enabled: false`, `contracts.max_spread_pct=0.015`, `contracts.min_open_interest=750`, `scale_percents` / `iv_halt` / `force_flatten_by`. `policy.decide()` `direction` / `conv_threshold` / `size_cap_mult` are dead; qty hardcoded 1. IV factor is realized-vol proxy (weight 0.10). 1-lot `scale` is a full close. `test_exit_rules.py` still describes `trailing_stop` / `iv_collapse` (test drift; do not fix in this pass). Inventory lives in [`system_architecture.md`](system_architecture.md) config table. **No YAML/launcher edit.** Do not reopen as a wiring task. Ref: `docs/research/2026-08-09_model_b_architecture_map_vol_research.md`. |
| **V2-VOL** / Finding 3.5 | RegimeBoss substrate (vol / COMPRESS / POST_SHOCK) | `HOLD` | 2026-08-09 | HOLD until honest read-side + observability mature. Vol episode v2 + replica arms done as research. **Naming collision:** conviction `factors["regime"]` is VWAP-stability purity (`RegimeObserver`), **not** RegimeBoss — see `docs/scoping/2026-08-10_regime_factor_composition_trace.md`. |
| **V2-EV** | Live EV formula identity (mashed vs honest) | `logging` (path 2) | 2026-08-14 / chosen 2026-08-16 | **Path 2 chosen 2026-08-16 (operator chat).** Live `_evaluate_conviction_and_ev` stays mashed `p·W + (1−p)·L − slip`; `honest_ev` write-only gross `p·W − (1−p)·\|L\|`; `ev_formula_path=2_dual_write_honest_observe`. Gate `ev_real <= 0` still mashed (inert on the 22-fill set; 8/18 mashed 1.016 also cannot bind). Identity lock unchanged on the Q1 window: mean stamped EV **+0.952R** vs realized **+0.167R**. **8/18 first stamped fill:** mashed **1.016** / honest **0.275** / realized **−1.023** (Momentum_0DTE provisional prior; honest residual +1.30 R — Stage 1 class, not a new formula). Do **not** retune `exit_profiles_v2.json`. Do **not** enable `min_ev_r`. Do **not** treat mashed residual as forecast error. Friction strip is a **second** decision, not implied. Prefer stamped `honest_ev` on 8/18+ fills. Refs: [`baseline_freeze.md`](baseline_freeze.md), [`findingsV2/2026-08-18_session_review.md`](findingsV2/2026-08-18_session_review.md) §3.3. |
| **V2-EV-AUDIT** | Fill + CC audit stamps | `shipped` (confirmed 8/18) | 2026-08-14 / land 2026-08-16 / confirm 2026-08-18 | **PASS on 2026-08-18:** fill `p_win`/`r_win`/`r_loss`/`ev_profile_*`/`est_slip`/`honest_ev`; CC `atr_15m`/`atr_baseline_15m`/`atr_baseline_id`/uncapped `atr_ratio` **195/195**. Historical 22 fills still lack these — join intent for that window. Stamp task closed. Freeze start is a separate operator act. Sibling: **V2-G1-FILL**. |
| **V2-EV-RANK** | Population B honest-EV ranking | `blocked` | 2026-08-14 | Scorecard Q3 ranking test needs option-premium forward outcome on skipped strict-NF. **Skip-only is intentional** (8/18 fire also `near_fire=false`; conv 0.8126 < 0.83 so it would not have emitted anyway). **8/18 does not unblock:** observer `honest_ev` **0/31** (schema still stamps mashed `ev` only); `forward_outcome` is still `underlying_price` at 30/60/120. CC `honest_ev` 195/195 is a fill/CC stamp, not an option-R label. Do **not** synthesize option R from underlying. Reopen only with file-direct 1-minute option bars **or** an approved additive option-premium stamp. A fire-linked observer row would also be write-path / approval-adjacent. Ref: [`2026-08-14_ev_rr_log_diagnostic_extraction.md`](2026-08-14_ev_rr_log_diagnostic_extraction.md), [`findingsV2/2026-08-18_session_review.md`](findingsV2/2026-08-18_session_review.md) §8.3. |
| **V2-DIAG** | Diagnostic tooling honesty + follow-on panels | `shipped` (baseline 8/09 + follow-on 8/18) | 2026-08-09 / panels 2026-08-18 | Fixes 1–6 landed 8/09. Follow-on shipped in `Analysis/v2_diag_followon.py` (analysis-only): in-trade MFE/MAE × exit class; timeout 10-min grid; NF honest EV × setup × skip_reason (skip-only, **not** a 5-min fired/blocked split); `atr_15m` on fire-family NF only; `iv_rank_used` histogram (rv_rank; tape key kept — **not** an `iv_factor_source` launcher stamp). Forward-outcome ranking panel **still dropped until V2-EV-RANK unblocks**. Alias/column identity lives in **V2-ID**. Usage: `python Analysis/v2_diag_followon.py` / `--w2`. Tests: `tests/test_v2_diag_followon.py`. |
| **V2-ID** | Identity / alias ledger (tape → honest) | `active` (docs 2026-08-17; A-IV sibling **confirmed 2026-08-24**) | 2026-08-17 | Tracking surface for misnamed live fields and layer blocking. **Keep tape names.** Reviews paste the header from [`2026-08-17_identity_blocking_ledger.md`](2026-08-17_identity_blocking_ledger.md). L1 labels / L2 binding / L3 formula / L4 population sit in front of L5 measurement and L6 live closes. Do **not** rename `iv` / `rr_score` / `ev_r`. Write-only `iv_factor_source` + raw `iv_rank` on CC/eval + fill copy **landed 2026-08-22** (`4624807`), **confirmed 2026-08-24** on CC 459/459 (`realized_vol`; fill N/A), **reconfirmed 2026-08-25** on CC 456/456. Identity work on this sibling **stops**. Do **not** pass `current_chain_iv`. |

---

## Tier B — Plumbing still worth finishing

| ID | Item | Status | Queued | Notes |
|----|------|--------|-------|-------|
| **2.1** / **5.7** | Near-fire / compress naming cluster (residual) + tenor freeze identity | `partially shipped` (calendar_dte confirmed 8/18) | 2026-06 / stamp 2026-08-16 / confirm 2026-08-18 | Recurrence evidence is thick; residual analysis-side naming remains. **Tenor is three objects:** setup family, `gate_tier`, contract DTE. Additive `calendar_dte` stamped from `expiry` on intent/fill — **8/18 QQQ fire `calendar_dte=3`** (label `Momentum_0DTE`, expiry 8/21). Docs-only for picker — **no picker change**. Window 2 `Breakout_0DTE` is a Friday-weekly book; 8/18 is post-W2. |
| **2.15** | `option_microstructure_spread_pct` unit-trap in NF fallback | `queued` | 2026-06-09 | Fraction vs percent-points sequential fallback (~100× under-report). Fix crosses observability-only line → approval if behavior changes. Surfaced again 8/02 pre-Bundle-A. **8/13 fire intent:** `option_microstructure_spread_pct=0.007752` next to `option_liq_spread_pct=0.775`. **8/18 fire intent:** `0.009009` next to `0.901` (stub/slippage used 0.901). Recurrence on two fill rows; still no fix this cycle. **8/14 NF lock:** stamped observer `ev` matches mashed − `spread/100` (spread = `option_spread_pct_at_signal`, percent-points) at max \|err\| 4.97e-6 — that path is **not** the unit trap. Do not “fix” NF `spread` as if it were `option_microstructure_spread_pct`. |
| **2.10** | `stale_greeks` intermittent recurrence | `watch` | 2026-06-06 | Gate stays; do not relax. Intermittent high-conv 0DTE clusters (7/10, 7/17). Characterization only until mechanism doc. |
| **2.40** | risk_guardrails PnL predicate split Phase 2 | `partially shipped` / `approval-gated` | 2026-06-24 | Ph1 diagnostic shipped; n≥3 halt-then-fill characterized. Ph2 = switch call sites to deduped PnL — **explicit operator approval**. |
| **2.41** | Per-setup fire threshold vs slope single-threshold | `queued` | 2026-06-26 | Slope gap KPI now prefers `min_required` (V2-DIAG fix 3) — reduces tool distortion. Phase 1 descriptive report still useful for operator framing; no threshold rewrite without measurement. **8/13:** two Pullback P3 rows at 0.83–0.84 stamped `low_conviction` (Pullback override 0.90); `Breakout_0DTE` fire used fallback 0.7835 (setup not in overrides). **8/14 window:** 162/675 blocked strict-NF skip `low_conviction`; 150 of those are Pullback (conv ≥ 0.83 but below 0.90). **8/18:** 13/31 P3 `low_conviction` (Pullback 12 / Fade 1); fire used Momentum_0DTE override **0.80** (0.8126). Characterization only — do not move the Pullback override off this. |
| **2.49** | Terzetto null-coercion on agreement flags | `queued` | 2026-07-12 | `None` coerced to DIVERGENCE. Export data-quality; path choice at authorship (three-state vs bool). |
| **2.2** | Multi-fire TERZETTO collapse / fire_divergence boolean | `queued` | 2026-06-05 | Still real on multi-fire days; pairs with 2.35 Ph2 (journal/export collapse to `fires[0]`). Lower urgency than honesty/G1. |
| **2.35** Ph2 | Multi-fire stub / TERZETTO export schema | `queued` | 2026-06-22 | Ph1 substrate dual_rsi shipped + forward-validated. Ph2 = multi-fire export; sequence with 2.2. |
| **2.7.tier2_key_parity_redesign** | Tier2 key-parity test redesign | `queued` | 2026-08-03 | Post-2.46 invariance assertion is degenerate. Small test fix. |
| **2.7.suite_failures_triage** | Waived suite failures triage | `queued` | 2026-08-03 | 3 failures + 1 error waived under stash-baseline; triage individually. |
| **2.16** residual | Notify labeling / first-tick / tee siblings | `partially shipped` | 2026-06-09 | Delivery works; (c) tee for regime shipped 8/03. Remaining: MACRO title mislabel, boot UNKNOWN→X, intent/near_fire tee siblings, first-tick investigation. P3 polish — batch when touching `notify.py`. |
| **2.43** residual | Intent-status filter siblings + writer convergence | `partially shipped` | 2026-07-06 | Bundle C filter shipped; test-loader siblings + systemic writer/reader unify still open. Defensive-only today (`SANDBOX_INTENT_ONLY=False`). |

---

## Tier C — Risk / exit (approval-gated)

| ID | Item | Status | Notes |
|----|------|--------|-------|
| **1.12(b)** | `flatten_on_halt_mode` → `enforce` | `approval-gated` | Data gate cleared (n≥3 dual-position log_only). Cap (a) closed as noise-not-mechanism at n=5. **8/18:** `halt_flatten_observation` `would_flatten=true` / `mode=log_only` at 12:13:33 on the QQQ position the `hard_stop` closed 10 s later; halt reason `max_day_loss_r`. Afternoon is `skip_risk` (new-entry stop). **No promote without literal chat approval.** |
| **1.13** | Entry-conditional hard stop | `approval-gated` | Per-position `hard_drawdown_pct` at intent. Distinct from 1.16. **8/14 in-trade (n=4 stops):** not one regime (fast 13 min / mid 22 / drift 63 and 85). **8/18:** fifth stop, peak-then-bleed into −25% at 68.7 min (peak +12% at 5.45 min). n=5 — no promote. |
| **1.16** | Model B dynamic stop → live paper | `approval-gated` | Trailing floor; coordinate timing with 1.13; do not bundle. Timeout overlay **n=8** (2026-08-23): 7/8 in `name_multidte`, 1/8 index weekly (7/27 SPY); 7/8 ever-green then giveback; A-TO 8/8 `pnl_r<=0`. **Operator (8/23): `time` is an allowed class** — keep `timed_out`; 40 vs 90 still A-DTE. Descriptive only; do **not** retune `kill_after_minutes` from n=8. Ref: [`findingsV2/2026-08-23_two_book_timeout_census.md`](findingsV2/2026-08-23_two_book_timeout_census.md). |
| **1.5** | direction_validation promote off log_only | `logging` / `blocked` | Hold enforce per 6/13 economics; G1 is the active direction substrate now — do not promote 1.5 as a substitute for G1 evidence. |
| **4.8** | Direction-validity 0DTE expansion | `partially shipped` | MultiDTE v1 shipped; 0DTE deferred. Live fire-path direction gate today = 4.8 TRENDING × MultiDTE only — near-no-op on SPY/QQQ (`gate_tier` always `0DTE` for those names); ~0.1% NF overlap with G1. Revisit only after G1 / CXD evidence. **Do not promote 0DTE expansion as a freeze prerequisite.** |

---

## Tier D — Process (V2)

| ID | Item | Status | Notes |
|----|------|--------|-------|
| **5.8** | Data-first weekly / session review | `active` | Start from logs + V2 predicate contract, not memory. |
| **5.9** | Queue catch-up ≤24h | `active` | Drafted V2 queue updates land or note “deferred — reason.” |
| **5.10** | Characterize blockers on high-conv (≥0.83) subset | `active` | Strict NF / observer JSONL primary; session-wide skip mass is supporting context. **8/14:** n=678 observer rows, all skip-stamped **by design** (fires do not emit observer rows). Pooled skip: regime_boss 450 / low_conviction 162 / spike 41 / microstructure 16 / sandbox 6. Honest>0 excluding Pullback: **n=250 on all observer** (678−428), **n=249 on population B** (675−426); RegimeBoss 68.8% of the 250. **8/18 P3 n=31:** ticker_compress 17 / low_conviction 13 / multidTE 1. Observer file does **not** contain fire rows (8/18 fire 0.8126 < 0.83 anyway). |
| **5.11** | Deferred-fix recurring-trigger tripwire | `active` | Holiday / expiry-cycle deferrals need a named next-trigger check. |
| **V2-HOME** | Keep findings in `findingsV2/` from 2026-08-10 | `active` | Session reviews stay in `findingsV2/`. EV/rr calibration notes live at `docsV2/` root (scorecard, investigation pass, log extraction). Do not dump new session reviews into `docs/findings/`. Last pre-V2 review is 8/07. |

---

## Approval-gated footer

Do **not** ship without explicit operator approval (chat message):

- 1.12(b) halt flatten `enforce`
- 1.13 / 1.16 stop behavior
- 2.30 classifier rewrite / overwrite of `regime_boss_block_type`
- Regime honesty **write-path** stamps on live JSONL
- G1 (or any direction gate) **enforce**
- 4.8 0DTE expansion (`gate_tiers` beyond `["MultiDTE"]`)
- 2.40 Phase 2 PnL call-site switch
- 2.15 unit conversion if it changes scored near-fire values
- Live EV formula sign-fix, or wiring `min_ev_r` onto the launcher path. **Dual-write `honest_ev` approved 2026-08-16 (path 2)** — mashed `ev_r` must remain the live scalar.
- `exit_profiles_v2.json` prior rewrite / provisional replacement (Breakout_MultiDTE 12/20 closes this window; others 0–3; threshold is 20)
- `_ATR_BASELINE_15M` recalibration (changes conviction; NF atr subset ≠ CC inferred-stale)
- Picker / `gate_tier` heuristic change — **docs absorption is not approval** to change who 4.8 / compress apply to, or to add daily 0DTE selection

---

## Parked / pruned from V2 (legacy only)

These stayed in [`docs/priority_queue.md`](../docs/priority_queue.md). Not deleted — **not active**. Re-open only with fresh evidence + a V2 row.

| Bucket | Examples | Why pruned |
|--------|----------|------------|
| Shipped complete | 1.2, 1.8, 1.9/b, 1.11, 1.14, 1.17, 2.6, 2.17–2.19, 2.21, 2.23–2.24, 2.27, 2.29, 2.35 Ph1, 2.39, 2.46, 4.14, … | Done; no open leverage |
| Deferred “next weekend” for weeks | DualRSI cluster **1.4 / 1.10 / 1.18**, **1.3**, **1.1**/4.4 VWAP path | Never revisited as active sprint; reopen only if promotion decision returns |
| One-off / n=1 never revisited | **2.48** shock_mag 6.4642, **2.11** AMD 11:45 drag, **2.14** late META/MSFT shock | Below promotion threshold |
| Stale pattern monitors | **2.34 / 2.36** AMD open-drive, **2.38** Reversal_Approaching (held), **2.42** spike clustering | No recent instances / sample not refreshing |
| Closed observations | **2.44** halt-boundary freeze | Characterized; consumers cross-check |
| Spec-scoping without authorship | **2.45** +1-bar counterfactual, **2.47** journal post-stop underlying | Authorship never scheduled |
| Tier 3 code-review sediment | **3.1–3.3** | Queued 6/5; untouched |
| Worldview backlog | **4.1, 4.3–4.7, 4.9–4.12** | Explicitly “don’t force on low-energy days”; not current track |
| Process docs never written | **5.1–5.6** | Optional; V2 README + this file cover ops split |
| June–July observation week tables / sprint boards / patch footers | Legacy §§ | Archaeology — not a work queue |

---

## Refs (Aug 8–10 spine)

| Topic | Path |
|-------|------|
| block_type root cause | `docs/research/2026-08-08_2_30_block_type_root_cause.md` |
| Substrate honesty brief | `docs/research/2026-08-08_substrate_honesty_investigation_brief.md` |
| Gate-correctness measurement | `docs/research/2026-08-08_gate_correctness_measurement_brief.md` |
| Regime honesty scoping | `docs/research/2026-08-10_regime_honesty_evidence_scoping.md` |
| Regime factor ≠ RegimeBoss | `docs/scoping/2026-08-10_regime_factor_composition_trace.md` |
| G1 log_only ship | `docs/findings/2026-08-09_g1_observability_log_only.md` |
| G1 apply-scoping (open) | `docs/research/2026-08-09_g1_apply_scoping_handoff.md` |
| G1 hard-gate deeper (do not apply) | `docs/research/2026-08-09_g1_hard_gate_deeper.md` |
| CXD commit findings | `docs/findings/2026-08-09_conviction_x_direction_commit.md` |
| Diagnostic fixes 1–6 | `docs/findings/2026-08-09_diagnostic_tools_audit_fixes.md` |
| Conviction × direction handoff | `docs/research/2026-08-09_conviction_x_direction_commit_handoff.md` |
| Vol / architecture map (Stage 7–12 DOC/CODE MISMATCH) | `docs/research/2026-08-09_model_b_architecture_map_vol_research.md` |
| 8/13 session (G1 would-block fill) | `docsV2/findingsV2/2026-08-13_session_review.md` |
| 8/18 session (Rank-1 stamp PASS; G1-pass hard_stop) | `docsV2/findingsV2/2026-08-18_session_review.md` |
| 8/22 G1 fire census (D; n=5; not a promote) | `docsV2/findingsV2/2026-08-22_g1_direction_census.md` |
| 8/23 two-book + timeout overlay (goal = `index_weekly`; `time` allowed) | [`findingsV2/2026-08-23_two_book_timeout_census.md`](findingsV2/2026-08-23_two_book_timeout_census.md) |
| 8/23 operator-path handoff (do not reopen freeze / GMM / chain IV) | [`2026-08-23_operator_path_handoff.md`](2026-08-23_operator_path_handoff.md) |
| 8/24 session review (convergent no-fire; A-IV sibling PASS) | [`findingsV2/2026-08-24_session_review.md`](findingsV2/2026-08-24_session_review.md) |
| 8/25 session review (convergent no-fire; A-IV reconfirm; fill N/A) | [`findingsV2/2026-08-25_session_review.md`](findingsV2/2026-08-25_session_review.md) |
| EV/rr calibration scorecard | [`2026-08-13_ev_rr_calibration_scorecard.md`](2026-08-13_ev_rr_calibration_scorecard.md) |
| EV identity lock (Q0–Q6) | [`2026-08-14_ev_rr_investigation_pass.md`](2026-08-14_ev_rr_investigation_pass.md) |
| EV log extraction (MFE/MAE, NF honest EV, Q4 blocked) | [`2026-08-14_ev_rr_log_diagnostic_extraction.md`](2026-08-14_ev_rr_log_diagnostic_extraction.md) |
| Baseline freeze contract | [`baseline_freeze.md`](baseline_freeze.md) |
| System architecture (current map; 2026-08-15 post-critique absorption) | [`system_architecture.md`](system_architecture.md) |
| Window 1 vs 2 decision-path split | [`2026-08-15_baseline_windows_handoff.md`](2026-08-15_baseline_windows_handoff.md) |
| GMM / baseline-trajectory mapping | [`2026-08-16_gmm_trajectory_mapping.md`](2026-08-16_gmm_trajectory_mapping.md) |
| GMM benefits / why-mixture / A-B-C blockers | [`2026-08-18_gmm_benefits_and_blockers.md`](2026-08-18_gmm_benefits_and_blockers.md) |
| GMM implementation companion (EM-MLE / spline / scorer) | [`2026-08-20_gmm_implementation_companion.md`](2026-08-20_gmm_implementation_companion.md) |
| sympy-mcp L3 formula calibration (CAS witness; not a calibrator) | [`2026-08-22_sympy_mcp_formula_calibration.md`](2026-08-22_sympy_mcp_formula_calibration.md) |
| Hot-path inventory (live / observe / dead) | [`2026-08-17_hot_path_inventory.md`](2026-08-17_hot_path_inventory.md) |
| Highest-ROI gap closures | [`2026-08-17_highest_roi_gap_closures.md`](2026-08-17_highest_roi_gap_closures.md) |
| Identity / alias ledger + layer blocking (V2-ID) | [`2026-08-17_identity_blocking_ledger.md`](2026-08-17_identity_blocking_ledger.md) |
| V2-DIAG follow-on CLI | `Analysis/v2_diag_followon.py` |

---

*End of docsV2 priority queue.*
