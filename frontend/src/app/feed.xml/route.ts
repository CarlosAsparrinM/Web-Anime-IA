import dbConnect from '@/lib/mongodb';
import Article from '@/models/Article';

export async function GET() {
  await dbConnect();
  
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3001';
  const siteName = process.env.NEXT_PUBLIC_SITE_NAME || 'KenkoAnime';
  
  const articles = await Article.find({ published: true })
    .sort({ createdAt: -1 })
    .limit(20)
    .lean();
    
  const generateRssItem = (article: any) => `
    <item>
      <guid>${siteUrl}/articulo/${article.slug}</guid>
      <title><![CDATA[${article.title.es}]]></title>
      <link>${siteUrl}/articulo/${article.slug}</link>
      <description><![CDATA[${article.excerpt.es}]]></description>
      <pubDate>${new Date(article.createdAt).toUTCString()}</pubDate>
      <category><![CDATA[${article.category}]]></category>
    </item>
  `;

  const rssFeed = `<?xml version="1.0" encoding="UTF-8" ?>
  <rss version="2.0">
    <channel>
      <title>${siteName}</title>
      <link>${siteUrl}</link>
      <description>El primer blog de anime generado por Inteligencia Artificial.</description>
      <language>es</language>
      ${articles.map(generateRssItem).join('')}
    </channel>
  </rss>`;

  return new Response(rssFeed, {
    headers: {
      'Content-Type': 'application/xml',
      'Cache-Control': 's-maxage=3600, stale-while-revalidate=86400',
    },
  });
}
