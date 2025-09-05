# User Requirements Document (URD)
## Web Application: Local RAG-based Document Q&A System

### 1. Introduction
This document defines the **User Requirements Document (URD)** for a local Retrieval-Augmented Generation (RAG) based web application. The purpose of this system is to enable users to upload documents (PDFs, books, and other text-based files), manage them locally, and perform accurate question-answering using a locally running Large Language Model (LLM). The URD is structured according to Sommerville’s guidelines for requirements engineering, distinguishing between functional and non-functional requirements.

---

### 2. User Needs
- Users need a way to **upload and manage multiple PDF or text-based documents** easily.
- Users need to **quickly find, identify, and organize their documents** to manage their knowledge base effectively.
- Users need the app to **analyze documents automatically** (chunking, embedding, indexing).
- Users require the system to **retrieve accurate and relevant answers** based on queries.
- Users want all processes (**LLM inference, embeddings, vector database**) to run **locally** without reliance on cloud services.
- Users want the system to be **resource-efficient** so it can run smoothly on a laptop.
- Users need to **know what the system is doing**, especially during long processes like indexing or answering a question, through clear feedback.
- Users want the app to **store, organize, and allow deletion** of previously uploaded documents.

---

### 3. Functional Requirements
1. **Document Upload**
   - The system shall allow users to upload PDF files, books, and text documents.
   - The system shall validate supported file types.

2. **Automated RAG Processing**
   - The system shall automatically chunk uploaded documents.
   - The system shall embed document chunks using a local embedding model.
   - The system shall store embeddings in a **flexible local vector database** (e.g., Chroma or FAISS).
   - The system shall handle document indexing and re-indexing when documents are updated or removed.

3. **Query Handling**
   - The system shall allow users to input natural language questions.
   - The system shall retrieve the most relevant chunks from the vector store.
   - The system shall generate answers using a locally running LLM.
   - The system shall provide source references (e.g., document name and section).

4. **Document Management**
   - The system shall provide a dashboard to view all uploaded documents.
   - The system shall allow users to delete documents and their embeddings.
   - The system shall allow users to organize documents (tags, categories, or folders).

5. **Local Operation**
   - The system shall ensure all processing (embedding, storage, LLM inference) is done locally.
   - No internet or external API calls shall be required for standard operation.

---

### 4. Non-Functional Requirements
1. **Accuracy**
   - The system shall maximize retrieval accuracy by using effective chunking and embedding strategies.

2. **Performance**
   - The system shall process documents within reasonable time limits on a consumer laptop.
   - Query responses shall be generated within a few seconds.

3. **Resource Efficiency**
   - The system shall not exceed typical laptop hardware capabilities (8–16 GB RAM, no dedicated GPU required).

4. **Usability**
   - The interface shall be intuitive and require minimal technical knowledge.
   - The upload and query workflow shall be simple and user-friendly.

5. **Flexibility**
   - The vector database shall be easily replaceable with another option if required.
   - The system shall support adding more local models in the future.

---

### 5. Constraints
- The system must run **completely locally**, without dependence on cloud infrastructure.
- The system must support **PDFs and text-based formats** at minimum.
- The system must not require hardware beyond a standard laptop.

---

### 6. Assumptions
- The user has sufficient storage capacity for documents and embeddings.
- The user is familiar with uploading documents and typing queries.
- Local models (LLM + embedding model) can be optimized to fit within the laptop’s resources.

---

### 7. Future Enhancements
- Support for additional file formats (Word, HTML, Markdown).
- Multi-user support with role-based access.
- Fine-tuning of the local LLM with user documents.
- Export of chat history and answers.

---

### 8. Approval
This URD is intended to be reviewed and validated by stakeholders before proceeding to the **System Requirements Specification (SRS)** stage.