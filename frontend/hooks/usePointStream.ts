/**
 * Point Stream Hook
 * Manages GPU-resident point cloud buffer for efficient rendering
 * Key feature: Updates buffer directly without triggering React re-renders
 */

import { useRef, useCallback, useMemo } from 'react';
import * as THREE from 'three';
import type { PointData } from './useWebSocket';

interface UsePointStreamOptions {
    maxPoints?: number;
}

export function usePointStream({ maxPoints = 1000000 }: UsePointStreamOptions = {}) {
    // Store points in refs to avoid React re-renders on every update
    const positionsRef = useRef<Float32Array>(new Float32Array(maxPoints * 3));
    const colorsRef = useRef<Float32Array>(new Float32Array(maxPoints * 3));
    const currentCountRef = useRef(0);

    // BufferGeometry and attributes (created once, updated in place)
    const geometryRef = useRef<THREE.BufferGeometry | null>(null);
    const positionAttributeRef = useRef<THREE.BufferAttribute | null>(null);
    const colorAttributeRef = useRef<THREE.BufferAttribute | null>(null);

    // Initialize geometry and attributes
    const initGeometry = useCallback(() => {
        if (!geometryRef.current) {
            const geometry = new THREE.BufferGeometry();

            // Create position attribute
            const positionAttribute = new THREE.BufferAttribute(positionsRef.current, 3);
            positionAttribute.setUsage(THREE.DynamicDrawUsage);
            geometry.setAttribute('position', positionAttribute);
            positionAttributeRef.current = positionAttribute;

            // Create color attribute
            const colorAttribute = new THREE.BufferAttribute(colorsRef.current, 3);
            colorAttribute.setUsage(THREE.DynamicDrawUsage);
            geometry.setAttribute('color', colorAttribute);
            colorAttributeRef.current = colorAttribute;

            // Set initial draw range to 0 (nothing visible until points are added)
            geometry.setDrawRange(0, 0);

            geometryRef.current = geometry;
        }

        return geometryRef.current;
    }, []);

    // Add points to the buffer
    const addPoints = useCallback((points: PointData[]) => {
        if (!geometryRef.current || !positionAttributeRef.current || !colorAttributeRef.current) {
            console.warn('Geometry not initialized');
            return;
        }

        const positions = positionsRef.current;
        const colors = colorsRef.current;
        let currentCount = currentCountRef.current;

        for (const point of points) {
            if (currentCount >= maxPoints) {
                console.warn(`Max points (${maxPoints}) reached, ignoring additional points`);
                break;
            }

            const idx = currentCount * 3;

            // Set position
            positions[idx] = point.x;
            positions[idx + 1] = point.y;
            positions[idx + 2] = point.z;

            // Set color (convert 0-255 to 0-1 range)
            colors[idx] = point.r / 255;
            colors[idx + 1] = point.g / 255;
            colors[idx + 2] = point.b / 255;

            currentCount++;
        }

        // Update the current count
        currentCountRef.current = currentCount;

        // Mark attributes as needing update
        positionAttributeRef.current.needsUpdate = true;
        colorAttributeRef.current.needsUpdate = true;

        // Update draw range to show new points
        geometryRef.current.setDrawRange(0, currentCount);

        // Update bounding sphere for proper frustum culling
        geometryRef.current.computeBoundingSphere();
    }, [maxPoints]);

    // Clear all points
    const clearPoints = useCallback(() => {
        if (geometryRef.current) {
            currentCountRef.current = 0;
            geometryRef.current.setDrawRange(0, 0);
        }
    }, []);

    // Get current point count
    const getPointCount = useCallback(() => {
        return currentCountRef.current;
    }, []);

    // Material for points (memoized)
    const material = useMemo(() => {
        return new THREE.PointsMaterial({
            size: 0.01,
            vertexColors: true,
            sizeAttenuation: true,
            transparent: false,
        });
    }, []);

    return {
        initGeometry,
        addPoints,
        clearPoints,
        getPointCount,
        geometry: geometryRef.current,
        material,
    };
}
