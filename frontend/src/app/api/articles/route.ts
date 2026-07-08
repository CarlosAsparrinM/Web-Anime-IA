import { NextResponse } from 'next/server';
import { getLatestArticles } from '@/lib/articles';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const page = parseInt(searchParams.get('page') || '1', 10);
  const category = searchParams.get('category') || undefined;
  const search = searchParams.get('search') || undefined;
  const limit = parseInt(searchParams.get('limit') || '12', 10);

  try {
    const data = await getLatestArticles(limit, category, page, search);
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching articles API:", error);
    return NextResponse.json({ error: 'Failed to fetch articles' }, { status: 500 });
  }
}
