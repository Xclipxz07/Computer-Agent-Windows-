import ollama
import json

def test_new_logic():
    print("--- Testing New Ollama Logic ---")
    try:
        models_info = ollama.list()
        models = []
        if hasattr(models_info, 'models'):
            models = models_info.models
        elif isinstance(models_info, dict):
            models = models_info.get('models', [])
        else:
            models = models_info
        
        print(f"Models found: {len(models)}")
        
        model_names = []
        for m in models:
            if hasattr(m, 'model'):
                model_names.append(m.model)
            elif hasattr(m, 'name'):
                model_names.append(m.name)
            elif isinstance(m, dict):
                model_names.append(m.get('name', m.get('model', '')))
        
        print(f"Model names: {model_names}")
        
        priority = ['smollm', 'phi3', 'tinydolphin', 'orca-mini', 'llama3', 'mistral']
        selected = None
        for p in priority:
            for name in model_names:
                if p in name.lower():
                    selected = name
                    break
            if selected: break
        
        if not selected and model_names:
            selected = model_names[0]
            
        print(f"Selected model: {selected}")
        
    except Exception as e:
        print(f"Error in test: {e}")

if __name__ == "__main__":
    test_new_logic()
