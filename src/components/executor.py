import time
from src.llm.engine import LLMEngine
from src.semantic_catalog.store import SemanticStore
from src.utils.safety import is_safe
from src.utils.db_connect import create_engine, text
from src.components.auditor import AutoAuditor
import agentlightning as agl

class SQLAgent:
    def __init__(self, db_url=None, model_path="llama3:8b", auto_audit=False):
        # We repurpose model_path as model_name for Ollama
        self.db_url = db_url
        self.llm = LLMEngine(model_version=model_path)
        self.store = SemanticStore()
        self.auto_audit = auto_audit
        if self.auto_audit:
            self.auditor = AutoAuditor(model_version=model_path) # Use same model or "judge" model
        super().__init__()
        self.db_url = db_url
        self.llm = LLMEngine(model_version=model_path)
        self.store = SemanticStore()
        
        # Refinement 2: Model Lifecycle Tracking
        self.current_model_version = "v1.0.0"

    def check_for_new_model(self):
        """
        Refinement 2: Mock check for hot-swapping model weights.
        In production, check a shared path/registry for 'adapter_latest.safetensors'.
        """
        # Mock logic
        found_new_version = False
        if found_new_version:
             print("New model version detected. Reloading weights... (Simulated)")
             # self.llm.reload(new_path)
             self.current_model_version = "v1.0.X"

    def run(self):
        # Placeholder for continuous agent loop
        pass

    def handle_query(self, user_query: str):
        # 0. Lifecycle Check
        self.check_for_new_model()
        
        print(f"Processing query: {user_query}")
        
        # 0. Agent-Lightning Trace Start (Manual)
        # agl.trace context doesn't exist in installed version
        try:
            agl.emit_message(f"[User Query] {user_query}")
        except Exception:
            pass # Tracing optional

        # 1. Retrieval (Hybrid Search + Graph Hints)
        context_items = self.store.search(user_query, top_k=5)
        schema_context = "\n".join([item['text'] for item in context_items])
        
        # 2. Ambiguity Resolution (Improvement 1)
        if "date" in user_query.lower():
            date_cols = [m['metadata']['column'] for m in context_items if m['metadata'].get('inferred_type') == 'date']
            if len(set(date_cols)) > 1:
                question = f"Ambiguity detected. Did you mean: {', '.join(date_cols)}?"
                try:
                    agl.emit_message(f"[Ambiguity Resolution] {question}")
                except Exception:
                    pass
                return f"[Clarification Needed] {question}"

        # 3. Generation (SLM)
        prompt = f"""
        You are a SQL expert.
        Schema Context:
        {schema_context}
        
        User Query: {user_query}
        
        Generate a valid SQL query for SQLite. Return ONLY the SQL.
        """
        
        sql = self.llm.generate(prompt)
        try:
            agl.emit_object({"type": "generated_sql", "sql": sql})
        except Exception:
            pass
            
        print(f"Generated SQL: {sql}")

        # 4. Safety Sandbox (Improvement 4)
        if self.db_url:
            if not is_safe(sql, self.db_url):
                msg = "Query blocked by Safe Execution Sandbox (High Cost/Unsafe)."
                try:
                    agl.emit_exception(Exception(msg))
                except Exception:
                    pass
                return f"[Blocked] {msg}"
        
        # 5. Execution & Auto-Explanation (Refinement 1)
        if self.db_url:
            try:
                engine = create_engine(self.db_url)
                with engine.connect() as conn:
                    result = conn.execute(text(sql))
                    rows = [dict(row._mapping) for row in result]
                    
                    try:
                        agl.emit_object({"type": "execution_result", "rows": rows})
                    except Exception:
                        pass
                    
                    # Refinement 1: Auto-Explanation (Self-Reflection)
                    explanation_prompt = f"""
                    Explain this SQL query to a non-technical user in 1 sentence:
                    Query: {sql}
                    """
                    explanation = self.llm.generate(explanation_prompt, max_tokens=64)
                    
                    # Feature: Auto-Audit
                    audit_info = ""
                    if self.auto_audit:
                        score, reason = self.auditor.audit(user_query, sql, rows)
                        audit_info = f" | [Auditor] {reason}"
                        if score == 1:
                            self.submit_feedback(user_query, sql, 1) # Auto-save good example
                            audit_info += " (Saved to Dataset)"
                    
                    return {
                        "data": rows,
                        "sql": sql,
                        "explanation": f"Logic: {explanation} (Model: {self.current_model_version}){audit_info}"
                    }
            except Exception as e:
                try:
                    agl.emit_exception(e)
                except Exception:
                    pass
                return f"[Execution Error] {e}"
        
        return sql # Return SQL if no DB connected


    def submit_feedback(self, query, sql, rating):
        """
        Called by UI to log feedback for the Trainer.
        rating: 1 (Good) or 0 (Bad)
        """
        import json
        entry = {
            "query": query,
            "sql": sql,
            "rating": rating,
            "timestamp": time.time()
        }
        # In a real app, this goes to a queue or DB. 
        # Here we append to a file that Trainer monitors.
        with open("feedback_queue.jsonl", "a") as f:
            f.write(json.dumps(entry) + "\n")
        print(f"Feedback logged: {rating}")



