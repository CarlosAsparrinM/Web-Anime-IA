# Registro de Cambios (Changelog) - KenkoAnime 🚀

Este documento resume la refactorización masiva y las mejoras implementadas en el proyecto para convertirlo en un sistema robusto, autónomo y estéticamente premium.

## 1. Migración de Arquitectura (De Monolito a Microservicios)
- **Desacoplamiento:** Se migró toda la lógica de Inteligencia Artificial (Orquestador y Agentes) que residía en Next.js (TypeScript) hacia un nuevo entorno backend en **Python usando FastAPI**.
- **Limpieza profunda:** Se eliminaron los scripts y carpetas obsoletas en el frontend (`src/lib/agent/`, `api/`, `generate/`, `test-api.ts`) asegurando que el frontend se dedique 100% a la interfaz de usuario.
- **Nuevo Gateway:** La ruta en Next.js (`app/api/generate/route.ts`) ahora funciona como un proxy limpio que se comunica directamente con el servidor de FastAPI en el puerto 8000.

## 2. Mejoras en el Pipeline de Agentes IA 🧠
- **Fusión de Categorías:** Se unificaron "Reseñas" y "Recomendaciones" en una categoría súper fuerte llamada **"Análisis"**. Las categorías finales son: `novedades`, `curiosidades` y `analisis`.
- **Filtro Anti-Noticias Viejas (Tavily):** Se le inyectó "consciencia temporal" al Investigador. Si busca `novedades`, automáticamente filtra resultados para traer solo artículos publicados en las **últimas 72 horas** desde fuentes confiables (ANN, Crunchyroll, Reddit).
- **Nuevo Agente Traductor (Pipeline de 5 fases):** Se introdujo un 5to agente exclusivo para la traducción. Ahora el *Escritor* redacta únicamente en español (aprovechando toda su memoria para explayarse) y el *Traductor* toma ese texto y lo pasa a inglés respetando el Markdown y los enlaces de imágenes.
- **Prevención de Textos Cortos:** Se impuso una *Regla Crítica* en los prompts exigiendo una extensión estricta (ej. mínimo 2 a 4 párrafos de 80 palabras por cada H2).
- **Manejo de Errores (JSON Parse):** Se corrigió la tendencia de los LLMs a romper el JSON usando comillas dobles internas, obligándolos a usar comillas simples, y se implementó un sistema de fallback (emergencia) para que el orquestador no colapse si falla un parseo.
- **Autopublicación:** Se solucionó el bug donde los artículos generados no se mostraban en el frontend al inyectar automáticamente el campo `"published": True` al guardar en MongoDB.

## 3. Rediseño Frontend (UI/UX) 💅
- **Estética Premium (Glassmorphism):** Se añadió la clase `.glass` (backdrop-filter) para dar un efecto de cristal esmerilado a las tarjetas de los artículos.
- **Tipografía y Colores:** Se configuró un entorno "Dark Mode" con gradientes Cyberpunk (Morado/Rosa/Cyan) para el logotipo y los títulos (`.text-gradient`).
- **Animaciones:** Se implementaron micro-interacciones (hover en tarjetas y botones) y animaciones de entrada (`.animate-fade-in`, `.animate-slide-up`) para evitar cargas bruscas de contenido.
- **Optimización de Imágenes (SEO):** Se reemplazaron todas las etiquetas `<img>` HTML estáticas por el componente `<Image>` nativo de Next.js. Se actualizó el `next.config.ts` para autorizar descargas dinámicas desde cualquier host remoto.
- **Diseño Responsive:** Se reescribió el menú de navegación (`Navbar.tsx`) integrando Flex-Wrap para que se adapte perfectamente a pantallas de dispositivos móviles sin romper la maquetación.

## 4. Integraciones y Refinamientos Recientes
- **Reparación del Gateway Frontend:** Se actualizó `app/api/generate/route.ts` para que funcione realmente como un proxy (`fetch`) hacia FastAPI, eliminando los imports locales obsoletos.
- **Fuentes Dinámicas por Categoría:** Se modificó `tavily.py` para extraer **10 fuentes** de información al investigar "Novedades" y **5 fuentes** para "Curiosidades" o "Análisis".
- **Estrategia de Investigación Nativa en Inglés:** Se depuró la lista de sitios de noticias en `generator.py` para buscar exclusivamente en gigantes de la industria en inglés (`animenewsnetwork`, `crunchyroll`, `myanimelist`, `comicbook`, `sportskeeda`). Esto permite ingerir la mejor calidad de información disponible a nivel global, aprovechando que el Agente Escritor redactará nativamente en español en el siguiente paso.

## 5. Cosas por Hacer (TODO)
- [ ] **Configuración del LLM en API-One:** Establecer el modelo por defecto a `Qwen 3 235B Instruct` (para máxima calidad) o `Gemma 4 31B` (para balance de velocidad/calidad) en el proveedor correspondiente.
- [ ] **Despliegue (Deploy):** Preparar el entorno de producción (ej. Subir el backend de Python a Render/Railway y el frontend a Vercel).
- [ ] **Programación (Cron):** Configurar una tarea programada (ej. Vercel Cron o GitHub Actions) que llame al endpoint `/api/generate` de manera diaria usando el `CRON_SECRET` para mantener la página viva en automático.
