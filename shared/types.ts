export interface PointData {
    x: number;
    y: number;
    z: number;
    r: number;
    g: number;
    b: number;
}

export interface WebSocketMessage {
    type: 'ping' | 'pong' | 'points' | 'image_data' | 'upload_complete' | 'image_received' | 'reconstruction_complete';
    data?: PointData[] | string | any;
    status?: string;
    total_points?: number;
    count?: number;
    filename?: string;
}
