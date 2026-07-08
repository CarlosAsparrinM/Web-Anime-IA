# Registro de Cambios (Changelog) - KenkoAnime 🚀

Este documento resume la refactorización masiva y las mejoras implementadas en el proyecto para convertirlo en un sistema robusto, autónomo y estéticamente premium.

## 1. Migración de Arquitectura (De Monolito a Microservicios)
- **Desacoplamiento:** Se migró toda la lógica de Inteligencia Artificial (Orquestador y Agentes) que residía en Next.js (TypeScript) hacia un nuevo entorno backend en **Python usando FastAPI**.
- **Limpieza profunda:** Se eliminaron los scripts y carpetas obsoletas en el frontend (`src/lib/agent/`, `api/`, `generate/`, `test-api.ts`) asegurando que el frontend se dedique 100% a la interfaz de usuario.
- **Nuevo Gateway:** La ruta en Next.js (`app/api/generate/route.ts`) ahora funciona como un proxy limpio que se comunica directamente con el servidor de FastAPI en el puerto 8000.

## 2. Mejoras en el Pipeline de Agentes IA 🧠
- **Bucle de Revisión (Reviewer Loop):** El Pipeline pasó de ser lineal a iterativo. Si el Agente Revisor no está de acuerdo con el contenido (por falta de coherencia con el título o formato), devolverá un feedback (en JSON) al Agente Escritor para que reescriba el artículo (hasta un máximo de 3 intentos) antes de rendirse.
- **Auditoría de Imágenes (Agente Inteligente):** Se creó el *Image QA Agent*, que analiza lógicamente si una imagen extraída de la fuente coincide con el anime real. Si encuentra una URL falsa o rota, hace uso de la herramienta `DuckDuckGo Search (DDGS)` internamente para buscar, descargar y reemplazar la imagen por una oficial en tiempo real.
- **Agente Titulador SEO:** Ahora el título y extracto del artículo no nacen al principio de la generación, sino al final. Un agente especializado lee el artículo finalizado y empaqueta un título atractivo, un excerpt corto y formatea la estructura del JSON final para la BD.
- **Fusión de Categorías:** Se unificaron "Reseñas" y "Recomendaciones" en una categoría súper fuerte llamada **"Análisis"**. Las categorías finales son: `novedades`, `curiosidades` y `analisis`.
- **Filtro Anti-Noticias Viejas (Tavily):** Se le inyectó "consciencia temporal" al Investigador para `novedades` (solo resultados de las últimas 72 horas).
- **Nuevo Agente Traductor (Pipeline de 7 fases):** Se integró la fase de traducción para mantener los artículos nativamente tanto en Español como en Inglés.
- **Manejo de Errores y JSON Parsing:** Se reescribieron los prompts para asegurar salida en JSON puro, además de rotación automática (Fallback) de LLMs (Gemini -> Llama 3 -> Cerebras) para resistir caídas de los proveedores.

## 3. Rediseño Frontend e Interactividad (UI/UX) 💅
- **Buscador en Tiempo Real:** Se implementó una barra de búsqueda (`ArticleFeed.tsx`) que filtra los artículos instantáneamente tanto por título como por nombre del anime, comunicándose vía API Routes de Next.js sin recargar la web.
- **Filtros por Categoría (Pills):** Se eliminó el `<select>` tradicional por hermosos botones tipo "Pill" en estilo Glassmorphism que resaltan con bordes de neón interactivos (`Todos`, `Análisis`, `Novedades`, `Curiosidades`).
- **Paginación / Scroll Asíncrono:** Se integró la función "Cargar más", reemplazando el feed inicial estático. Los usuarios pueden extraer de a 12 artículos nuevos a medida que navegan usando comandos de `$skip` en MongoDB.
- **Estética Premium:** Múltiples mejoras CSS (fondos desenfocados, hover effects, colores degradados `.text-gradient`, animaciones `.animate-fade-in`) para garantizar una sensación de alta gama.

## 3.1. Motores SEO 🚀
- **Sitemap Dinámico:** Generación automática en `/sitemap.xml` integrando nativamente las herramientas de Next.js (MetadataRoute). Google indexará cada nueva URL de artículo generada por la IA casi en tiempo real.
- **Feed RSS Automático:** Nuevo endpoint `/feed.xml` que transforma los últimos 20 artículos a estándar RSS 2.0. Listo para integrarse con bots de Discord y Feedly.

## 4. Integraciones y Refinamientos Recientes
- **Reparación del Gateway Frontend:** Se actualizó `app/api/generate/route.ts` para que funcione realmente como un proxy (`fetch`) hacia FastAPI, eliminando los imports locales obsoletos.
- **Fuentes Dinámicas por Categoría:** Se modificó `tavily.py` para extraer **10 fuentes** de información al investigar "Novedades" y **5 fuentes** para "Curiosidades" o "Análisis".
- **Estrategia de Investigación Nativa en Inglés:** Se depuró la lista de sitios de noticias en `generator.py` para buscar exclusivamente en gigantes de la industria en inglés (`animenewsnetwork`, `crunchyroll`, `myanimelist`, `comicbook`, `sportskeeda`). Esto permite ingerir la mejor calidad de información disponible a nivel global, aprovechando que el Agente Escritor redactará nativamente en español en el siguiente paso.

## 5. Cosas por Hacer (TODO)
- [ ] **Cola de Tareas en Backend (Task Queue):** Implementar un administrador de pausas asíncronas (`asyncio.Queue` / Celery) para distanciar la generación de múltiples artículos en el tiempo, evitando colisiones de los errores "Rate Limit (429)" al abusar de los LLMs.
- [ ] **Configuración del LLM en API-One:** Establecer el modelo por defecto a `Qwen 3 235B Instruct` (para máxima calidad) o `Gemma 4 31B` (para balance de velocidad/calidad) en el proveedor correspondiente.
- [ ] **Despliegue (Deploy):** Preparar el entorno de producción (ej. Subir el backend de Python a Render/Railway y el frontend a Vercel).
- [ ] **Programación (Cron):** Configurar una tarea programada (ej. Vercel Cron o GitHub Actions) que llame al endpoint `/api/generate` de manera diaria usando el `CRON_SECRET` para mantener la página viva en automático.
