import os
import ollama

class LLMEngine:
    def __init__(self, model_version="phi3"):
        self.model_version = model_version
        self.is_mock = False
        
        try:
            # Check if ollama is reachable and has the model
            # Note: This is a lightweight check.
            # In a real app, we might do `ollama.list()` to verify.
            print(f"Initializing LLM Engine with Ollama model: {self.model_version}")
        except Exception as e:
            print(f"Ollama check failed: {e}. Defaulting to Mock Mode.")
            self.is_mock = True

    def generate(self, prompt, stop=None, max_tokens=256):
        if self.is_mock:
             print(f"[MockLLM] Prompt length: {len(prompt)}")
             return "SELECT * FROM mock_table LIMIT 10;"

        try:
            # Ollama Python client usage
            response = ollama.generate(
                model=self.model_version,
                prompt=prompt,
                options={
                    "num_predict": max_tokens,
                    "temperature": 0.1,
                    # "stop": stop or ["\n\n"] # Ollama handles stops differently, but this is fine for now
                }
            )
            return response['response'].strip()
        except Exception as e:
            print(f"Generation Error (Ollama): {e}")
            return "SELECT * FROM error_log;"


