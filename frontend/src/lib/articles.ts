import dbConnect from './mongodb';
import Article from '@/models/Article';

export async function getLatestArticles(limit = 10, category?: string, page = 1, search?: string) {
  await dbConnect();
  
  const query: any = { published: true };
  if (category && category !== 'all') {
    query.category = category;
  }
  
  if (search) {
    query.$or = [
      { 'title.es': { $regex: search, $options: 'i' } },
      { animeName: { $regex: search, $options: 'i' } }
    ];
  }
  
  const skip = (page - 1) * limit;
  
  const articles = await Article.find(query)
    .sort({ createdAt: -1 })
    .skip(skip)
    .limit(limit)
    .lean();
    
  const total = await Article.countDocuments(query);
    
  return {
    articles: JSON.parse(JSON.stringify(articles)),
    total,
    page,
    totalPages: Math.ceil(total / limit)
  };
}

export async function getArticleBySlug(slug: string) {
  await dbConnect();
  const article = await Article.findOne({ slug, published: true }).lean();
  return article ? JSON.parse(JSON.stringify(article)) : null;
}

export async function getRelatedArticles(slug: string, tags: string[], limit = 4) {
  await dbConnect();
  
  if (!tags || tags.length === 0) {
    // Fallback if no tags: get random recent articles
    const randomArticles = await Article.aggregate([
      { $match: { slug: { $ne: slug }, published: true } },
      { $sample: { size: limit } }
    ]);
    return JSON.parse(JSON.stringify(randomArticles));
  }
  
  // Find articles with matching tags, excluding the current article
  const related = await Article.find({
    slug: { $ne: slug },
    tags: { $in: tags },
    published: true
  })
    .sort({ createdAt: -1 })
    .limit(limit)
    .lean();
    
  // If not enough related articles, pad with recent ones
  if (related.length < limit) {
    const existingSlugs = related.map((a: any) => a.slug);
    existingSlugs.push(slug);
    
    const padArticles = await Article.find({
      slug: { $nin: existingSlugs },
      published: true
    })
      .sort({ createdAt: -1 })
      .limit(limit - related.length)
      .lean();
      
    related.push(...padArticles);
  }
  
  return JSON.parse(JSON.stringify(related));
}
