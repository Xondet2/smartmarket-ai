# 🔧 Solución de Problemas - SmartMarket AI Backend

## El backend no inicia

### Problema 1: ModuleNotFoundError
\`\`\`
ModuleNotFoundError: No module named 'fastapi'
\`\`\`

**Solución:**
\`\`\`bash
cd backend
pip install -r requirements.txt
\`\`\`

### Problema 2: Puerto 8000 en uso
\`\`\`
Error: [Errno 48] Address already in use
\`\`\`

**Solución:**

**Windows:**
\`\`\`bash
netstat -ano | findstr :8000
taskkill /PID <PID> /F
\`\`\`

**Linux/Mac:**
\`\`\`bash
lsof -ti:8000 | xargs kill -9
\`\`\`

O usa otro puerto:
\`\`\`bash
python run.py --port 8001
\`\`\`

### Problema 3: Error de imports
\`\`\`
ImportError: attempted relative import with no known parent package
\`\`\`

**Solución:**
Asegúrate de ejecutar desde la carpeta backend:
\`\`\`bash
cd backend
python run.py
\`\`\`

### Problema 4: Torch no se instala
\`\`\`
ERROR: Could not find a version that satisfies the requirement torch
\`\`\`

**Solución:**
Instala torch manualmente primero:
\`\`\`bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

### Problema 5: Error con `EmailStr` de Pydantic
```
ImportError: email-validator is not installed, run `pip install pydantic[email]`
```

**Causa:**
El proyecto usa `EmailStr` en los modelos (por ejemplo, en `routes/auth.py`). En Pydantic v2 esta funcionalidad requiere el extra `email`, que instala la librería `email-validator`.

**Solución:**
- Ya está corregido en `requirements.txt` usando `pydantic[email]`.
- Si instalas manualmente, usa:
```bash
pip install "pydantic[email]>=2.12.0,<3.0.0"
```
\`\`\`

## Verificar que el backend funciona

1. **Abre tu navegador** y ve a: http://localhost:8000
   - Deberías ver: `{"message": "SmartMarket AI API", "version": "1.0.0", "status": "running"}`

2. **Verifica la documentación** en: http://localhost:8000/docs
   - Deberías ver la interfaz Swagger con todos los endpoints

3. **Prueba el health check**: http://localhost:8000/health
   - Deberías ver: `{"status": "healthy"}`

## Comandos útiles

### Iniciar el backend
\`\`\`bash
cd backend
python run.py
\`\`\`

### Verificar dependencias instaladas
\`\`\`bash
pip list | grep fastapi
pip list | grep uvicorn
\`\`\`

### Reinstalar todas las dependencias
\`\`\`bash
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
\`\`\`

### Ver logs detallados
\`\`\`bash
python run.py --log-level debug
\`\`\`

## Errores comunes de Python

### Python no encontrado
Asegúrate de tener Python 3.9+ instalado:
\`\`\`bash
python --version
\`\`\`

Si no funciona, intenta:
\`\`\`bash
python3 --version
\`\`\`

### pip no encontrado
\`\`\`bash
python -m pip --version
\`\`\`

Si no está instalado:
\`\`\`bash
python -m ensurepip --upgrade
\`\`\`

## ¿Aún no funciona?

1. **Verifica que estés en la carpeta correcta:**
   \`\`\`bash
   pwd  # Linux/Mac
   cd   # Windows
   \`\`\`
   Deberías estar en: `tu-proyecto/backend`

2. **Verifica que el archivo main.py existe:**
   \`\`\`bash
   ls main.py  # Linux/Mac
   dir main.py # Windows
   \`\`\`

3. **Intenta iniciar manualmente con uvicorn:**
   \`\`\`bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   \`\`\`

4. **Revisa los logs completos** para ver el error exacto

## Contacto

Si ninguna solución funciona, comparte:
- El comando exacto que ejecutaste
- El error completo que aparece
- Tu versión de Python (`python --version`)
- Tu sistema operativo
