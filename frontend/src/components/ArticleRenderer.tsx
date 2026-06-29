"use client";

import { useLanguage } from './LanguageProvider';
import ReactMarkdown from 'react-markdown';

export default function ArticleRenderer({ 
  article, 
  createdAt 
}: { 
  article: any, 
  createdAt: string 
}) {
  const { language } = useLanguage();

  const title = article.title[language] || article.title.es;
  const content = article.content[language] || article.content.es;
  
  const dateStr = new Date(createdAt).toLocaleDateString(
    language === 'es' ? 'es-ES' : 'en-US', 
    { dateStyle: 'long' }
  );

  return (
    <>
      <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
        <span style={{
          background: 'rgba(139, 92, 246, 0.2)',
          color: 'var(--neon-purple)',
          padding: '0.5rem 1rem',
          borderRadius: '20px',
          fontWeight: 600,
          textTransform: 'uppercase',
          letterSpacing: '1px',
          fontSize: '0.8rem'
        }}>
          {article.category}
        </span>
        <h1 style={{ fontSize: '2.5rem', marginTop: '1.5rem', lineHeight: 1.2 }}>
          {title}
        </h1>
        <div style={{ color: '#64748b', marginTop: '1rem' }}>
          {dateStr}
        </div>
      </div>

      <div className="glass" style={{ padding: '2rem 3rem', borderRadius: '16px' }}>
        <div className="markdown-content">
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
      </div>
    </>
  );
}
