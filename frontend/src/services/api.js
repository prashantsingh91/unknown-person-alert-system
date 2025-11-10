/**
 * API Service for communicating with backend
 */
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

class APIService {
  constructor() {
    this.wsConnection = null;
    this.wsCallbacks = {
      frame: [],
      alert: [],
      metrics: [],
      known_person: []
    };
    this.sessionId = localStorage.getItem('sessionId') || null;
  }

  /**
   * Get session ID from localStorage
   */
  getSessionId() {
    return this.sessionId || localStorage.getItem('sessionId');
  }

  /**
   * Set session ID
   */
  setSessionId(sessionId) {
    this.sessionId = sessionId;
    if (sessionId) {
      localStorage.setItem('sessionId', sessionId);
    } else {
      localStorage.removeItem('sessionId');
    }
  }

  /**
   * Get default headers with session ID
   */
  getHeaders() {
    const headers = {};
    const sessionId = this.getSessionId();
    if (sessionId) {
      headers['X-Session-ID'] = sessionId;
    }
    return headers;
  }

  /**
   * Login
   */
  async login(username, password) {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/auth/login`, {
        username,
        password
      });
      if (response.data.session_id) {
        this.setSessionId(response.data.session_id);
      }
      return response.data;
    } catch (error) {
      console.error('Error logging in:', error);
      throw error;
    }
  }

  /**
   * Logout
   */
  async logout() {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/auth/logout`, {}, {
        headers: this.getHeaders()
      });
      this.setSessionId(null);
      return response.data;
    } catch (error) {
      console.error('Error logging out:', error);
      // Clear session even if logout fails
      this.setSessionId(null);
      throw error;
    }
  }

  /**
   * Check authentication status
   */
  async checkAuth() {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/auth/check`, {
        headers: this.getHeaders()
      });
      if (!response.data.authenticated) {
        this.setSessionId(null);
      }
      return response.data;
    } catch (error) {
      console.error('Error checking auth:', error);
      this.setSessionId(null);
      return { authenticated: false };
    }
  }

  /**
   * Connect to WebSocket for real-time streaming
   */
  connectWebSocket() {
    return new Promise((resolve, reject) => {
      try {
        const sessionId = this.getSessionId();
        if (!sessionId) {
          reject(new Error('Not authenticated'));
          return;
        }
        // Include session_id as query parameter
        this.wsConnection = new WebSocket(`${WS_BASE_URL}/api/stream?session_id=${sessionId}`);
        
        this.wsConnection.onopen = () => {
          console.log('WebSocket connected');
          resolve(this.wsConnection);
        };
        
        this.wsConnection.onmessage = (event) => {
          try {
            console.log('WebSocket message received:', event.data);
            const data = JSON.parse(event.data);
            const type = data.type;
            console.log('Parsed message type:', type, data);

            if (this.wsCallbacks[type]) {
              this.wsCallbacks[type].forEach(callback => callback(data));
            } else {
              console.warn('No callback registered for message type:', type);
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error, event.data);
          }
        };
        
        this.wsConnection.onerror = (error) => {
          console.error('WebSocket error:', error);
          // Don't reject on error, just log it - connection might still work
          // reject(error);
        };
        
        this.wsConnection.onclose = () => {
          console.log('WebSocket disconnected');
          // Attempt to reconnect after 3 seconds
          setTimeout(() => {
            if (this.wsConnection.readyState === WebSocket.CLOSED) {
              console.log('Attempting to reconnect...');
              this.connectWebSocket();
            }
          }, 3000);
        };
        
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Register callback for specific message type
   */
  on(type, callback) {
    if (this.wsCallbacks[type]) {
      this.wsCallbacks[type].push(callback);
    }
  }

  /**
   * Remove callback
   */
  off(type, callback) {
    if (this.wsCallbacks[type]) {
      this.wsCallbacks[type] = this.wsCallbacks[type].filter(cb => cb !== callback);
    }
  }

  /**
   * Disconnect WebSocket
   */
  disconnectWebSocket() {
    if (this.wsConnection) {
      this.wsConnection.close();
      this.wsConnection = null;
    }
  }

  /**
   * Get system statistics
   */
  async getStats() {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/stats`, {
        headers: this.getHeaders()
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching stats:', error);
      throw error;
    }
  }

  /**
   * Get list of snapshots
   */
  async getSnapshots() {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/snapshots`, {
        headers: this.getHeaders()
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching snapshots:', error);
      throw error;
    }
  }

  /**
   * Get known persons log
   */
  async getKnownPersons() {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/known-persons`, {
        headers: this.getHeaders()
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching known persons:', error);
      throw error;
    }
  }

  /**
   * Change video source
   */
  async setVideoSource(sourceType, path = null, cameraId = 0) {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/source`, {
        source_type: sourceType,
        path: path,
        camera_id: cameraId
      }, {
        headers: this.getHeaders()
      });
      return response.data;
    } catch (error) {
      console.error('Error setting video source:', error);
      throw error;
    }
  }

  /**
   * Control video playback
   */
  async controlPlayback(action) {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/control`, {
        action: action
      }, {
        headers: this.getHeaders()
      });
      return response.data;
    } catch (error) {
      console.error('Error controlling playback:', error);
      throw error;
    }
  }

  /**
   * Get health status
   */
  async getHealth() {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/health`);
      return response.data;
    } catch (error) {
      console.error('Error fetching health:', error);
      throw error;
    }
  }
}

export default new APIService();

