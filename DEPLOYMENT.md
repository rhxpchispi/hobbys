# Despliegue de Proyecto Hobbys en Render y Qdrant Cloud

## 1. Resumen

Este documento describe los pasos para desplegar el backend FastAPI en Render y usar Qdrant Cloud como vector DB gestionada.

- Backend: `backend/main.py`
- Frontend: `frontend/src/api/search.ts`
- Variables de entorno utilizadas:
  - `QDRANT_HOST`
  - `QDRANT_API_KEY`
  - `QDRANT_PORT` (opcional)
  - `VITE_API_URL`

## 2. Configuración del backend en Render

### 2.1 Crear servicio en Render

1. En el dashboard de Render, crea un nuevo servicio:
   - Tipo: `Web Service`
   - Conecta tu repositorio GitHub que contiene el proyecto `Proyecto Hobbys`
   - Branch: la rama principal de tu MVP (por ejemplo `main`)
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
     - Render define la variable de entorno `PORT`; usar `$PORT` asegura que el servicio escuche en el puerto asignado automáticamente.

### 2.2 Variables de entorno del servicio backend

En la sección `Environment` del servicio de backend en Render, agrega:

- `QDRANT_HOST`
  - Para Qdrant Cloud gestionado, usa la URL completa del cluster, por ejemplo:
    `https://<your-cluster-id>.qdrant.cloud`
  - Para desarrollo local con Docker Compose, deja el fallback `localhost` o usa `qdrant`.

- `QDRANT_API_KEY`
  - La API Key de tu proyecto Qdrant Cloud.
  - Si usas Qdrant local, puede quedar vacío.

- `QDRANT_PORT`
  - Solo necesario para conexiones locales a `localhost` o `qdrant`.
  - Valor recomendado para local: `6333`
  - Para Qdrant Cloud no es necesario si usas `QDRANT_HOST` con esquema HTTPS.

Nota: no uses credenciales en el código. `backend/main.py` ya usa `os.getenv(...)`.

## 3. Configuración de Qdrant Cloud

### 3.1 Crear colección y acceso seguro

1. En Qdrant Cloud, crea un proyecto o usa uno existente.
2. Copia el `API Key` y el endpoint HTTPS del cluster.
3. No es necesario crear la colección manualmente antes del primer despliegue. El backend verifica si la colección existe y, si no, la crea automáticamente.

### 3.2 Comportamiento de inicialización

El backend ya maneja este flujo:

- Conecta a Qdrant usando `QDRANT_HOST` y `QDRANT_API_KEY`.
- Consulta las colecciones existentes.
- Si `cursos_hobby` no existe, la crea.
- Si la colección existe pero está vacía, inserta los cursos desde `backend/data.json`.
- Si ya tiene puntos, no vuelve a insertar datos para evitar duplicaciones.

## 4. Configuración del frontend Vite

### 4.1 Variables de entorno para el frontend

En el servicio frontend, agrega la variable de entorno de build:

- `VITE_API_URL`
  - Ejemplo: `https://mi-backend-render.onrender.com`
  - Si frontend y backend se sirven desde el mismo origen, puede ser `""` o `/`.

### 4.2 Qué hace `frontend/src/api/search.ts`

El frontend usa `import.meta.env.VITE_API_URL` para construir la URL base de la API:

- Si `VITE_API_URL` está definida, usa `https://mi-backend-render.onrender.com/api/search`
- Si no está definida, usa la ruta relativa `/api/search`

Esto permite un build único para local y para producción.

## 5. Inicialización local antes de push a GitHub

### 5.1 Backend local con Docker Compose

En la raíz del repositorio, ejecuta:

```bash
docker compose up --build -d
```

Esto levantará:

- Qdrant en `http://localhost:6333`
- Backend en `http://localhost:8000`
- Frontend en `http://localhost`

### 5.2 Variables locales opcionales

Crea un archivo `.env` en `backend/` con:

```env
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=
```

Y en `frontend/` un `.env` con:

```env
VITE_API_URL=http://localhost:8000
```

### 5.3 Comprobación previa al push

1. Verifica que el backend arranca sin errores.
2. Accede a `http://localhost:8000/health`.
3. Ejecuta una búsqueda de prueba en el frontend.
4. Asegúrate de que los datos de Qdrant están cargados y no se duplican tras reiniciar.

## 6. Push al repositorio

1. Confirma cambios en el repositorio:

```bash
git add backend/main.py frontend/src/api/search.ts DEPLOYMENT.md
git commit -m "Preparar despliegue a Render y Qdrant Cloud"
git push origin main
```

2. En Render, habilita el despliegue automático de tu rama principal si aún no está activado.

## 7. Notas de seguridad y producción

- Mantén `QDRANT_API_KEY` fuera del repositorio.
- Usa Render Environment Secrets / variables protegidas.
- No expongas `QDRANT_API_KEY` en el frontend.
- Para producción, considera activar HTTPS y CORS restringido en Render.

---

`Proyecto Hobbys` ya está listo para conectarse a Qdrant Cloud de forma segura y para usar configuración dinámica de API en Vite.