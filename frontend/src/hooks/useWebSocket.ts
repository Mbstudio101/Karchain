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

export const useWebSocket = (url: string = 'ws://localhost:8000/ws'): UseWebSocketReturn => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const shouldReconnect = useRef<boolean>(true);

  const connect = useCallback(() => {
    // If we shouldn't reconnect (e.g. unmounted), stop
    if (!shouldReconnect.current) return;

    // Close existing connection if any
    if (wsRef.current) {
      wsRef.current.close();
    }

    setConnectionStatus('connecting');
    
    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        // Double check if we are still mounted/valid
        if (!shouldReconnect.current) {
          ws.close();
          return;
        }

        setIsConnected(true);
        setConnectionStatus('connected');
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
        if (!shouldReconnect.current) return;

        setIsConnected(false);
        setConnectionStatus('disconnected');
        console.log('🔄 WebSocket disconnected');
        
        // Clear intervals
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
          pingIntervalRef.current = null;
        }
        
        // Auto-reconnect after 5 seconds
        if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = setTimeout(() => {
          if (shouldReconnect.current) {
            console.log('🔄 Attempting to reconnect...');
            connect();
          }
        }, 5000);
      };

      ws.onerror = (error) => {
        if (!shouldReconnect.current) return;
        setConnectionStatus('error');
        console.error('🔄 WebSocket error:', error);
      };

    } catch (error) {
      if (shouldReconnect.current) {
        setConnectionStatus('error');
        console.error('🔄 Failed to connect WebSocket:', error);
        // Try to reconnect even on initial failure
        if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = setTimeout(connect, 5000);
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
    if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
    connect();
  }, [connect]);

  useEffect(() => {
    shouldReconnect.current = true;
    connect();

    return () => {
      shouldReconnect.current = false;
      if (wsRef.current) {
        wsRef.current.close();
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
