/**
 * Drag and Drop Upload Component
 * Streams uploaded files to backend via WebSocket
 */

'use client';

import { useCallback, useState } from 'react';
import { Upload, Image as ImageIcon } from 'lucide-react';

interface DropZoneProps {
    onFilesSelected: (files: File[]) => void;
    isProcessing?: boolean;
}

export function DropZone({ onFilesSelected, isProcessing = false }: DropZoneProps) {
    const [isDragging, setIsDragging] = useState(false);
    const [selectedFiles, setSelectedFiles] = useState<File[]>([]);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback(
        (e: React.DragEvent) => {
            e.preventDefault();
            e.stopPropagation();
            setIsDragging(false);

            const files = Array.from(e.dataTransfer.files).filter((file) =>
                file.type.startsWith('image/')
            );

            if (files.length > 0) {
                setSelectedFiles(files);
                onFilesSelected(files);
            }
        },
        [onFilesSelected]
    );

    const handleFileInput = useCallback(
        (e: React.ChangeEvent<HTMLInputElement>) => {
            const files = Array.from(e.target.files || []).filter((file) =>
                file.type.startsWith('image/')
            );

            if (files.length > 0) {
                setSelectedFiles(files);
                onFilesSelected(files);
            }
        },
        [onFilesSelected]
    );

    return (
        <div className="w-full">
            <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`
          relative border-2 border-dashed rounded-2xl p-12 text-center
          transition-all duration-300 cursor-pointer
          ${isDragging
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-950/20 scale-105'
                        : 'border-gray-300 dark:border-gray-700 hover:border-blue-400 dark:hover:border-blue-600'
                    }
          ${isProcessing ? 'opacity-50 pointer-events-none' : ''}
        `}
            >
                <input
                    type="file"
                    multiple
                    accept="image/*"
                    onChange={handleFileInput}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    disabled={isProcessing}
                />

                <div className="flex flex-col items-center gap-4">
                    <div className="p-4 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full">
                        <Upload className="w-10 h-10 text-white" />
                    </div>

                    <div className="space-y-2">
                        <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                            {isDragging ? 'Drop images here' : 'Drag & drop images'}
                        </h3>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                            or click to browse your files
                        </p>
                    </div>

                    {selectedFiles.length > 0 && (
                        <div className="flex items-center gap-2 px-4 py-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                            <ImageIcon className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                            <span className="text-sm font-medium text-blue-900 dark:text-blue-100">
                                {selectedFiles.length} image{selectedFiles.length > 1 ? 's' : ''} selected
                            </span>
                        </div>
                    )}

                    {isProcessing && (
                        <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400">
                            <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                            <span className="text-sm font-medium">Processing...</span>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
