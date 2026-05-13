"""
Ollama Integration for Advanced Reasoning Mode
Using official 'ollama' library for better performance
"""
import ollama
from typing import Optional, List, Dict

class OllamaIntegration:
    def __init__(self):
        self.model = "smollm2:latest" # Default fast model
        self.conversation_history: List[Dict[str, str]] = []
        self.is_available = False
        self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if Ollama is running and select best model"""
        try:
            # The library might return a dict-like object or a ListResponse
            models_info = ollama.list()
            models = []
            if hasattr(models_info, 'models'):
                models = models_info.models
            elif isinstance(models_info, dict):
                models = models_info.get('models', [])
            else:
                models = models_info # Fallback if it's already a list
            
            if models:
                self.is_available = True
                # Get the names (handle both objects and dicts)
                model_names = []
                for m in models:
                    if hasattr(m, 'model'): # Newer versions
                        model_names.append(m.model)
                    elif hasattr(m, 'name'):
                        model_names.append(m.name)
                    elif isinstance(m, dict):
                        model_names.append(m.get('name', m.get('model', '')))
                
                # Priority list for speed
                priority = ['smollm', 'phi3', 'tinydolphin', 'orca-mini', 'llama3', 'mistral']
                for p in priority:
                    for name in model_names:
                        if p in name.lower():
                            self.model = name
                            print(f"[Ollama] Detected and using: {self.model}")
                            return True
                
                # Final fallback - use whatever is there
                if model_names:
                    self.model = model_names[0]
                    print(f"[Ollama] Detected and using fallback: {self.model}")
                return True
            
            print("[Ollama] Connected but no models found. Please run 'ollama pull phi3'")
            return False
        except Exception as e:
            print(f"[Ollama] Connection failed: {e}")
            self.is_available = False
            return False
    
    def query(self, prompt: str, use_context: bool = True) -> str:
        """Send a query using the official library"""
        if not self.is_available:
            return "Advanced mode is not available. Please ensure Ollama is running."
        
        try:
            messages = []
            if use_context:
                messages = self.conversation_history[-2:] # Keep it short for speed
            
            # Inject system message for conciseness limit
            if not any(m.get("role") == "system" for m in messages):
                messages.insert(0, {"role": "system", "content": "You are a quick AI assistant. Give responses strictly within 50 words and use under 50 tokens."})
            
            messages.append({"role": "user", "content": prompt})
            
            # Use short predict limit for speed and token limit
            response = ollama.chat(
                model=self.model,
                messages=messages,
                options={
                    "num_predict": 50,
                    "temperature": 0.6
                }
            )
            
            answer = response['message']['content']
            
            if use_context:
                self.conversation_history.append({"role": "user", "content": prompt})
                self.conversation_history.append({"role": "assistant", "content": answer})
            
            return answer
                
        except Exception as e:
            print(f"[Ollama] Query error: {e}")
            return "I' encountered an error with reasoning."
    
    def clear_context(self):
        self.conversation_history = []
