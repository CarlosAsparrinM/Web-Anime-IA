"use client";

import Link from 'next/link';
import Image from 'next/image';
import { useLanguage } from './LanguageProvider';

export interface ArticleData {
  _id?: string;
  slug: string;
  title: { es: string, en: string };
  excerpt: { es: string, en: string };
  imageUrl: string;
  category: string;
  createdAt: string;
  comments?: any[];
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
      <article className="glass animate-slide-up article-card">
        <div className="article-image-container">
          <Image 
            src={article.imageUrl} 
            alt={title} 
            fill
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
            style={{ objectFit: 'cover' }}
          />
          <span className="category-badge">
            {article.category}
          </span>
        </div>
        <div className="article-content">
          <h3 className="article-title">
            {title.length > 60 ? title.substring(0, 60) + '...' : title}
          </h3>
          <p className="article-excerpt">
            {excerpt}
          </p>
          <div className="article-date" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>{date}</span>

          </div>
        </div>
      </article>
    </Link>
  );
}
