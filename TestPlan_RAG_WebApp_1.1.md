# Master Test Plan (MTP) — Local RAG WebApp

**Version:** 1.1 (Enhanced with Resilience & Edge Case Tests) 
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
(Content unchanged)

---

## 4) Test Strategy
(Content unchanged)

---

## 5) Test Environment
(Content unchanged)

---

## 6) Test Data
- **Mini-eval pack:** 10–20 gold Q/A pairs across 1–2 sample docs to compute Hit@5, MRR@10, coverage.  
- **Heterogeneous corpus:** Dense report; slide-like deck; table-heavy PDF; short memo; CJK sample; password-protected PDF; image-only PDF; very large PDF (>500MB).
- **Negative samples:** Corrupted/unsupported files; long queries; empty queries; out-of-scope queries.

---

## 7) Functional Test Cases (selected)

### Document Handling & Ingestion
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

### TC-FUNC-004 — Ingest Password-Protected PDF
**Steps:** Upload a password-protected PDF.
**Expected:** System does not crash. Document status updates to "Error" with a clear message (e.g., "File is password-protected").

### TC-FUNC-005 — Ingest PDF with Only Images
**Steps:** Upload a PDF containing only scanned images with no text layer.
**Expected:** Document status becomes "Error" or "Unsupported" with a message (e.g., "No text content found for indexing").

### TC-FUNC-006 — Ingest Document with Mixed Content (Tables, Text, Images)
**Steps:** Ingest a document containing paragraphs, tables, and images. Ask a query about specific data within a table.
**Expected:** The document indexes successfully. The query about the table returns an accurate answer, proving the parser handled the structure correctly.

### RAG Pipeline: Chunking & Indexing
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

### RAG Pipeline: Retrieval & Generation
### TC-FUNC-030 — Retrieval + **dynamic-k** control
**Steps:** Run short factual vs broad summary queries.  
**Expected:** Chosen `k` smaller for narrow and larger for broad queries; no context overflow; k logged.

### TC-FUNC-031 — Citations appear and are clickable
**Steps:** Ask a question; click [1]/[2].  
**Expected:** Sources panel focuses cited snippet with doc/page & score.

### TC-FUNC-032 — Follow-up question uses context
**Steps:** Ask Q1 then Q2: “and what about section 3?”  
**Expected:** Q2 considers Q1; Clear-Context resets behavior.

### TC-FUNC-033 — Query with No Relevant Chunks (Out-of-Scope)
**Steps:** Ask a question completely unrelated to the content of the indexed documents.
**Expected:** The LLM generates a polite "I cannot answer this question based on the provided documents" response. No citations are displayed. The system does not hallucinate.

### TC-FUNC-034 — Query with Very Low-Confidence Chunks
**Steps:** Ask an ambiguous question that only weakly matches some chunks.
**Expected:** The system qualifies its answer, stating that its confidence is low or that the information is limited, rather than presenting a weak answer as factual.

### TC-FUNC-035 — Context Window Exhaustion in Chat
**Steps:** Engage in a long conversation (15+ turns). Ask a follow-up question that relies on context from the first turn.
**Expected:** The system's response should indicate if the initial context is no longer available, rather than providing an incorrect answer.

### TC-FUNC-036 — Complex Citation Generation
**Steps:** Ask a query that requires synthesizing an answer from 3 or more different source chunks.
**Expected:** The generated answer correctly integrates information from all sources and includes citations for each part (e.g., `[1]`, `[2]`, `[3]`).

---

## 8) UI & Streaming Test Cases

### TC-UI-040 — **StreamingIndicator** during generation
**Steps:** Submit a query; observe RETRIEVING → STREAMING → COMPLETE.  
**Expected:** Animated indicator shows only during RETRIEVING/STREAMING; hides on COMPLETE/ERROR; respects reduced-motion.

### TC-UI-041 — Chat transcript & accessibility
**Steps:** 10 turns; keyboard-only nav.  
**Expected:** All turns visible & timestamped; transcript has `role="log"`; focus moves to latest assistant message at END.

### TC-UI-042 — WebSocket Disconnection Mid-Stream
**Steps:** While an answer is streaming, disable the network interface.
**Expected:** The UI immediately stops streaming, updates the message state to "Error," and provides a "Retry" button for that turn.

---

## 9) Non-Functional Tests

### Performance
- **TC-PERF-100 — Time-to-first-token (TTFT)**  
  **Metric:** TTFT ≤ **1.0 s** p95 on reference laptop; steady stream cadence (≥5 tokens/s avg).
- **TC-PERF-101 — Retrieval latency**  
  **Metric:** p95 ≤ **1.5 s** for 2k-chunk corpus (balanced profile).
- **TC-PERF-102 — Index throughput**  
  **Metric:** ≥ **400 pages/min** on text-PDFs (no OCR).
- **TC-PERF-103 — Sustained Resource Usage**  
  **Metric:** During a large batch ingest, monitor CPU/RAM. Usage should align with the selected Performance Profile and show no memory leaks (RAM usage stabilizes or decreases after the task completes).

### Reliability & Robustness
- **TC-REL-110 — Crash during indexing** → restart resumes or rolls back cleanly.  
- **TC-REL-111 — Large batch ingest** → UI responsive; progress & cancel function correctly.
- **TC-REL-112 — Graceful Degradation on Model Load Failure**
  **Steps:** Corrupt or remove the local LLM file and start the application.
  **Expected:** The application starts without crashing and displays a clear error in the UI (e.g., "LLM failed to load. Query functionality is disabled.").
- **TC-REL-113 — Vector Index Corruption**
  **Steps:** Manually corrupt or delete a Qdrant index file on disk.
  **Expected:** The system detects the corruption on the next query, flags the affected document as "Needs re-index," and allows the user to trigger the re-indexing.

### Security & Privacy (Local-only)
- **TC-SEC-120 — No outbound traffic** with NIC disabled: ingestion, retrieval, generation succeed.  
- **TC-SEC-121 — Secure delete** removes raw, parsed, and index payloads (verify on disk).

### Usability & Accessibility
- **TC-UX-130 — First Q&A in ≤2 minutes** (new user) with clear empty states & sample prompts.  
- **TC-A11Y-131 — Keyboard & ARIA**: chat `role="log"`, indicator `role="status"`, labels present.
- **TC-UX-132 — Layout Responsiveness**
  **Steps:** Resize the browser window to desktop, tablet, and mobile widths.
  **Expected:** The UI correctly adapts per the UI Spec (sidebar collapses, panel becomes a drawer, layout switches to tabs).
- **TC-UX-133 — Copy/Export Functionality**
  **Steps:** Use the UI to copy the full text of an assistant's response.
  **Expected:** The content is copied to the clipboard correctly and completely.

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
(Content unchanged)

---

## 13) Execution Plan (high level)
(Content unchanged)

---

## 14) Sign-off
- QA Lead: ________  Date: ____  
- Eng Manager: _____ Date: ____  
- Product: _________ Date: ____