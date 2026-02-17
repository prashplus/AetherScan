/**
 * WebSocket Hook for AetherScan
 * Manages WebSocket connection to backend reconstruction service
 */

import { useEffect, useRef, useState, useCallback } from 'react';

export interface PointData {
    x: number;
    y: number;
    z: number;
    r: number;
    g: number;
    b: number;
}

export interface WebSocketMessage {
    type: string;
    data?: any;
    status?: string;
    total_points?: number;
}

interface UseWebSocketOptions {
    url: string;
    onMessage?: (message: WebSocketMessage) => void;
    onOpen?: () => void;
    onClose?: () => void;
    onError?: (error: Event) => void;
    autoReconnect?: boolean;
    reconnectInterval?: number;
}

export function useWebSocket({
    url,
    onMessage,
    onOpen,
    onClose,
    onError,
    autoReconnect = true,
    reconnectInterval = 3000,
}: UseWebSocketOptions) {
    const [isConnected, setIsConnected] = useState(false);
    const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
    const shouldReconnectRef = useRef(true);

    const connect = useCallback(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            console.log('WebSocket already connected, skipping...');
            return;
        }

        try {
            console.log(`[WebSocket] Attempting to connect to: ${url}`);
            setConnectionStatus('connecting');
            const ws = new WebSocket(url);

            ws.onopen = () => {
                console.log('[WebSocket] ✅ Connection established successfully');
                setIsConnected(true);
                setConnectionStatus('connected');
                onOpen?.();
            };

            ws.onmessage = (event) => {
                try {
                    const message: WebSocketMessage = JSON.parse(event.data);
                    onMessage?.(message);
                } catch (error) {
                    console.error('[WebSocket] Failed to parse message:', error);
                }
            };

            ws.onclose = (event) => {
                console.log(`[WebSocket] Connection closed. Code: ${event.code}, Reason: ${event.reason || 'No reason provided'}, Clean: ${event.wasClean}`);
                setIsConnected(false);
                setConnectionStatus('disconnected');
                onClose?.();

                // Auto-reconnect
                if (autoReconnect && shouldReconnectRef.current) {
                    console.log(`[WebSocket] Will attempt to reconnect in ${reconnectInterval}ms...`);
                    reconnectTimeoutRef.current = setTimeout(() => {
                        console.log('[WebSocket] Reconnecting...');
                        connect();
                    }, reconnectInterval);
                }
            };

            ws.onerror = (error) => {
                console.error('[WebSocket] ❌ Error occurred:', {
                    readyState: ws.readyState,
                    readyStateText: ['CONNECTING', 'OPEN', 'CLOSING', 'CLOSED'][ws.readyState],
                    url: url,
                    error: error
                });
                setConnectionStatus('error');
                onError?.(error);
            };

            wsRef.current = ws;
        } catch (error) {
            console.error('[WebSocket] ❌ Failed to create WebSocket:', error);
            setConnectionStatus('error');
        }
    }, [url, onMessage, onOpen, onClose, onError, autoReconnect, reconnectInterval]);

    const disconnect = useCallback(() => {
        shouldReconnectRef.current = false;
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
        }
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
    }, []);

    const send = useCallback((data: any) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(data));
        } else {
            console.warn('WebSocket is not connected');
        }
    }, []);

    useEffect(() => {
        shouldReconnectRef.current = true;
        connect();

        return () => {
            disconnect();
        };
    }, [connect, disconnect]);

    return {
        isConnected,
        connectionStatus,
        send,
        disconnect,
        reconnect: connect,
    };
}
