import { getLatestArticles } from '@/lib/articles';
import ArticleFeed from '@/components/ArticleFeed';

export const dynamic = 'force-dynamic';

export default async function Home() {
  const { articles, total } = await getLatestArticles(12);

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

      <ArticleFeed initialArticles={articles} initialTotal={total} />
    </div>
  );
}
