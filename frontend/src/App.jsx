import { useState } from 'react';
import './App.css';

function App() {
  const [apiStatus, setApiStatus] = useState('checking...');

  // Check backend connection on mount
  const checkBackend = async () => {
    try {
      const response = await fetch(import.meta.env.VITE_API_URL || 'http://localhost:8000');
      const data = await response.json();
      setApiStatus(`Connected - ${data.message}`);
    } catch (error) {
      setApiStatus('Backend not running');
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>K-Pop Dance Trainer</h1>
        <p>Real-time dance feedback using AI</p>
        <button onClick={checkBackend}>Check Backend Connection</button>
        <p>Backend Status: {apiStatus}</p>
      </header>
    </div>
  );
}

export default App;
