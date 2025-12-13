import os
import ollama

class LLMEngine:
    def __init__(self, model_version="phi3"):
        self.model_version = model_version
        self.is_mock = False
        
        # Support for Remote Ollama (e.g. via Ngrok)
        self.base_url = os.getenv("OLLAMA_BASE_URL")
        self.client = None

        try:
            if self.base_url:
                print(f"Initializing LLM Engine with Remote Ollama at: {self.base_url}")
                self.client = ollama.Client(host=self.base_url)
            else:
                print(f"Initializing LLM Engine with Local Ollama model: {self.model_version}")
                self.client = ollama.Client() # Defaults to localhost:11434
            
            # Lightweight check - we don't block heavily here to allow lazy connection
        except Exception as e:
            print(f"Ollama check failed: {e}. Defaulting to Mock Mode.")
            self.is_mock = True

    def generate(self, prompt, stop=None, max_tokens=256):
        if self.is_mock:
             print(f"[MockLLM] Prompt length: {len(prompt)}")
             return "SELECT * FROM mock_table LIMIT 10;"

        try:
            # Ollama Python client usage via instance
            response = self.client.generate(
                model=self.model_version,
                prompt=prompt,
                options={
                    "num_predict": max_tokens,
                    "temperature": 0.1,
                    # "stop": stop or ["\n\n"] 
                }
            )
            return response['response'].strip()
        except Exception as e:
            print(f"Generation Error (Ollama): {e}")
            return f"SELECT * FROM error_log; -- Error: {str(e)}"


