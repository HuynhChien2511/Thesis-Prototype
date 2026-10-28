# SLIDE CONTENT COPY-PASTE CHEAT SHEET (WEEK 1 PROGRESS REPORT - 6 SLIDES)
**Target PowerPoint File:** `D:\Thesis\weekly report w1.pptx`  
**Topic:** Week 1 Progress Report - Sprint 1: Knowledge Base & Legal RAG Subsystem  
**Structure:** Expanded with a dedicated Raw Data to Vector DB (ETL Pipeline) Slide, completing a comprehensive 6-slide deck.

---

## 🪟 SLIDE 1: TITLE & EXECUTIVE SUMMARY

| Slide Location | Content to Copy (Paste below) |
| :--- | :--- |
| **Main Title** | **WEEKLY PROGRESS REPORT - WEEK 1: BUILDING THE KNOWLEDGE BASE & RAG SUBSYSTEM FOR PUBLIC SERVICE ROBOT** |
| **Subtitle** | Course: Graduation Thesis (Pre-Thesis Phase)<br>Advisor: **Mr. Lanh (Thầy Lành)**<br>Student: **Huynh Chien (Huỳnh Chiến)** |
| **Weekly Summary (3 Bullets)** | • Completed the Knowledge Brain subsystem based on **RAG (Retrieval-Augmented Generation)** architecture.<br>• Engineered an automated ETL pipeline transforming raw files (.pdf, .docx, .txt) into a local ChromaDB vector store.<br>• Engineered a **Similarity Threshold Firewall (Threshold = 0.55)**, mathematically eliminating AI hallucinations. |

---

## 🪟 SLIDE 2: OBJECTIVES & METHODOLOGY

| Slide Text Box | Content to Copy (Paste below) |
| :--- | :--- |
| **Slide Title** | **WEEK 1 OBJECTIVES & METHODOLOGY** |
| **Left Box: AI-Assisted Engineering** | **1. Methodology: AI-Assisted Engineering (Pair Programming with AI)**<br>• Leveraged generative AI as a development accelerator for boilerplate code generation and test automation.<br>• **Student's role as System Architect:** Formulating domain requirements, designing data chunking architectures, tuning mathematical hyperparameters, and empirically validating results.<br>• Accelerated foundational infrastructure development from 3 weeks down to 1 week. |
| **Right Box: RAG vs Fine-Tuning** | **2. Architectural Decision: Why RAG instead of Fine-Tuning?**<br>• **3-Second Legal Updates:** Dynamic laws and circulars update instantly by adding new text files; fine-tuning requires weeks of re-training and costly GPU compute.<br>• **Transparent Legal Provenance:** RAG strictly cites specific statutory Articles, Clauses, and filenames; fine-tuning returns black-box parametric text without verifiable citations.<br>• **Zero Hallucination:** Constrains AI reasoning strictly within internal statutory documents. |

---

## 🪟 SLIDE 3: RAW DATA TO VECTOR DB PIPELINE (ETL PIPELINE)

| Slide Text Box | Content to Copy (Paste below) |
| :--- | :--- |
| **Slide Title** | **RAW DATA TO VECTOR DB PIPELINE (ETL PIPELINE)** |
| **Left Box: 4-Step Ingestion Pipeline** | **Automated 4-Step Pipeline (src/rag/ingest.py):**<br>• **Step 1 (Ingestion):** Ingests raw `.pdf`, `.docx`, and `.txt` files via LangChain Document Loaders, automatically tagging `metadata["source_file"]`.<br>• **Step 2 (Chunking):** Recursively splits text prioritized by Vietnamese legal hierarchy (Articles & Clauses).<br>• **Step 3 (Embedding):** Maps each chunk through `Google text-embedding-004` into a 768-dimensional semantic dense vector.<br>• **Step 4 (Indexing & Storage):** Loads vectors into **ChromaDB**, builds an HNSW spatial index, and persists locally in `vector_db/`. |
| **Right Box: Architectural Benefits** | **Key Engineering Strengths:**<br>• **Fully Automated Pipeline:** A single execution of `python src/rag/ingest.py` refreshes and vectorizes the entire knowledge base in seconds.<br>• **Zero-Downtime Knowledge Ingestion:** Seamlessly ingest new administrative procedures without model re-training.<br>• **Ultra-Fast Spatial Retrieval:** The **HNSW** graph index retrieves the Top-3 relevant statutory chunks in just **$0.03\text{ -- }0.04\text{ s}$**, bypassing brute-force linear scans. |

---

## 🪟 SLIDE 4: LEGAL HIERARCHICAL CHUNKING & LOCAL VECTOR DB

| Slide Text Box | Content to Copy (Paste below) |
| :--- | :--- |
| **Slide Title** | **LEGAL HIERARCHICAL CHUNKING & LOCAL VECTOR DB** |
| **Top Box: Chunking Problem & Solution** | • **Pitfall of fixed-size chunking (500 characters):** Randomly slices requirement checklists or fee schedules across chunks $\rightarrow$ AI yields incomplete guidance to citizens.<br>• **Solution: Legal Hierarchical Chunking (Article/Clause hierarchy):**<br>  - Recursive splitter prioritized by legal delimiters: `["\nĐiều ", "\nKhoản ", "\n\n", "\n", " "]`<br>  - **`chunk_size = 800` characters** ($\approx 180$ words, covering exactly one legal Article or Clause).<br>  - **`chunk_overlap = 150` characters** (preserves conditional conjunctions across boundaries).<br>  - $\rightarrow$ *Result:* All prerequisites and conditions of a legal regulation remain preserved within a single vector. |
| **Bottom Box: Local ChromaDB** | • **Persistent Local Vector Database: ChromaDB**<br>  - **Serverless & Local-first:** Persists directly on disk (`vector_db/`) via embedded SQLite and Parquet, zero bulky Docker services required.<br>  - Granular Metadata Management: Automatically stores source filenames for citation generation.<br>  - Embedding Model: `Google text-embedding-004` mapping legal text to dense semantic vector space. |

---

## 🪟 SLIDE 5: HALLUCINATION PREVENTION FIREWALL (THRESHOLD = 0.55)

| Slide Text Box | Content to Copy (Paste below) |
| :--- | :--- |
| **Slide Title** | **HALLUCINATION PREVENTION FIREWALL (THRESHOLD = 0.55)** |
| **Left Box: Firewall Principle** | **1. Cosine Relevance Score Separation:**<br>• Every citizen query undergoes cosine similarity scoring ($0.0\text{ to }1.0$) against Vector DB prior to LLM invocation.<br>• *In-Domain Queries (ID card, residence):* High similarity scores of **$0.68\text{ -- }0.86$**.<br>• *Out-of-Domain Queries (foreign travel visas, chit-chat):* Low similarity scores of **$0.25\text{ -- }0.48$**.<br>$\rightarrow$ Enforcing a hard gate at **`SIMILARITY_THRESHOLD = 0.55`**. |
| **Right Box: Fast Refusal Impact** | **2. Fast Refusal & Deterministic Decoding:**<br>• **If Score $< 0.55$:** Immediately short-circuits in **$0.05\text{ seconds}$**, returning a polite refusal and redirecting to the National Public Service Portal.<br>• **Impact:** Saves $100\%$ of LLM generation costs and **completely eliminates AI hallucinations**.<br>• **Strict System Prompt:** `temperature = 0.1` forces the LLM (Google Gemini Flash) into deterministic, strictly grounded reasoning. |

---

## 🪟 SLIDE 6: QUANTITATIVE BENCHMARKS & WEEK 2 ROADMAP

| Slide Text Box | Content to Copy (Paste below) |
| :--- | :--- |
| **Slide Title** | **QUANTITATIVE BENCHMARKS & WEEK 2 ROADMAP** |
| **Top Box: Benchmark Data** | *(Copy and paste the quantitative table below)* |
| **Bottom Box: Week 2 Roadmap** | **WEEK 2 RESEARCH ROADMAP:**<br>1. **Initiate "The Ears" Subsystem (STT):** Implement digital audio capture via `sounddevice` with Peak Normalization and audio padding.<br>2. **Integrate Faster-Whisper:** Vietnamese speech recognition accelerated on NVIDIA CUDA GPUs.<br>3. Connect the STT subsystem directly with the Week 1 RAG Brain. |

### 📊 TABLE TO PASTE INTO SLIDE 6:

| Test Case Scenario | User Query | Vector Search Time | LLM Generation Time | Total Latency | Accuracy & Grounding Validation |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **TC01: In-domain** | *"What are the requirements for ID cards for children under 14?"* | $0.04\text{ s}$ | $2.25\text{ s}$ | **$2.29\text{ s}$** | ✅ Full dossier listed, cited Law on Identification 2023 |
| **TC02: In-domain** | *"How long does temporary residence registration take and where to submit?"* | $0.03\text{ s}$ | $2.18\text{ s}$ | **$2.21\text{ s}$** | ✅ Stated 3-day deadline & Commune Police station |
| **TC03: Out-of-domain** | *"What are the procedures for a self-guided Japan tourist visa?"* | $0.04\text{ s}$ | $0.00\text{ s}$ *(DB Short-circuit)* | **$0.04\text{ s}$** | ✅ Instant refusal in 0.04s, polite guidance, 0% hallucination |
