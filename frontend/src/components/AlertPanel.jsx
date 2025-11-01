import React from 'react';
import { FaBell, FaExclamationTriangle } from 'react-icons/fa';

const AlertPanel = ({ alerts, compact = false }) => {
  const formatTimestamp = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleTimeString();
  };

  if (compact) {
    return (
      <div className="bg-slate-800 rounded-lg shadow-xl overflow-hidden">
        <div className="bg-gradient-to-r from-red-600 to-red-700 px-4 py-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white flex items-center">
            <FaBell className="mr-2" />
            Recent Alerts
          </h2>
          {alerts.length > 0 && (
            <span className="bg-white text-red-600 text-xs font-bold px-2 py-1 rounded-full">
              {alerts.length}
            </span>
          )}
        </div>
        
        <div className="p-4 max-h-80 overflow-y-auto">
          {alerts.length === 0 ? (
            <p className="text-gray-400 text-center py-4">No alerts yet</p>
          ) : (
            <div className="space-y-3">
              {alerts.slice(0, 5).map((alert, index) => (
                <div
                  key={index}
                  className="bg-slate-700 rounded-lg p-3 border-l-4 border-red-500"
                >
                  <div className="flex items-start space-x-3">
                    {alert.snapshot_path && (
                      <img
                        src={`http://localhost:8001${alert.snapshot_path}`}
                        alt="Unknown person"
                        className="w-16 h-16 rounded object-cover"
                      />
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-red-400">{alert.uid}</p>
                      <p className="text-xs text-gray-400">{formatTimestamp(alert.timestamp)}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        Confidence: {(alert.confidence * 100).toFixed(1)}%
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-800 rounded-lg shadow-xl overflow-hidden">
      <div className="bg-gradient-to-r from-red-600 to-red-700 px-6 py-4 flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white flex items-center">
          <FaExclamationTriangle className="mr-3" />
          Unknown Person Alerts
        </h2>
        {alerts.length > 0 && (
          <span className="bg-white text-red-600 text-sm font-bold px-3 py-1 rounded-full">
            {alerts.length} Alert{alerts.length !== 1 ? 's' : ''}
          </span>
        )}
      </div>
      
      <div className="p-6">
        {alerts.length === 0 ? (
          <div className="text-center py-12">
            <FaBell className="text-6xl text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400 text-lg">No alerts yet</p>
            <p className="text-gray-500 text-sm mt-2">
              Unknown persons will appear here when detected
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {alerts.map((alert, index) => (
              <div
                key={index}
                className="bg-slate-700 rounded-lg overflow-hidden border-2 border-red-500 hover:border-red-400 transition-colors"
              >
                {alert.snapshot_path && (
                  <img
                    src={`http://localhost:8001${alert.snapshot_path}`}
                    alt="Unknown person"
                    className="w-full h-48 object-cover"
                  />
                )}
                <div className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-lg font-bold text-red-400">{alert.uid}</span>
                    <span className="text-xs text-gray-400">{formatTimestamp(alert.timestamp)}</span>
                  </div>
                  <div className="text-sm text-gray-300">
                    <p>Detection Confidence: {(alert.confidence * 100).toFixed(1)}%</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AlertPanel;

