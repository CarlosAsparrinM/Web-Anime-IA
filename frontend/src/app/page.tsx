import { getLatestArticles } from '@/lib/articles';
import ArticleCard, { ArticleData } from '@/components/ArticleCard';

export const dynamic = 'force-dynamic';

export default async function Home({ searchParams }: { searchParams: Promise<{ cat?: string }> }) {
  const params = await searchParams;
  const category = params.cat;
  
  const articles = await getLatestArticles(12, category);

  return (
    <div className="container">
      <section className="hero-header animate-fade-in">
        <h1 className="hero-title">
          <span className="text-gradient">Kenko</span>Anime
        </h1>
        <p className="hero-subtitle">
          El primer blog de anime generado 100% por Inteligencia Artificial. Novedades, curiosidades y recomendaciones diarias.
        </p>
      </section>

      <section className="article-grid">
        {articles.length === 0 ? (
          <div className="empty-state">
            <h2>Aún no hay artículos publicados.</h2>
            <p>Vuelve mañana o ejecuta el generador manualmente.</p>
          </div>
        ) : (
          articles.map((article: ArticleData) => (
            <ArticleCard key={article._id} article={article} />
          ))
        )}
      </section>
    </div>
  );
}
