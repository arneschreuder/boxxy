# Boxxy

Welcome to Boxxy

### Quick Start:

1. Set the system voice to Siri in System Preferences -> Accessibility -> Spoken Context -> System Voice

2. Make sure you have an internet connection

3. Rename the .env.example file to .env and replace the keys inside with your OpenAI keys

4. Setup environment and execute

```bash
cd /path/to/repo
python3 -m virtualenv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 boxxy.py
```

5. Make sure to change the preprompt code in `boxxy.py`
