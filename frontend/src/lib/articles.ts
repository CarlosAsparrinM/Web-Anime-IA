import dbConnect from './mongodb';
import Article from '@/models/Article';

export async function getLatestArticles(limit = 10, category?: string) {
  await dbConnect();
  const query = category ? { category, published: true } : { published: true };
  
  const articles = await Article.find(query)
    .sort({ createdAt: -1 })
    .limit(limit)
    .lean();
    
  return JSON.parse(JSON.stringify(articles)); // Serialize for Next.js Server Components
}

export async function getArticleBySlug(slug: string) {
  await dbConnect();
  const article = await Article.findOne({ slug, published: true }).lean();
  return article ? JSON.parse(JSON.stringify(article)) : null;
}
