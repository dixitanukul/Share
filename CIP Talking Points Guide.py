# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,CIP Talking Points Guide
# MAGIC %md
# MAGIC # CIP Talking Points Guide — Section-by-Section Presenter Notes
# MAGIC
# MAGIC **Purpose:** Walk your leadership through the "CIP Process and Quality Assurance Overview" document. Each section below mirrors a section in that document and gives you:
# MAGIC - **Key message** (the one sentence they should remember)
# MAGIC - **Talking points** (what to say out loud)
# MAGIC - **Anticipated questions** (what they'll ask + your answers)
# MAGIC - **Analogies** (how to explain technical concepts simply)
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC # OPENING — "What This Platform Does"
# MAGIC
# MAGIC ## Key Message
# MAGIC > We turned 10,000 PDF contracts into an instant-answer system that's faster, cheaper, and more accurate than human lookup.
# MAGIC
# MAGIC ## Talking Points
# MAGIC - **The old way:** Someone asks "What's Stanford's per diem rate?" A contracts analyst opens a SharePoint folder, finds the right PDF (which one? there are 12 versions), searches 200 pages, and responds in 2-3 days. Error-prone, unscalable.
# MAGIC - **The new way:** Ask in plain English, get a cited answer in under 3 seconds. Every fact traces back to a specific document and page number.
# MAGIC - **Scale numbers to mention:** 10,329 PDFs, 597 unique providers, 50+ structured tables, 2,125 rate rules extracted so far (from first 29 files processed).
# MAGIC - **Cost:** Less than $0.05 per query. A human analyst at $80/hour spending 30 minutes = $40 per question. That's an 800× cost reduction.
# MAGIC
# MAGIC ## Anticipated Questions
# MAGIC
# MAGIC **Q: "Why can't we just use Ctrl+F in the PDFs?"**
# MAGIC > A: Three reasons: (1) 5% of files are scanned images — no text to search. (2) The same concept appears in different words across contracts ("SNF daily rate" vs "subacute per diem"). (3) Ctrl+F can't aggregate — you can't ask "which provider has the highest rate" across 10,000 docs.
# MAGIC
# MAGIC **Q: "What if the AI gets it wrong?"**
# MAGIC > A: That's the entire point of Parts 1-4 of this document. We have 8 independent checkpoints — 4 on the data going in, 4 on the answers coming out. The system refuses to answer rather than guess. More on that as we walk through each part.
# MAGIC
# MAGIC **Q: "Is this replacing the contracts team?"**
# MAGIC > A: No. It's replacing the *search* part of their job. They still negotiate, interpret nuance, and make decisions. This gives them instant access to facts so they can spend time on judgment, not hunting.

# COMMAND ----------

# DBTITLE 1,Part 1 — Data Extraction Pipeline
# MAGIC %md
# MAGIC ---
# MAGIC
# MAGIC # PART 1: Data Extraction Pipeline — Talking Points
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Key Message
# MAGIC > Every piece of data goes through 4 mandatory quality gates before it's allowed into our production tables. Bad data is physically blocked — not just flagged.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## The Big Picture (explain this first)
# MAGIC
# MAGIC There are 5 stages and 4 gates. Think of it like airport security — you pass each checkpoint or you don't board.
# MAGIC
# MAGIC ```
# MAGIC PDF → OCR → Gate 1 → AI Extract → Gate 2/2B → Quality Score → Gate 3 → Transform → Gate 4 → Production
# MAGIC ```
# MAGIC
# MAGIC A file that fails ANY gate is stopped. It never moves forward.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Stage 1: Discovery
# MAGIC
# MAGIC **What to say:** "The system automatically watches the source folder. New or modified PDFs get registered. If there's a newer version of a contract, the old one is marked superseded so we never serve stale data."
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Stage 2: OCR + Gate 1
# MAGIC
# MAGIC **What to say:** "We convert every PDF to text. 95% are digital — easy, free, instant. The 5% that are scanned (faxes, handwriting) go through AI-powered OCR."
# MAGIC
# MAGIC **Gate 1 — explain like this:**
# MAGIC "Before we let any document proceed, we ask: can we even READ this thing?"
# MAGIC
# MAGIC 5 checks:
# MAGIC - Is the average word confidence above 50%? (If not, too many garbled words — the AI will extract garbage.)
# MAGIC - Are there at least 10 words per page? (If not, it's probably blank pages or images.)
# MAGIC - Are there at least 100 words total? (If not, the document is mostly unreadable.)
# MAGIC - Is the non-ASCII character ratio below 5%? (If not, OCR is producing symbols instead of letters.)
# MAGIC - Are fewer than 20% of pages blank? (If not, the document is mostly empty.)
# MAGIC
# MAGIC **Gate 1B — follow up with:**
# MAGIC "We also verify it's actually a healthcare contract — not a random file someone dropped in. We scan the first 5 pages for healthcare terms (payer, provider, legal, financial keywords). If it doesn't hit at least 3 categories with 5 markers, it's rejected."
# MAGIC
# MAGIC **If they ask "what happens when it fails?":** 
# MAGIC "It gets FAILED status, classified by error type, and goes to a recovery queue for manual investigation. It never proceeds."
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Stage 3: AI Extraction + Gates 2 & 2B
# MAGIC
# MAGIC **What to say:** "A large language model reads the text and produces structured data — rates, clauses, dates, everything. But we don't trust the AI blindly. Two immediate checks follow."
# MAGIC
# MAGIC **Gate 2 — explain like this:**
# MAGIC "We ask: did the AI extract the minimum required information?"
# MAGIC
# MAGIC 4 checks:
# MAGIC - Provider name and date must exist. (If the AI can't tell us WHO the contract is with and WHEN, the rest is useless.)
# MAGIC - AI confidence must be ≥70%. (The model reports its own confidence. Below 70% means IT thinks the input was ambiguous.)
# MAGIC - Base agreements must have at least 1 rate extracted. (A base agreement without financial terms = the AI missed something fundamental.)
# MAGIC - At least some items must cite page numbers. (Without page references, we can't trace facts back to the source.)
# MAGIC
# MAGIC **Gate 2B — this is the hallucination catch:**
# MAGIC "We cross-reference what the AI extracted against the original document text. Three checks:"
# MAGIC
# MAGIC 1. **Date grounding:** "We take the date the AI says is the effective date, and search for it in the OCR text. If '2024' doesn't appear anywhere in the document but the AI says effective date is 2024 — it hallucinated."
# MAGIC
# MAGIC 2. **Page validity:** "If the AI says something is on page 72 but the document only has 45 pages — caught."
# MAGIC
# MAGIC 3. **Provider name:** "We try 5 different ways to match the provider name the AI extracted against what's actually in the document. If none of the 5 match — the AI substituted a name from its training data."
# MAGIC
# MAGIC **Key point to emphasize:** "All of these use simple string matching — no regex, no additional AI calls. Just 'does this text appear in that text?' Instant, deterministic, free."
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Stage 4: Quality Scoring + Gate 3
# MAGIC
# MAGIC **What to say:** "Now we score each file across 9 quality dimensions, then send a sample to a second AI for independent verification."
# MAGIC
# MAGIC **The 9 dimensions — summarize as:**
# MAGIC "We check: Were dollar amounts found? Were percentage rates found? Do we have start/end dates? Are services labeled specifically (not just 'Inpatient' but 'Inpatient - ICU')? Were all contract sections extracted? Can items trace to pages? Are fields filled in? Are page numbers valid? Are items unique?"
# MAGIC
# MAGIC **If they want detail on any dimension, key points:**
# MAGIC - Dimensions are scored 0-100%, then weighted differently by document type
# MAGIC - Base agreements weight dollar values at 20% (most critical for financial contracts)
# MAGIC - Amendments weight topic coverage at 25% (clauses matter more than rates there)
# MAGIC - This prevents unfairly penalizing an amendment for not having rates — it was never supposed to have rates
# MAGIC
# MAGIC **Gate 3 — the composite:**
# MAGIC "We combine two scores:"
# MAGIC - Coverage (60% weight) = weighted average of all 9 dimensions
# MAGIC - Accuracy (40% weight) = a SECOND AI independently checks a sample of extracted items
# MAGIC
# MAGIC "The threshold is 65%. Our actual run scored 88%. Well above."
# MAGIC
# MAGIC **The judge (if they ask how accuracy works):**
# MAGIC "We take 3 rates per file that cite page numbers. We give a second AI the original page text and ask: Is this rate actually on this page? Is the number exact? Did it miss anything? The judge reports grounded/accurate/complete."
# MAGIC
# MAGIC "In our run: 84% accuracy (58 out of 69 items were exactly correct). Cost: about $1-2 total for the whole batch."
# MAGIC
# MAGIC **Why 60/40 not 50/50?** "Coverage measures everything across all items. Accuracy only samples 3 per file. Broad coverage matters slightly more than spot-checking accuracy."
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Stage 5: Transform + Gate 4
# MAGIC
# MAGIC **What to say:** "The validated JSON gets exploded into normalized Delta tables. One more integrity check:"
# MAGIC
# MAGIC 5 checks:
# MAGIC - Row drop rate ≤10% (are items getting lost in conversion?)
# MAGIC - Null rate ≤50% for dollar amounts (did extraction actually produce usable values?)
# MAGIC - All dates between 1990-2035 (impossible dates = parsing error)
# MAGIC - All rates ≤$15M (above that = contract ID misread as a dollar amount)
# MAGIC - Zero duplicate primary keys (duplicates = double-counted financial exposure)
# MAGIC
# MAGIC "Only after passing all 4 gates does data reach the tables the application queries."
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Anticipated Questions
# MAGIC
# MAGIC **Q: "What percentage of files fail?"**
# MAGIC > In our first batch of 29 files, all passed. The gates are calibrated to catch genuine failures, not be overly strict. A 5-page amendment scoring lower on 'topic coverage' is expected — the thresholds account for that.
# MAGIC
# MAGIC **Q: "How long does the full pipeline take?"**
# MAGIC > Discovery + OCR is minutes. AI extraction is the slowest step — one file at a time, ~30-60 seconds per file. Quality scoring adds another few seconds. End-to-end for a batch of 30 files: about 30-45 minutes.
# MAGIC
# MAGIC **Q: "What if a file keeps failing?"**
# MAGIC > It goes to the recovery queue. We can re-extract with a specialized prompt, adjust thresholds for that document type, or flag it for manual extraction. The pipeline never forces bad data through.
# MAGIC
# MAGIC **Q: "Why use AI for extraction — why not a rules-based parser?"**
# MAGIC > Because every contract is different. Layout, formatting, terminology all vary by provider. Rules break on variation. AI handles the diversity but we don't trust it blindly — hence the 4 gates.

# COMMAND ----------

# DBTITLE 1,Part 2 — Intelligence Layer
# MAGIC %md
# MAGIC ---
# MAGIC
# MAGIC # PART 2: Intelligence Layer — Talking Points
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Key Message
# MAGIC > Raw extracted data isn't enough. We compute analytics (benchmarks, rankings, priorities) and build a semantic search layer so the system can answer comparative and natural language questions.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Rate Benchmarking & Provider Positioning
# MAGIC
# MAGIC **What to say:** "Once we have all the rates extracted, we compute WHERE each provider sits relative to the network. For every combination of service type and payment formula, we calculate percentile distributions — p10, p25, p50, p75, p90."
# MAGIC
# MAGIC **Why this matters (the business value):**
# MAGIC "This means a negotiator can instantly know: 'Stanford's inpatient per diem is at the 72nd percentile — more expensive than 72% of our network.' That's not a vague 'seems high' — it's a precise position backed by data across all 597 providers."
# MAGIC
# MAGIC **4 outputs to mention:**
# MAGIC
# MAGIC 1. **Rate benchmarks** — 250 combinations (service domain × formula type). Enables "is this rate high or low?"
# MAGIC 2. **Provider percentiles** — 250 rows. Each provider positioned against the network.
# MAGIC 3. **Renewal priority scores** — Formula: Urgency(0-40) + Impact(0-40) + Risk(0-20). Tells you which contracts need attention FIRST.
# MAGIC    - ESCALATE ≥ 80, PRIORITIZE 60–79, MONITOR 40–59, MAINTAIN < 40
# MAGIC 4. **Clause deviations** — Flags non-standard provisions:
# MAGIC    - MISSING = >70% of network has this clause but this provider doesn't
# MAGIC    - EXTRA = <20% of network has this clause but this provider does
# MAGIC    - STANDARD = normal
# MAGIC
# MAGIC **If they ask "how is priority score calculated?":**
# MAGIC "Three components: Urgency (is the contract expiring soon? sigmoid decay function gives higher scores as deadline approaches), Impact (what's the financial exposure? log-scaled), and Risk (any compliance gaps or unusual clauses?). Combined into 0-100."
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Semantic Search Index (Vector Search)
# MAGIC
# MAGIC **What to say:** "All extracted content gets converted into searchable text chunks we call 'legal units' — and embedded into a vector search index."
# MAGIC
# MAGIC **Explain vector search simply:**
# MAGIC "Traditional keyword search fails for natural language. If someone asks 'SNF daily rate' but the contract says 'subacute per diem' — keyword search finds nothing. Vector search understands they mean the same thing because it searches by MEANING, not exact words."
# MAGIC
# MAGIC **The process (5 steps):**
# MAGIC 1. Extracted data (rates, clauses, stop-loss, carve-outs, definitions) gets formatted into readable text blocks
# MAGIC 2. Each block goes through an embedding model that converts it into a 1,024-number mathematical representation
# MAGIC 3. All 1,363 legal units get stored in the vector index
# MAGIC 4. When a user asks a question, their question gets the same treatment — converted to a 1,024-number vector
# MAGIC 5. The system finds the closest matches by mathematical similarity (cosine distance)
# MAGIC
# MAGIC **Scale numbers:** 1,363 legal units across 6 types (rate tables, clauses, stop-loss, carve-outs, definitions, metadata). Searchable in under 100 milliseconds.
# MAGIC
# MAGIC **If they ask "what's a legal unit?":**
# MAGIC "A self-contained chunk of contract content. One rate table. One clause. One definition. Small enough to be specific, large enough to be meaningful. It's the unit of retrieval — when the application searches for evidence, it retrieves these."
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Where We Stand After Part 2
# MAGIC
# MAGIC Summarize: "At this point we have three things ready:
# MAGIC 1. Quality-assured structured tables (passed 4 gates)
# MAGIC 2. Comparative analytics (benchmarks, percentiles, priorities)
# MAGIC 3. A meaning-based search index for natural language questions
# MAGIC
# MAGIC The data foundation is complete. Now the application answers questions."
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Anticipated Questions
# MAGIC
# MAGIC **Q: "How often do benchmarks get recalculated?"**
# MAGIC > Every time the pipeline runs and new data enters production tables. The intelligence stage re-runs on the updated dataset.
# MAGIC
# MAGIC **Q: "What embedding model do we use?"**
# MAGIC > databricks-gte-large-en — produces 1,024-dimensional vectors. It's enterprise-grade and runs on Databricks infrastructure (no external API calls, no data leaving our environment).
# MAGIC
# MAGIC **Q: "Can we search by specific provider?"**
# MAGIC > Yes. Vector search supports metadata filters. You can restrict search to a specific provider, document type, or time range.
# MAGIC
# MAGIC **Q: "How is this different from just putting everything in a database and doing SQL?"**
# MAGIC > SQL handles structured queries perfectly ("What is Stanford's rate?"). But SQL can't handle meaning-based queries ("What provisions protect us if the provider leaves the network?"). Vector search handles the natural language side. The application uses BOTH — SQL for precise lookups, vector search for conceptual questions.

# COMMAND ----------

# DBTITLE 1,Part 3 — The Application: How Questions Are Answered
# MAGIC %md
# MAGIC ---
# MAGIC
# MAGIC # PART 3: The Application — Talking Points
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Key Message
# MAGIC > When a user asks a question, the system follows 4 steps: understand it, gather evidence, validate the answer, then deliver with citations. 80% of questions are answered in 2-3 seconds via direct lookup. The other 20% use multi-step reasoning, bounded by strict cost and time limits.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Step 1: Question Routing
# MAGIC
# MAGIC **What to say:** "Not all questions are the same. We classify every question into one of 16 specialized categories and route it to the most efficient retrieval strategy."
# MAGIC
# MAGIC **Examples to give (pick 3-4):**
# MAGIC - "What is Stanford's per diem rate?" → Direct SQL lookup on rate tables. Fastest path.
# MAGIC - "Does Stanford have an offset clause?" → SQL + vector search. Needs both structured data and document text.
# MAGIC - "Compare Stanford vs Sutter rates" → Multi-step: query each provider separately, then merge results.
# MAGIC - "What is a carve-out?" → Semantic search only. This is a concept explanation, not a data lookup.
# MAGIC
# MAGIC **Why routing matters:**
# MAGIC "A question about dollar rates needs precise SQL — not fuzzy text search. A question about contract language needs semantic understanding that SQL can't provide. Wrong routing = slow answer or wrong answer."
# MAGIC
# MAGIC **Safety mechanisms:**
# MAGIC "6 deterministic override rules catch misrouting. Example: if the system detects rate-related keywords but accidentally classifies it as a clause search, the override forces it back to a rate lookup. These are hardcoded rules, not AI judgment."
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Step 2: Evidence Gathering
# MAGIC
# MAGIC **What to say:** "Once classified, the system gathers evidence. Two modes:"
# MAGIC
# MAGIC **Simple questions (80% of traffic):**
# MAGIC - Single tool execution
# MAGIC - Direct route to one query
# MAGIC - Answer in 2-3 seconds
# MAGIC - Example: "What is Stanford's per diem rate?" → one SQL query → done
# MAGIC
# MAGIC **Complex questions (20% of traffic):**
# MAGIC - Multi-step reasoning (the system breaks it into sub-questions)
# MAGIC - Executes multiple tools and synthesizes results
# MAGIC - Bounded by:
# MAGIC   - Maximum 10 reasoning steps (prevents infinite loops)
# MAGIC   - $15 cost cap per query (prevents runaway AI spending)
# MAGIC   - 120-second timeout (guarantees responsiveness)
# MAGIC
# MAGIC **Example to walk through:**
# MAGIC "User asks: 'Compare Stanford and Sutter rates and which has better compliance?'
# MAGIC
# MAGIC The system decomposes this into 4 sub-queries: Stanford rates, Sutter rates, Stanford compliance, Sutter compliance. Runs all four, then synthesizes into one comparative answer."
# MAGIC
# MAGIC **If they ask about the cost cap:**
# MAGIC "Each reasoning step costs money — AI calls aren't free. We cap at $15 per query to prevent a badly formed question from triggering a $200 chain of calls. In practice, even complex questions cost under $1."
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Step 3: Validation (briefly)
# MAGIC
# MAGIC **What to say:** "Before showing the answer, 4 independent quality layers validate it. That's all of Part 4 — I'll walk through each layer in detail next."
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Step 4: Delivery
# MAGIC
# MAGIC **What to say:** "Every answer comes with:"
# MAGIC - A confidence level (HIGH / MODERATE / LOW)
# MAGIC - Source citations (specific document + page number)
# MAGIC - Every fact is traceable — the user can click through to the exact page in the original PDF
# MAGIC
# MAGIC "We never just give an answer. We show WHERE it came from."
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Anticipated Questions
# MAGIC
# MAGIC **Q: "What if the question doesn't fit any of the 16 categories?"**
# MAGIC > It falls into a general category and uses vector search + broad retrieval. The system always has a path — no question gets dropped. It might just take slightly longer.
# MAGIC
# MAGIC **Q: "How does it handle follow-up questions?"**
# MAGIC > The system maintains conversation context. If you ask "What about Sutter?" after asking about Stanford, it understands you mean the same type of query for a different provider.
# MAGIC
# MAGIC **Q: "What are the 6 tools available?"**
# MAGIC > Rate lookup (SQL), clause lookup (SQL + vector), SQL query (flexible), vector search (semantic), provider profile (multi-table), and provider deep dive (comprehensive). Each tool is specialized for a type of evidence.
# MAGIC
# MAGIC **Q: "What happens at the 120-second timeout?"**
# MAGIC > The system returns whatever it has gathered so far, with a MODERATE confidence and a note that the answer may be incomplete. It never hangs.
# MAGIC
# MAGIC **Q: "Why 16 categories — isn't that a lot?"**
# MAGIC > Healthcare contracts cover diverse topics — rates, clauses, compliance, risk, timelines, comparisons, definitions, etc. Each needs a different retrieval approach. 16 routes = precise targeting. The alternative is one-size-fits-all which is slower and less accurate.

# COMMAND ----------

# DBTITLE 1,Part 4 — Answer Validation: 4-Layer Quality Engine
# MAGIC %md
# MAGIC ---
# MAGIC
# MAGIC # PART 4: Answer Validation — Talking Points
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Key Message
# MAGIC > Every answer passes through 4 independent validation layers before reaching the user. Each layer catches a DIFFERENT type of failure. If validation fails, the system refuses to answer rather than guess.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Why 4 Layers?
# MAGIC
# MAGIC **What to say:** "No single check catches everything. Think of it like 4 different specialists reviewing a report:"
# MAGIC
# MAGIC | Layer | What it catches | Real-world risk it prevents |
# MAGIC | --- | --- | --- |
# MAGIC | 1. Completeness | Partial answers (asked 3 things, got 1) | Decision made on incomplete info |
# MAGIC | 2. Absence Verification | False "no data found" claims | Negotiator misses a provision that IS in the contract |
# MAGIC | 3. Hallucination | Invented numbers, dates, providers | Financial decision based on fabricated rate |
# MAGIC | 4. Grounding | Claims with zero backing evidence | Presenting confident answers that can't be verified |
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Layer 1: Completeness Check
# MAGIC
# MAGIC **What to say:** "If someone asks about rates AND compliance, we make sure BOTH are addressed. Not just one."
# MAGIC
# MAGIC **How to explain it:**
# MAGIC "The system detects 7 dimensions a question can touch: financial, compliance, risk, clause, temporal, network, profile. It counts how many the question asks about, then checks how many the answer actually addresses."
# MAGIC
# MAGIC **Threshold:** 60% coverage required. But for 2-dimension questions, BOTH must be present.
# MAGIC
# MAGIC **Example to give:**
# MAGIC "User asks 'What are Stanford's rates and compliance status?' That's 2 dimensions. If the initial lookup only returns rates (50% coverage), Layer 1 catches it and triggers a separate compliance lookup. The user gets both."
# MAGIC
# MAGIC **Skip conditions:** Single-dimension questions (nothing to be incomplete about) and broad tools like provider_deep_dive (returns everything by default).
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Layer 2: Absence Verification
# MAGIC
# MAGIC **What to say:** "This is one of our most important checks. When the system says 'no data found' — we verify that's actually true."
# MAGIC
# MAGIC **Why this matters (use this analogy):**
# MAGIC "Imagine a negotiator asks 'Does Stanford have an offset clause?' and the system says 'No offset clause found.' But it IS there on page 47 — the system just looked in the wrong table. The negotiator doesn't push for it. That's a costly miss."
# MAGIC
# MAGIC **How it works:**
# MAGIC 1. Detect absence language in the answer ("does not have", "no data found", etc.)
# MAGIC 2. Map the question to the correct table ("clause" → clauses table, "rate" → rates table)
# MAGIC 3. Run a simple SQL existence check: does data for this provider exist in the right table?
# MAGIC 4. If data exists → original answer was wrong → retry. If truly absent → pass through.
# MAGIC
# MAGIC **Cost:** One SQL query. No AI. Only fires on ~15% of answers (those with absence language).
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Layer 3: Hallucination Detection (7 Checks)
# MAGIC
# MAGIC **What to say:** "This is 7 automated checks that catch fabricated facts. Zero AI calls — all pattern matching. Instant and free."
# MAGIC
# MAGIC **Where do citations come from? (explain this first):**
# MAGIC "When a user asks a question, the system retrieves actual text passages from the vector search index — real text from the original signed contracts. These passages become 'citations.' The hallucination guard compares the AI's answer against these real source passages."
# MAGIC
# MAGIC **The 7 checks — explain each briefly:**
# MAGIC
# MAGIC 1. **Confidence Floor:** "If there's NO evidence backing the answer (empty citations, no SQL data), confidence is capped at MODERATE. Can't claim HIGH certainty with zero backing."
# MAGIC
# MAGIC 2. **Numeric Grounding:** "Every dollar amount in the answer must exist in the source data. If the answer says '$2,200/day' but the citation says '$2,150/day' — flagged. Only checks specific numbers (>4 digits) because small numbers like '2' or '100' are too common to track."
# MAGIC
# MAGIC 3. **Provider Name Check:** "If the answer mentions a provider we don't have contracts with — the AI made it up from training data. BLOCKED."
# MAGIC
# MAGIC 4. **Date Plausibility:** "Any year outside 2000–2035 in the answer is flagged. Active contracts don't predate 2000 and no contract extends past 2035."
# MAGIC
# MAGIC 5. **Competitor Blocklist:** "If the answer attributes contract data to Kaiser, Aetna, Cigna, etc. — that's always hallucination. We don't have their data. Only flagged when the competitor name appears NEAR financial data ('Kaiser's rate is $X'), not casual mentions ('unlike Kaiser')."
# MAGIC
# MAGIC 6. **Universality Guard:** "If the answer says 'ALL providers have X' but the SQL only showed 180 out of 597 — caught. Overgeneralizing from a subset is dangerous in negotiations."
# MAGIC
# MAGIC 7. **Cross-Dimensional:** "If the answer claims 'Stanford tops both rates AND compliance' but the data shows Stanford tops rates and Sutter tops compliance — flagged."
# MAGIC
# MAGIC **Outcomes:**
# MAGIC - WARN = confidence downgraded (HIGH → MODERATE)
# MAGIC - BLOCK = answer rejected entirely, user gets refusal message
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Layer 4: Evidence Grounding
# MAGIC
# MAGIC **What to say:** "Final check: is there ANY verified evidence supporting this answer? If not — refuse."
# MAGIC
# MAGIC **How to explain:**
# MAGIC "Three steps:
# MAGIC 1. Check if any SQL query returned actual data (rows). If yes → grounded, pass.
# MAGIC 2. If no SQL data, score the retrieved text passages against the question keywords. If at least one passage matches 50%+ of the keywords → grounded, pass.
# MAGIC 3. If nothing grounds the answer → the system says 'I don't know' instead of guessing."
# MAGIC
# MAGIC **Why refuse instead of guess?**
# MAGIC "In contract negotiations, a wrong answer could cost millions in mispriced contracts. A polite 'I don't have enough evidence to answer this' costs nothing. The user just rephrases or looks manually."
# MAGIC
# MAGIC **What the user sees on refusal:**
# MAGIC "A message saying: 'I could not find verified evidence for this question. Please try with more specific provider names or contract terms.'"
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Confidence Scoring (after all 4 layers)
# MAGIC
# MAGIC **What to say:** "Every answer gets a confidence level based on what survived validation:"
# MAGIC
# MAGIC - **HIGH** = All layers pass, citations present, data from structured tables. Typical for rate lookups.
# MAGIC - **MODERATE** = Mostly grounded but minor gaps (e.g., vector search only, no SQL confirmation). Typical for explanation questions.
# MAGIC - **LOW** = Some evidence found but validation flagged concerns. Typical for complex multi-hop questions with partial data.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Anticipated Questions
# MAGIC
# MAGIC **Q: "How often does the system refuse to answer?"**
# MAGIC > Rarely — maybe 5-10% of questions. Those are typically very vague questions ("tell me everything about contracts") or questions about providers we genuinely don't have data for. Most real questions have evidence.
# MAGIC
# MAGIC **Q: "Can the hallucination checks be wrong? False positives?"**
# MAGIC > Yes, that's why most are WARN not BLOCK. A number might appear in a slightly different format than the check expects. WARN just lowers confidence — the answer still goes through. Only truly dangerous cases (wrong provider, competitor data, universality claims) are BLOCK.
# MAGIC
# MAGIC **Q: "Why no AI in the hallucination checks?"**
# MAGIC > Speed and determinism. AI calls cost money and take time. Pattern matching is instant, free, and gives the same result every time. No variability. When you run the same check twice, you get the same answer.
# MAGIC
# MAGIC **Q: "What's the total latency added by these 4 layers?"**
# MAGIC > Negligible. Layer 1 and 3 are pure string matching (milliseconds). Layer 2 is one SQL query (<100ms). Layer 4 is arithmetic on already-retrieved passages. Total overhead: under 200ms.

# COMMAND ----------

# DBTITLE 1,Summary and Closing — Talking Points
# MAGIC %md
# MAGIC ---
# MAGIC
# MAGIC # SUMMARY & CLOSING — Talking Points
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Key Message
# MAGIC > 8 independent quality checkpoints — 4 on data going in, 4 on answers coming out. Defense-in-depth. No single point of failure can produce a wrong answer.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## The Visual (draw this or point to it)
# MAGIC
# MAGIC ```
# MAGIC DATA SIDE:  PDF → Gate 1 → Gate 2 → Gate 3 → Gate 4 → Trusted Tables
# MAGIC                   (OCR)    (AI)     (Score)   (Transform)
# MAGIC
# MAGIC APP SIDE:   Query → Layer 1 → Layer 2 → Layer 3 → Layer 4 → Verified Answer
# MAGIC                   (Complete) (Absence) (Halluc.)  (Ground)
# MAGIC ```
# MAGIC
# MAGIC "8 independent checkpoints. Data is validated 4 times before it enters production. Answers are validated 4 more times before they reach the user."
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Key Business Outcomes (what leadership cares about)
# MAGIC
# MAGIC | Promise | How we deliver it |
# MAGIC | --- | --- |
# MAGIC | No wrong rates | Every dollar verified against source text (Pipeline Gate 2B + App Layer 3 Check 2) |
# MAGIC | No missed provisions | Absence claims cross-checked (App Layer 2) |
# MAGIC | No hallucinated facts | 7 independent automated checks |
# MAGIC | Complete answers | Multi-dimension detection ensures all parts addressed |
# MAGIC | Traceable to source | Every fact cites specific document + page |
# MAGIC | Graceful uncertainty | System says "I don't know" rather than guessing |
# MAGIC | Enterprise scale | 10,000+ docs, 597 providers, <3s responses |
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Success Metrics to Mention
# MAGIC
# MAGIC | Metric | Target |
# MAGIC | --- | --- |
# MAGIC | Answer accuracy (grounded in source) | > 95% |
# MAGIC | Retrieval precision (right docs found) | MRR@10 > 0.85 |
# MAGIC | Response time (complete answer) | < 3 seconds |
# MAGIC | Streaming first token | < 800ms |
# MAGIC | User satisfaction | > 4.5 / 5.0 |
# MAGIC | Cost per query | < $0.05 |
# MAGIC | Zero PHI exposure incidents | 0 |
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## The Bottom Line (closing statement)
# MAGIC
# MAGIC **What to say:**
# MAGIC "Four takeaways:
# MAGIC
# MAGIC 1. Data is validated 4 times before it enters production tables.
# MAGIC 2. Answers are validated 4 more times before they reach the user.
# MAGIC 3. Every fact is traceable to a specific source document and page.
# MAGIC 4. When evidence is insufficient, the system says 'I don't know' rather than risk a wrong answer.
# MAGIC
# MAGIC The result: stakeholders can trust the answers they receive. Every rate, every clause, every date — verified against the actual signed agreements."
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Final Anticipated Questions
# MAGIC
# MAGIC **Q: "Is this in production?"**
# MAGIC > The pipeline has processed 29 files (2,125 rate rules extracted, 320 clauses, 198 stop-loss provisions). Full production processing of all 10,329 files is ready to run. The application layer is operational.
# MAGIC
# MAGIC **Q: "What's the cost to run this?"**
# MAGIC > Pipeline: about $0.01-0.02 per file for AI extraction + judge. Queries: under $0.05 each. No expensive infrastructure — runs on serverless Databricks compute. No GPUs needed.
# MAGIC
# MAGIC **Q: "Who maintains this?"**
# MAGIC > The pipeline is automated. New files get processed automatically. The quality gates are self-enforcing. Maintenance is only needed when: (1) new document types appear that need new extraction prompts, or (2) thresholds need adjustment based on business feedback.
# MAGIC
# MAGIC **Q: "What's next?"**
# MAGIC > Three things: (1) Process all 10,329 PDFs through the pipeline (currently 29 done). (2) Expand the application to more user groups. (3) Add alerts for contract expiration and compliance deadlines.
# MAGIC
# MAGIC **Q: "How does this compare to what we had before?"**
# MAGIC > Before: 2-3 days per question, $40+ per lookup (analyst time), error-prone, unscalable.
# MAGIC > After: 3 seconds, $0.05, verified against source, available to anyone.
# MAGIC > That's an 800× cost reduction and 100,000× speed improvement.

# COMMAND ----------

# DBTITLE 1,Deep Dive — Parameter Explanations for Follow-Up Questions
# MAGIC %md
# MAGIC ---
# MAGIC
# MAGIC # PARAMETER DEEP DIVE — "What Is It? How? Why?"
# MAGIC
# MAGIC Use this section when someone asks for more detail on a specific threshold, score, or mechanism. Organized by Part.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC # PART 1 PARAMETERS
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Gate 1: OCR Quality Checks
# MAGIC
# MAGIC ### Average OCR Confidence ≥ 50%
# MAGIC
# MAGIC **What is it?**
# MAGIC Every word that the OCR engine reads from a PDF gets a confidence score from 0% to 100%. This is the OCR engine's own estimate of how sure it is that it read the word correctly. We average ALL word scores across ALL pages in the document to get one number.
# MAGIC
# MAGIC **How is it calculated?**
# MAGIC The OCR engine (PyMuPDF for digital PDFs, or AI-powered for scanned) outputs a list like: [{"word": "rate", "confidence": 0.95}, {"word": "$2,150", "confidence": 0.72}, ...]. We take the average of all confidence values: `Spark avg(confidence) across the entire document`.
# MAGIC
# MAGIC **Why 50%?**
# MAGIC We tested this empirically. Scanned faxes (which are still perfectly usable) naturally score 60-80%. Clean digital PDFs score 95-100%. Below 50% means more than half the words are uncertain — so a dollar amount like "$2,150" might actually be read as "$2,1S0" or "$Z,150". If we can't trust the numbers, the AI extraction downstream will produce garbage. We picked 50% (not higher) because we didn't want to reject readable-but-imperfect scans.
# MAGIC
# MAGIC **If someone says "why not 70% or 80%?":**
# MAGIC > A higher threshold would reject too many legitimate scanned documents. Some faxed contracts from smaller providers come in at 60-65% confidence but are still perfectly readable. 50% is the floor where text becomes unreliable.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### Words Per Page ≥ 10
# MAGIC
# MAGIC **What is it?**
# MAGIC Total word count from OCR divided by number of pages. This is the average number of words per page.
# MAGIC
# MAGIC **How is it calculated?**
# MAGIC `total_words / total_pages`. Simple division.
# MAGIC
# MAGIC **Why 10?**
# MAGIC A normal contract page has 200-400 words. 10 words/page is absurdly low — it means most pages are essentially blank, or they're images/charts with no extractable text. This catches:
# MAGIC - Cover pages mistakenly submitted as standalone documents
# MAGIC - Image-only PDFs where OCR produced almost nothing
# MAGIC - Corrupt files where only page headers were readable
# MAGIC
# MAGIC **If someone says "10 seems really low":**
# MAGIC > It IS really low — intentionally. This is a floor check, not a quality bar. It catches documents that are FUNDAMENTALLY unreadable, not ones that are just short. A 5-page amendment with 50 words/page (250 total) passes fine.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### Total Words ≥ 100
# MAGIC
# MAGIC **What is it?**
# MAGIC Sum of all words across all pages.
# MAGIC
# MAGIC **How is it calculated?**
# MAGIC `sum(word_count)` across all pages.
# MAGIC
# MAGIC **Why 100?**
# MAGIC 100 words is roughly half a paragraph. A real contract has thousands to tens of thousands of words. This catches files where the OCR engine essentially failed — producing almost nothing. It's complementary to words/page: a 50-page document could have 2 words per page (100 total) and pass words/page, but 100 total words from a 50-page doc is clearly broken.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### Non-ASCII Ratio < 5%
# MAGIC
# MAGIC **What is it?**
# MAGIC The percentage of characters that are NOT standard English letters, numbers, or punctuation (ASCII codes 32-126).
# MAGIC
# MAGIC **How is it calculated?**
# MAGIC Spark `regexp_replace` strips all standard ASCII characters. What remains = non-standard characters (things like ©, ®, ¿, §, Asian characters, etc.). Then: `remaining_chars / total_chars`.
# MAGIC
# MAGIC **Why 5%?**
# MAGIC When OCR engines misread text, they often produce random symbols. A document with 10% non-ASCII typically has corrupted text throughout — the OCR is hallucinating characters. 5% allows for the occasional trademark symbol (™) or section marker (§) which are legitimate in legal documents, but catches systemic corruption.
# MAGIC
# MAGIC **If someone says "what about contracts with Spanish text?":**
# MAGIC > Valid concern. Characters like é, ñ, ü are technically outside basic ASCII. In practice, our provider contracts are in English. If we ever process bilingual contracts, this threshold would need adjustment.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### Blank Page Ratio ≤ 20%
# MAGIC
# MAGIC **What is it?**
# MAGIC Percentage of pages that have fewer than 5 words.
# MAGIC
# MAGIC **How is it calculated?**
# MAGIC Count pages where `word_count < 5`, divide by total pages.
# MAGIC
# MAGIC **Why 20%?**
# MAGIC Many legitimate contracts have separator pages ("EXHIBIT A" on an otherwise blank page), fax cover sheets, or section dividers. Up to 20% blank is normal. Above 20% suggests either: the document is mostly empty, or the OCR failed on most pages (produced text only for a few pages).
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Gate 1B: Domain Check
# MAGIC
# MAGIC ### ≥3 Categories with ≥5 Total Markers
# MAGIC
# MAGIC **What is it?**
# MAGIC We check the first 5 pages for healthcare contract keywords in 6 categories: payer terms ("Blue Shield", "health plan"), provider terms ("hospital", "physician group"), legal language ("whereas", "shall"), financial terms ("rate", "capitation", "per diem"), dates ("effective date", "term"), structural elements ("exhibit", "appendix", "schedule").
# MAGIC
# MAGIC **How is it calculated?**
# MAGIC For each category, we have a keyword list. We use Spark `contains()` on the concatenated text of pages 1-5. Each keyword hit increments that category's counter. We then count: how many categories got at least 1 hit, and what's the total hits across all categories.
# MAGIC
# MAGIC **Why ≥3 categories and ≥5 markers?**
# MAGIC - 3 categories: A healthcare contract should mention at least payer/provider terms, legal language, AND financial terms. If only 1 or 2 categories are present, it might be a letter or memo, not a contract.
# MAGIC - 5 markers total: Prevents a single lucky keyword from passing. You need multiple signals distributed across categories.
# MAGIC
# MAGIC **What this catches:**
# MAGIC Someone accidentally drops a non-contract PDF (a presentation, a spreadsheet export, a fax receipt) into the source folder. Without this gate, the AI would try to "extract rates" from a PowerPoint PDF and produce nonsense.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Gate 2: AI Extraction Checks
# MAGIC
# MAGIC ### AI Confidence ≥ 70%
# MAGIC
# MAGIC **What is it?**
# MAGIC The LLM returns a self-assessed confidence score (0.0-1.0) with every extraction. This is a field in the structured JSON output called `extraction_confidence`. It reflects how certain the model is about its output given the quality of the input text.
# MAGIC
# MAGIC **How is it calculated?**
# MAGIC The AI model determines this internally based on: clarity of input text, whether it found contradictions, how much ambiguity it encountered, and whether required fields were clearly present vs. inferred.
# MAGIC
# MAGIC **Why 70%?**
# MAGIC - Below 70% = the model ITSELF is saying "I'm not confident about this." If the AI is confused, we shouldn't trust the output.
# MAGIC - Why not higher (like 90%)? Complex multi-page contracts naturally produce lower confidence even when extraction is correct. A 200-page agreement with inconsistent formatting might get 75% confidence but still have perfectly valid extraction. 70% captures genuinely ambiguous cases without being overly strict.
# MAGIC
# MAGIC **If someone says "isn't the AI marking its own homework?":**
# MAGIC > Partially yes — which is why we don't rely on this alone. Gate 2B cross-references against source text, and Gate 3 uses a SEPARATE AI to verify. The self-confidence is just the first quick filter.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### Rates Present ≥ 1 (Base Agreements Only)
# MAGIC
# MAGIC **What is it?**
# MAGIC If the document is classified as a "Base Agreement" (new contract or renewal), the AI must have extracted at least 1 rate item.
# MAGIC
# MAGIC **How is it calculated?**
# MAGIC `F.size(extraction.rates) > 0` — checks if the rates array has any items.
# MAGIC
# MAGIC **Why only for base agreements?**
# MAGIC Base agreements define the financial relationship — they MUST have rates. But amendments often only modify clauses ("change the termination notice period from 90 to 120 days") without touching rates. Templates may not have specific dollar amounts. Requiring rates from amendments would create false failures.
# MAGIC
# MAGIC **If someone says "what if it's a base agreement that genuinely has no rates?":**
# MAGIC > That would be unusual — a base agreement without financial terms is arguably not a complete agreement. But if it happens, it fails this gate and goes to manual review, which is the correct outcome for an unusual document.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Gate 2B: Hallucination Cross-Reference
# MAGIC
# MAGIC ### Date Grounding — 3 Format Check
# MAGIC
# MAGIC **What is it?**
# MAGIC We take the effective_date the AI extracted and search the original OCR text to confirm that date actually appears in the document.
# MAGIC
# MAGIC **How is it calculated?**
# MAGIC Three `contains()` checks:
# MAGIC 1. ISO format: "2024-01-01" — search the OCR text for this exact string
# MAGIC 2. US format: "01/01/2024" — rearrange the ISO date into MM/DD/YYYY and search
# MAGIC 3. Year only: "2024" — search for just the year
# MAGIC
# MAGIC If ANY of the three returns true, the date is grounded. If ALL three return false, the date is flagged.
# MAGIC
# MAGIC **Why 3 formats?**
# MAGIC Contracts write dates inconsistently: "January 1, 2024", "1/1/2024", "01/01/2024", "2024-01-01". Rather than trying to handle every possible format, we check the three most common patterns. The year-only check ("2024") is the safety net — even if the specific date format doesn't match, the year should appear SOMEWHERE in the document.
# MAGIC
# MAGIC **Why NULL dates auto-pass?**
# MAGIC If the AI couldn't find a date and returned NULL, that's honest — it's admitting uncertainty. We don't want to penalize honesty. The "fields present" check in Gate 2 separately handles the requirement that dates must exist.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### Provider Name — 5-Strategy Match
# MAGIC
# MAGIC **What is it?**
# MAGIC We verify the provider name the AI extracted actually appears in the document, trying 5 different matching approaches.
# MAGIC
# MAGIC **The 5 strategies:**
# MAGIC 1. **Exact match:** Is the full extracted name in the OCR text? (e.g., "Stanford Health Care" found in document)
# MAGIC 2. **Registry inside extracted:** Is our known registry name a substring of what the AI extracted? (e.g., registry has "Stanford Health", AI extracted "Stanford Health Care Associates" — the registry name is inside it)
# MAGIC 3. **Extracted inside registry:** Is what the AI extracted a substring of our registry name? (e.g., AI extracted "Stanford", registry has "Stanford Health Care" — the extracted is inside the registry)
# MAGIC 4. **ID match:** Does the provider_id in the extraction match our provider registry?
# MAGIC 5. **First word in text:** Does just the first word of the extracted name appear in the OCR text? (e.g., "Stanford" found in document)
# MAGIC
# MAGIC **Why 5 strategies?**
# MAGIC Provider names are messy. The same provider might be:
# MAGIC - "Stanford Health Care" (official)
# MAGIC - "Stanford Medical Center" (colloquial)
# MAGIC - "Stanford University Medical Center" (legal name on contract)
# MAGIC - "STANFORD HEALTH CARE" (all caps in headers)
# MAGIC
# MAGIC A single exact-match approach would fail too often. 5 strategies provide generous matching while still catching COMPLETE fabrications (AI inventing a provider from training data that has no trace in the document).
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Gate 3: Quality Scoring
# MAGIC
# MAGIC ### The 9 Dimensions — What Each Measures and Why
# MAGIC
# MAGIC **Dimension 1: Dollar Values**
# MAGIC - **What:** Count of extracted rates that have actual dollar amounts (rate_numeric > 0)
# MAGIC - **Formula:** `min(dollar_rates_found / min_expected, 1.0)` — capped at 100%
# MAGIC - **min_expected by doc type:**
# MAGIC   - Base Agreements: 5 (a real base agreement defines multiple service lines)
# MAGIC   - Amendments: 0 (may only change clauses)
# MAGIC   - Templates: 0 (may have no specific amounts)
# MAGIC - **Edge case:** If min_expected = 0, score = 100% if any rates found, 50% if none (neutral)
# MAGIC - **Why this matters:** If you extract a base agreement and find 0 dollar amounts, something went fundamentally wrong
# MAGIC
# MAGIC **Dimension 2: Percentages**
# MAGIC - **What:** Count of rates where `formula_text` contains "%" (e.g., "85% of Medicare")
# MAGIC - **Formula:** `min(pct_rates / 3, 1.0)`
# MAGIC - **Why 3?** Most base agreements have at minimum: a coinsurance rate (80/20 split), a Medicare percentage reference ("110% of Medicare"), and a stop-loss percentage ("after 100% of $500K"). Finding 3+ means the AI captured percentage-based terms properly.
# MAGIC - **Why this matters:** Many healthcare rates are percentage-based, not flat dollar amounts. Missing these means missing a major payment mechanism.
# MAGIC
# MAGIC **Dimension 3: Dates**
# MAGIC - **What:** Are effective_date and expiration_date present in the extraction?
# MAGIC - **Formula:** `0.6 × (1 if effective_date exists) + 0.4 × (1 if expiration_date exists)`
# MAGIC - **Why 60/40?** Effective date tells you WHEN terms activate — critical for knowing which rates are current. Expiration date matters less because many contracts auto-renew without an explicit end date.
# MAGIC - **Example:** Has effective date but no expiration = 60%. Has both = 100%. Has neither = 0%.
# MAGIC
# MAGIC **Dimension 4: Service Specificity**
# MAGIC - **What:** Are rate services granularly labeled ("Inpatient - ICU") or vague ("Inpatient")?
# MAGIC - **How detected:** If the rate_domain contains a hyphen ("-"), it's granular — the AI broke it into domain + sub-service.
# MAGIC - **Formula:** `min((granular_count / total_rates) × 2, 1.0)`
# MAGIC - **Why multiply by 2?** Getting specific service names is HARD for the AI (it has to infer structure from unformatted PDF text). We reward specificity. Even 50% granularity (half your rates are specific) gives a perfect score.
# MAGIC - **Why this matters:** "Inpatient" alone is useless for negotiations. "Inpatient - ICU" vs "Inpatient - Subacute" vs "Inpatient - Med/Surg" is what negotiators actually need.
# MAGIC
# MAGIC **Dimension 5: Topic Coverage**
# MAGIC - **What:** How many of the expected contract sections were extracted?
# MAGIC - **6 possible sections:** rates, clauses, stop_loss, carve_outs, compliance_requirements, definitions
# MAGIC - **Formula:** `found_sections / expected_sections`
# MAGIC - **Expected by doc type:**
# MAGIC   - Base Agreements: all 6
# MAGIC   - Amendments: 2-3 (clauses, compliance, maybe definitions)
# MAGIC   - Templates: 3 (clauses, definitions, compliance)
# MAGIC - **Why this matters:** A base agreement with only rates extracted (no clauses, no stop-loss) is incomplete — missing critical legal provisions that affect financial risk.
# MAGIC
# MAGIC **Dimension 6: Source References**
# MAGIC - **What:** Can extracted items be traced back to specific PDF pages?
# MAGIC - **Formula:** `(items_with_page_number × 0.6 + items_with_exhibit_reference × 0.4) / total_items`
# MAGIC - **Why 60/40?** Page numbers ("page 14") let you go directly to the source. Exhibit references ("Exhibit A") are vaguer but still useful. Page numbers are more precise, hence weighted higher.
# MAGIC - **Why this matters:** Without page references, users can't verify answers. The whole "cited answer" promise depends on traceability.
# MAGIC
# MAGIC **Dimension 7: Schema Fill**
# MAGIC - **What:** Are key data fields populated (not null) in the extracted items?
# MAGIC - **Checks:** Sample first 20 items, check 5 specific fields each:
# MAGIC   - Rates: rate_domain, formula_type, rate_numeric, page_number, network_tier
# MAGIC   - Clauses: clause_category, clause_text, section_reference, page_number
# MAGIC - **Formula:** `non_null_fields / total_field_slots`
# MAGIC - **Why only 20?** Performance. If the first 20 are well-filled, the rest likely are too. Full scan would be wasteful.
# MAGIC - **Why this matters:** An extracted rate with a dollar amount but no domain label ("$2,150" for WHAT service?) is nearly useless.
# MAGIC
# MAGIC **Dimension 8: Page Accuracy**
# MAGIC - **What:** Are the cited page numbers actually valid (within the document's page count)?
# MAGIC - **Formula:** `1.0 - (invalid_pages / total_items)` where invalid = page_number > total_pages or < 1
# MAGIC - **Example:** 50 items, 2 cite page 72 in a 45-page doc = 1.0 - (2/50) = 96%
# MAGIC - **Why this matters:** Invalid page references mean the AI invented citations. This erodes trust.
# MAGIC
# MAGIC **Dimension 9: Deduplication**
# MAGIC - **What:** Are extracted items unique? (No identical duplicates.)
# MAGIC - **Key construction:** `"{rate_domain}|{rate_numeric}|{page_number}"` for rates, `"{clause_category}|{clause_text[:50]}|{page_number}"` for clauses
# MAGIC - **Formula:** `unique_keys / total_keys`
# MAGIC - **Example:** 50 rates but 2 have identical domain+amount+page = 48/50 = 96%
# MAGIC - **Why this matters:** Duplicate rates would double-count financial exposure in benchmarks. Duplicate clauses would corrupt analytics.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### Weighted Scoring — Why Different Weights?
# MAGIC
# MAGIC **Base Agreements (dollar values weighted 20%):**
# MAGIC "For a base agreement, rates ARE the contract. If you miss the dollar amounts, you missed the point. That's why dollar values get the highest weight."
# MAGIC
# MAGIC **Amendments (topic coverage weighted 25%):**
# MAGIC "Amendments exist to CHANGE specific provisions. Whether the AI found the right sections is more important than whether it found dollar amounts (amendments often don't have any). Topic coverage tells us: did we capture what this amendment actually changes?"
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### Composite Score: Coverage × 60% + Accuracy × 40%
# MAGIC
# MAGIC **What is Coverage?**
# MAGIC Weighted average of the 9 dimension scores. One number (0-100%) that says "how thoroughly did we extract this document?"
# MAGIC
# MAGIC **What is Accuracy?**
# MAGIC A second AI (the "judge") independently verifies a sample: 3 rates per file. Checks if the numbers are exactly correct against the source page text.
# MAGIC
# MAGIC **Why 60/40 (not 50/50)?**
# MAGIC - Coverage measures ALL dimensions across ALL items
# MAGIC - Accuracy only measures 3 items per file (a sample)
# MAGIC - A file could have 100% accuracy on 3 items but only extracted 3 items out of 50 (terrible coverage)
# MAGIC - Broad extraction matters slightly more than pinpoint accuracy on a small sample
# MAGIC
# MAGIC **Why ≥ 65% threshold (not higher)?**
# MAGIC - Healthcare contracts vary enormously in structure
# MAGIC - A 5-page amendment naturally scores lower on "topic coverage" than a 200-page base agreement
# MAGIC - 65% captures documents that are meaningfully extracted while allowing natural variation
# MAGIC - Below 65% = genuine quality concern that needs human review
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### The Judge (Accuracy Score)
# MAGIC
# MAGIC **What does the judge see?**
# MAGIC Two things: (1) the actual OCR text from a specific page, (2) what the first AI claims it extracted from that page.
# MAGIC
# MAGIC **What does the judge answer?**
# MAGIC - GROUNDED: "Is this rate actually on this page?" (not confused with another page)
# MAGIC - ACCURATE: "Is the dollar amount exactly right?" (not rounded, not transposed)
# MAGIC - COMPLETE: "Were other items on this page missed?" (anything else the first AI didn't extract)
# MAGIC
# MAGIC **Why do we use the "accurate" score (not grounded or complete)?**
# MAGIC - Grounded is too lenient: item might be on the page but the number could be wrong ($2,150 vs $2,200)
# MAGIC - Complete is too strict: missing items are already caught by the coverage score (dimension 5, topic coverage)
# MAGIC - Accurate is the sweet spot: "the facts you DID extract are correct"
# MAGIC
# MAGIC **Temperature = 0.0 — what does that mean?**
# MAGIC "We run the judge with zero temperature, which means deterministic output — no randomness, no creativity. Run it twice, get the same answer. This is critical for a quality gate — you want consistent, repeatable judgments."
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Gate 4: Transform Integrity
# MAGIC
# MAGIC ### Row Drop Rate ≤ 10%
# MAGIC
# MAGIC **What is it?**
# MAGIC Percentage of items in the extraction JSON that didn't make it into the final Delta table.
# MAGIC
# MAGIC **Why does this happen?**
# MAGIC Some items legitimately fail parsing during the JSON-to-table conversion. Example: a rate item with no numeric value ("as negotiated") can't be inserted into a column expecting a number.
# MAGIC
# MAGIC **Why 10%?**
# MAGIC Up to 10% loss is acceptable as normal parsing edge cases. Beyond 10% = something systematic is wrong (e.g., a schema mismatch, a bug in the transformation code).
# MAGIC
# MAGIC ### Null Rate ≤ 50%
# MAGIC
# MAGIC **What is it?**
# MAGIC Percentage of rows in the rates table where `rate_numeric` is NULL.
# MAGIC
# MAGIC **Why 50% and not lower?**
# MAGIC Some contract items genuinely lack explicit dollar amounts: "rates as per attached schedule", "rates per Medicare fee schedule", or percentage-only rates. These are legitimate NULL rate_numeric values. 50% is generous for this reason. But if MORE than half of all rates have no dollar amount, the extraction fundamentally failed to capture the financials.
# MAGIC
# MAGIC ### Date Range: 1990-2035
# MAGIC
# MAGIC **Why 1990?**
# MAGIC Blue Shield's earliest digitized contracts date to approximately 1990. Nothing legitimate in our system predates that.
# MAGIC
# MAGIC **Why 2035?**
# MAGIC The longest healthcare contract terms we've seen are 5-10 years. No contract signed today extends to 2035+. A date of 2078 or 1850 is clearly a parsing error.
# MAGIC
# MAGIC **If someone says "what about historical contracts?":**
# MAGIC > Historical contracts from before 1990 weren't digitized. If we ever scan historical paper archives, we'd adjust this bound. For now, 1990 is the floor of what we have.
# MAGIC
# MAGIC ### Rate Ceiling: ≤ $15,000,000
# MAGIC
# MAGIC **What is it?**
# MAGIC Maximum allowed dollar amount for any single rate.
# MAGIC
# MAGIC **Why $15M?**
# MAGIC The highest legitimate healthcare rates are shared savings targets or large institutional contracts that can reach several million dollars. $15M provides comfortable headroom. Above $15M is always a parsing error — typically the AI read a contract ID number (like "Agreement #25000000") as a dollar amount.
# MAGIC
# MAGIC ### Duplicate PKs = 0 (Zero Tolerance)
# MAGIC
# MAGIC **What is it?**
# MAGIC The combination of (file_id + item_type + sequence_number) must be unique. No exceptions.
# MAGIC
# MAGIC **Why zero tolerance?**
# MAGIC Duplicates mean the same rate or clause was inserted twice. This would:
# MAGIC - Double-count financial exposure in benchmarks
# MAGIC - Produce wrong percentile rankings
# MAGIC - Corrupt analytics
# MAGIC - Cause incorrect answers to queries
# MAGIC
# MAGIC Unlike the other checks (which allow some tolerance), duplicates are ALWAYS a bug, never a legitimate data state.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC # PART 2 PARAMETERS
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Renewal Priority Score: Urgency(0-40) + Impact(0-40) + Risk(0-20)
# MAGIC
# MAGIC **Urgency (0-40):**
# MAGIC - Based on how soon the contract expires
# MAGIC - Uses sigmoid decay: score increases sharply as deadline approaches
# MAGIC - A contract expiring in 6 months might score 30. One expiring next month scores 40.
# MAGIC - Why sigmoid (not linear)? Because urgency isn't linear — there's a tipping point where "coming soon" becomes "critical."
# MAGIC
# MAGIC **Impact (0-40):**
# MAGIC - Based on financial exposure (how much money flows through this contract)
# MAGIC - Log-scaled: going from $100K to $1M adds more urgency than going from $10M to $11M
# MAGIC - Why log-scaled? Because a $1M contract going unrenewed is proportionally more dangerous than adding $1M to an already-$10M contract.
# MAGIC
# MAGIC **Risk (0-20):**
# MAGIC - Compliance gaps, unusual clauses, missing provisions
# MAGIC - Binary flags that add up: has compliance gap (+5), has non-standard clause (+5), etc.
# MAGIC
# MAGIC **Thresholds:**
# MAGIC - ESCALATE ≥ 80: Needs immediate executive attention (expiring soon + high financial exposure + risk factors)
# MAGIC - PRIORITIZE 60-79: Should be in active negotiation
# MAGIC - MONITOR 40-59: On the radar but not urgent
# MAGIC - MAINTAIN < 40: Healthy contract, routine management
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Vector Search Parameters
# MAGIC
# MAGIC ### 1,024 Dimensions
# MAGIC
# MAGIC **What is it?**
# MAGIC Each text chunk gets converted into a list of 1,024 numbers. This is its "meaning" represented mathematically.
# MAGIC
# MAGIC **Why 1,024?**
# MAGIC This is determined by the embedding model (`databricks-gte-large-en`). Larger dimensions = more nuance in meaning representation. 1,024 is the sweet spot: enough precision to distinguish "subacute per diem" from "ICU per diem" while being computationally efficient.
# MAGIC
# MAGIC ### Cosine Similarity
# MAGIC
# MAGIC **What is it?**
# MAGIC The mathematical way we compare two vectors to see how similar they are. It measures the angle between two vectors — if they point in the same direction, similarity = 1.0. Perpendicular = 0.0.
# MAGIC
# MAGIC **Why cosine (not Euclidean distance)?**
# MAGIC Cosine ignores magnitude and focuses on direction. Two passages about "subacute rates" will point in similar directions regardless of their length. Euclidean distance would penalize length differences.
# MAGIC
# MAGIC ### 1,363 Legal Units
# MAGIC
# MAGIC **What are they?**
# MAGIC Each legal unit is a self-contained chunk of contract content: one rate table, one clause, one stop-loss provision, one carve-out, one definition, or one metadata block.
# MAGIC
# MAGIC **Why chunk into units?**
# MAGIC Whole documents are too large for embedding (meaning gets diluted). Individual sentences are too small (lose context). Legal units are the Goldilocks size: specific enough to be useful, complete enough to be meaningful.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC # PART 3 PARAMETERS
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Question Routing: 16 Categories
# MAGIC
# MAGIC **Why 16?**
# MAGIC Healthcare contracts cover diverse domains: financial rates, legal clauses, compliance requirements, risk factors, temporal history, network composition, provider profiles, comparative analysis, etc. Each domain needs a different retrieval approach. 16 categories = precise targeting. Fewer categories would mean one-size-fits-all which is slower and less accurate.
# MAGIC
# MAGIC ## 6 Override Rules
# MAGIC
# MAGIC **What are they?**
# MAGIC Deterministic rules that correct common AI misclassifications. They fire BEFORE the AI's routing decision takes effect.
# MAGIC
# MAGIC **Examples:**
# MAGIC - RE-1: If question contains rate keywords ("$", "per diem", "capitation") but was classified as clause search → override to rate lookup
# MAGIC - RE-2: If question mentions specific dollar amounts → force SQL path (vector search can't do precise number matching)
# MAGIC - CE-FIX: If question mentions compliance terms → ensure compliance table is included
# MAGIC - PROF-SQL: If question asks about provider status/demographics → force profile lookup
# MAGIC
# MAGIC **Why hardcoded rules instead of letting AI decide?**
# MAGIC Determinism. AI routing is right 90% of the time, but the 10% it gets wrong produces bad answers. Hardcoded rules are 100% predictable and catch the known failure modes.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Multi-Step Reasoning Bounds
# MAGIC
# MAGIC ### Maximum 10 Steps
# MAGIC
# MAGIC **What is it?**
# MAGIC For complex questions requiring multiple sub-queries, the system can execute at most 10 reasoning steps before it MUST return an answer.
# MAGIC
# MAGIC **Why 10?**
# MAGIC Empirical testing showed that even the most complex questions (4-way provider comparison across 3 dimensions) resolve in 6-7 steps. 10 provides headroom while preventing infinite loops from badly-formed questions or circular reasoning.
# MAGIC
# MAGIC ### $15 Cost Cap
# MAGIC
# MAGIC **What is it?**
# MAGIC Total AI spend per single user query cannot exceed $15.
# MAGIC
# MAGIC **Why $15?**
# MAGIC Each AI call costs $0.01-0.05. At 10 steps with multiple calls each, the theoretical maximum is ~$5-10 for a complex query. $15 provides safety margin. In practice, even complex questions cost under $1. The cap prevents a pathological case (e.g., a very long document triggering repeated full-text AI calls) from running up charges.
# MAGIC
# MAGIC ### 120-Second Timeout
# MAGIC
# MAGIC **What is it?**
# MAGIC If the system hasn't completed after 120 seconds, it returns whatever it has so far with a MODERATE confidence note.
# MAGIC
# MAGIC **Why 120 seconds?**
# MAGIC User experience research shows anything over 30 seconds feels "broken" to users. We allow up to 120s for complex multi-step questions, but the vast majority (80%) complete in 2-3 seconds. The timeout guarantees the system never hangs indefinitely.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC # PART 4 PARAMETERS
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Layer 1: Completeness
# MAGIC
# MAGIC ### 60% Coverage Threshold
# MAGIC
# MAGIC **What is it?**
# MAGIC If the answer addresses fewer than 60% of the detected question dimensions, it's considered incomplete.
# MAGIC
# MAGIC **Why 60%?**
# MAGIC For 3+ dimension questions, answering 2 out of 3 (67%) is acceptable — maybe one dimension has legitimately no data. But answering 1 out of 3 (33%) is clearly incomplete.
# MAGIC
# MAGIC **The 2-dimension special rule:**
# MAGIC If exactly 2 dimensions are asked, BOTH must be present (100% coverage required). Rationale: with only 2 topics, missing one is a 50% gap — the user notices immediately.
# MAGIC
# MAGIC ### 7 Dimensions
# MAGIC
# MAGIC **Why these 7?**
# MAGIC They map to the main question categories healthcare negotiators ask about: money (financial), regulatory (compliance), exposure (risk), legal provisions (clause), history (temporal), geography/systems (network), and demographics (profile). These were derived from analyzing the actual questions our contracts team asks.
# MAGIC
# MAGIC ### Keyword Detection (not AI)
# MAGIC
# MAGIC **Why substring matching instead of AI classification?**
# MAGIC Speed and cost. Running an AI classifier on every dimension check for every question would add latency and cost. Simple keyword matching (`"rate" in question.lower()`) is instant, free, and catches 95% of cases. The 5% edge cases (creative phrasing) are handled by the override rules.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Layer 2: Absence Verification
# MAGIC
# MAGIC ### "Only fires on ~15% of answers"
# MAGIC
# MAGIC **Why not check every answer?**
# MAGIC Most answers contain positive data ("Stanford's rate is $2,150"). There's nothing to verify about existence — the data is right there in the answer. This layer only fires when it detects absence language: "no data found", "does not have", "not available". That's about 15% of responses.
# MAGIC
# MAGIC ### SELECT 1 ... LIMIT 1
# MAGIC
# MAGIC **Why this specific query?**
# MAGIC It's the cheapest possible existence check. We don't need to retrieve the data — just confirm it EXISTS. `SELECT 1 LIMIT 1` returns in <100ms regardless of table size because it stops at the first matching row.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Layer 3: Hallucination Checks
# MAGIC
# MAGIC ### >4 Digits (Check 2, Numeric Grounding)
# MAGIC
# MAGIC **Why only flag numbers with more than 4 digits?**
# MAGIC Small numbers appear everywhere: "2 providers", "30 days", "100%". Flagging these would produce thousands of false positives. But a specific number like "$2,150" or "$145,000" should be traceable to a source. The 4-digit threshold separates common numbers from contract-specific figures.
# MAGIC
# MAGIC ### 2000-2035 Date Range (Check 4)
# MAGIC
# MAGIC **Why different from the pipeline's 1990-2035?**
# MAGIC The pipeline validates extraction of historical dates from old contracts (hence 1990). The application layer validates ANSWERS to users — users are asking about active contracts, which don't predate 2000. The tighter 2000 bound catches more hallucinations in the answer context.
# MAGIC
# MAGIC ### 150-Character Context Window (Check 5, Competitor)
# MAGIC
# MAGIC **What is it?**
# MAGIC When we find a competitor name (like "Kaiser"), we look at the 150 characters surrounding it to check for data indicators ("rate", "$", "per diem", "contract"). If data indicators are present within 150 chars of the competitor name, it's flagged.
# MAGIC
# MAGIC **Why 150 characters?**
# MAGIC - Long enough to capture a complete sentence with the competitor name + associated data
# MAGIC - Short enough to avoid false positives from unrelated content paragraphs away
# MAGIC - Empirically tested: "Kaiser Permanente's rate is $X per diem" is well within 150 chars. But a competitor mentioned 3 paragraphs before a rate discussion won't trigger.
# MAGIC
# MAGIC ### WARN vs BLOCK Outcomes
# MAGIC
# MAGIC **WARN (Checks 1, 2, 4, 7):** Confidence downgrade only. The answer still reaches the user, but at a lower confidence level. Used for checks where false positives are possible (formatting differences, edge cases).
# MAGIC
# MAGIC **BLOCK (Checks 3, 5, 6):** Answer is rejected entirely. Used for checks where a positive finding is ALWAYS a real hallucination:
# MAGIC - Wrong provider name = always fabricated
# MAGIC - Competitor data = always hallucinated (we don't have their data)
# MAGIC - Universality claims without proof = always dangerous
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Layer 4: Grounding
# MAGIC
# MAGIC ### 0.5 Relevance Threshold
# MAGIC
# MAGIC **What is it?**
# MAGIC A retrieved passage must match at least 50% of the question's keywords to count as "grounded evidence."
# MAGIC
# MAGIC **How is it calculated?**
# MAGIC Extract meaningful keywords from the question (remove stop words like "the", "is", "what"). For each passage: count how many of those keywords appear in it. `score = keywords_found / total_keywords`.
# MAGIC
# MAGIC **Why 0.5?**
# MAGIC A passage matching fewer than half the keywords is probably tangential — it was retrieved by vector similarity but doesn't actually address the question. Example: question is about "Stanford inpatient per diem rates" (4 keywords). A passage that only mentions "Stanford" (25% match) is probably about something else. One that mentions "Stanford" + "per diem" + "rates" (75%) is clearly relevant.
# MAGIC
# MAGIC ### Structured Data Bypasses Passage Scoring
# MAGIC
# MAGIC **Why?**
# MAGIC If a SQL query returned actual rows of data (provider name, rate amount, effective date), that's stronger evidence than any text passage. The data IS the answer — no need to score passages against keywords. This makes rate lookups instant-pass for grounding.
# MAGIC
# MAGIC ### Refuse vs Guess
# MAGIC
# MAGIC **Why refuse?**
# MAGIC In healthcare contract negotiations:
# MAGIC - A wrong rate could misprice a contract worth millions
# MAGIC - A false absence claim could cause a negotiator to miss a critical provision
# MAGIC - A confident-sounding guess with no evidence could change a deal outcome
# MAGIC
# MAGIC The cost of saying "I don't know" = the user asks differently or checks manually (minutes of delay).
# MAGIC The cost of a wrong answer = potentially millions in mispriced contracts or legal exposure.
# MAGIC
# MAGIC The math is clear: refuse when uncertain.