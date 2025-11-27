import React, { useState, useEffect } from 'react';
import axios from 'axios';

const STTForm = ({ onJobCreated }) => {
  const [url, setUrl] = useState('');
  const [model, setModel] = useState('base');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // 설정 저장
      await axios.post('http://localhost:8000/api/settings', {
        stt_model: model
      });

      const response = await axios.post('http://localhost:8000/api/stt', {
        url,
        model
      });
      onJobCreated(response.data);
      setUrl('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start STT job');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/settings');
      if (response.data.stt_model) setModel(response.data.stt_model);
    } catch (err) {
      console.error('Failed to load settings:', err);
    }
  };

  return (
    <div className="card">
      <h2>YouTube STT</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>YouTube URL:</label>
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://www.youtube.com/watch?v=..."
            required
          />
        </div>
        <div className="form-group">
          <label>Model Size:</label>
          <select value={model} onChange={(e) => setModel(e.target.value)}>
            <option value="tiny">Tiny (Fastest, Lower Accuracy)</option>
            <option value="base">Base (Balanced)</option>
            <option value="small">Small</option>
            <option value="medium">Medium</option>
            <option value="large">Large (Slowest, Best Accuracy)</option>
          </select>
        </div>
        <button type="submit" disabled={loading}>
          {loading ? 'Starting...' : 'Start Transcription'}
        </button>
        {error && <p className="error">{error}</p>}
      </form>
    </div>
  );
};

export default STTForm;
