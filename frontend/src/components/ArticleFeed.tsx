"use client";

import { useState, useEffect } from 'react';
import ArticleCard, { ArticleData } from './ArticleCard';
import { Search } from 'lucide-react';

export default function ArticleFeed({ initialArticles, initialTotal }: { initialArticles: ArticleData[], initialTotal: number }) {
  const [articles, setArticles] = useState<ArticleData[]>(initialArticles);
  const [page, setPage] = useState(1);
  const [category, setCategory] = useState('all');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(initialTotal > initialArticles.length);

  const fetchArticles = async (pageNum: number, cat: string, query: string, append: boolean = false) => {
    setLoading(true);
    try {
      const url = new URL('/api/articles', window.location.origin);
      url.searchParams.set('page', pageNum.toString());
      if (cat !== 'all') url.searchParams.set('category', cat);
      if (query) url.searchParams.set('search', query);
      
      const res = await fetch(url.toString());
      const data = await res.json();
      
      if (append) {
        setArticles(prev => [...prev, ...data.articles]);
      } else {
        setArticles(data.articles);
      }
      
      setHasMore(data.page < data.totalPages);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Reset to page 1 and fetch on category or search change
    setPage(1);
    const timeout = setTimeout(() => {
      fetchArticles(1, category, search, false);
    }, 500); // Debounce search
    return () => clearTimeout(timeout);
  }, [category, search]);

  const loadMore = () => {
    const nextPage = page + 1;
    setPage(nextPage);
    fetchArticles(nextPage, category, search, true);
  };

  return (
    <div className="feed-wrapper">
      <div className="filters-container" style={{ 
        display: 'flex', 
        flexDirection: 'column', 
        gap: '1.5rem', 
        marginBottom: '3rem', 
        alignItems: 'center' 
      }}>
        
        {/* Search Bar */}
        <div style={{ position: 'relative', width: '100%', maxWidth: '500px' }}>
          <Search size={20} style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', color: '#888' }} />
          <input 
            type="text" 
            placeholder="Buscar anime (ej. Evangelion)..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ 
              padding: '1rem 1rem 1rem 3rem', 
              borderRadius: '50px', 
              border: '1px solid rgba(255,255,255,0.1)', 
              background: 'rgba(20, 20, 20, 0.6)', 
              backdropFilter: 'blur(10px)',
              color: '#fff', 
              width: '100%',
              fontSize: '1rem',
              outline: 'none',
              boxShadow: '0 4px 30px rgba(0, 0, 0, 0.1)',
              transition: 'all 0.3s ease'
            }}
            onFocus={(e) => e.target.style.border = '1px solid rgba(255,107,107,0.5)'}
            onBlur={(e) => e.target.style.border = '1px solid rgba(255,255,255,0.1)'}
          />
        </div>
        
        {/* Category Pills */}
        <div style={{ display: 'flex', gap: '0.8rem', flexWrap: 'wrap', justifyContent: 'center' }}>
          {[
            { id: 'all', label: 'Todos' },
            { id: 'analisis', label: 'Análisis' },
            { id: 'novedades', label: 'Novedades' },
            { id: 'curiosidades', label: 'Curiosidades' }
          ].map(cat => (
            <button
              key={cat.id}
              onClick={() => setCategory(cat.id)}
              style={{
                padding: '0.6rem 1.5rem',
                borderRadius: '30px',
                border: category === cat.id ? 'none' : '1px solid rgba(255,255,255,0.1)',
                background: category === cat.id ? 'linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%)' : 'rgba(255,255,255,0.05)',
                color: category === cat.id ? '#fff' : '#aaa',
                fontWeight: category === cat.id ? 'bold' : 'normal',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                boxShadow: category === cat.id ? '0 4px 15px rgba(255, 107, 107, 0.3)' : 'none'
              }}
              onMouseEnter={(e) => {
                if (category !== cat.id) {
                  e.currentTarget.style.background = 'rgba(255,255,255,0.1)';
                  e.currentTarget.style.color = '#fff';
                }
              }}
              onMouseLeave={(e) => {
                if (category !== cat.id) {
                  e.currentTarget.style.background = 'rgba(255,255,255,0.05)';
                  e.currentTarget.style.color = '#aaa';
                }
              }}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      <section className="article-grid">
        {articles.length === 0 ? (
          <div className="empty-state" style={{ gridColumn: '1 / -1' }}>
            <h2>Aún no hay artículos publicados.</h2>
            <p>Vuelve mañana o ejecuta el generador manualmente.</p>
          </div>
        ) : (
          articles.map((article: ArticleData, index) => (
            <ArticleCard key={article._id || index} article={article} />
          ))
        )}
      </section>

      {hasMore && (
        <div style={{ textAlign: 'center', marginTop: '3rem' }}>
          <button 
            onClick={loadMore} 
            disabled={loading}
            style={{ 
              padding: '1rem 2rem', 
              borderRadius: '30px', 
              border: 'none', 
              background: 'linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%)', 
              color: 'white', 
              fontWeight: 'bold', 
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.7 : 1
            }}
          >
            {loading ? 'Cargando...' : 'Cargar más artículos'}
          </button>
        </div>
      )}
    </div>
  );
}
