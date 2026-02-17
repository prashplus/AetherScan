/**
 * Point Cloud Canvas Component
 * Uses React Three Fiber for WebGL/WebGPU rendering
 */

'use client';

import { useRef, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera } from '@react-three/drei';
import * as THREE from 'three';
import { usePointStream } from '@/hooks/usePointStream';
import type { PointData } from '@/hooks/useWebSocket';

interface PointCloudCanvasProps {
    points?: PointData[];
    onPointCountChange?: (count: number) => void;
}

function PointCloud({ points, onPointCountChange }: PointCloudCanvasProps) {
    const { initGeometry, addPoints, getPointCount, geometry, material } = usePointStream({
        maxPoints: 1000000,
    });

    const meshRef = useRef<THREE.Points>(null);

    // Initialize geometry on mount
    useEffect(() => {
        initGeometry();
    }, [initGeometry]);

    // Add points when they arrive
    useEffect(() => {
        if (points && points.length > 0) {
            addPoints(points);
            onPointCountChange?.(getPointCount());
        }
    }, [points, addPoints, getPointCount, onPointCountChange]);

    if (!geometry) return null;

    return (
        <points ref={meshRef} geometry={geometry} material={material}>
            {/* Material is passed as prop */}
        </points>
    );
}

export function PointCloudCanvas({ points, onPointCountChange }: PointCloudCanvasProps) {
    return (
        <div className="w-full h-full rounded-2xl overflow-hidden bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
            <Canvas
                gl={{
                    antialias: true,
                    alpha: true,
                    powerPreference: 'high-performance',
                }}
                dpr={[1, 2]}
            >
                {/* Camera */}
                <PerspectiveCamera makeDefault position={[3, 3, 3]} fov={50} />

                {/* Lights */}
                <ambientLight intensity={0.5} />
                <directionalLight position={[10, 10, 5]} intensity={1} />
                <directionalLight position={[-10, -10, -5]} intensity={0.3} />

                {/* Point Cloud */}
                <PointCloud points={points} onPointCountChange={onPointCountChange} />

                {/* Grid Helper */}
                <gridHelper args={[10, 10, '#444444', '#222222']} />

                {/* Axes Helper */}
                <axesHelper args={[2]} />

                {/* Controls */}
                <OrbitControls
                    enableDamping
                    dampingFactor={0.05}
                    minDistance={1}
                    maxDistance={20}
                    enablePan
                    enableZoom
                    enableRotate
                />
            </Canvas>
        </div>
    );
}
