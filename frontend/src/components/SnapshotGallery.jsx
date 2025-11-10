import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { FaImages, FaSearch, FaDownload } from 'react-icons/fa';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const SnapshotGallery = () => {
  const [snapshots, setSnapshots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSnapshot, setSelectedSnapshot] = useState(null);

  useEffect(() => {
    loadSnapshots();
  }, []);

  const loadSnapshots = async () => {
    try {
      setLoading(true);
      const data = await api.getSnapshots();
      setSnapshots(data.snapshots || []);
    } catch (error) {
      console.error('Failed to load snapshots:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatTimestamp = (isoString) => {
    try {
      if (!isoString) return 'N/A';
      const date = new Date(isoString);
      if (isNaN(date.getTime())) return 'Invalid Date';
      return date.toLocaleString();
    } catch (error) {
      return 'N/A';
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const filteredSnapshots = snapshots.filter(snapshot =>
    snapshot.filename.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header with Search */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden border border-gray-200">
        <div className="bg-gradient-to-r from-purple-500 to-purple-600 px-6 py-4">
          <h2 className="text-2xl font-bold text-white flex items-center">
            <FaImages className="mr-3" />
            Unknown Person Snapshots
          </h2>
        </div>
        
        <div className="p-6">
          <div className="relative">
            <FaSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search snapshots..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-3 bg-white border border-gray-300 rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:border-purple-500"
            />
          </div>
        </div>
      </div>

      {/* Gallery */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden border border-gray-200">
        <div className="p-6">
          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-500 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading snapshots...</p>
            </div>
          ) : filteredSnapshots.length === 0 ? (
            <div className="text-center py-12">
              <FaImages className="text-6xl text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 text-lg">
                {searchTerm ? 'No snapshots match your search' : 'No snapshots yet'}
              </p>
              <p className="text-gray-500 text-sm mt-2">
                Snapshots of unknown persons will appear here
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {filteredSnapshots.map((snapshot, index) => (
                <div
                  key={index}
                  className="bg-white rounded-lg overflow-hidden border border-gray-200 hover:ring-2 hover:ring-purple-500 transition-all cursor-pointer shadow-sm"
                  onClick={() => setSelectedSnapshot(snapshot)}
                >
                  <img
                    src={`${API_BASE_URL}${snapshot.url}`}
                    alt={snapshot.filename}
                    className="w-full h-48 object-cover"
                    onError={(e) => {
                      e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="200"%3E%3Crect fill="%23ddd" width="200" height="200"/%3E%3Ctext fill="%23999" font-family="sans-serif" font-size="14" x="50%25" y="50%25" text-anchor="middle" dy=".3em"%3EImage not found%3C/text%3E%3C/svg%3E';
                    }}
                  />
                  <div className="p-3">
                    <p className="text-sm font-semibold text-gray-900 truncate">{snapshot.filename}</p>
                    <p className="text-xs text-gray-600 mt-1">{formatTimestamp(snapshot.timestamp)}</p>
                    <p className="text-xs text-gray-500 mt-1">{formatFileSize(snapshot.size)}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Modal for enlarged view */}
      {selectedSnapshot && (
        <div
          className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4"
          onClick={() => setSelectedSnapshot(null)}
        >
          <div
            className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-4 border-b border-gray-200 flex items-center justify-between">
              <h3 className="text-xl font-bold text-gray-900">{selectedSnapshot.filename}</h3>
              <button
                onClick={() => setSelectedSnapshot(null)}
                className="text-gray-600 hover:text-gray-900"
              >
                ✕
              </button>
            </div>
            <div className="p-4">
              <img
                src={`${API_BASE_URL}${selectedSnapshot.url}`}
                alt={selectedSnapshot.filename}
                className="w-full h-auto rounded"
                onError={(e) => {
                  e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="200"%3E%3Crect fill="%23ddd" width="200" height="200"/%3E%3Ctext fill="%23999" font-family="sans-serif" font-size="14" x="50%25" y="50%25" text-anchor="middle" dy=".3em"%3EImage not found%3C/text%3E%3C/svg%3E';
                }}
              />
              <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-600">Timestamp:</p>
                  <p className="text-gray-900">{formatTimestamp(selectedSnapshot.timestamp)}</p>
                </div>
                <div>
                  <p className="text-gray-600">File Size:</p>
                  <p className="text-gray-900">{formatFileSize(selectedSnapshot.size)}</p>
                </div>
              </div>
              <a
                href={`${API_BASE_URL}${selectedSnapshot.url}`}
                download={selectedSnapshot.filename}
                className="mt-4 w-full bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg flex items-center justify-center space-x-2 transition-colors"
              >
                <FaDownload />
                <span>Download</span>
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SnapshotGallery;

