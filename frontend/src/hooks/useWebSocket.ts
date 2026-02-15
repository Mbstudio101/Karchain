import { useEffect, useRef, useState, useCallback } from 'react';

export interface WebSocketMessage {
  type: 'data_update' | 'connection' | 'ping' | 'pong' | 'error';
  data_type?: 'games' | 'players' | 'player_props';
  data?: any;
  message?: string;
  timestamp?: number;
}

export interface UseWebSocketReturn {
  isConnected: boolean;
  lastMessage: WebSocketMessage | null;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  reconnect: () => void;
  sendMessage: (message: any) => void;
}

export const useWebSocket = (url: string = 'ws://127.0.0.1:8000/ws'): UseWebSocketReturn => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const connectDelayRef = useRef<NodeJS.Timeout | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const shouldReconnect = useRef<boolean>(true);
  const reconnectAttemptsRef = useRef<number>(0);
  const isConnectingRef = useRef<boolean>(false);

  const connect = useCallback(() => {
    // If we shouldn't reconnect (e.g. unmounted), stop
    if (!shouldReconnect.current) return;

    // Keep a single in-flight socket to avoid status flicker.
    if (
      isConnectingRef.current ||
      (wsRef.current &&
        (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING))
    ) {
      return;
    }

    isConnectingRef.current = true;
    setConnectionStatus('connecting');
    
    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        if (wsRef.current !== ws) return;
        // Double check if we are still mounted/valid
        if (!shouldReconnect.current) {
          ws.close();
          return;
        }

        isConnectingRef.current = false;
        setIsConnected(true);
        setConnectionStatus('connected');
        reconnectAttemptsRef.current = 0;
        console.log('🔄 WebSocket connected to backend');
        
        // Start ping interval to keep connection alive
        if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000); // Ping every 30 seconds
      };

      ws.onmessage = (event) => {
        if (wsRef.current !== ws) return;
        if (!shouldReconnect.current) return;
        try {
          const message: any = JSON.parse(event.data);
          setLastMessage(message);
          
          // Handle different message types
          switch (message.type) {
            case 'connection':
              console.log('🔄 WebSocket:', message.message);
              break;
            case 'data_update':
              console.log(`🔄 Real-time update: ${message.data_type} data updated`);
              // Trigger data refresh based on update type
              if (message.data_type === 'games') {
                window.dispatchEvent(new CustomEvent('gamesUpdated', { detail: message.data }));
              } else if (message.data_type === 'players') {
                window.dispatchEvent(new CustomEvent('playersUpdated', { detail: message.data }));
              } else if (message.data_type === 'player_props') {
                window.dispatchEvent(new CustomEvent('propsUpdated', { detail: message.data }));
              }
              break;
            case 'pong':
              // Keep-alive response
              break;
            case 'error':
              console.error('🔄 WebSocket error:', message.message);
              break;
          }
        } catch (error) {
          console.error('🔄 Error parsing WebSocket message:', error);
        }
      };

      ws.onclose = () => {
        if (wsRef.current !== ws) return;
        if (!shouldReconnect.current) return;

        isConnectingRef.current = false;
        wsRef.current = null;
        setIsConnected(false);
        setConnectionStatus('disconnected');
        console.log('🔄 WebSocket disconnected');
        
        // Clear intervals
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
          pingIntervalRef.current = null;
        }
        
        // Auto-reconnect with backoff
        reconnectAttemptsRef.current += 1;
        const delayMs = Math.min(30000, 1000 * Math.pow(2, reconnectAttemptsRef.current));
        if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = setTimeout(() => {
          if (shouldReconnect.current) {
            console.log(`🔄 Attempting to reconnect (attempt ${reconnectAttemptsRef.current})...`);
            connect();
          }
        }, delayMs);
      };

      ws.onerror = () => {
        if (wsRef.current !== ws) return;
        if (!shouldReconnect.current) return;
        setConnectionStatus('connecting');
        // Expected during backend startup/restarts. onclose handles reconnect.
        console.warn('🔄 WebSocket connection issue, retrying...');
      };

    } catch (error) {
      isConnectingRef.current = false;
      if (shouldReconnect.current) {
        setConnectionStatus('connecting');
        console.warn('🔄 Failed to connect WebSocket, retrying...');
        // Try to reconnect even on initial failure
        reconnectAttemptsRef.current += 1;
        const delayMs = Math.min(30000, 1000 * Math.pow(2, reconnectAttemptsRef.current));
        if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = setTimeout(connect, delayMs);
      }
    }
  }, [url]);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('🔄 WebSocket not connected, cannot send message');
    }
  }, []);

  const manualReconnect = useCallback(() => {
    shouldReconnect.current = true;
    reconnectAttemptsRef.current = 0;
    isConnectingRef.current = false;
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
    connect();
  }, [connect]);

  useEffect(() => {
    shouldReconnect.current = true;
    // Small defer prevents StrictMode double-mount from opening then instantly
    // tearing down a socket, which causes noisy "closed before established" logs.
    connectDelayRef.current = setTimeout(() => {
      if (shouldReconnect.current) connect();
    }, 150);

    return () => {
      shouldReconnect.current = false;
      isConnectingRef.current = false;
      if (connectDelayRef.current) {
        clearTimeout(connectDelayRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
      }
    };
  }, [connect]);

  return {
    isConnected,
    lastMessage,
    connectionStatus,
    reconnect: manualReconnect,
    sendMessage,
  };
};
