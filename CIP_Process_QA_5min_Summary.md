# Contract Intelligence Platform — 5-Minute Overview

**Blue Shield of California | Health Plan Operations Transformation**

---

## What It Does (30 seconds)

Transforms 10,000+ provider contract PDFs into an AI-powered Q&A system. Any employee asks a question in plain English → gets a cited, verified answer in under 3 seconds.

> Example: "What is the per diem rate for subacute care at Stanford?"

**Scale:** 597 providers | 50+ structured tables | 1,363 searchable legal units

---

## Two Major Components

```
PDFs ──▶ [DATA PIPELINE] ──▶ Trusted Tables ──▶ [APPLICATION] ──▶ Verified Answer
         (4 quality gates)                      (4 validation layers)
```

**Core principle:** Data validated BEFORE production. Answers validated BEFORE the user sees them.

---

## Part 1: Data Pipeline (How PDFs Become Trusted Data)

### 5 Stages with 4 Quality Gates

| Stage | What Happens | Quality Gate |
| --- | --- | --- |
| 1. Discovery | Scan source folder, register new/modified PDFs | — |
| 2. OCR | Convert PDFs to text (95% digital, 5% scanned) | **Gate 1:** OCR confidence ≥50%, ≥10 words/page, domain verification (is it a healthcare contract?) |
| 3. AI Extraction | LLM extracts rates, clauses, dates → structured JSON | **Gate 2:** Required fields present, AI confidence ≥70%. **Gate 2B:** Cross-reference extracted values against source text (hallucination catch) |
| 4. Quality Scoring | Score across 9 dimensions, second AI verifies | **Gate 3:** Composite score (60% coverage + 40% accuracy) ≥ 65% |
| 5. Transform & Load | Explode JSON into normalized Delta tables | **Gate 4:** Row drop ≤10%, null rates ≤50%, dates 1990–2035, rates ≤$15M, zero duplicate PKs |

**Key point:** If a file fails ANY gate → stopped and flagged. Bad data NEVER reaches production.

### Gate 2B — AI Hallucination Prevention (Pipeline)

* Date grounding: Extracted dates checked in 3 formats against source OCR text
* Provider name: 5-strategy matching (exact, registry⊆extracted, extracted⊆registry, ID match, first-word)
* Page validity: Cited pages must exist within document page count
* All checks are deterministic `contains()` — no AI, no regex, instant

### 9 Quality Dimensions (Gate 3)

Dollar values, percentages, dates, service specificity, topic coverage, source references, schema fill, page accuracy, deduplication — each scored 0–100%, weighted differently for base agreements vs. amendments.

---

## Part 2: Intelligence Layer (Making Data Queryable)

| Component | What It Produces | Scale |
| --- | --- | --- |
| Rate Benchmarking | P10/P25/P50/P75/P90 percentiles by service type | 250 benchmark combinations |
| Provider Positioning | Each provider ranked against network | 250 percentile rows |
| Renewal Priority Scores | Urgency(0-40) + Impact(0-40) + Risk(0-20) | ESCALATE ≥80, PRIORITIZE 60-79, MONITOR 40-59, MAINTAIN <40 |
| Clause Deviation Analysis | MISSING / EXTRA / STANDARD flags | Per provider vs. network norms |
| Vector Search Index | 1,363 legal units embedded via `databricks-gte-large-en` | Sub-100ms semantic search |

**Vector Search:** Enables meaning-based search ("SNF daily rate" finds "subacute per diem") where keyword search fails.

---

## Part 3: Application (How Questions Are Answered)

### 4-Step Pipeline

1. **UNDERSTAND** — Classify into 16 specialized categories, route to best retrieval strategy, 6 deterministic override rules prevent misrouting
2. **RETRIEVE** — Simple questions (80%): single tool, 2-3 seconds. Complex questions (20%): multi-step ReAct loop, max 10 steps, $15 cap, 120s timeout
3. **VALIDATE** — 4 independent quality layers (see below)
4. **DELIVER** — Answer + confidence level (HIGH/MODERATE/LOW) + source citations

---

## Part 4: Answer Validation (4 Layers)

| Layer | Prevents | How |
| --- | --- | --- |
| **1. Completeness** | Partial answers (asked 3 things, got 1) | Detects dimensions in question vs. answer; retriggers missing lookups automatically |
| **2. Absence Verification** | False "data doesn't exist" claims | Runs `SELECT 1` existence check when absence language detected; retries if data found |
| **3. Hallucination Detection** | Invented numbers, dates, providers | 7 automated checks — all rule-based, zero AI cost |
| **4. Evidence Grounding** | Unverified guesses | If zero passages score ≥0.5 relevance AND no SQL data → refuses to answer |

### The 7 Hallucination Checks (Layer 3)

1. **Confidence Floor** — No evidence at all → cap confidence at MODERATE
2. **Numeric Grounding** — Dollar amounts must trace to source data
3. **Provider Name Check** — Must be in contracted network
4. **Date Plausibility** — Years must be within 2000–2035
5. **Competitor Blocklist** — Block attribution to Kaiser, Aetna, Cigna, etc.
6. **Universality Guard** — "All providers" claims must be backed by COUNT
7. **Cross-Dimensional** — "Tops both X and Y" must be verified in both result sets

**Outcomes:** WARN → downgrade confidence. BLOCK → reject answer entirely, show refusal message.

---

## Safety & Guardrails Summary

| Control | What It Prevents |
| --- | --- |
| Table whitelist (13 tables only) | Unauthorized data access |
| DDL/DML regex blocking | Any data modification (system is read-only) |
| Provider substitution guard | Returning data about wrong provider |
| Budget cap ($15/question) | Runaway AI costs |
| 10-step max + 120s timeout | Infinite reasoning loops |
| Graceful refusal | Guessing when evidence is insufficient |

---

## Key Business Outcomes

* **No wrong rates** — every dollar verified against source text
* **No missed provisions** — absence claims cross-checked
* **No hallucinated facts** — 7 independent checks before delivery
* **Complete answers** — multi-dimension detection ensures all parts addressed
* **Traceable** — every fact cites document + page number
* **Graceful uncertainty** — says "I don't know" rather than guessing

---

## Success Metrics

| Metric | Target |
| --- | --- |
| Answer accuracy | > 95% |
| Retrieval precision (MRR@10) | > 0.85 |
| Response time (complete) | < 3 seconds |
| Cost per query | < $0.05 |
| Provider coverage | 100% |
| PHI exposure incidents | 0 |

---

## The Bottom Line

**Defense-in-depth:** 4 pipeline gates + 4 application validation layers = 8 independent quality checkpoints. No single failure can produce a wrong answer. When in doubt, the system refuses rather than risks a wrong answer that could cost millions in mispriced contracts.

---

*Summary of: CIP Process and Quality Assurance Overview — Contract Intelligence Platform V5*
