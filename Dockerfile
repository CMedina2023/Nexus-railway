# Usar imagen base de Python con dependencias de Playwright
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Instalar Playwright browsers
RUN playwright install chromium

# Copiar el resto de la aplicación
COPY . .

# Crear directorios necesarios
RUN mkdir -p temp_uploads sessions backups

# Exponer puerto (Render usa $PORT)
EXPOSE $PORT

# Comando de inicio (será sobrescrito por Render)
CMD gunicorn -w 4 -b 0.0.0.0:$PORT --timeout 120 run:app








