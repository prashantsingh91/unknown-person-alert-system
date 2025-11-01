import React, { useState, useEffect, useRef } from 'react';
import api from '../services/api';

const VideoPlayer = () => {
  const [frame, setFrame] = useState(null);
  const canvasRef = useRef(null);

  useEffect(() => {
    const handleFrame = (data) => {
      if (data.frame) {
        setFrame({
          imageData: data.frame,
          detections: data.detections || []
        });
      }
    };

    api.on('frame', handleFrame);

    return () => {
      api.off('frame', handleFrame);
    };
  }, []);

  useEffect(() => {
    if (frame && canvasRef.current) {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      const img = new Image();
      
      img.onload = () => {
        // Set canvas size to match image
        canvas.width = img.width;
        canvas.height = img.height;
        
        // Draw image
        ctx.drawImage(img, 0, 0);
        
        // Draw detections (bounding boxes are already drawn on server side)
        // This canvas is mainly for displaying the frame
      };
      
      img.src = `data:image/jpeg;base64,${frame.imageData}`;
    }
  }, [frame]);

  return (
    <div className="bg-slate-800 rounded-lg shadow-xl overflow-hidden">
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-4 py-3">
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
              <p className="text-gray-400">Connecting to video stream...</p>
            </div>
          </div>
        )}
      </div>
      
      {/* Detection Stats */}
      {frame && frame.detections && frame.detections.length > 0 && (
        <div className="px-4 py-3 bg-slate-750 border-t border-slate-700">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-4">
              <span className="text-gray-400">
                Detected: <span className="text-white font-semibold">{frame.detections.length}</span> face(s)
              </span>
              <span className="text-gray-400">
                Known: <span className="text-green-400 font-semibold">
                  {frame.detections.filter(d => d.is_known).length}
                </span>
              </span>
              <span className="text-gray-400">
                Unknown: <span className="text-red-400 font-semibold">
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

