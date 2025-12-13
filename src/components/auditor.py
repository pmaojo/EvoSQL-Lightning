from src.llm.engine import LLMEngine
import agentlightning as agl

class AutoAuditor:
    def __init__(self, model_version="llama3:8b"):
        self.llm = LLMEngine(model_version=model_version)

    def audit(self, query, sql, results):
        """
        Critiques the interaction. Returns (score, reason).
        score: 1 (Pass) or 0 (Fail)
        """
        
        # Fast heuristic checks
        if "error" in sql.lower() or "blocked" in sql.lower():
            return 0, "SQL Generation Failed or Blocked"
            
        if not results and "count" not in sql.lower():
            # Empty results might be valid, but suspicious for training data unless verified
            # We'll be conservative
            return 0, "Empty result set (Conservative Reject)"

        # LLM Judge with Chain-of-Thought (CoT) for SLM Robustness
        prompt = f"""
        You are a SQL Expert Auditor. Verify if the generated SQL correctly answers the User Question.
        
        User Question: {query}
        Generated SQL: {sql}
        Result Sample: {str(results)[:200]}
        
        Steps:
        1. Check if the SQL columns match the intent of the question.
        2. Check for common traps (e.g., matching "orders" but selecting "users").
        3. Verify the result is not an Error.
        
        Output format:
        Reasoning: <one sentence analysis>
        Verdict: PASS or FAIL
        """
        
        evaluation = self.llm.generate(prompt, max_tokens=128)
        
        print(f"[Auditor] Full Evaluation: {evaluation}")
        
        # Robust parsing for SLM output
        if "Verdict: PASS" in evaluation or evaluation.strip().startswith("PASS"):
            return 1, evaluation
        else:
            return 0, evaluation
