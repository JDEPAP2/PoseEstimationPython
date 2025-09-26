# Imagen base ligera y reproducible
FROM python:3.12

# Carpeta de trabajo dentro del contenedor
WORKDIR /home/src

# Instalar dependencias de OpenCV
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

# 1) Copiar solo requirements 
COPY requirements.txt .

# 2) Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# 3) Copiar el resto del proyecto
COPY . .

# 4) Crear directorios requeridos por la app (si no existen)
RUN mkdir -p assets/models

# 5) Comando por defecto
CMD ["python", "main.py", "--cert=adhoc"]