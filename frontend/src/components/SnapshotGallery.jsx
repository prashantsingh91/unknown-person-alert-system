import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { FaImages, FaSearch, FaDownload } from 'react-icons/fa';

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
    const date = new Date(isoString);
    return date.toLocaleString();
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
      <div className="bg-slate-800 rounded-lg shadow-xl overflow-hidden">
        <div className="bg-gradient-to-r from-purple-600 to-purple-700 px-6 py-4">
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
              className="w-full pl-10 pr-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-500"
            />
          </div>
        </div>
      </div>

      {/* Gallery */}
      <div className="bg-slate-800 rounded-lg shadow-xl overflow-hidden">
        <div className="p-6">
          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-500 mx-auto mb-4"></div>
              <p className="text-gray-400">Loading snapshots...</p>
            </div>
          ) : filteredSnapshots.length === 0 ? (
            <div className="text-center py-12">
              <FaImages className="text-6xl text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400 text-lg">
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
                  className="bg-slate-700 rounded-lg overflow-hidden hover:ring-2 hover:ring-purple-500 transition-all cursor-pointer"
                  onClick={() => setSelectedSnapshot(snapshot)}
                >
                  <img
                    src={`http://localhost:8001${snapshot.url}`}
                    alt={snapshot.filename}
                    className="w-full h-48 object-cover"
                  />
                  <div className="p-3">
                    <p className="text-sm font-semibold text-white truncate">{snapshot.filename}</p>
                    <p className="text-xs text-gray-400 mt-1">{formatTimestamp(snapshot.timestamp)}</p>
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
            className="bg-slate-800 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-4 border-b border-slate-700 flex items-center justify-between">
              <h3 className="text-xl font-bold text-white">{selectedSnapshot.filename}</h3>
              <button
                onClick={() => setSelectedSnapshot(null)}
                className="text-gray-400 hover:text-white"
              >
                ✕
              </button>
            </div>
            <div className="p-4">
              <img
                src={`http://localhost:8001${selectedSnapshot.url}`}
                alt={selectedSnapshot.filename}
                className="w-full h-auto rounded"
              />
              <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-400">Timestamp:</p>
                  <p className="text-white">{formatTimestamp(selectedSnapshot.timestamp)}</p>
                </div>
                <div>
                  <p className="text-gray-400">File Size:</p>
                  <p className="text-white">{formatFileSize(selectedSnapshot.size)}</p>
                </div>
              </div>
              <a
                href={`http://localhost:8001${selectedSnapshot.url}`}
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

