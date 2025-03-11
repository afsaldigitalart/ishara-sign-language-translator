import { NextRequest } from 'next/server';

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  return new Response("This endpoint is for WebSocket connections only", { status: 400 });
}