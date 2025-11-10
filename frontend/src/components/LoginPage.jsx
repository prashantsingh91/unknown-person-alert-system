import React, { useState } from 'react';
import api from '../services/api';
import { FaLock, FaUser } from 'react-icons/fa';

const LoginPage = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const result = await api.login(username, password);
      if (result.status === 'success') {
        onLoginSuccess();
      } else {
        setError('Login failed. Please check your credentials.');
      }
    } catch (err) {
      console.error('Login error details:', err);
      console.error('Error response:', err.response);
      console.error('Error message:', err.message);
      if (err.response && err.response.status === 401) {
        setError('Invalid username or password');
      } else if (err.response) {
        setError(`Login failed: ${err.response.status} - ${err.response.statusText}`);
      } else if (err.message) {
        setError(`Login failed: ${err.message}`);
      } else {
        setError('Login failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      backgroundColor: '#1a1a1a',
      color: '#fff'
    }}>
      <div style={{
        backgroundColor: '#2a2a2a',
        padding: '40px',
        borderRadius: '10px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.3)',
        width: '100%',
        maxWidth: '400px'
      }}>
        <h1 style={{
          textAlign: 'center',
          marginBottom: '30px',
          fontSize: '28px',
          fontWeight: 'bold'
        }}>
          Face Alert System
        </h1>
        <h2 style={{
          textAlign: 'center',
          marginBottom: '30px',
          fontSize: '18px',
          color: '#aaa'
        }}>
          Admin Login
        </h2>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '20px' }}>
            <label style={{
              display: 'block',
              marginBottom: '8px',
              fontSize: '14px',
              color: '#ccc'
            }}>
              <FaUser style={{ marginRight: '8px' }} />
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              style={{
                width: '100%',
                padding: '12px',
                fontSize: '16px',
                backgroundColor: '#1a1a1a',
                border: '1px solid #444',
                borderRadius: '5px',
                color: '#fff',
                boxSizing: 'border-box'
              }}
              placeholder="Enter username"
            />
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={{
              display: 'block',
              marginBottom: '8px',
              fontSize: '14px',
              color: '#ccc'
            }}>
              <FaLock style={{ marginRight: '8px' }} />
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{
                width: '100%',
                padding: '12px',
                fontSize: '16px',
                backgroundColor: '#1a1a1a',
                border: '1px solid #444',
                borderRadius: '5px',
                color: '#fff',
                boxSizing: 'border-box'
              }}
              placeholder="Enter password"
            />
          </div>

          {error && (
            <div style={{
              backgroundColor: '#d32f2f',
              color: '#fff',
              padding: '12px',
              borderRadius: '5px',
              marginBottom: '20px',
              fontSize: '14px'
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '12px',
              fontSize: '16px',
              fontWeight: 'bold',
              backgroundColor: loading ? '#555' : '#4CAF50',
              color: '#fff',
              border: 'none',
              borderRadius: '5px',
              cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'background-color 0.3s'
            }}
            onMouseOver={(e) => {
              if (!loading) e.target.style.backgroundColor = '#45a049';
            }}
            onMouseOut={(e) => {
              if (!loading) e.target.style.backgroundColor = '#4CAF50';
            }}
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;

