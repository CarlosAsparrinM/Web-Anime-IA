import { getArticleBySlug, getRelatedArticles } from '@/lib/articles';
import { notFound } from 'next/navigation';
import type { Metadata } from 'next';
import ArticleRenderer from '@/components/ArticleRenderer';
import Image from 'next/image';
import CommentsSection from '@/components/CommentsSection';
import RelatedArticles from '@/components/RelatedArticles';

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const resolvedParams = await params;
  const article = await getArticleBySlug(resolvedParams.slug);
  if (!article) return { title: 'Not Found' };
  
  return {
    title: `${article.title.es} | KenkoAnime`,
    description: article.excerpt.es,
    openGraph: {
      title: article.title.es,
      description: article.excerpt.es,
      images: [article.imageUrl],
      locale: 'es_ES',
      alternateLocale: ['en_US'],
    }
  };
}

export default async function ArticlePage({ params }: { params: Promise<{ slug: string }> }) {
  const resolvedParams = await params;
  const article = await getArticleBySlug(resolvedParams.slug);
  
  if (!article) {
    notFound();
  }

  const relatedArticles = await getRelatedArticles(article.slug, article.tags || [], 4);

  return (
    <article style={{ maxWidth: '800px', margin: '0 auto', paddingBottom: '4rem' }} className="animate-fade-in">
      <div style={{ position: 'relative', width: '100%', height: '400px', borderRadius: '16px', overflow: 'hidden', marginBottom: '2rem' }}>
        <Image 
          src={article.imageUrl} 
          alt={article.imageAlt}
          fill
          priority
          sizes="(max-width: 800px) 100vw, 800px"
          style={{ objectFit: 'cover' }}
        />
        <div style={{
          position: 'absolute',
          bottom: 0, left: 0, right: 0,
          background: 'linear-gradient(to top, rgba(15,17,26,1) 0%, rgba(15,17,26,0) 100%)',
          height: '50%'
        }}></div>
      </div>
      
      <ArticleRenderer article={article} createdAt={article.createdAt} />
      
      <CommentsSection slug={article.slug} initialComments={article.comments || []} />
      <RelatedArticles articles={relatedArticles} />
    </article>
  );
}

