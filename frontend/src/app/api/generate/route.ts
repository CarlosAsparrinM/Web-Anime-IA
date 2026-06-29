import { NextRequest, NextResponse } from 'next/server';
import dbConnect from '@/lib/mongodb';
import Article from '@/models/Article';
import { generateArticle } from '@/lib/agent/generator';

export async function GET(request: NextRequest) {
  // Authentication check (Cron Job or Manual execution)
  const authHeader = request.headers.get('authorization');
  const secretQuery = request.nextUrl.searchParams.get('secret');
  const expectedSecret = process.env.CRON_SECRET;

  if (authHeader !== `Bearer ${expectedSecret}` && secretQuery !== expectedSecret) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    await dbConnect();

    // Prevent duplicates: Check if an article was already created today
    const startOfDay = new Date();
    startOfDay.setHours(0, 0, 0, 0);
    const force = request.nextUrl.searchParams.get('force') === 'true';

    if (!force) {
      const existingArticle = await Article.findOne({
        createdAt: { $gte: startOfDay },
      });

      if (existingArticle) {
        return NextResponse.json(
          { message: 'An article was already generated today. Use &force=true to override.', article: existingArticle },
          { status: 200 }
        );
      }
    }

    // Generate the new article
    const requestedCategory = request.nextUrl.searchParams.get('category');
    const generatedData = await generateArticle(requestedCategory as any);

    // Save to Database
    const newArticle = await Article.create(generatedData);

    return NextResponse.json(
      { message: 'Article generated and saved successfully.', article: newArticle },
      { status: 201 }
    );
  } catch (error: any) {
    console.error('Error in /api/generate:', error);
    return NextResponse.json({ error: error.message || 'Internal Server Error' }, { status: 500 });
  }
}
