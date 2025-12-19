# Configuración Híbrida de Generación de PDFs

## Resumen

El sistema ahora soporta **dos motores de generación de PDFs** que se seleccionan automáticamente según el ambiente:

- **🎭 Playwright** - Para desarrollo local (mejor calidad, renderizado perfecto)
- **📄 WeasyPrint** - Para producción en Railway (más ligero, sin dependencias de navegador)

## ¿Cómo Funciona?

### Detección Automática de Ambiente

El sistema detecta automáticamente en qué ambiente está corriendo:

```python
def is_railway_environment():
    """Detecta si estamos corriendo en Railway"""
    return os.getenv('RAILWAY_ENVIRONMENT') is not None or os.getenv('RAILWAY_PROJECT_ID') is not None
```

### Selección de Motor

```python
def get_pdf_engine():
    # En Railway → WeasyPrint
    if is_railway_environment():
        return 'weasyprint'
    
    # En local → Playwright (preferido)
    if PLAYWRIGHT_AVAILABLE:
        return 'playwright'
    
    # Fallback → WeasyPrint
    return 'weasyprint'
```

## Ventajas de Cada Motor

### Playwright (Local)

✅ **Ventajas:**
- Renderiza exactamente como se ve en el navegador
- Soporta todos los emojis, iconos y fuentes
- Mejor manejo de CSS moderno
- Colores y estilos perfectos
- JavaScript ejecutado (si es necesario)

❌ **Desventajas:**
- Requiere instalar navegador Chromium (~200MB)
- Más pesado en recursos
- No funciona bien en Railway

### WeasyPrint (Railway)

✅ **Ventajas:**
- Más ligero (no requiere navegador)
- Funciona bien en Railway
- Más rápido en ambientes limitados

❌ **Desventajas:**
- Limitaciones con emojis Unicode
- Requiere fuentes del sistema
- CSS limitado comparado con navegadores

## Instalación

### Para Desarrollo Local

```bash
# Instalar dependencias
pip install -r requirements.txt

# Instalar navegador Chromium para Playwright
python -m playwright install chromium
```

### Para Railway

No se requiere instalación adicional. Railway usará WeasyPrint automáticamente con las dependencias definidas en `nixpacks.toml`.

## Archivos Modificados

### 1. `app/core/app.py`

**Funciones agregadas:**
- `is_railway_environment()` - Detecta el ambiente
- `get_pdf_engine()` - Selecciona el motor apropiado
- `generate_pdf_with_playwright()` - Genera PDF con Playwright
- `generate_pdf_with_weasyprint()` - Genera PDF con WeasyPrint

**Rutas modificadas:**
- `/api/jira/download-report` - Usa motor híbrido
- `/api/metrics/download-report` - Usa motor híbrido

### 2. `requirements.txt`

```txt
# Generación de PDFs
# Playwright para desarrollo local (mejor calidad, requiere navegador)
playwright>=1.40.0
# WeasyPrint para producción/Railway (más ligero, no requiere navegador)
weasyprint>=60.0.0
```

### 3. `nixpacks.toml`

No requiere cambios. WeasyPrint seguirá funcionando en Railway con las dependencias existentes.

## Uso

No se requiere ningún cambio en el código del usuario. El sistema selecciona automáticamente el motor apropiado:

```python
# El código es el mismo para ambos motores
@app.route('/api/jira/download-report', methods=['POST'])
def jira_download_report():
    # ... preparar datos ...
    
    # Automáticamente usa Playwright (local) o WeasyPrint (Railway)
    pdf_engine = get_pdf_engine()
    
    if pdf_engine == 'playwright':
        pdf_buffer = generate_pdf_with_playwright(html_content)
    else:
        pdf_buffer = generate_pdf_with_weasyprint(html_content)
    
    return Response(pdf_buffer, mimetype='application/pdf')
```

## Logs

El sistema registra qué motor está usando:

```
INFO:app.core.app:Usando Playwright (ambiente local)
INFO:app.core.app:Iniciando generación de PDF para proyecto PC usando playwright
```

o

```
INFO:app.core.app:Usando WeasyPrint (ambiente Railway)
INFO:app.core.app:Iniciando generación de PDF para proyecto PC usando weasyprint
```

## Troubleshooting

### Error: "Playwright no disponible"

**Solución:**
```bash
pip install playwright
python -m playwright install chromium
```

### Error: "WeasyPrint no disponible en Railway"

**Solución:**
Verificar que `nixpacks.toml` tenga las dependencias correctas:
```toml
[phases.setup]
nixPkgs = ["python311", "cairo", "pango", "gdk-pixbuf", "libffi", "fontconfig", "dejavu_fonts", "noto-fonts-emoji"]
```

### PDFs se ven diferentes en local vs Railway

Esto es **esperado** porque usan motores diferentes:
- **Local (Playwright)**: Renderizado perfecto, como en navegador
- **Railway (WeasyPrint)**: Puede tener diferencias menores en fuentes/iconos

Para testing, puedes forzar WeasyPrint en local comentando la importación de Playwright:

```python
# Temporal: forzar WeasyPrint en local para testing
PLAYWRIGHT_AVAILABLE = False
```

## Próximos Pasos

### Mejoras Opcionales

1. **Variable de Entorno para Forzar Motor:**
   ```python
   PDF_ENGINE = os.getenv('PDF_ENGINE', 'auto')  # 'auto', 'playwright', 'weasyprint'
   ```

2. **Cache de PDFs:**
   - Cachear PDFs generados para evitar regeneración

3. **Generación Asíncrona:**
   - Para reportes grandes, generar PDFs en background

## Contacto

Si encuentras problemas:
1. Revisar logs del servidor
2. Verificar qué motor está usando
3. Probar con el otro motor si es posible
