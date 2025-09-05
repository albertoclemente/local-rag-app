# UI Specification — Local RAG-based Document Q&A WebApp (React)
**Version:** 1.0
**Date:** 04 Sep 2025
**References:** SRS v1.1, HLD v1.0, LLD v1.1 (React + Streaming Indicator), Sommerville

---

## 1. Purpose
Define the **user interface architecture, interaction flows, components, states, and accessibility** of the Local RAG WebApp. This spec informs frontend implementation (React + TypeScript) and ensures consistency with requirements (streaming responses, chat history, adaptive RAG controls).

---

## 2. UX Principles
- **Clarity first:** Single primary action per view; progressive disclosure for advanced options.
- **Grounded answers:** Citations visible and one-click inspectable.
- **Responsiveness:** Token-level **streaming** with an animated indicator.
- **Local-first:** Diagnostics and resource usage surfaced (no network indicators).
- **Accessibility:** WCAG 2.1 AA, keyboard-first navigation, reduced-motion support.

---

## 3. Information Architecture (Pages / Panels)
- **Main App Shell** (single page app):
  - **Top App Bar**: App title, Model badge, Profile selector (Eco/Balanced/Performance), Settings button.
  - **Left Sidebar (Collapsible)**: Library (Documents), Collections/Tags, Quick Filters.
  - **Center Panel (Primary)**: **Chat View** (prompt box + transcript + streaming).
  - **Right Panel (Togglable)**: **Sources/Why** — citations, retrieved chunk previews, coverage meter.
  - **Bottom Status Bar**: CPU/RAM indicator, indexer status, offline badge.

### Layout (Desktop ≥1280px)
`┌───────────────────────────────────────────────────────────────────────────────┐
│ App Bar: [Logo] Local RAG | Model: local-llm-small | Profile: Balanced | ⚙  │
├───────────────┬───────────────────────────────────────────┬──────────────────┤
│ Sidebar       │          Chat View (Primary)              │   Sources/Why    │
│ - Library     │  [Prompt Input...] [Send] [Settings]      │  [Citations]     │
│ - Tags        │  ───────────────── Transcript ─────────   │  [Snippets]      │
│ - Filters     │  [User] question...                       │  [Coverage]      │
│               │  [Assistant] streamed answer + [1][2]     │                  │
├───────────────┴───────────────────────────────────────────┴──────────────────┤
│ Status: Offline | CPU 45% | RAM +1.7GB | Indexing: 3 docs (2m)               │
└───────────────────────────────────────────────────────────────────────────────┘`

### Layout (Tablet 768–1279px)
- Sidebar collapses to icons; Sources/Why slides over the chat (drawer).

### Layout (Mobile ≤767px)
- Single column. Tabs: **Chat** | **Library** | **Sources** | **Settings**.

---

## 4. Key User Flows
(Content unchanged)

---

## 5. React Components (TypeScript)

### 5.1–5.4
(Content unchanged)

### 5.5 StreamingIndicator
Shows animated dots/spinner. Honors `prefers-reduced-motion`.
**Props:** `{ state: UiStatus; label?: string }`.

### 5.6–5.10
(Content unchanged)

---

## 6. Component Contracts (Types)

`export type Profile = "eco" | "balanced" | "performance";

export type DocRow = {
  id: string;
  name: string;
  type: "pdf" | "docx" | "txt" | "md" | "epub";
  sizeBytes: number;
  pages?: number;
  tags: string[];
  status: "indexed" | "needs-reindex" | "error" | "indexing";
  addedAt: string;
};

export type SourceItem = {
  label: number;
  docId: string;
  chunkId: string;
  pageStart?: number;
  text: string;
  score?: number;
};

export type Citation = { label: number; docId: string; chunkId: string };

export type ChatTurn = {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  createdAt: string;
};

export type UiStatus = "idle" | "retrieving" | "streaming" | "complete" | "error";`

---

## 7. Events & API Integration
(Content unchanged)

---

## 8. Visual Language & Styling
(Content unchanged)

---

## 9. Accessibility
(Content unchanged)

---

## 10. Empty/Loading/Error States
(Content unchanged)

---

## 11. Performance & Telemetry (Local Only)
(Content unchanged)

---

## 12. Internationalization
(Content unchanged)

---

## 13. Wireframes (ASCII)
(Content unchanged)

---

## 14. QA Checklist (UI)
(Content unchanged)

---

## 15. Open Questions
- Do we render PDF pages in the Sources panel for page-accurate previews?
- Should per-message copy/share/export be included at launch?
- Do we support drag-to-quote (select text from sources to prompt)?

**Note:** These questions will be addressed in a design review before the end of the current sprint. Q1 is a candidate for a post-MVP feature spike. Q2 and Q3 will be evaluated against the remaining time in the MVP schedule.

---

*End of UI Specification.*