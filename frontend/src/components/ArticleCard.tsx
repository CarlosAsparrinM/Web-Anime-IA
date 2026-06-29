"use client";

import Link from 'next/link';
import Image from 'next/image';
import { useLanguage } from './LanguageProvider';

interface ArticleData {
  slug: string;
  title: { es: string, en: string };
  excerpt: { es: string, en: string };
  imageUrl: string;
  category: string;
  createdAt: string;
}

export default function ArticleCard({ article }: { article: ArticleData }) {
  const { language } = useLanguage();
  
  const title = article.title[language] || article.title.es;
  const excerpt = article.excerpt[language] || article.excerpt.es;
  
  const date = new Date(article.createdAt).toLocaleDateString(
    language === 'es' ? 'es-ES' : 'en-US', 
    { month: 'long', day: 'numeric', year: 'numeric' }
  );

  return (
    <Link href={`/articulo/${article.slug}`} style={{ display: 'block' }}>
      <article className="glass animate-slide-up" style={{
        borderRadius: '16px',
        overflow: 'hidden',
        transition: 'transform 0.3s ease, box-shadow 0.3s ease',
        height: '100%',
        display: 'flex',
        flexDirection: 'column'
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-5px)';
        e.currentTarget.style.boxShadow = '0 10px 30px -10px rgba(139, 92, 246, 0.3)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.boxShadow = 'none';
      }}
      >
        <div style={{ position: 'relative', height: '200px', width: '100%', overflow: 'hidden' }}>
          <Image 
            src={article.imageUrl} 
            alt={title} 
            fill
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
            style={{ objectFit: 'cover' }}
          />
          <span style={{
            position: 'absolute',
            top: '1rem',
            right: '1rem',
            background: 'rgba(0,0,0,0.7)',
            backdropFilter: 'blur(4px)',
            padding: '0.25rem 0.75rem',
            borderRadius: '20px',
            fontSize: '0.75rem',
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '1px',
            color: 'var(--neon-cyan)',
            zIndex: 10
          }}>
            {article.category}
          </span>
        </div>
        <div style={{ padding: '1.5rem', flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
          <h3 style={{ fontSize: '1.25rem', marginBottom: '0.75rem', lineHeight: 1.3 }}>
            {title.length > 60 ? title.substring(0, 60) + '...' : title}
          </h3>
          <p style={{ color: '#94a3b8', fontSize: '0.9rem', lineHeight: 1.5, flexGrow: 1 }}>
            {excerpt}
          </p>
          <div style={{ marginTop: '1.5rem', color: '#64748b', fontSize: '0.8rem', fontWeight: 500 }}>
            {date}
          </div>
        </div>
      </article>
    </Link>
  );
}
