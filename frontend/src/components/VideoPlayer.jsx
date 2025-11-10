import React, { useState, useEffect, useRef } from 'react';
import api from '../services/api';

const VideoPlayer = () => {
  const [frame, setFrame] = useState(null);
  const canvasRef = useRef(null);
  const [cachedDetections, setCachedDetections] = useState([]); // Phase 4: Cache detections

  useEffect(() => {
    const handleFrame = (data) => {
      console.log('🎥 Received frame message:', {
        hasFrame: !!data.frame,
        frameLength: data.frame ? data.frame.length : 0,
        detectionsCount: data.detections ? data.detections.length : 0
      });

      if (data.frame) {
        // Phase 4: Cache detections only when they are sent (non-empty)
        let detections = data.detections || [];
        if (detections.length > 0) {
          setCachedDetections(detections);
        } else {
          // Use cached detections if none sent
          detections = cachedDetections;
        }

        setFrame({
          imageData: data.frame,
          detections: detections
        });
      }
    };

    api.on('frame', handleFrame);

    return () => {
      api.off('frame', handleFrame);
    };
  }, [cachedDetections]);

  useEffect(() => {
    if (frame && canvasRef.current) {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      const img = new Image();
      
      img.onload = () => {
        // Set canvas size to match image
        canvas.width = img.width;
        canvas.height = img.height;

        // Clear canvas and draw image
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0);

        console.log(`✅ Image loaded successfully: ${img.width}x${img.height}`);
      };

      img.onerror = (error) => {
        console.error('Failed to load image:', error);
        // Draw error message on canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#f3f4f6';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#ef4444';
        ctx.font = '16px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('Failed to load video frame', canvas.width / 2, canvas.height / 2);
      };

      console.log(`Loading image data: ${frame.imageData.substring(0, 50)}...`);
      img.src = `data:image/jpeg;base64,${frame.imageData}`;
    }
  }, [frame]);

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden border border-gray-200">
      <div className="bg-gradient-to-r from-blue-500 to-blue-600 px-4 py-3">
        <h2 className="text-lg font-semibold text-white">Live Video Feed</h2>
      </div>
      
      <div className="relative bg-black aspect-video">
        {frame ? (
          <canvas
            ref={canvasRef}
            className="w-full h-full object-contain"
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <p className="text-gray-300">Connecting to video stream...</p>
            </div>
          </div>
        )}
      </div>
      
      {/* Detection Stats */}
      {frame && frame.detections && frame.detections.length > 0 && (
        <div className="px-4 py-3 bg-gray-50 border-t border-gray-200">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-4">
              <span className="text-gray-600">
                Detected: <span className="text-gray-900 font-semibold">{frame.detections.length}</span> face(s)
              </span>
              <span className="text-gray-600">
                Known: <span className="text-green-600 font-semibold">
                  {frame.detections.filter(d => d.is_known).length}
                </span>
              </span>
              <span className="text-gray-600">
                Unknown: <span className="text-red-600 font-semibold">
                  {frame.detections.filter(d => !d.is_known).length}
                </span>
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VideoPlayer;

