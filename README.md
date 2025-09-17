# Proyecto de Visión/3D + Control en Tiempo Real

Este repositorio contiene una aplicación Python para visión por computador y/o control de un modelo 3D en tiempo real (p. ej., OpenCV + YOLO + Panda3D).

## Requisitos
![Python 3.12](https://img.shields.io/badge/python-3.12-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

## Estructura 
```
assets/
  models/              # Modelos (.pt, .onnx, .pkl, etc.)
tests/                 # Pruebas unitarias (pytest)
src/                   # Archivos source del proyecto
main.py                # Punto de entrada por defecto (puedes usar ENTRY=app.py)
app.py                 # Alternativo, si existe
pyproject.toml         # PEP 621 (opcional)
requirements.txt       # Requerimientos (si no usas pyproject)
Makefile               # Tareas comunes
```

**Pipeline (resumen):**

```mermaid
flowchart LR

    %% Entrada
    A[📷 Cámara (OpenCV - Cv2Camera)] -->|captura frame BGR| B[🧠 Pose Estimator<br/>(YOLOv8)]

    %% Inferencia
    B -->|keypoints, confianza| C[(Post-procesamiento<br/>Keypoints → Pose Entities)]

    %% Control
    C --> D[🎮 Controlador de Animación<br/>(mapping de joints)]
    D --> E[🕴️ Modelo 3D<br/>(Panda3D/Engine 3D)]

    %% Retroalimentación opcional
    E -->|estado, feedback| F[⚙️ Lógica de Control / UI]

    %% Tests y herramientas
    subgraph Herramientas
        T1[pytest] --> B
        T1 --> C
        T1 --> D
    end

    style A fill:#bbf,stroke:#333,stroke-width:1px
    style B fill:#f9f,stroke:#333,stroke-width:2px
    style C fill:#ffb,stroke:#333,stroke-width:1px
    style D fill:#bfb,stroke:#333,stroke-width:1px
    style E fill:#fdd,stroke:#333,stroke-width:1px
    style F fill:#ddd,stroke:#333,stroke-width:1px
    style T1 fill:#eee,stroke:#333,stroke-width:1px
```

## Primeros pasos
```bash
# 1) Instalar dependencias usando uv
make init

# 2) El comando init te creará una carpeta assets/models, acá tienes que colocar el modelo .glb para ejecutar la aplicación 

# 3) Ejecutar pruebas
make test

# 4) Ejecutar la app
make run                 

```

## Pruebas
Usamos `pytest`. y se puede ejecutar con:
```bash
make test
```

## Modelos
Coloca tus pesos/artefactos de modelos en `assets/models`. Ejemplos:
- `assets/models/model.glb`
- `assets/models/pose.onnx`

## Solución de problemas
- **Windows**: usa Git Bash para `make`. Alternativa: ejecutar los comandos dentro del Makefile manualmente en PowerShell.

## Licencia
MIT.
