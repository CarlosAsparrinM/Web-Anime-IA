"use client";

import { useLanguage } from './LanguageProvider';
import ArticleCard, { ArticleData } from './ArticleCard';

export default function RelatedArticles({ articles }: { articles: ArticleData[] }) {
  const { language } = useLanguage();
  
  if (!articles || articles.length === 0) return null;

  const title = language === 'es' ? 'Artículos Relacionados' : 'Related Articles';

  return (
    <div style={{ marginTop: '3rem', paddingTop: '2rem', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
      <h3 style={{ fontSize: '1.5rem', marginBottom: '1.5rem', fontWeight: 'bold' }}>
        {title}
      </h3>
      
      <div className="article-grid">
        {articles.map((article) => (
          <ArticleCard key={article._id || article.slug} article={article} />
        ))}
      </div>
    </div>
  );
}
