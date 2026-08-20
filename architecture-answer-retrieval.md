# Contract Intelligence V4 — Answer Retrieval Architecture

## Overview

This document explains the complete end-to-end process that occurs when a user asks a question in the Contract Intelligence application. It is written for both **management** (who need to understand the safety and confidence guarantees) and **engineers** (who need to understand the technical flow and component interactions).

### Example Question

> "Give me a full deep-dive profile on Sierra Vista Hemodialysis Facility."

---

## Phase 1: Input Reception & Pre-Flight Safety Gates

**Where:** `app/main.py` → `AgentController.run()`  
**LLM Used:** None (zero cost, instant)  
**Purpose:** Reject questions the system cannot answer — before spending any money on LLM calls.

When the user submits a question in the web frontend, the system runs a battery of **deterministic safety gates** before any expensive processing begins:

| Gate | What It Checks | Why |
|------|---------------|-----|
| Empty Input Guard | Is the question blank? | Prevents wasted LLM calls |
| Temporal Real-Time Guard | Does question reference "today/yesterday"? | Database is a static extract — real-time data doesn't exist |
| Contract Value Guard | Does user ask "how much is the contract worth"? | Total dollar values aren't stored — prevents hallucination |
| Contact Info Guard | Is user asking for phone numbers/emails? | PII/personnel data not in system |
| Claims/Payment Guard | Is user asking about actual claims paid? | Claims data lives in a different system entirely |

**For our example:** None of these gates fire. The question is about contract profile data — which IS in the system. The request proceeds.

---

## Phase 2: Provider Identification & Grounding

**Where:** `QuestionRouter._detect_providers()` + `_inject_profile_facts()`  
**LLM Used:** None for detection (deterministic substring matching against the provider database)  
**Purpose:** Establish with certainty WHO the user is asking about, and pre-load verified facts.

### Step 2A — Who are they talking about?

The system has a database of **308 contracted providers** (their canonical names, aliases, health system affiliations). It performs **deterministic substring matching** on the question text — NOT an LLM guess. "Sierra Vista Hemodialysis Facility" is matched against `tbl_genie_provider_profile.provider_name`.

This gives us a **verified provider identity** — the exact database record for this provider.

### Step 2B — Pre-load verified ground truth

Before any reasoning begins, the system queries the structured profile table and stores **verified facts** in the session context:

- Contract status (active/inactive)
- Payment model (Fee-for-Service, Capitation, etc.)
- Line of business (Commercial, Medicare Advantage, etc.)
- Contract term and auto-renewal status
- Key clause flags (Offset: HAS/NO_MENTION, DOFR: HAS/NO_MENTION, IPA Delegation: HAS/NO_MENTION)

**Why this matters for confidence:** These facts are treated as **authoritative ground truth**. If the LLM later synthesizes something that contradicts these pre-loaded facts, the system knows the LLM is wrong. The facts come from structured, validated database fields — not from LLM interpretation of unstructured text.

---

## Phase 3: Intent Classification (Question Routing)

**Where:** `QuestionRouter.route()`  
**LLM Used:** Yes — Claude Sonnet 4.6 (one classification call, ~200 tokens)  
**Purpose:** Determine which specialized tool(s) should handle this question.

The system must decide **which tool(s) to use**. There are **16 specialized tools** in the system, each expert in a different domain:

| Tool | Domain |
|------|--------|
| `sql_query` | Structured data queries (profile, rates, counts) |
| `rate_query` | Contracted reimbursement rates |
| `clause_text` | Verbatim contract clause language |
| `clause_existence` | Does a clause exist? (passage analysis) |
| `compliance_query` | Regulatory compliance status |
| `temporal_analysis` | Amendment timeline and history |
| `financial_analysis` | Financial exposure and repricing |
| `risk_alert` | Risk scores and contract alerts |
| `system_membership` | Health system affiliation |
| `passage_search` | Full-text search in contract PDFs |
| `provider_deep_dive` | Comprehensive single-provider view |
| `network_geography` | Geographic coverage and market context |
| `provider_scorecard` | Composite multi-domain scorecard |
| `field_extraction` | Specific structured field values |
| `comparison` | Multi-provider comparisons |
| `provenance` | Data lineage and audit trail |

### How routing works:

1. **LLM classifies** the question into one of the 16 routes (returns JSON with route name + extracted entities)
2. **Six deterministic override rules** validate and correct the LLM's decision:
   - Rate-signal rescue (catches misrouted rate questions)
   - Comparison constraint (comparison needs 2+ providers)
   - Profile shortcut (simple yes/no questions bypass heavy tools)
   - Extraction-signal override (detects specific field value requests)
   - Clause-existence concept rescue (regex extracts concept when LLM omits it)
   - PROF-SQL shortcut (offset/DOFR/IPA existence → sql_query on profile table)

3. **Cross-validation against deterministic detection:** The LLM might hallucinate a provider name that doesn't exist. The system compares the LLM's extracted provider list against the deterministic substring matches from Phase 2. If they disagree, the **deterministic match wins**.

**For our example:** Router classifies it as `single_provider` → maps to `provider_deep_dive` tool (the comprehensive profile assembler).

---

## Phase 4: Direct Dispatch Attempt (Fast Path)

**Where:** `AgentController._run_direct_dispatch()`  
**LLM Used:** Depends on the tool (sql_query uses LLM for SQL generation; others may not)  
**Purpose:** Try to answer with a single tool call. If successful, return immediately (faster, cheaper).

The system first tries a **single-tool fast path**: call the selected tool directly and return its result. This is optimized for simple questions that only need one data source.

**For our example:** The router selected `provider_deep_dive`, but this tool is currently redirected to the multi-tool ReAct loop for richer, more comprehensive answers. Direct dispatch returns `None` → falls through to Phase 5.

---

## Phase 5: ReAct Loop (Multi-Tool Reasoning Engine)

**Where:** `AgentController._react_step()` — bounded iterative loop  
**LLM Used:** Yes — Claude Sonnet 4.6 (multiple reasoning calls)  
**Purpose:** Orchestrate multiple tool calls to assemble a comprehensive answer.

This is the **core intelligence engine**. It implements the ReAct pattern (Reason + Act + Observe):

```
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: REASON                                                  │
│  LLM thinks: "I need the provider profile first. Let me query    │
│  tbl_genie_provider_profile for Sierra Vista."                   │
│                                                                   │
│  → Action: CALL_TOOL                                             │
│  → Tool: sql_query                                               │
│  → Input: {question: "Get full profile for Sierra Vista..."}     │
├─────────────────────────────────────────────────────────────────┤
│  STEP 1: ACT                                                     │
│  sql_query tool executes:                                        │
│    1. LLM generates SQL from the question + schema context       │
│    2. SQL validated (whitelist check, DDL/DML blocked)            │
│    3. Spark SQL executes against Unity Catalog                   │
│    4. Rows returned as structured data                           │
├─────────────────────────────────────────────────────────────────┤
│  STEP 1: OBSERVE                                                 │
│  Result: {provider_name: "Sierra Vista Hemodialysis Facility",   │
│           payment_type: "Capitation", lob: "Commercial + MA",    │
│           is_active: true, offset_clause_status: "NO_MENTION"... │
│           }                                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  STEP 2: REASON                                                  │
│  LLM thinks: "I have profile. Now I need their rate schedule."   │
│  → Action: CALL_TOOL → Tool: sql_query                          │
│  → Gets rate data from tbl_contract_rates_all                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  STEP 3: REASON                                                  │
│  LLM thinks: "I have rates. Now I need amendment history."       │
│  → Action: CALL_TOOL → Tool: sql_query                          │
│  → Gets timeline from tbl_genie_amendment_timeline               │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  STEP 4: REASON                                                  │
│  LLM thinks: "I need key clause information."                    │
│  → Action: CALL_TOOL → Tool: clause_text                        │
│  → Gets clause data from tbl_contract_clauses                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  STEP 5: REASON                                                  │
│  LLM thinks: "I have enough data to write the executive report." │
│  → Action: SYNTHESIZE                                            │
│  → Produces the final formatted answer                           │
└─────────────────────────────────────────────────────────────────┘
```

### Bounded Execution (Safety Controls):

| Control | Limit | Purpose |
|---------|-------|---------|
| Maximum Steps | 10 | Prevents infinite reasoning loops |
| Budget Cap | $15 per question | Prevents runaway LLM costs |
| Total Timeout | 300 seconds | Prevents hung requests |

### Provider Substitution Guard (runs BEFORE every tool call):

Before EVERY tool call in the ReAct loop, the system checks:
1. **Does this provider actually exist** in the Blue Shield network? (validates against the canonical provider database)
2. **Is the provider name grounded in the question text?** (prevents the LLM from silently substituting a different, real provider when the asked-about provider doesn't exist)

If the LLM tries to call a tool with "Bakersfield Memorial Hospital" when the user asked about "Bakersfield General Hospital" (which doesn't exist), the substitution is **blocked** and the system reports the actual situation rather than showing wrong data.

---

## Phase 6: SQL Generation & Execution (Inside Each Tool)

**Where:** `tools/sql_query.py`  
**LLM Used:** Yes — Claude Sonnet 4.6 generates the SQL query  
**Purpose:** Translate natural language into safe, validated SQL and retrieve data.

When a tool needs data, it asks the LLM to write a SQL query. This is where **critical safety controls** exist:

### Security Layers:

| Layer | What It Does |
|-------|--------------|
| **Table Whitelist** | Only 13 pre-approved tables can be queried. LLM cannot access any table outside `dev_adb.raw.*` |
| **DDL/DML Blocking** | Regex rejects any CREATE, INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, GRANT, REVOKE. The system can NEVER modify data. |
| **Schema Context** | LLM receives column names + descriptions for allowed tables only — cannot "discover" hidden tables |
| **Catalog/Schema Prefix** | All table references are forced to `dev_adb.raw.*` — cannot escape to other catalogs |
| **Spark SQL Execution** | Queries run via Databricks SQL Warehouse with read-only permissions |

### Example SQL generated for profile:

```sql
SELECT provider_name, agreement_type, payment_type, line_of_business,
       contract_term_years, auto_renewal, is_active, total_amendments,
       offset_clause_status, dofr_status, ipa_delegation_status
FROM dev_adb.raw.tbl_genie_provider_profile
WHERE LOWER(provider_name) LIKE LOWER('%Sierra Vista%')
```

---

## Phase 7: Post-Synthesis Validation (Safety Checks)

**Where:** Multiple validators run sequentially  
**LLM Used:** None (all rule-based, zero cost)  
**Purpose:** Catch errors, hallucinations, and incomplete answers BEFORE they reach the user.

After the LLM produces its final answer, the system runs **four independent validators**:

### 7A. Answer Validator ("Prove It" Guardrail)

- **Detects wrong-domain answers**: If the question asks about "amendment history" but the tool answered from the alerts table, it catches this and triggers a retry from the correct table.
- **Absence claim verification**: If the LLM says "this provider doesn't have X," the validator runs a cheap `SELECT 1 FROM table WHERE provider_name LIKE ...` to verify. If data DOES exist, the answer is rejected and re-queried from the correct source.

### 7B. Answer Completeness Validator

- Extracts the **analytical dimensions** from the question (rates? compliance? clauses? timeline? network? risk? profile?)
- Checks if the answer actually addresses **all** requested dimensions
- Computes coverage ratio = dimensions_addressed / dimensions_asked
- If coverage < threshold AND the question has 2+ dimensions → answer is rejected, ReAct loop is re-triggered with additional tools to cover missing dimensions

### 7C. Hallucination Guard

Five checks (all rule-based, no LLM cost):

1. **Numeric consistency** — Every dollar amount, percentage, or count in the answer must trace back to a row in the source SQL results. Highly specific numbers (>4 digits) that appear nowhere in the tool results are flagged.
2. **Provider identity** — Does the answer reference providers that actually exist in the Blue Shield network? (blocks hallucinated references to Kaiser, Aetna, UnitedHealth, etc.)
3. **Date plausibility** — Are dates in the answer within reasonable ranges for healthcare contracts? (e.g., no contracts from 1850 or 2099)
4. **Ungrounded assertion detection** — Sentences with high specificity (dollar amounts, section numbers, dates) but zero citation support are flagged.
5. **Confidence floor** — If the answer has no citations AND no SQL data backing it, the confidence level is capped to MODERATE regardless of what the LLM claims.

### 7D. Answer Grounding Enforcer

- Scores each passage/tool result for **relevance** to the original question
- If zero passages/results score above the 0.5 relevance threshold → answer is blocked entirely
- Returns a clear refusal message ("I could not find verified evidence") instead of allowing an ungrounded guess through to the user

---

## Phase 8: Question Decomposition (Complex Questions Only)

**Where:** `QuestionDecomposer`  
**LLM Used:** Yes, for genuinely complex questions  
**Purpose:** Break multi-hop questions into parallel-executable sub-tasks.

For complex questions that require multiple independent information needs (e.g., "Compare rates between Provider A and Provider B AND show their compliance status"), the system:

1. **Heuristic check first** (regex/keyword) — avoids LLM cost on simple questions
2. **LLM-based decomposition** only for genuinely complex questions
3. Returns a **DecompositionPlan** with execution groups for parallel scheduling
4. Sub-questions are executed independently (with dependency ordering), then results are synthesized into a unified answer

---

## Phase 9: Response Assembly & Delivery

**Where:** `AgentController._build_response()`  
**LLM Used:** None  
**Purpose:** Package the validated answer for the frontend.

The final response includes:

- **Formatted markdown answer** (executive report structure with headers, tables, bullet points)
- **Confidence level** (HIGH / MODERATE / LOW)
- **Process trail** (which tools were used, latency per step — visible in the UI footer)
- **Cost tracking** (total LLM spend for this question)

---

## Complete Data Flow Diagram

```
User Question
     │
     ▼
┌────────────────────────┐
│  PRE-FLIGHT GATES      │  ◄─── No LLM (instant, rule-based)
│  (5 safety checks)     │       Cost: $0
└──────────┬─────────────┘
           │ passes
           ▼
┌────────────────────────┐
│  PROVIDER DETECT       │  ◄─── No LLM (deterministic DB match)
│  + FACTS INJECTION     │       Cost: $0 (1 SQL query)
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐
│  QUESTION ROUTER       │  ◄─── LLM Call #1 (classification)
│  + 6 Override Rules    │       + Deterministic cross-validation
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐
│  DIRECT DISPATCH       │  ◄─── Sometimes 1 LLM call (SQL gen)
│  (fast path attempt)   │       Usually no LLM for simple queries
└──────────┬─────────────┘
           │ if insufficient
           ▼
┌────────────────────────┐
│  ReAct LOOP            │  ◄─── 3-8 LLM Calls (reasoning + SQL)
│  (multi-tool engine)   │       Each step: Think → Act → Observe
│  • Max 10 steps        │       Tools execute SQL on Spark
│  • $15 budget cap      │       Provider Guard before EACH call
│  • 300s timeout        │
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐
│  POST-SYNTHESIS        │  ◄─── No LLM (all rule-based)
│  VALIDATORS            │       Cost: $0
│  • Answer Validator    │
│  • Completeness Check  │
│  • Hallucination Guard │
│  • Grounding Enforcer  │
│  • Provider Guard      │
└──────────┬─────────────┘
           │ all pass
           ▼
┌────────────────────────┐
│  RESPONSE ASSEMBLY     │
│  Markdown + Confidence │
│  + Process Trail       │
└──────────┬─────────────┘
           │
           ▼
      Final Answer
      (displayed to user)
```

---

## Where LLM is Used vs. Not Used

| Component | Uses LLM? | Model | Purpose |
|-----------|-----------|-------|---------|
| Pre-flight Guards | No | — | Rule-based safety filters |
| Provider Detection | No | — | Deterministic DB substring match |
| Profile Injection | No | — | Direct SQL query (no generation needed) |
| Question Routing | **Yes** | Claude Sonnet 4.6 | Intent classification |
| Override Rules | No | — | 6 deterministic regex/rule corrections |
| SQL Generation | **Yes** | Claude Sonnet 4.6 | Writes the SQL query from natural language |
| SQL Validation | No | — | Whitelist + DDL/DML regex blocking |
| SQL Execution | No | — | Spark SQL on Databricks SQL Warehouse |
| ReAct Reasoning | **Yes** | Claude Sonnet 4.6 | Multi-step planning and tool selection |
| Answer Synthesis | **Yes** | Claude Sonnet 4.6 | Final report composition |
| All 5 Validators | No | — | Rule-based hallucination detection |
| Provider Guard | No | — | String matching against provider DB |

**Typical LLM call count for a deep-dive question:** 5-8 calls total

- 1 for routing classification
- 3-5 for reasoning steps (each step = thought + action decision)
- 1-3 for SQL generation within tools
- 1 for final synthesis

---

## Confidence Assurance — How We Know the Answer is Correct

### 1. Data comes from verified sources

All facts originate from structured tables in Unity Catalog (`dev_adb.raw.*`), which were populated by controlled extraction pipelines from actual contract PDF documents. The data is not generated — it is extracted and validated.

### 2. SQL is sandboxed

The LLM can ONLY read from 13 approved tables. It cannot write, delete, or access any other data. Even if the LLM were to attempt a malicious query, the DDL/DML regex and table whitelist would block it before execution.

### 3. Provider identity is verified twice

Once by deterministic substring matching (Phase 2), and again by the Provider Substitution Guard before every single tool call in the ReAct loop. There is no path for the LLM to silently return data about the wrong provider.

### 4. Numbers are traceable

The Hallucination Guard verifies that every number in the answer (dollar amounts, percentages, counts, dates) traces back to a specific row in the SQL results. Ungrounded numbers are flagged.

### 5. Wrong-domain answers are caught

If a tool returns data from the wrong table (e.g., alert data instead of amendment history), the Answer Validator detects the mismatch and forces a retry from the correct source.

### 6. Completeness is enforced

If the question asks about 4 dimensions (rates + compliance + clauses + timeline) but the answer only covers 2, it's rejected and re-processed with additional tools until all dimensions are addressed.

### 7. Budget limits prevent runaway

Maximum 10 steps, $15 cost cap, 300-second timeout. The system cannot get stuck in an infinite reasoning loop or accumulate unbounded costs.

### 8. Ground truth overrides LLM guesses

The pre-loaded profile facts (contract term, payment type, LOB, clause flags) are marked as authoritative. If the LLM's synthesis contradicts these structured fields, the structured data wins.

---

## Infrastructure Stack

| Layer | Technology |
|-------|------------|
| Frontend | Web app on Databricks Apps (XLARGE compute) |
| Reasoning LLM | `databricks-claude-sonnet-4-6` (via Model Serving endpoint) |
| Fast LLM | `databricks-claude-haiku-4-5` (for lightweight classification) |
| Data Execution | Databricks SQL Warehouse (`0f30c4e1661ac057`) |
| Data Store | Unity Catalog — `dev_adb.raw` (13 contract tables, 308 providers) |
| Source Documents | Contract PDFs processed via extraction pipelines |
| Deployment | Databricks Apps with OAuth, XLARGE compute, auto-scaling |
| Security | Service principal with scoped API permissions (catalog read, SQL, model-serving) |

---

## Key Tables in the Data Layer

| Table | What It Contains | Row Count |
|-------|------------------|-----------|
| `tbl_genie_provider_profile` | Provider master data (status, LOB, payment type, clause flags) | 308 |
| `tbl_contract_rates_all` | All contracted reimbursement rates (current + superseded) | ~15,000+ |
| `tbl_genie_amendment_timeline` | Amendment history per provider | ~2,500+ |
| `tbl_contract_clauses` | Extracted clause text (21 categories) | ~6,700 |
| `tbl_compliance_tracking` | Regulatory compliance status (7 regulations) | ~2,100 |
| `tbl_contract_documents_master` | Document metadata and supersession chains | ~1,200 |
| `tbl_extraction_provenance` | Extraction audit trail (confidence scores, methods) | ~15,300 |
| `tbl_financial_exposure` | Financial exposure estimates | ~300 |
| `tbl_risk_alerts` | Active contract risk alerts and deadlines | ~500+ |
| `tbl_rate_benchmarks` | Network-wide rate percentiles (P25, P50, P75) | ~200 |
| `tbl_clause_deviations` | How each provider deviates from network norms | ~6,400 |
| `tbl_quality_performance` | Quality metrics (HEDIS, P4P, star ratings) | ~300 |
| `tbl_repricing_scenarios` | What-if repricing scenario results | ~600 |

---

## FAQ for Management

**Q: Can the system ever modify or delete contract data?**  
A: No. The SQL validation layer blocks all write operations (INSERT, UPDATE, DELETE, DROP, etc.) with a regex check before execution. The SQL Warehouse connection is read-only. There is zero risk of data modification.

**Q: Can the LLM hallucinate false information about a provider?**  
A: The system has multiple layers to prevent this: pre-loaded ground truth facts override LLM guesses, the Hallucination Guard checks numeric consistency, and the Provider Substitution Guard prevents answering about the wrong provider. However, no AI system is 100% hallucination-proof — the confidence level (HIGH/MODERATE/LOW) shown with each answer indicates our certainty.

**Q: What happens if the LLM gets stuck in a loop?**  
A: Three hard limits prevent this: maximum 10 reasoning steps, $15 budget cap, and a 300-second timeout. If any limit is hit, the system returns the best answer it has so far (or a clear refusal if insufficient evidence exists).

**Q: How much does each question cost?**  
A: A typical deep-dive question costs $0.05–$0.15 in LLM API charges (5-8 calls to Claude Sonnet 4.6). Simple factual questions cost $0.01–$0.03 (1-2 calls via the fast path).

**Q: Can the system access data outside our contract database?**  
A: No. The table whitelist restricts access to exactly 13 pre-approved tables in the `dev_adb.raw` catalog. The LLM cannot discover, query, or reference any other tables regardless of what it's asked.

**Q: How do we know the page numbers and source files are correct?**  
A: Source filenames come directly from the `source_filename` column in `tbl_contract_clauses`, populated during the extraction pipeline from actual PDF metadata. Page numbers (where available) come from `tbl_extraction_provenance.source_page_numbers`. The system cites what the extraction pipeline recorded.

---

## FAQ for Engineers

**Q: How is the ReAct loop implemented?**  
A: It's a bounded `while` loop in `AgentController.run()`. Each iteration calls the LLM with accumulated context (prior tool results + system prompt + tool catalogue). The LLM returns JSON with `{thought, action, tool_name, tool_input}` or `{thought, action: SYNTHESIZE, final_answer}`. Tools are called via `ToolRegistry.call()` with full kwargs passing.

**Q: How does the router decide between LLM classification and heuristic rules?**  
A: Both always run. LLM classification fires first (`_llm_route()`), then 6 deterministic override rules in `_apply_overrides()` correct known misclassification patterns. The override rules are final — they can change the LLM's decision but not vice versa.

**Q: How is SQL injection prevented?**  
A: Three layers: (1) Table whitelist — only allowed table names pass validation, (2) DDL/DML regex — blocks all write keywords, (3) Catalog/schema prefix enforcement — all tables resolve to `dev_adb.raw.*` regardless of what the LLM writes. The SQL is executed via Spark SQL (not raw JDBC), adding another layer of isolation.

**Q: What happens when a tool returns 0 rows?**  
A: In direct dispatch, 0 rows causes a fallback to the ReAct loop (the LLM tries a different approach). In the ReAct loop, the system prompt instructs the LLM to retry with (1) a different tool, (2) a simpler query, or (3) a broader LIKE filter. Only after 2+ failed attempts does the system consider reporting insufficient data.

**Q: How do the two LLM models divide work?**  
A: `databricks-claude-sonnet-4-6` handles all reasoning, SQL generation, and answer synthesis (the heavy lifting). `databricks-claude-haiku-4-5` is available for lightweight classification tasks where speed matters more than reasoning depth (e.g., quick route classification in simple cases).

**Q: Can I add a new table to the system?**  
A: Yes — add it to `CONTRACT_TABLES_FOR_SQL` in `config/table_whitelist.py` and provide column descriptions in the schema context. The LLM will automatically be able to query it. No other code changes required.

**Q: What's the difference between direct dispatch and ReAct?**  
A: Direct dispatch = single tool call, no LLM reasoning overhead, result formatted as-is. ReAct = LLM plans multi-step strategy, calls multiple tools, synthesizes a comprehensive answer. Direct dispatch is faster/cheaper but only works for single-dimension questions. ReAct handles complex, multi-faceted questions.

---

*Document generated from source code analysis of Contract Intelligence V4.*  
*Source: `/Workspace/Users/adixit01@blueshieldca.com/contract-intelligence-v4/platform/v4/core/agent_controller.py`*
