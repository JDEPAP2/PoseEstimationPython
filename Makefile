init:
	uv venv --python 3.12
	uv pip install -r "requirements.txt"

	@if not exist assets\models mkdir assets\models

# Variable para el modelo (por defecto)
MODEL ?= ./assets/models/model.glb

start: 
	uv run main.py $(MODEL) 

test:
	uv run pytest