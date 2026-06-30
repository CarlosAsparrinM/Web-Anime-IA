import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  // Authentication check (Cron Job or Manual execution)
  const authHeader = request.headers.get('authorization');
  const secretQuery = request.nextUrl.searchParams.get('secret');
  const expectedSecret = process.env.CRON_SECRET;

  if (authHeader !== `Bearer ${expectedSecret}` && secretQuery !== expectedSecret) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    // Proxy the request to the Python FastAPI backend
    const pythonBackendUrl = 'http://127.0.0.1:8000/api/generate';
    
    // Pass along query parameters
    const params = new URLSearchParams();
    if (secretQuery) params.append('secret', secretQuery);
    const category = request.nextUrl.searchParams.get('category');
    if (category) params.append('category', category);
    const force = request.nextUrl.searchParams.get('force');
    if (force) params.append('force', force);

    const response = await fetch(`${pythonBackendUrl}?${params.toString()}`);
    
    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data, { status: response.status });
  } catch (error: any) {
    console.error('Error in /api/generate proxy:', error);
    return NextResponse.json({ error: 'Failed to communicate with Python backend' }, { status: 500 });
  }
}
