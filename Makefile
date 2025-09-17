# Variable para el modelo (por defecto)
MODEL ?= ./assets/models/model.glb

# Regla única que lanza el modelo y el dashboard en paralelo
run:
	@if not exist assets\models mkdir assets\models
	uv run main.py $(MODEL) &
