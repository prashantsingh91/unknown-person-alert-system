import React from 'react';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { FaChartLine, FaMicrochip, FaTachometerAlt, FaCog, FaVideo } from 'react-icons/fa';

const MetricsDashboard = ({ metrics, compact = false }) => {
  if (!metrics) {
    return (
      <div className="bg-slate-800 rounded-lg shadow-xl p-6">
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading metrics...</p>
        </div>
      </div>
    );
  }

  const { video, model, unknown_tracker } = metrics;

  if (compact) {
    return (
      <div className="bg-slate-800 rounded-lg shadow-xl overflow-hidden">
        <div className="bg-gradient-to-r from-green-600 to-green-700 px-4 py-3">
          <h2 className="text-lg font-semibold text-white flex items-center">
            <FaChartLine className="mr-2" />
            System Metrics
          </h2>
        </div>
        
        <div className="p-4 space-y-4">
          {/* FPS */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">Processing FPS</span>
            <span className="text-lg font-bold text-green-400">{video?.processing_fps || 0}</span>
          </div>
          
          {/* GPU */}
          {video?.gpu_available && (
            <>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-400">GPU Utilization</span>
                <span className="text-lg font-bold text-blue-400">{video.utilization}%</span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all"
                  style={{ width: `${video.utilization}%` }}
                />
              </div>
            </>
          )}
          
          {/* Model Info */}
          <div className="pt-2 border-t border-slate-700">
            <p className="text-xs text-gray-400">Model: {model?.model_name || 'N/A'}</p>
            <p className="text-xs text-gray-400">Known Persons: {model?.known_persons || 0}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Performance Metrics */}
      <div className="bg-slate-800 rounded-lg shadow-xl overflow-hidden">
        <div className="bg-gradient-to-r from-green-600 to-green-700 px-6 py-4">
          <h2 className="text-2xl font-bold text-white flex items-center">
            <FaTachometerAlt className="mr-3" />
            Performance Metrics
          </h2>
        </div>
        
        <div className="p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-slate-700 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400">Processing FPS</span>
              <FaVideo className="text-blue-500" />
            </div>
            <p className="text-3xl font-bold text-white">{video?.processing_fps || 0}</p>
            <p className="text-sm text-gray-500 mt-1">Frames per second</p>
          </div>
          
          <div className="bg-slate-700 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400">Video FPS</span>
              <FaVideo className="text-green-500" />
            </div>
            <p className="text-3xl font-bold text-white">{video?.video_fps || 0}</p>
            <p className="text-sm text-gray-500 mt-1">Source framerate</p>
          </div>
          
          <div className="bg-slate-700 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400">Processed</span>
              <FaCog className="text-purple-500" />
            </div>
            <p className="text-3xl font-bold text-white">{video?.processed_count || 0}</p>
            <p className="text-sm text-gray-500 mt-1">Total frames</p>
          </div>
          
          <div className="bg-slate-700 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400">Unknowns</span>
              <FaCog className="text-red-500" />
            </div>
            <p className="text-3xl font-bold text-white">{unknown_tracker?.total_snapshots || 0}</p>
            <p className="text-sm text-gray-500 mt-1">Detected</p>
          </div>
        </div>
      </div>

      {/* GPU Metrics */}
      {video?.gpu_available && (
        <div className="bg-slate-800 rounded-lg shadow-xl overflow-hidden">
          <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4">
            <h2 className="text-2xl font-bold text-white flex items-center">
              <FaMicrochip className="mr-3" />
              GPU Metrics
            </h2>
          </div>
          
          <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-slate-700 rounded-lg p-4">
              <p className="text-gray-400 mb-2">GPU Utilization</p>
              <p className="text-4xl font-bold text-blue-400">{video.utilization}%</p>
              <div className="w-full bg-slate-600 rounded-full h-3 mt-3">
                <div
                  className="bg-blue-500 h-3 rounded-full transition-all"
                  style={{ width: `${video.utilization}%` }}
                />
              </div>
            </div>
            
            <div className="bg-slate-700 rounded-lg p-4">
              <p className="text-gray-400 mb-2">Memory Usage</p>
              <p className="text-4xl font-bold text-green-400">{video.memory_percent?.toFixed(1)}%</p>
              <p className="text-sm text-gray-500 mt-2">
                {video.memory_used} MB / {video.memory_total} MB
              </p>
              <div className="w-full bg-slate-600 rounded-full h-3 mt-2">
                <div
                  className="bg-green-500 h-3 rounded-full transition-all"
                  style={{ width: `${video.memory_percent}%` }}
                />
              </div>
            </div>
            
            <div className="bg-slate-700 rounded-lg p-4">
              <p className="text-gray-400 mb-2">Temperature</p>
              <p className="text-4xl font-bold text-orange-400">{video.temperature}°C</p>
              <p className="text-sm text-gray-500 mt-2">GPU Core Temp</p>
            </div>
          </div>
        </div>
      )}

      {/* Model Information */}
      <div className="bg-slate-800 rounded-lg shadow-xl overflow-hidden">
        <div className="bg-gradient-to-r from-purple-600 to-purple-700 px-6 py-4">
          <h2 className="text-2xl font-bold text-white flex items-center">
            <FaCog className="mr-3" />
            Model Information
          </h2>
        </div>
        
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Detection & Recognition</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-400">Model Name:</span>
                  <span className="text-white font-medium">{model?.model_name || 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Detector:</span>
                  <span className="text-white font-medium">{model?.detector || 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Recognizer:</span>
                  <span className="text-white font-medium">{model?.recognizer || 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Embedding Dim:</span>
                  <span className="text-white font-medium">{model?.embedding_dim || 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Similarity Threshold:</span>
                  <span className="text-white font-medium">{model?.similarity_threshold || 'N/A'}</span>
                </div>
              </div>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Database & Video</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-400">Known Persons:</span>
                  <span className="text-white font-medium">{model?.known_persons || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Video Source:</span>
                  <span className="text-white font-medium">{video?.source_type || 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Resolution:</span>
                  <span className="text-white font-medium">{video?.resolution || 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Status:</span>
                  <span className={`font-medium ${video?.is_playing ? 'text-green-400' : 'text-red-400'}`}>
                    {video?.is_playing ? 'Playing' : 'Stopped'}
                  </span>
                </div>
                {video?.progress > 0 && (
                  <div className="flex justify-between">
                    <span className="text-gray-400">Progress:</span>
                    <span className="text-white font-medium">{video.progress.toFixed(1)}%</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MetricsDashboard;

