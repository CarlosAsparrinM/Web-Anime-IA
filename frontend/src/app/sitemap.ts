import { MetadataRoute } from 'next';
import dbConnect from '@/lib/mongodb';
import Article from '@/models/Article';

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  await dbConnect();
  
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3001';
  
  // Get all published articles
  const articles = await Article.find({ published: true })
    .select('slug updatedAt')
    .sort({ createdAt: -1 })
    .lean();

  const articleUrls = articles.map((article: any) => ({
    url: `${siteUrl}/articulo/${article.slug}`,
    lastModified: article.updatedAt ? new Date(article.updatedAt) : new Date(),
    changeFrequency: 'weekly' as const,
    priority: 0.8,
  }));

  // Static routes
  const staticUrls = [
    {
      url: siteUrl,
      lastModified: new Date(),
      changeFrequency: 'daily' as const,
      priority: 1.0,
    },
  ];

  return [...staticUrls, ...articleUrls];
}
