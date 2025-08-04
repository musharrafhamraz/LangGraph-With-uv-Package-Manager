import os
import sys
from pathlib import Path

def load_env_file():
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent / ".env"
    
    if not env_path.exists():
        print(f"Warning: .env file not found at {env_path}")
        return
    
    print(f"Loading environment variables from {env_path}")
    
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            
            # Remove quotes if present
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            
            os.environ[key] = value
            
    # Verify GROQ_API_KEY is set
    if 'GROQ_API_KEY' in os.environ:
        print("GROQ_API_KEY is set")
    else:
        print("Warning: GROQ_API_KEY is not set")