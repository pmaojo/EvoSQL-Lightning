# ⚡ EvoSQL-Lightning

**EvoSQL-Lightning** is a robust, modular Natural Language to SQL (NL2SQL) system built on **Lightning AI** and **Small Language Models (SLMs)**. It prioritizes low latency, data privacy, and self-improvement through user feedback.

## 🚀 Key Features

- **Modular Architecture**: Built with `LightningWork` components for scalability (`Explorer`, `Executor`, `Trainer`).
- **SLM-First**: Optimized for **Ollama** (Llama 3, Mistral, Phi-3), running locally on your machine.
- **Robust Intelligence**:
  - **Auto-Explanation**: The system explains its SQL logic in plain English to catch silent errors.
  - **Graph Awareness**: Indexes Foreign Keys and Join Hints to handle complex relationships.
  - **Safe Execution**: Sandboxed execution preventing destructive queries (`DROP`, `DELETE`).
  - **Active Ambiguity**: Asks for clarification when column names are confusing.
  - **Auto-Auditor**: AI Critic that evaluates query quality and automatically labels data.
  - **Chain-of-Thought (CoT)**: Auditor uses reasoning steps before verdict to ensure SLM accuracy.
- **Self-Improving Loop**: Collects "Thumbs Up/Down" feedback to build a dataset for DPO/Fine-tuning.
- **Regression Testing**: Validates model updates against a Golden Dataset before acceptance.

## 🛠️ Installation

### Prerequisites

1.  **Python 3.9+**
2.  **Ollama**: [Download and install](https://ollama.com).
3.  **Pull a Model**:
    ```bash
    ollama pull llama3:8b
    ```

### Setup

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## 🏃‍♂️ Usage

### 1. Interactive Chat UI (Streamlit)

The best way to use the system is via the Dashboard.

```bash
./.venv/bin/python -m streamlit run src/components/ui.py
# OR if your venv is active:
# streamlit run src/components/ui.py
```

- **Ask**: "Show me users in Madrid"
- **Verify**: Check the generic SQL + Explanation.
- **Feedback**: Click 👍 or 👎 to save data for training.

### 2. Verify Backend only

Run the verification script to simulate a CLI flow.

```bash
python3 verify_setup.py
```

## 🏗️ Architecture

```mermaid
graph TD
    User[User / UI] --> Executor[Executor SQLAgent]
    Executor <--> Store[Semantic Store ChromaDB]
    Executor --> Ollama[Local SLM Ollama]
    Executor --> DB[Target Database]

    Explorer[Explorer SchemaDiscovery] -->|Introspect| DB
    Explorer -->|Populate| Store

    User -->|Feedback| Trainer[Trainer (SelfImprover)]
    Trainer -->|Fine-tune| Ollama
```

## 🧠 Components

- **`src/components/explorer.py`**: Scans DB schema, profiles data, creates embeddings.
- **`src/components/executor.py`**: Handles queries, RAG retrieval, ambiguity checks, generation.
- **`src/components/trainer.py`**: Manages the feedback loop and regression testing.
- **`src/components/ui.py`**: Streamlit frontend.

## 📈 Training (Self-Improvement)

The system saves feedback to `training_data.jsonl`.
To fine-tune your model:

1.  Collect ~50+ good examples via the UI.
2.  Use **MLX** (Mac) or **Unsloth** (Linux/Windows) to fine-tune `llama3:8b` on `training_data.jsonl`.
3.  Export the new model to Ollama (`ollama create my-sql-v2 ...`).
4.  Update `SQLAgent` to use `my-sql-v2`.
