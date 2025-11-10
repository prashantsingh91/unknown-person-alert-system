import React, { useState, useEffect } from 'react';
import VideoPlayer from './components/VideoPlayer';
import AlertPanel from './components/AlertPanel';
import SnapshotGallery from './components/SnapshotGallery';
import MetricsDashboard from './components/MetricsDashboard';
import KnownPersonsLog from './components/KnownPersonsLog';
import ControlPanel from './components/ControlPanel';
import LoginPage from './components/LoginPage';
import api from './services/api';
import { FaVideo, FaBell, FaImages, FaChartLine, FaUsers, FaSignOutAlt } from 'react-icons/fa';

function App() {
  const [authenticated, setAuthenticated] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [activeView, setActiveView] = useState('main');
  const [systemHealth, setSystemHealth] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [knownPersons, setKnownPersons] = useState([]);
  const [metrics, setMetrics] = useState(null);

  const handleLogout = async () => {
    try {
      await api.logout();
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      setAuthenticated(false);
      setAlerts([]);
      setKnownPersons([]);
      setMetrics(null);
      api.disconnectWebSocket();
    }
  };

  // Check authentication on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const authStatus = await api.checkAuth();
        setAuthenticated(authStatus.authenticated);
      } catch (err) {
        console.error('Auth check failed:', err);
        setAuthenticated(false);
      } finally {
        setCheckingAuth(false);
      }
    };
    checkAuth();
  }, []);

  // Initialize app only if authenticated
  useEffect(() => {
    if (!authenticated) {
      return;
    }

    // Check system health
    api.getHealth().then(health => {
      setSystemHealth(health);
    }).catch(err => {
      console.error('Failed to get health:', err);
      // If 401, logout
      if (err.response && err.response.status === 401) {
        handleLogout();
      }
    });

    // Connect WebSocket
    api.connectWebSocket().then(() => {
      console.log('Connected to backend');
    }).catch(err => {
      console.error('Failed to connect:', err);
      // If auth error, logout
      if (err.message === 'Not authenticated') {
        handleLogout();
      }
    });

    // Register WebSocket callbacks
    const handleAlert = (data) => {
      try {
        if (data && data.data) {
          setAlerts(prev => [data.data, ...prev].slice(0, 20));
        }
      } catch (error) {
        console.error('Error handling alert:', error);
      }
    };

    const handleKnownPerson = (data) => {
      try {
        if (data && data.data) {
          setKnownPersons(prev => [data.data, ...prev].slice(0, 50));
        }
      } catch (error) {
        console.error('Error handling known person:', error);
      }
    };

    const handleMetrics = (data) => {
      try {
        if (data && data.data) {
          setMetrics(data.data);
        }
      } catch (error) {
        console.error('Error handling metrics:', error);
      }
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
  }, [authenticated]);

  const handleLoginSuccess = () => {
    setAuthenticated(true);
  };

  const handlePlayStart = () => {
    // Clear UI state for fresh start
    setAlerts([]);
    setKnownPersons([]);
    setMetrics(null);
    console.log("🔄 UI cleared for fresh detection");
  };

  // Show loading while checking auth
  if (checkingAuth) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        backgroundColor: '#1a1a1a',
        color: '#fff'
      }}>
        <div>Loading...</div>
      </div>
    );
  }

  // Show login page if not authenticated
  if (!authenticated) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
  }

  const renderMainView = () => (
    <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
      {/* Left column - Video and Controls */}
      <div className="xl:col-span-2 space-y-6">
        <VideoPlayer />
        <ControlPanel onPlayStart={handlePlayStart} />
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
    <div className="min-h-screen bg-gray-50 text-gray-900">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            {/* Logo on left */}
            <div className="flex items-center">
              <img 
                src="/iqline.png" 
                alt="Company Logo" 
                className="h-12 w-auto object-contain"
              />
            </div>
            
            {/* Centered Title and Subtitle */}
            <div className="flex-1 flex flex-col items-center justify-center text-center">
              <h1 className="text-2xl font-bold text-gray-900">Intrusion detection system</h1>
              <p className="text-sm text-gray-600">Real-time Face Recognition & Monitoring</p>
            </div>
            
            {/* System Status and Logout on right */}
            <div className="flex items-center space-x-4">
              {systemHealth && (
                <div className="flex items-center space-x-2">
                  <div className={`w-3 h-3 rounded-full ${systemHealth.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'} animate-pulse`}></div>
                  <span className="text-sm text-gray-700">
                    {systemHealth.processing ? 'Processing' : 'Ready'}
                  </span>
                </div>
              )}
              <button
                onClick={handleLogout}
                className="flex items-center space-x-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                title="Logout"
              >
                <FaSignOutAlt />
                <span>Logout</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200">
        <div className="container mx-auto px-4">
          <div className="flex space-x-1">
            <button
              onClick={() => setActiveView('main')}
              className={`flex items-center space-x-2 px-4 py-3 border-b-2 transition-colors ${
                activeView === 'main'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              <FaVideo />
              <span>Live Feed</span>
            </button>
            
            <button
              onClick={() => setActiveView('alerts')}
              className={`flex items-center space-x-2 px-4 py-3 border-b-2 transition-colors ${
                activeView === 'alerts'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
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
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              <FaImages />
              <span>Snapshots</span>
            </button>
            
            <button
              onClick={() => setActiveView('metrics')}
              className={`flex items-center space-x-2 px-4 py-3 border-b-2 transition-colors ${
                activeView === 'metrics'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              <FaChartLine />
              <span>Metrics</span>
            </button>
            
            <button
              onClick={() => setActiveView('known')}
              className={`flex items-center space-x-2 px-4 py-3 border-b-2 transition-colors ${
                activeView === 'known'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
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
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="container mx-auto px-4 py-4">
          <p className="text-center text-sm text-gray-600">
            Intrusion detection system v1.0
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;

