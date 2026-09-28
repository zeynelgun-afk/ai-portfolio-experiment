# FinZora: Autonomous Multi-Agent Hedge Fund Architecture 🤖📈

**The hypothesis:** Can a portfolio whose decisions are handed entirely to an autonomous Multi-Agent AI system—one that discovers opportunities dynamically, reacts to market shocks in real-time, and aggressively hunts for asymmetric alpha—beat the market over 12 months? 

This repository is not a simple "trading bot". It is an **Event-Driven, Multi-Agent Autonomous Hedge Fund** built on a mixture-of-experts (MoE) architecture. The system discovers its own watchlist, evaluates macro/fundamental/sentiment data, and executes trades with high-conviction sizing, all while operating fully unsupervised via GitHub Actions.

- **Start Date:** 5 August 2026
- **Starting Capital:** $100,000 (Paper trading)
- **Universe:** Dynamic (Technology, AI Infrastructure, Supply-Chain Bottlenecks, Energy)
- **Benchmarks:** SPY & SMH

---

## 🧠 Core Architecture & AI Agents

The system operates on a dual-cadence architecture: **Weekly Strategy Discovery** and **Intraday Event-Driven Execution**. It utilizes multiple LLMs (GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Flash) specializing in different analytical domains.

### 1. The Scout Agent (`scout.py`)
Traditional screeners rely on rigid filters (e.g., Market Cap > $2B). The Scout Agent is a **Dynamic Watchlist Generator** powered by GPT-4o. 
- **Trigger:** Runs every Saturday before the main decision round.
- **Function:** Ingests the top 50 financial news articles and top market gainers via the FMP (Financial Modeling Prep) API.
- **Mandate:** Hunts for "Second-Order Bottlenecks" (e.g., optical interconnects, cooling systems), corporate pivots (e.g., miners becoming AI datacenters), and asymmetric supply/demand shocks. It autonomously generates `watchlist.json` containing 15-20 highly relevant tickers.

### 2. The Multi-Agent Research Team (`weekly_data.py`)
Before the Lead Strategist makes any decision, a team of specialized AI agents analyzes the dynamic watchlist:
- **Macro Strategist (GPT-4o):** Analyzes Federal Funds Rates, 10-Year Treasury Yields, and sector performance to provide a global macroeconomic outlook.
- **Fundamental Analyst (Claude 3.5 Sonnet):** Evaluates P/E ratios, market cap, and corporate insider trading data (CEO/CFO open-market purchases).
- **Sentiment Analyst (Gemini 1.5 Flash):** Evaluates analyst consensus grades, price targets, and recent news headlines.

### 3. The Lead Alpha Strategist (Claude via OpenRouter)
The core decision-maker that executes trades based on the Research Team's dossiers. It is governed by `WEEKLY_INSTRUCTIONS.md`, which enforces the **5 Pillars of Asymmetric Alpha**:
1. **Market Overreaction Divergence:** Buy the dip on retail panic if fundamentals remain intact.
2. **Conviction Sizing (Kelly Criterion):** Allocate up to 40-50% of the portfolio to a single flawless setup rather than equal weighting.
3. **Supply-Chain Sympathy Plays:** Capitalize on downstream beneficiaries before the market prices them in.
4. **Insider Trading Tracking:** Heavily weight open-market corporate insider buying.
5. **Politician/Senate Signals:** Monitor congressional accumulation as a supporting signal.

### 4. Intraday News & Price Detector (`detector.py`)
A deterministic Python state machine that polls the market every 30 minutes. 
- **Price/Volume Shocks:** Checks for standard threshold breaches, utilizing hysteresis and cooldown layers to prevent flapping.
- **News Sentiment Shock (Gemini 1.5 Flash):** Fetches real-time FMP breaking news. If a breaking headline drops, Gemini evaluates if the news *fundamentally contradicts the core thesis*. If YES, it triggers an immediate reassessment (`reassess.py`) causing the system to rewrite the thesis and potentially close the position mid-session, achieving zero-latency risk management.

### 5. The Adversarial Audit Layer (`audit.py` & `reviewers.py`)
A fully automated post-mortem layer. 
- **Dual Auditor Consensus:** Two different model families (e.g., Claude and GPT) independently review the Lead Strategist's past decisions. 
- **Automated Rule Amendment:** If both auditors detect the same reasoning failure three times in a row, `amend.py` automatically drafts a pull request to inject a new behavioral rule into `WEEKLY_INSTRUCTIONS.md`.

---

## ⚙️ System Workflows (GitHub Actions)

The entire hedge fund runs serverless on GitHub Actions.

| Workflow | Schedule | Purpose |
|---|---|---|
| **Intraday Detector** | Every 30 mins (Mon-Fri) | Polls prices and breaking news. If a shock occurs, wakes up the LLM to reassess and trade. |
| **Weekly Round** | Saturday 06:00 UTC | Runs the Scout Agent, Research Team, Audit Layer, and the Lead Strategist for weekly rebalancing. |
| **Pages Deployment** | On Push to Main | Builds and deploys the live `Thesis Watch` React Dashboard to GitHub Pages. |

---

## 📂 Repository Structure

- `scout.py` — The GPT-4o dynamic opportunity and bottleneck discoverer.
- `detector.py` — The 30-min event-driven state machine (Price + News Sentiment Shock).
- `weekly_data.py` — Data aggregation and Multi-Agent Research pre-processing.
- `reassess.py` / `execute_trade.py` — LLM thesis rewriting and deterministic trade arithmetic.
- `portfolio.json` — The single source of truth for all current holdings, cash, and trade history.
- `theses.json` — The measurable, event-driven conditions for every held position.
- `WEEKLY_INSTRUCTIONS.md` — The Alpha Strategist's prompt/constitution.
- `audit.py` & `reviewers.py` — Adversarial decision auditing.
- `dashboard/` — The static site generator for the live portfolio monitoring page.

---

## 🚀 Running the System Locally

```bash
# 1. Scout the market for a dynamic watchlist
python scout.py

# 2. Collect fundamental/macro data and run the Multi-Agent Research Team
python weekly_data.py

# 3. Check for Intraday Price/News Shocks (Dry-run mode)
python detector.py --dry-run

# 4. Generate the Deterministic Audit Scorecard
python audit.py --review
```

> ⚠️ **Disclaimer:** This is a fully autonomous AI experiment. It is not financial advice. The models execute real logical trades based on live market data, but operate on a paper-trading basis.
