import React, { useState, useEffect } from 'react';
import VideoPlayer from './components/VideoPlayer';
import AlertPanel from './components/AlertPanel';
import SnapshotGallery from './components/SnapshotGallery';
import MetricsDashboard from './components/MetricsDashboard';
import KnownPersonsLog from './components/KnownPersonsLog';
import ControlPanel from './components/ControlPanel';
import api from './services/api';
import { FaVideo, FaBell, FaImages, FaChartLine, FaUsers } from 'react-icons/fa';

function App() {
  const [activeView, setActiveView] = useState('main');
  const [systemHealth, setSystemHealth] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [knownPersons, setKnownPersons] = useState([]);
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    // Check system health
    api.getHealth().then(health => {
      setSystemHealth(health);
    }).catch(err => {
      console.error('Failed to get health:', err);
    });

    // Connect WebSocket
    api.connectWebSocket().then(() => {
      console.log('Connected to backend');
    }).catch(err => {
      console.error('Failed to connect:', err);
    });

    // Register WebSocket callbacks
    const handleAlert = (data) => {
      setAlerts(prev => [data.data, ...prev].slice(0, 20));
    };

    const handleKnownPerson = (data) => {
      setKnownPersons(prev => [data.data, ...prev].slice(0, 50));
    };

    const handleMetrics = (data) => {
      setMetrics(data.data);
    };

    api.on('alert', handleAlert);
    api.on('known_person', handleKnownPerson);
    api.on('metrics', handleMetrics);

    return () => {
      api.off('alert', handleAlert);
      api.off('known_person', handleKnownPerson);
      api.off('metrics', handleMetrics);
      api.disconnectWebSocket();
    };
  }, []);

  const renderMainView = () => (
    <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
      {/* Left column - Video and Controls */}
      <div className="xl:col-span-2 space-y-6">
        <VideoPlayer />
        <ControlPanel />
      </div>

      {/* Right column - Metrics, Alerts, Known Persons */}
      <div className="space-y-6">
        <MetricsDashboard metrics={metrics} compact />
        <AlertPanel alerts={alerts} compact />
        <KnownPersonsLog persons={knownPersons} compact />
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-900 text-gray-100">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 shadow-lg">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <FaVideo className="text-blue-500 text-3xl" />
              <div>
                <h1 className="text-2xl font-bold text-white">Unknown Person Alert System</h1>
                <p className="text-sm text-gray-400">Real-time Face Recognition & Monitoring</p>
              </div>
            </div>
            
            {/* System Status */}
            <div className="flex items-center space-x-4">
              {systemHealth && (
                <div className="flex items-center space-x-2">
                  <div className={`w-3 h-3 rounded-full ${systemHealth.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'} animate-pulse`}></div>
                  <span className="text-sm text-gray-300">
                    {systemHealth.processing ? 'Processing' : 'Ready'}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-slate-800 border-b border-slate-700">
        <div className="container mx-auto px-4">
          <div className="flex space-x-1">
            <button
              onClick={() => setActiveView('main')}
              className={`flex items-center space-x-2 px-4 py-3 border-b-2 transition-colors ${
                activeView === 'main'
                  ? 'border-blue-500 text-blue-500'
                  : 'border-transparent text-gray-400 hover:text-gray-300'
              }`}
            >
              <FaVideo />
              <span>Live Feed</span>
            </button>
            
            <button
              onClick={() => setActiveView('alerts')}
              className={`flex items-center space-x-2 px-4 py-3 border-b-2 transition-colors ${
                activeView === 'alerts'
                  ? 'border-blue-500 text-blue-500'
                  : 'border-transparent text-gray-400 hover:text-gray-300'
              }`}
            >
              <FaBell />
              <span>Alerts</span>
              {alerts.length > 0 && (
                <span className="bg-red-500 text-white text-xs px-2 py-1 rounded-full">
                  {alerts.length}
                </span>
              )}
            </button>
            
            <button
              onClick={() => setActiveView('snapshots')}
              className={`flex items-center space-x-2 px-4 py-3 border-b-2 transition-colors ${
                activeView === 'snapshots'
                  ? 'border-blue-500 text-blue-500'
                  : 'border-transparent text-gray-400 hover:text-gray-300'
              }`}
            >
              <FaImages />
              <span>Snapshots</span>
            </button>
            
            <button
              onClick={() => setActiveView('metrics')}
              className={`flex items-center space-x-2 px-4 py-3 border-b-2 transition-colors ${
                activeView === 'metrics'
                  ? 'border-blue-500 text-blue-500'
                  : 'border-transparent text-gray-400 hover:text-gray-300'
              }`}
            >
              <FaChartLine />
              <span>Metrics</span>
            </button>
            
            <button
              onClick={() => setActiveView('known')}
              className={`flex items-center space-x-2 px-4 py-3 border-b-2 transition-colors ${
                activeView === 'known'
                  ? 'border-blue-500 text-blue-500'
                  : 'border-transparent text-gray-400 hover:text-gray-300'
              }`}
            >
              <FaUsers />
              <span>Known Persons</span>
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        {activeView === 'main' && renderMainView()}
        {activeView === 'alerts' && <AlertPanel alerts={alerts} />}
        {activeView === 'snapshots' && <SnapshotGallery />}
        {activeView === 'metrics' && <MetricsDashboard metrics={metrics} />}
        {activeView === 'known' && <KnownPersonsLog persons={knownPersons} />}
      </main>

      {/* Footer */}
      <footer className="bg-slate-800 border-t border-slate-700 mt-12">
        <div className="container mx-auto px-4 py-4">
          <p className="text-center text-sm text-gray-400">
            Unknown Person Alert System v1.0 | Powered by InsightFace & FastAPI
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;

