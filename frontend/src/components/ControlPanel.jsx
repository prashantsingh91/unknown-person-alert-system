import React, { useState } from 'react';
import api from '../services/api';
import { FaPlay, FaPause, FaVideo, FaCamera, FaSync } from 'react-icons/fa';

const ControlPanel = () => {
  const [sourceType, setSourceType] = useState('file');
  const [videoPath, setVideoPath] = useState('');
  const [cameraId, setCameraId] = useState(0);
  const [loading, setLoading] = useState(false);
  const [isPaused, setIsPaused] = useState(false);

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

  const handlePlayPause = async () => {
    try {
      const result = await api.controlPlayback('toggle');
      setIsPaused(result.is_paused);
    } catch (error) {
      console.error('Failed to toggle playback:', error);
    }
  };

  return (
    <div className="bg-slate-800 rounded-lg shadow-xl overflow-hidden">
      <div className="bg-gradient-to-r from-indigo-600 to-indigo-700 px-4 py-3">
        <h2 className="text-lg font-semibold text-white">Control Panel</h2>
      </div>
      
      <div className="p-4 space-y-4">
        {/* Playback Controls */}
        <div className="flex items-center space-x-2">
          <button
            onClick={handlePlayPause}
            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-3 rounded-lg flex items-center justify-center space-x-2 transition-colors"
          >
            {isPaused ? <FaPlay /> : <FaPause />}
            <span>{isPaused ? 'Resume' : 'Pause'}</span>
          </button>
        </div>

        {/* Source Type Selection */}
        <div className="border-t border-slate-700 pt-4">
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Video Source
          </label>
          <div className="flex space-x-2 mb-3">
            <button
              onClick={() => setSourceType('file')}
              className={`flex-1 px-4 py-2 rounded-lg flex items-center justify-center space-x-2 transition-colors ${
                sourceType === 'file'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
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
                  : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
              }`}
            >
              <FaCamera />
              <span>Camera</span>
            </button>
          </div>

          {/* Video File Input */}
          {sourceType === 'file' && (
            <div className="mb-3">
              <label className="block text-xs text-gray-400 mb-1">Video File Path</label>
              <input
                type="text"
                value={videoPath}
                onChange={(e) => setVideoPath(e.target.value)}
                placeholder="Leave empty for default test video"
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white text-sm placeholder-gray-500 focus:outline-none focus:border-indigo-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                Default: extracted_2min_to_4min_trimmed.mp4
              </p>
            </div>
          )}

          {/* Camera Input */}
          {sourceType === 'camera' && (
            <div className="mb-3">
              <label className="block text-xs text-gray-400 mb-1">Camera ID</label>
              <input
                type="number"
                value={cameraId}
                onChange={(e) => setCameraId(parseInt(e.target.value))}
                min="0"
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white text-sm focus:outline-none focus:border-indigo-500"
              />
            </div>
          )}

          {/* Apply Button */}
          <button
            onClick={handleSourceChange}
            disabled={loading}
            className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg flex items-center justify-center space-x-2 transition-colors"
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

