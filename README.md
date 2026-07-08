# KenkoAnime 🌸🤖

Bienvenido a **KenkoAnime**, un portal de noticias, análisis y curiosidades sobre la industria del Anime generado **100% de manera autónoma por Inteligencia Artificial**.

Este proyecto se divide en dos grandes componentes arquitectónicos: un sistema orquestador de **7 Agentes IA** en el backend (Python) y una interfaz ultrarrápida y estilizada en el frontend (Next.js).

---

## 🏗️ Arquitectura del Proyecto

El repositorio está separado en dos ecosistemas distintos:

### 1. `backend/` (El Cerebro) 🧠
Construido con **Python y FastAPI**, este es el motor de los agentes de Inteligencia Artificial. Cuando se activa, ejecuta un pipeline de 7 fases iterativas que investigan, redactan, auditan, traducen y publican contenido sin intervención humana.

**Pipeline de los 7 Agentes:**
1. **Editor:** Obtiene los datos crudos de bases de datos de anime (Jikan/MyAnimeList) y define el titular y enfoque.
2. **Investigador:** Busca en tiempo real en la web (usando la API de Tavily) noticias y datos verídicos de las últimas 72 horas para evitar alucinaciones. Extrae un JSON estructurado.
3. **Escritor:** Redacta un artículo extenso, detallado y apasionado en formato Markdown.
4. **Revisor de Calidad:** Audita el artículo contra el título. Si detecta desviaciones o falta de coherencia, fuerza al Escritor a rehacer el artículo en un bucle cerrado (máx. 3 intentos).
5. **Traductor:** Traduce el Markdown español a un inglés perfecto, respetando las rutas de imágenes y estructura.
6. **Agente de Imágenes:** Verifica analíticamente cada URL de imagen. Si una imagen está rota o no concuerda con el anime, la sustituye dinámicamente usando DuckDuckGo Search.
7. **Titulador SEO:** Crea un título viral, un resumen SEO optimizado y empaqueta el archivo final JSON para inyectarlo en **MongoDB**.

**Tecnologías:** FastAPI, Motor (MongoDB Async), httpx, Tavily API.

### 2. `frontend/` (La Presentación) 💅
Construido con **Next.js 16 (App Router)**, ofrece una experiencia de usuario (UX) *premium*. 
- **Buscador & Paginación Dinámica:** Buscador ultra rápido asíncrono y sistema de "Cargar más" sin recargar la web.
- **Glassmorphism:** Tarjetas esmeriladas e inputs curvos con efectos de neón.
- **SEO Automático:** Autogeneración nativa de `sitemap.xml` y `feed.xml` (RSS) para ser absorbido por Google News y crawlers web.
- **Internacionalización:** Soporte nativo para cambiar entre Inglés y Español usando Context API.
- Totalmente responsive y adaptado a móviles.

**Tecnologías:** Next.js, React 19, CSS Vanilla (Variables/Animaciones), React-Markdown.

---

## 🚀 Cómo Correr el Proyecto en Local

### Prerrequisitos
- Node.js (v18 o superior)
- Python (3.10 o superior)
- MongoDB (Atlas o Local)

### 1. Configurar el Backend (Python)
1. Entra a la carpeta backend: `cd backend`
2. Activa el entorno virtual: `.\venv\Scripts\activate` (Windows) o `source venv/bin/activate` (Mac/Linux).
3. Instala dependencias: `pip install -r requirements.txt`
4. Inicia el servidor de agentes:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### 2. Configurar el Frontend (Next.js)
1. Entra a la carpeta frontend: `cd frontend`
2. Instala los paquetes: `npm install`
3. Crea un archivo `.env.local` con tus credenciales (Ver sección *Variables de Entorno*).
4. Inicia el servidor de desarrollo:
   ```bash
   npm run dev
   ```
5. Abre `http://localhost:3001` en tu navegador.

---

## ⚙️ Variables de Entorno (`frontend/.env.local`)

El backend de Python ha sido configurado para leer este mismo archivo, por lo que solo necesitas configurarlo una vez en la carpeta `frontend/`:

```env
# Conexión a Base de Datos
MONGODB_URI=mongodb+srv://<usuario>:<password>@cluster...

# APIs de Inteligencia Artificial
API_ONE_URL=http://localhost:3000
API_ONE_KEY=tu-api-key-aqui
TAVILY_API_KEY=tu-api-key-de-tavily

# Seguridad
CRON_SECRET=mi-secreto-local-123
```

---

## ✍️ Forzar Generación de Artículos
Si tienes ambos servidores corriendo, puedes disparar la generación manual navegando a las siguientes URLs en tu navegador:
- `http://localhost:8000/api/generate?secret=mi-secreto-local-123&force=true&category=novedades`
- `http://localhost:8000/api/generate?secret=mi-secreto-local-123&force=true&category=curiosidades`
- `http://localhost:8000/api/generate?secret=mi-secreto-local-123&force=true&category=analisis`
