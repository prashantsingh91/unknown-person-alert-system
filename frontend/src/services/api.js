/**
 * API Service for communicating with backend
 */
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';
const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8001';

class APIService {
  constructor() {
    this.wsConnection = null;
    this.wsCallbacks = {
      frame: [],
      alert: [],
      metrics: [],
      known_person: []
    };
  }

  /**
   * Connect to WebSocket for real-time streaming
   */
  connectWebSocket() {
    return new Promise((resolve, reject) => {
      try {
        this.wsConnection = new WebSocket(`${WS_BASE_URL}/api/stream`);
        
        this.wsConnection.onopen = () => {
          console.log('WebSocket connected');
          resolve(this.wsConnection);
        };
        
        this.wsConnection.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            const type = data.type;
            
            if (this.wsCallbacks[type]) {
              this.wsCallbacks[type].forEach(callback => callback(data));
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };
        
        this.wsConnection.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
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
      const response = await axios.get(`${API_BASE_URL}/api/stats`);
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
      const response = await axios.get(`${API_BASE_URL}/api/snapshots`);
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
      const response = await axios.get(`${API_BASE_URL}/api/known-persons`);
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

