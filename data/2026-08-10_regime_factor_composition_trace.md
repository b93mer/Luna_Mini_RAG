# Regime factor composition trace

**Date:** 2026-08-10  
**Scope:** Analysis-only code trace. No fire-path / launcher / config changes in this pass.  
**Question:** How is `conviction_detail.factors["regime"]` computed, and does it consume `regime_boss_block_type` or aliases from the 2.30 honesty-gap chain?  
**Refs (block_type consumer truth):** `docs/research/2026-08-08_2_30_block_type_root_cause.md`, `docs/research/2026-08-10_regime_honesty_evidence_scoping.md` (user also cited `docs/findings/` mirrors of those titles).  
**Triage under discussion:** chat / intended path `docs/findings/2026-08-10_regime_labeling_audit_triage.md` (**file not present in repo at write time**).

---

## Verdict

**`conviction_detail.factors["regime"]` is independent-of-block_type.**

It does **not** consume `regime_boss_block_type`, `infer_was_macro_blocked`, `_is_macro_compress_event`, the multidTE→`ticker_disagreement` classifier output, or the 5.7 `macro_compress_pct` alias.

It is a **naming collision** with RegimeBoss: the conviction “regime” factor is the **VolatilityRegimeClassifier / RegimeObserver** stability score driven by **`vwap_dist`**, not the RegimeBoss hard-block / label path.

---

## Code path (producer → stamp → consumer)

### 1. Upstream producer (score definition)

| Item | Location |
|------|----------|
| Classifier | `utils/vol_regime.py` → `VolatilityRegimeClassifier.update` (~L86–131) |
| Stability | `utils/vol_regime.py` → `VolatilityRegimeClassifier._stability` (~L133–138) |
| Observer wrapper | `utils/vol_regime.py` → `RegimeObserver.step` (~L153–177) |
| Config | `config/regime_observer.yaml` (`source_metric: vwap_dist`, window/p95 thresholds, multipliers) |
| Instantiation | `Launcher/run_live_paper_full.py` ~L207–225 |

**Computation:**

1. Input scalar = `vwap_dist` (magnitude via `abs(v)`).
2. Rolling window (`window=90`) → `vol_median`, `vol_p95`.
3. Label from p95 vs compress/expand thresholds + hysteresis → `COMPRESS` / `EXPAND` / `TRANSITION` / `UNKNOWN`.
4. **`regime_stability`** = share of most-common label over `stability_lookback` labels (Counter majority / len).
5. `RegimeObserver.step` returns `regime_stability` (and label / vol_multiplier / drivers).

No RegimeBoss fields; no `block_type`; no skip_reason.

### 2. State stamp (before conviction)

| Item | Location |
|------|----------|
| Throttled step | `Launcher/run_live_paper_full.py` ~L5443–5461 |
| Log stamp | ~L5462–5494 |

When `vwap_dist` is present and throttle allows (`REGIME_UPDATE_INTERVAL_SECONDS = 30`):

```text
regime_payload = regime_observer.step(vwap_dist)
state["regime"] = {
  "label": regime_payload["regime_label"],
  "score": float(regime_payload["regime_stability"]),  # ← purity / stability
  "vol_multiplier": ...,
  "ts": now_ts,
}
log_record["regime_score"] = reg.get("score")
log_record["regime_label"] = reg.get("label")
```

Comment in-code: *“use stability as the [0,1] regime purity score”*.

### 3. Conviction factor entry (the field under audit)

| Item | Location |
|------|----------|
| Function | `Launcher/run_live_paper_full.py` → `_evaluate_conviction_and_ev` |
| Read | ~L2126–2132 |
| Write into factors | hard-block early return ~L2276–2286; normal path ~L2309–2316 |
| Top-level re-stamp | ~L2407 `log_record["regime_score"] = factors.get("regime")` |

```text
regime_score = 0.7  # neutral fallback
regime_state = state.get("regime") or {}
regime_score = float(regime_state.get("score", regime_score))
# else: state.get("regime_score")
…
factors["regime"] = regime_score
→ conviction_detail.factors["regime"]
```

Also used as a **hard block** when `regime_score < 0.70` (~L2225–2226) → reason `"regime"` / `GATE:REGIME`. That gate still uses this same VWAP-stability score, not RegimeBoss `block_type`.

RegimeBoss hard block (`_apply_regime_boss_hard_block`, `_classify_regime_boss_reason`) is a **separate** control path and is what stamps `regime_boss_block_type`.

---

## Input fields consumed

| Input | Role | Classification |
|-------|------|----------------|
| `vwap_dist` | Sole metric into `regime_observer.step` / classifier | **independent-of-block_type** |
| `state["regime"]["score"]` | Cached purity = last `regime_stability` | **independent-of-block_type** |
| `state["regime_score"]` | Fallback if `state["regime"]` not a dict | **independent-of-block_type** |
| Default `0.7` | Neutral if neither present | **independent-of-block_type** |
| Classifier internals: rolling `\|vwap_dist\|`, `vol_p95`, `vol_median`, label history, hysteresis thresholds from `regime_observer.yaml` | Produce `regime_stability` | **independent-of-block_type** |
| `regime_boss_block_type` | Not read on this path | — |
| `infer_was_macro_blocked` / NF snapshot | Not on this path | — |
| `_is_macro_compress_event` / `macro_compress_pct` | Analysis/stub helpers only | — |
| `_classify_regime_boss_reason` / multidTE→disagreement | RegimeBoss write path only | — |

**block_type-adjacent:** none on the regime-factor path. (Adjacent only in the sense that both subsystems share the English word “regime” and both can emit COMPRESS-like vocabulary — different objects.)

---

## Upstream signals (since verdict = independent)

Actual signals behind `factors["regime"]`:

1. **Raw:** `vwap_dist` (distance to VWAP; magnitude used).
2. **Computed metrics:** rolling abs-`vwap_dist` window → median, p95; label sequence → **stability** (majority fraction).
3. **Feature / config:** `config/regime_observer.yaml` thresholds (`compress_p95_max`, `expand_p95_min`, `hysteresis`, `window`, `stability_lookback`, `min_samples`).
4. **Not included:** RegimeBoss macro/ticker labels, `regime_boss_reason`, `skip_reason`, `blocked_by_primary`, vol_cluster / shock features used by RegimeBoss, `block_type`.

Optional side outputs from the same observer (not the conviction factor itself): `regime_label`, `vol_multiplier` / `vol_mult`, ages / stale flags — still from this observer, not from block_type.

---

## Impact on Finding 3.5 disposition

**Does this change Finding 3.5 disposition (HOLD on classifier substrate until honest read-side + observability)?**

**No — HOLD stands.** Finding 3.5 concerns **RegimeBoss** substrate behavior (COMPRESS on high-RV days, POST_SHOCK reachability, vol_cluster on 5m replica, etc.). That substrate is **not** what fills `factors["regime"]`. Independence of the conviction regime factor neither clears nor worsens the RegimeBoss claim; it simply shows the conviction headroom “regime” pole is a **different instrument**.

**Flag for triage update** (do not edit triage in this pass):

- Add an explicit note that slope-tracker factor headroom for **regime** measures **VWAP-stability purity**, not RegimeBoss gate honesty / classifier health.
- Finding 3.2 (“regime last in headroom”) must **not** be used as evidence for or against Finding 3.5.
- Finding 3.1 (block_type honesty) remains relevant to RegimeBoss analytics / consumers, **not** to the numeric composition of `factors["regime"]`.
- Intended triage path `docs/findings/2026-08-10_regime_labeling_audit_triage.md` was **missing** at write time; when that doc is landed or updated, fold the above naming-collision note into §3.2 / §3.5 cross-links.

---

## Verification (this pass)

- Only deliverable added: this note under `docs/scoping/`.
- No edits to `Launcher/`, configs, or other production paths for this task.
- Trace resolved cleanly within the time budget; no incomplete branches left open.

---

*End of trace.*
