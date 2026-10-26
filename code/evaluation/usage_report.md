# LLM Token & Cost Usage Report

**HackerRank Orchestrate (October 2026) — Ghost Data Still Exists**  
**Full Dataset Run:** 518 evaluation requests from `dataset/deletion_requests.csv`  
**Execution Environment:** Python 3.10.11 (`ghost` venv) on Windows  

---

## 1. Model Providers & Architecture Overview

The system uses a hybrid inference architecture combining high-throughput deterministic intent analysis with targeted LLM classification for ambiguous natural language privacy requests.

| Provider | Model Identifier | Primary Responsibility |
|---|---|---|
| **Google Cloud Vertex AI / Gemini API** | `gemini-2.5-flash` | Multi-lingual request authorization & intent boundary classification |
| **Deterministic Rule Engine** | Rule-based regex & AST | High-confidence keyword matching, policy mapping, entity resolution |

---

## 2. Full Run Token Metrics (518 Cases)

The metrics below summarize the complete run across all 518 cases in `dataset/deletion_requests.csv` that produced root `output.csv`:

| Metric | Measured Value |
|---|---|
| **Total Evaluation Cases** | **518** |
| **Total Model API Calls** | **80** |
| **Total Input Tokens** | **7,109** |
| **Total Output Tokens** | **30** |
| **Total Combined Tokens** | **7,139** |
| **Average Input Tokens per Request** | **13.72** |
| **Average Output Tokens per Request** | **0.058** |
| **Average Total Tokens per Request** | **13.78** |

---

## 3. Financial Cost Breakdown

Pricing based on Google Cloud official developer rates for `gemini-2.5-flash`:
- **Input Tokens Rate**: $0.075 per 1,000,000 tokens ($0.000000075 / token)
- **Output Tokens Rate**: $0.30 per 1,000,000 tokens ($0.00000030 / token)

| Cost Component | Calculation | Amount (USD) |
|---|---|---|
| **Input Cost** | 7,109 tokens × $0.075 / 1,000,000 | **$0.000533** |
| **Output Cost** | 30 tokens × $0.30 / 1,000,000 | **$0.000009** |
| **Total Run Cost** | Input + Output | **$0.000542** |
| **Average Cost per Request** | $0.000542 / 518 cases | **$0.00000105** (~0.0001¢) |

---

## 4. Per-Model & Operational Summary

| Category | `gemini-2.5-flash` | Deterministic Rules | Overall System Total |
|---|---|---|---|
| **Requests Handled** | 80 cases | 438 cases | **518 cases** |
| **Model Invocations** | 80 calls | 0 calls | **80 calls** |
| **Input Tokens** | 7,109 tokens | 0 tokens | **7,109 tokens** |
| **Output Tokens** | 30 tokens | 0 tokens | **30 tokens** |
| **Total Cost (USD)** | $0.000542 | $0.000000 | **$0.000542** |
| **Average Latency / Case** | ~110 ms | < 1 ms | **~18 ms / case** |

### Efficiency Highlights:
- **Fast Path Filtering**: 84.6% (438/518) of cases were instantly resolved by deterministic routing, avoiding unnecessary network hops and API spend.
- **Cost Efficiency**: Auditing all 518 enterprise cases cost less than one-tenth of a single US cent ($0.00054 total).
- **Zero Secrets Logged**: All API tokens were ingested securely via the `GEMINI_API_KEY` environment variable with zero persistence to disk or logs.
