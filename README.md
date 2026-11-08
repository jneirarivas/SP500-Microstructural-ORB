# Microstructural Alpha in US Equities: A Quantitative Approach to the Opening Range Breakout

**Author:** Jorge Neira (Independent Quantitative Researcher)

---

## Abstract
This repository contains the foundational quantitative research investigating short-term pricing inefficiencies within the opening auction of United States equity markets. Utilizing a rigorous Walk-Forward Out-Of-Sample (OOS) framework on 1-minute Bid data (2022–2026), this study addresses the vulnerabilities of traditional Opening Range Breakout (ORB) models to high-frequency noise. We introduce an event-driven filtering mechanism incorporating an explicit directional excursion threshold (0.15%) and a strict structural retest tolerance band (± 0.05%). Results indicate robust statistical stability, positive mathematical expectancy across diverse market regimes, and highly constrained tail-risk profiles evaluated via Bootstrap Monte Carlo simulations.

---

## 1. Mathematical Formulation & Ruleset
The algorithmic architecture relies strictly on price topology and explicitly removes standard volumetric or time-series indicators (e.g., VWAP) to prevent geometric overlap. 

* **Topology & Window:** The Opening Range (OR) is established strictly between 09:30:00 and 09:44:59 EST. The operational window to detect institutional impulses and subsequent retests is restricted to 09:45:00 – 13:00:00 EST.
* **Friction Filter (Δ):** A static buffer of 0.25 points is applied to the absolute High and Low of the OR to establish the theoretical breakout threshold.
* **Institutional Retest Filter (Pineda Protocol):** A valid trade is triggered exclusively if the price achieves a minimum directional excursion of 0.15% and subsequently pulls back to the breakout level within a ± 0.05% tolerance. The retest must occur within a 120-minute expiry window.
* **State Locks & Asymmetric Exit Logic:** 
  * Strict session constraint of maximum 1 Long and 1 Short per day to mitigate re-entry bias.
  * Step-Trailing Stop mechanism: Initial stop defined by the opposite OR extreme (1R). The stop advances to Break-Even at +1.0R of favorable excursion, and locks +0.5R when reaching +1.5R.
  * Absolute Take Profit is statically set at +2.0R.

---

## 2. Empirical Results & Walk-Forward Validation
To eliminate data snooping and curve-fitting, parameters were subjected to a strict Walk-Forward optimization protocol, anchoring variables in an In-Sample block (2022–2024) and executing blindly on an Out-Of-Sample sequence (2025–2026). 

**Out-Of-Sample Blind Execution (2025–2026)**
The system demonstrated predictive survival and mathematical robustness without parameter re-calibration in the unseen dataset:
* **Total Trades (N):** 306
* **Win Rate:** 61.76%
* **Cumulative Net Expectancy:** +69.09 R

*(Note: The empirical restriction of the operational window to 13:00 EST successfully neutralized midday mean-reversion noise, elevating the system from a baseline breakeven profile to institutional-grade yield).*

---

## 3. Tail-Risk Analysis (Bootstrap Monte Carlo)
To determine safe capital allocation parameters, a Bootstrap Monte Carlo simulation (5,000 iterations with replacement) was executed over the sequence of 779 verified In-Sample and Out-Of-Sample trades. This evaluates the empirical distribution of maximum peak-to-trough drawdowns given a random future sequence of returns:

- **Dataset Scope:** S&P 500 Index proxy (Executed via MES logic)
- **Timeframe:** In-Sample (2022-2024) | Out-Of-Sample (2025 - Aug 2026)
- **Total Valid Trades:** 779
- **Historical Max Drawdown:** -11.69 R
- **Bootstrap Monte Carlo (95th Percentile MDD):** -14.54 R

**Position Sizing:** Based on the 95th percentile risk, maintaining a global maximum account drawdown below a strict 10% compliance threshold requires a static fractional allocation of 0.25% to 0.40% risk per trade (1R).

---

## 4. Epistemic Scope & Execution Frictions
This repository publishes the mathematical research and exploratory quantitative logic. The execution engine intentionally incorporates synthetic gap-slippage normalizations—where fill prices are penalized on bar open gaps (`Entry Price = max(Open, OR_High + Δ)` for Longs)—to simulate real-world market mechanics. 

*Disclaimer: The proprietary Event-Driven MQL5/C++ architecture required to navigate live Order Book dynamics (Level 2 data), latency arbitrage, and Limit Order fill-rate probability is excluded from this public repository to protect operational edge.*