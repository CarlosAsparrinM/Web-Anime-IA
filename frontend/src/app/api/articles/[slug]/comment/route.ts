import { NextResponse } from 'next/server';
import dbConnect from '@/lib/mongodb';
import Article from '@/models/Article';

// Simple in-memory rate limiter
const rateLimit = new Map<string, number>();
const RATE_LIMIT_WINDOW = 60 * 1000; // 60 seconds

export async function POST(
  request: Request,
  { params }: { params: Promise<{ slug: string }> }
) {
  try {
    const ip = request.headers.get('x-forwarded-for') || 'unknown';
    
    // Check rate limit
    const now = Date.now();
    const lastRequest = rateLimit.get(ip);
    
    if (lastRequest && now - lastRequest < RATE_LIMIT_WINDOW) {
      return NextResponse.json(
        { error: 'Too many requests. Please wait before commenting again.' }, 
        { status: 429 }
      );
    }
    
    // Update rate limit for this IP
    rateLimit.set(ip, now);
    
    // Optional cleanup of old rate limits (could be improved, but sufficient for simple anti-spam)
    if (rateLimit.size > 1000) {
      rateLimit.clear();
    }
    const resolvedParams = await params;
    const slug = resolvedParams.slug;
    
    const body = await request.json();
    const { text } = body;

    if (!text || text.trim().length === 0) {
      return NextResponse.json({ error: 'Comment text is required' }, { status: 400 });
    }

    await dbConnect();

    const newComment = {
      text: text.trim(),
      date: new Date()
    };

    // Push the new comment to the comments array
    const result = await Article.findOneAndUpdate(
      { slug: slug },
      { $push: { comments: newComment } },
      { returnDocument: 'after' }
    );

    if (!result) {
      return NextResponse.json({ error: 'Article not found' }, { status: 404 });
    }

    return NextResponse.json({ success: true, comment: newComment });
  } catch (error) {
    console.error('Error adding comment:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
