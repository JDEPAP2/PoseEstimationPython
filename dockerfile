# Imagen base con Python 3.12
FROM python:3.12-slim

# Instalar dependencias del sistema necesarias para OpenCV y YOLO
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        git \
        ffmpeg \
        libsm6 \
        libxext6 \
        libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Instalar uv 
RUN pip install --upgrade pip setuptools wheel \
    && pip install uv

# Crear directorio de la app
WORKDIR /app

# Copiar requirements primero para cache eficiente
COPY requirements.txt .

# Instalar dependencias del proyecto con uv
RUN uv pip install -r requirements.txt

# Copiar el resto del proyecto
COPY src/ src/
COPY tests/ tests/
COPY assets/ assets/
COPY main.py .
copy assets/ assets/models/

# Comando por defecto: correr la app
CMD ["python", "main.py"]
