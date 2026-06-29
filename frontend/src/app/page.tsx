import { getLatestArticles } from '@/lib/articles';
import ArticleCard from '@/components/ArticleCard';

export const dynamic = 'force-dynamic';

export default async function Home({ searchParams }: { searchParams: Promise<{ cat?: string }> }) {
  const params = await searchParams;
  const category = params.cat;
  
  const articles = await getLatestArticles(12, category);

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      <section style={{ textAlign: 'center', padding: '4rem 1rem 3rem' }} className="animate-fade-in">
        <h1 style={{ fontSize: '4rem', marginBottom: '1rem', lineHeight: 1.1 }}>
          <span className="text-gradient">Kenko</span>Anime
        </h1>
        <p style={{ fontSize: '1.2rem', color: '#94a3b8', maxWidth: '600px', margin: '0 auto' }}>
          El primer blog de anime generado 100% por Inteligencia Artificial. Novedades, curiosidades y recomendaciones diarias.
        </p>
      </section>

      <section style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', 
        gap: '2rem',
        padding: '2rem 0'
      }}>
        {articles.length === 0 ? (
          <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '4rem', color: '#64748b' }}>
            <h2>Aún no hay artículos publicados.</h2>
            <p>Vuelve mañana o ejecuta el generador manualmente.</p>
          </div>
        ) : (
          articles.map((article: any) => (
            <ArticleCard key={article._id} article={article} />
          ))
        )}
      </section>
    </div>
  );
}
