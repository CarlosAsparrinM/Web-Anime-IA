"use client";

import { useLanguage } from './LanguageProvider';
import ReactMarkdown from 'react-markdown';
import { ArticleData } from './ArticleCard';

export default function ArticleRenderer({ 
  article, 
  createdAt 
}: { 
  article: ArticleData, 
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
      <div className="hero-header" style={{ paddingBottom: '1rem' }}>
        <span className="badge-purple">
          {article.category}
        </span>
        <h1 className="hero-title" style={{ fontSize: '2.5rem', marginTop: '1.5rem' }}>
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
