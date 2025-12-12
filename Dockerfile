# Usar imagen base de Python oficial y ligera
FROM python:3.10-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para WeasyPrint y otros
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    python3-cffi \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# (Playwright eliminado ya que se usa WeasyPrint)

# Copiar el resto de la aplicación
COPY . .

# Crear directorios necesarios
RUN mkdir -p temp_uploads sessions backups

# Exponer puerto (Render usa $PORT)
EXPOSE $PORT

# Comando de inicio (será sobrescrito por Render)
CMD gunicorn -w 4 -b 0.0.0.0:$PORT --timeout 120 run:app








