# Master Test Plan (MTP) — Local RAG WebApp

**Version:** 1.0  
**Date:** 2025-09-05  
**Owner:** <QA Lead>  
**Reviewed by:** <Eng Manager / Architect / Product>  
**Approved by:** <Sponsor>

---

## 1) Purpose & Scope
Verify that the system satisfies the user-facing flow (upload → parse → **adaptive chunking** → embed → index → retrieve → **dynamic-k** → generate & **stream** with citations) and the non-functional constraints (local-only, responsiveness, resource awareness), while conforming to the **architecture (HLD)** and **component design (LLD)**.

**In-scope**
- Features and constraints captured in **SRS_RAG_WebApp.md** (functional & non-functional).
- Architectural elements in **HLD_RAG_WebApp.md** (subsystems, interfaces, data flow).
- Components & APIs in **LLD_RAG_WebApp.md** (React UI, WS events, algorithms, Qdrant wrapper).

**Out-of-scope**
- Third-party cloud integrations (none by design).
- Multi-user tenancy and remote deployment (future work).

---

## 2) References
- SRS: `SRS_RAG_WebApp.md`
- HLD: `HLD_RAG_WebApp.md`
- LLD: `LLD_RAG_WebApp.md`
- Policies/Standards: WCAG 2.1 AA (UI), local-only privacy policy, internal coding standards.

---

## 3) Traceability Strategy

### 3.1 ID Conventions
- **SRS Functional:** `SRS-FR-###`  
- **SRS Non-Functional:** `SRS-NFR-###`  
- **HLD Module/Dataflow/API:** `HLD-MOD/DF/API-###`  
- **LLD Component/Class/Interface/DB:** `LLD-CMP/CLS/INT/DB-###`  
- **Test Case:** `TC-<level>-####` (e.g., `TC-UNIT-0021`, `TC-SYS-0045`)  
- **Defect:** `BUG-#####`  
- **Risk:** `RISK-###`

### 3.2 Mapping Rules
- Every SRS item maps to ≥1 HLD element and ≥1 test case.  
- Every HLD element maps to ≥1 LLD element and ≥1 integration/system test.  
- Every LLD element maps to ≥1 unit/component test.  
- Defects map upstream to the lowest unmet artifact (TC → LLD → HLD → SRS).

### 3.3 Master Traceability Matrix (excerpt)
| SRS ID | Title | HLD Mapping | LLD Mapping | Representative Tests | Status |
|---|---|---|---|---|---|
| SRS-FR-3.1 | Upload & Library Management | HLD-MOD-DocMgmt; HLD-DF-Storage | LLD-CMP-DocumentService; LLD-INT-`/api/documents` | TC-FUNC-001/002/003 | Planned |
| SRS-FR-3.2 | Auto Preprocessing & **Adaptive Chunking** | HLD-MOD-RAG | LLD-CMP-AdaptiveChunker; `choose_chunk_policy()` | TC-FUNC-010/011/012 | Planned |
| SRS-FR-3.2 | Local Embeddings & Indexing | HLD-MOD-RAG; HLD-MOD-DataStore | LLD-CMP-Embedder; LLD-DB-QdrantIndex | TC-FUNC-020/021 | Planned |
| SRS-FR-3.3 | Query→Retrieve→**Dynamic-k**→Generate | HLD-MOD-RAG; HLD-MOD-LLM | LLD-CMP-Retriever; DynamicKController; LLMRunner | TC-FUNC-030/031/032 | Planned |
| SRS-FR-3.3/3.4 | **Streaming** Answers & Chat History | HLD-MOD-ChatUI | LLD-INT-WS `/ws/stream`; ChatView; StreamingIndicator | TC-UI-040/041; TC-E2E-050 | Planned |
| SRS-NFR | Local-only; Performance; Reliability; A11y | HLD Local Client/Server | LLD Security/Perf sections | TC-SEC-120; TC-PERF-100/101/102; TC-REL-110/111; TC-A11Y-131 | Planned |

> Full RTM maintained in the QA workbook.

---

## 4) Test Strategy

### 4.1 Levels
- **Unit (LLD)** — Functions/classes & error handling per LLD.
  - *Entry:* LLD reviewed; builds pass.
  - *Exit:* ≥90% critical logic coverage; high/critical defects fixed.
- **Component (LLD↔LLD)** — Contracts between collaborating classes/components.
  - *Entry:* Dependent units pass; stubs/mocks ready.
  - *Exit:* All component contracts validated; negative paths covered.
- **Integration (HLD)** — Interfaces across services/modules (REST, WebSocket, Qdrant).  
- **System (SRS)** — End-to-end user journeys.  
- **E2E (UI)** — Browser-level automation (Playwright/Cypress).  
- **Non-Functional** — Performance, Reliability, Security/Privacy, Usability/A11y, Portability.

### 4.2 Tooling
- **Unit/Component:** pytest + coverage; React Testing Library + Vitest.
- **Integration/System:** pytest (HTTPX) + dockerized Qdrant (embedded/local mode).
- **E2E:** Playwright (trace/video on fail).
- **Perf:** Locust/k6 for API; custom timers for TTFT and retrieval latency.
- **A11y:** axe-core + keyboard nav checks.
- **Reporting:** Allure/HTML report + JUnit XML for CI.

---

## 5) Test Environment
- **OS:** macOS & Windows laptops (CPU-only baseline).  
- **Models:** One “small” and one “balanced” local LLM; one local embedding model.  
- **Vector store:** Qdrant (embedded/local mode).  
- **Network:** NIC disabled for local-only test scenarios.  
- **Data:** Public-domain PDFs (short/long, table-heavy, CJK sample).

---

## 6) Test Data
- **Mini-eval pack:** 10–20 gold Q/A pairs across 1–2 sample docs to compute Hit@5, MRR@10, coverage.  
- **Heterogeneous corpus:** Dense report; slide-like deck; table-heavy PDF; short memo; CJK sample.  
- **Negative samples:** Corrupted/unsupported files; long queries; empty queries.

---

## 7) Functional Test Cases (selected)

### TC-FUNC-001 — Upload single PDF (happy path)
**Refs:** SRS §3.1; HLD DocMgmt; LLD `/api/documents`  
**Steps:** Upload valid text-PDF; wait for Parse→Chunk→Embed→Index.  
**Expected:** Status becomes **Indexed**; library row shows pages/tags; index vector count > 0.

### TC-FUNC-002 — Unsupported file warning
**Steps:** Upload `.xls`.  
**Expected:** Clear error; no index artifacts created.

### TC-FUNC-003 — Duplicate handling
**Steps:** Upload same file twice.  
**Expected:** Prompt to Replace or Keep both; metadata reflects choice.

### TC-FUNC-010 — **Adaptive chunking** selection logged
**Steps:** Ingest five heterogeneous docs.  
**Expected:** Auto chunk size/overlap differs across docs; policy rationale logged; structure-aware boundaries where detectable.

### TC-FUNC-011 — Re-index on param change
**Steps:** Switch a doc from Auto → Manual (e.g., 600 tokens, 15% overlap), trigger re-index.  
**Expected:** Status flips to “Needs re-index,” then **Indexed** with new chunk counts.

### TC-FUNC-020 — Local embeddings only
**Steps:** Disable network; ingest a doc.  
**Expected:** Embeddings succeed; no outbound connections observed.

### TC-FUNC-021 — Qdrant collection created & searchable
**Steps:** After ingest, inspect diagnostics and run a test search via API.  
**Expected:** Collection exists; vector count matches chunks; payload filters work.

### TC-FUNC-030 — Retrieval + **dynamic-k** control
**Steps:** Run short factual vs broad summary queries.  
**Expected:** Chosen `k` smaller for narrow and larger for broad queries; no context overflow; k logged.

### TC-FUNC-031 — Citations appear and are clickable
**Steps:** Ask a question; click [1]/[2].  
**Expected:** Sources panel focuses cited snippet with doc/page & score.

### TC-FUNC-032 — Follow-up question uses context
**Steps:** Ask Q1 then Q2: “and what about section 3?”  
**Expected:** Q2 considers Q1; Clear-Context resets behavior.

---

## 8) UI & Streaming Test Cases

### TC-UI-040 — **StreamingIndicator** during generation
**Steps:** Submit a query; observe RETRIEVING → STREAMING → COMPLETE.  
**Expected:** Animated indicator shows only during RETRIEVING/STREAMING; hides on COMPLETE/ERROR; respects reduced-motion.

### TC-UI-041 — Chat transcript & accessibility
**Steps:** 10 turns; keyboard-only nav.  
**Expected:** All turns visible & timestamped; transcript has `role="log"`; focus moves to latest assistant message at END.

---

## 9) Non-Functional Tests

### Performance
- **TC-PERF-100 — Time-to-first-token (TTFT)**  
  **Metric:** TTFT ≤ **1.0 s** p95 on reference laptop; steady stream cadence (≥5 tokens/s avg).
- **TC-PERF-101 — Retrieval latency**  
  **Metric:** p95 ≤ **1.5 s** for 2k-chunk corpus (balanced profile).
- **TC-PERF-102 — Index throughput**  
  **Metric:** ≥ **400 pages/min** on text-PDFs (no OCR).

### Reliability & Robustness
- **TC-REL-110 — Crash during indexing** → restart resumes or rolls back cleanly.  
- **TC-REL-111 — Large batch ingest** → UI responsive; progress & cancel function correctly.

### Security & Privacy (Local-only)
- **TC-SEC-120 — No outbound traffic** with NIC disabled: ingestion, retrieval, generation succeed.  
- **TC-SEC-121 — Secure delete** removes raw, parsed, and index payloads (verify on disk).

### Usability & Accessibility
- **TC-UX-130 — First Q&A in ≤2 minutes** (new user) with clear empty states & sample prompts.  
- **TC-A11Y-131 — Keyboard & ARIA**: chat `role="log"`, indicator `role="status"`, labels present.

### Portability
- **TC-PORT-140 — macOS vs Windows parity**: identical flows and performance within ±15%.

---

## 10) Entry / Exit Criteria
**Entry**: Build deploys locally; models present; Qdrant initialized; test docs loaded.  
**Exit**: All functional cases pass; p95 perf met; no critical/P1 defects open; local-only verified.

---

## 11) Risks & Mitigations
- **OCR variance (scanned PDFs):** mark OCR path optional; exclude from perf baselines; provide warnings.  
- **Hardware variability:** standardize on a reference laptop; use profiles (Eco/Balanced/Performance).  
- **Index growth:** enforce disk caps; snapshot/cleanup routines.

---

## 12) Reporting
- CI: unit/component coverage; integration & E2E reports (HTML/JUnit); perf graphs; a11y audit.  
- **Defect workflow:** triage daily; P1 within 24h; RCAs for regressions.  
- **RTM:** spreadsheet linking SRS/HLD/LLD → TC → results.

---

## 13) Execution Plan (high level)
1. **Unit & Component** (dev+QA pairing).  
2. **Integration & System** (nightly on reference laptop).  
3. **E2E & A11y** (Playwright + axe in CI).  
4. **Performance & Reliability** (scheduled runs; trend charts).  
5. **UAT** (scripted scenarios with stakeholders).

---

## 14) Sign-off
- QA Lead: ________  Date: ____  
- Eng Manager: _____ Date: ____  
- Product: _________ Date: ____
