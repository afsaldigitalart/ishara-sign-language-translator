// app/api/ws/route.ts
import { NextRequest } from 'next/server';

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  const { socket: _socket, response } = await new Promise<any>((resolve) => {
    const upgrade = Reflect.get(request, 'socket')?.server?.upgrade;
    
    if (!upgrade) {
      return resolve({
        response: new Response('WebSocket upgrade not supported', { status: 426 })
      });
    }

    try {
      upgrade(request.raw, {
        protocol: 'websocket',
      }, (client: any) => {
        // Connect to Python backend websocket
        const backendWs = new WebSocket('ws://localhost:8000/ws');

        // Forward messages from frontend to backend
        client.addEventListener('message', (event: MessageEvent) => {
          if (backendWs.readyState === WebSocket.OPEN) {
            backendWs.send(event.data);
          }
        });

        // Forward messages from backend to frontend
        backendWs.addEventListener('message', (event: MessageEvent) => {
          client.send(event.data);
        });

        // Handle closures
        client.addEventListener('close', () => {
          backendWs.close();
        });

        backendWs.addEventListener('close', () => {
          client.close();
        });

        resolve({ socket: client, response: new Response(null) });
      });
    } catch (err) {
      console.error('WebSocket upgrade error:', err);
      resolve({
        response: new Response('WebSocket upgrade failed', { status: 500 })
      });
    }
  });

  return response;
}