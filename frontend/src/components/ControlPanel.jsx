import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { FaPlay, FaPause, FaStop, FaVideo, FaCamera, FaSync } from 'react-icons/fa';

const ControlPanel = ({ onPlayStart }) => {
  const [sourceType, setSourceType] = useState('file');
  const [videoPath, setVideoPath] = useState('');
  const [cameraId, setCameraId] = useState(0);
  const [loading, setLoading] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleSourceChange = async () => {
    try {
      setLoading(true);
      await api.setVideoSource(
        sourceType,
        sourceType === 'file' ? videoPath : null,
        sourceType === 'camera' ? cameraId : 0
      );
      alert('Video source changed successfully!');
    } catch (error) {
      alert('Failed to change video source: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePlay = async () => {
    try {
      // Clear UI state first
      if (onPlayStart) {
        onPlayStart();
      }
      // Then start playback
      const result = await api.controlPlayback('play');
      setIsPaused(false);
      setIsProcessing(result.is_processing || true);
    } catch (error) {
      console.error('Failed to start playback:', error);
    }
  };

  const handleStop = async () => {
    try {
      const result = await api.controlPlayback('stop');
      setIsPaused(true);
      setIsProcessing(false);
    } catch (error) {
      console.error('Failed to stop playback:', error);
    }
  };

  const handlePause = async () => {
    try {
      const result = await api.controlPlayback('pause');
      setIsPaused(result.is_paused);
    } catch (error) {
      console.error('Failed to pause playback:', error);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden border border-gray-200">
      <div className="bg-gradient-to-r from-indigo-500 to-indigo-600 px-4 py-3">
        <h2 className="text-lg font-semibold text-white">Control Panel</h2>
      </div>
      
      <div className="p-4 space-y-4">
        {/* Playback Controls */}
        <div className="flex items-center space-x-2">
          {!isProcessing ? (
            <button
              onClick={handlePlay}
              className="flex-1 bg-green-600 hover:bg-green-700 text-white px-4 py-3 rounded-lg flex items-center justify-center space-x-2 transition-colors"
            >
              <FaPlay />
              <span>Play</span>
            </button>
          ) : (
            <>
              <button
                onClick={handlePause}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-3 rounded-lg flex items-center justify-center space-x-2 transition-colors"
              >
                <FaPause />
                <span>Pause</span>
              </button>
              <button
                onClick={handleStop}
                className="flex-1 bg-red-600 hover:bg-red-700 text-white px-4 py-3 rounded-lg flex items-center justify-center space-x-2 transition-colors"
              >
                <FaStop />
                <span>Stop</span>
              </button>
            </>
          )}
        </div>

        {/* Source Type Selection */}
        <div className="border-t border-gray-200 pt-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Video Source
          </label>
          <div className="flex space-x-2 mb-3">
            <button
              onClick={() => setSourceType('file')}
              className={`flex-1 px-4 py-2 rounded-lg flex items-center justify-center space-x-2 transition-colors ${
                sourceType === 'file'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <FaVideo />
              <span>Video File</span>
            </button>
            <button
              onClick={() => setSourceType('camera')}
              className={`flex-1 px-4 py-2 rounded-lg flex items-center justify-center space-x-2 transition-colors ${
                sourceType === 'camera'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <FaCamera />
              <span>Camera</span>
            </button>
          </div>

          {/* Video File Input */}
          {sourceType === 'file' && (
            <div className="mb-3">
              <label className="block text-xs text-gray-600 mb-1">Video File Path</label>
              <input
                type="text"
                value={videoPath}
                onChange={(e) => setVideoPath(e.target.value)}
                placeholder="Leave empty for default test video"
                className="w-full px-3 py-2 bg-white border border-gray-300 rounded text-gray-900 text-sm placeholder-gray-400 focus:outline-none focus:border-indigo-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                Default: extracted_2min_to_4min_trimmed.mp4
              </p>
            </div>
          )}

          {/* Camera Input */}
          {sourceType === 'camera' && (
            <div className="mb-3">
              <label className="block text-xs text-gray-600 mb-1">Camera ID</label>
              <input
                type="number"
                value={cameraId}
                onChange={(e) => setCameraId(parseInt(e.target.value))}
                min="0"
                className="w-full px-3 py-2 bg-white border border-gray-300 rounded text-gray-900 text-sm focus:outline-none focus:border-indigo-500"
              />
            </div>
          )}

          {/* Apply Button */}
          <button
            onClick={handleSourceChange}
            disabled={loading}
            className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg flex items-center justify-center space-x-2 transition-colors"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Switching...</span>
              </>
            ) : (
              <>
                <FaSync />
                <span>Switch Source</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ControlPanel;

