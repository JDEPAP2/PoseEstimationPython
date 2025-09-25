.PHONY: init start test proto

init:
	uv venv --python 3.12
	uv pip install -r "requirements.txt"
	uv run python -c "import os; os.makedirs('assets/models', exist_ok=True)"
	
start: 
	uv run main.py

test:
	uv run pytest
