import React, { useState } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function TestLogin() {
  const [email, setEmail] = useState('demo@csaaudit.com');
  const [password, setPassword] = useState('demo123');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('Intentando login...');

    try {
      console.log('Enviando login a:', `${API}/auth/login`);
      
      const response = await axios.post(`${API}/auth/login`, {
        email,
        password
      });
      
      console.log('Respuesta:', response.data);
      
      const { user, access_token } = response.data;
      
      // Guardar token
      localStorage.setItem('access_token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      setMessage(`¡Login exitoso! Usuario: ${user.name}`);
      
      // Redirigir al dashboard
      setTimeout(() => {
        window.location.href = '/dashboard';
      }, 1000);
      
    } catch (error) {
      console.error('Error de login:', error);
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ 
      minHeight: '100vh', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      backgroundColor: '#1e293b',
      color: 'white',
      fontFamily: 'Arial, sans-serif'
    }}>
      <div style={{
        backgroundColor: 'rgba(255,255,255,0.1)',
        padding: '40px',
        borderRadius: '10px',
        width: '400px',
        textAlign: 'center'
      }}>
        <h1>🔒 CSA Safety Audit - Test Login</h1>
        
        <form onSubmit={handleLogin} style={{ marginTop: '20px' }}>
          <div style={{ marginBottom: '15px', textAlign: 'left' }}>
            <label style={{ display: 'block', marginBottom: '5px' }}>Email:</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={{
                width: '100%',
                padding: '10px',
                border: 'none',
                borderRadius: '5px',
                backgroundColor: 'rgba(255,255,255,0.2)',
                color: 'white'
              }}
              required
            />
          </div>
          
          <div style={{ marginBottom: '20px', textAlign: 'left' }}>
            <label style={{ display: 'block', marginBottom: '5px' }}>Password:</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{
                width: '100%',
                padding: '10px',
                border: 'none',
                borderRadius: '5px',
                backgroundColor: 'rgba(255,255,255,0.2)',
                color: 'white'
              }}
              required
            />
          </div>
          
          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '12px',
              backgroundColor: '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              fontSize: '16px',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.7 : 1
            }}
          >
            {loading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
          </button>
        </form>
        
        {message && (
          <div style={{ 
            marginTop: '20px', 
            padding: '10px',
            backgroundColor: message.includes('Error') ? '#ef4444' : '#22c55e',
            borderRadius: '5px'
          }}>
            {message}
          </div>
        )}
        
        <div style={{ marginTop: '20px', fontSize: '14px', opacity: 0.8 }}>
          <strong>Cuentas Demo:</strong><br/>
          Admin: admin@csaaudit.com / admin123<br/>
          User: demo@csaaudit.com / demo123
        </div>
      </div>
    </div>
  );
}

export default TestLogin;