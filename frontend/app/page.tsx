/**
 * AetherScan - Main Application Page
 * 3D Reconstruction with Real-time Point Cloud Streaming
 */

'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { DropZone } from '@/components/DropZone';
import { PointCloudCanvas } from '@/components/PointCloudCanvas';
import { useWebSocket, type PointData } from '@/hooks/useWebSocket';
import { Download, Activity, Wifi, WifiOff } from 'lucide-react';

export default function Home() {
  const [points, setPoints] = useState<PointData[]>([]);
  const [pointCount, setPointCount] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadedFileCount, setUploadedFileCount] = useState(0);
  const allPointsRef = useRef<PointData[]>([]);

  // WebSocket connection
  const wsUrl = process.env.NEXT_PUBLIC_BACKEND_WS || 'ws://localhost:8000';
  const { isConnected, connectionStatus, send } = useWebSocket({
    url: `${wsUrl}/ws/reconstruct`,
    onMessage: (message) => {
      console.log('Received message:', message.type);

      if (message.type === 'points' && message.data) {
        // Add new points
        const newPoints = message.data as PointData[];
        allPointsRef.current = [...allPointsRef.current, ...newPoints];
        setPoints([...newPoints]); // Trigger render with new batch
      } else if (message.type === 'reconstruction_complete') {
        console.log('Reconstruction complete!', message.total_points);
        setIsProcessing(false);
      } else if (message.type === 'pong') {
        console.log('Pong received');
      }
    },
    onOpen: () => {
      console.log('Connected to backend');
    },
    onClose: () => {
      console.log('Disconnected from backend');
    },
  });

  // Send ping every 30 seconds to keep connection alive
  useEffect(() => {
    if (!isConnected) return;

    const interval = setInterval(() => {
      send({ type: 'ping' });
    }, 30000);

    return () => clearInterval(interval);
  }, [isConnected, send]);

  const handleFilesSelected = useCallback(
    async (files: File[]) => {
      if (!isConnected) {
        alert('Not connected to backend. Please wait...');
        return;
      }

      setIsProcessing(true);
      setUploadedFileCount(files.length);

      // Reset points
      allPointsRef.current = [];
      setPoints([]);
      setPointCount(0);

      // For demo: Send files metadata to backend
      // In production, you'd convert files to base64 or use a different upload method
      for (const file of files) {
        const reader = new FileReader();
        reader.onload = () => {
          const base64 = reader.result as string;
          send({
            type: 'image_data',
            data: base64,
            filename: file.name,
          });
        };
        reader.readAsDataURL(file);
      }

      // Signal upload complete
      setTimeout(() => {
        send({
          type: 'upload_complete',
          count: files.length,
        });
      }, 1000);
    },
    [isConnected, send]
  );

  const handleExport = useCallback(async () => {
    if (allPointsRef.current.length === 0) {
      alert('No points to export');
      return;
    }

    // Create PLY file content
    const header = `ply
format ascii 1.0
comment AetherScan Point Cloud Export
element vertex ${allPointsRef.current.length}
property float x
property float y
property float z
property uchar red
property uchar green
property uchar blue
end_header
`;

    const vertices = allPointsRef.current
      .map((p) => `${p.x} ${p.y} ${p.z} ${Math.round(p.r)} ${Math.round(p.g)} ${Math.round(p.b)}`)
      .join('\n');

    const plyContent = header + vertices;

    // Download file
    const blob = new Blob([plyContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `aetherscan_${Date.now()}.ply`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-black text-white">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Activity className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                  AetherScan
                </h1>
                <p className="text-xs text-gray-400">3D Reconstruction</p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              {/* Connection Status */}
              <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-800 rounded-lg">
                {isConnected ? (
                  <>
                    <Wifi className="w-4 h-4 text-green-400" />
                    <span className="text-sm text-green-400">Connected</span>
                  </>
                ) : (
                  <>
                    <WifiOff className="w-4 h-4 text-red-400" />
                    <span className="text-sm text-red-400">Disconnected</span>
                  </>
                )}
              </div>

              {/* Export Button */}
              <button
                onClick={handleExport}
                disabled={pointCount === 0}
                className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                <Download className="w-4 h-4" />
                Export PLY
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[calc(100vh-140px)]">
          {/* Left Panel - Upload */}
          <div className="flex flex-col gap-6">
            <div className="bg-gray-900/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-800">
              <h2 className="text-lg font-semibold mb-4">Upload Images</h2>
              <DropZone onFilesSelected={handleFilesSelected} isProcessing={isProcessing} />
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gradient-to-br from-blue-900/50 to-blue-800/30 backdrop-blur-sm rounded-xl p-4 border border-blue-700/30">
                <p className="text-sm text-blue-300 mb-1">Total Points</p>
                <p className="text-3xl font-bold">{pointCount.toLocaleString()}</p>
              </div>
              <div className="bg-gradient-to-br from-purple-900/50 to-purple-800/30 backdrop-blur-sm rounded-xl p-4 border border-purple-700/30">
                <p className="text-sm text-purple-300 mb-1">Images</p>
                <p className="text-3xl font-bold">{uploadedFileCount}</p>
              </div>
            </div>

            {/* Instructions */}
            <div className="bg-gray-900/50 backdrop-blur-sm rounded-xl p-4 border border-gray-800">
              <h3 className="text-sm font-semibold mb-2 text-gray-300">Quick Start</h3>
              <ol className="text-sm text-gray-400 space-y-1 list-decimal list-inside">
                <li>Upload multiple images of your object</li>
                <li>Watch the 3D reconstruction in real-time</li>
                <li>Export the point cloud as a PLY file</li>
              </ol>
            </div>
          </div>

          {/* Right Panel - 3D Viewer */}
          <div className="bg-gray-900/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-800">
            <h2 className="text-lg font-semibold mb-4">3D Point Cloud</h2>
            <div className="h-[calc(100%-3rem)]">
              <PointCloudCanvas points={points} onPointCountChange={setPointCount} />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

