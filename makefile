.PHONY: init start test proto

init:
	uv venv --python 3.12
	uv pip install -r "requirements.txt"

	@if not exist assets\models mkdir assets\models
	
start: 
	uv run main.py

test:
	uv run pytest
