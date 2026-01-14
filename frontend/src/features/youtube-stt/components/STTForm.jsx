import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_URL } from '../../../config';

const STTForm = ({ onJobCreated }) => {
  const [inputMode, setInputMode] = useState('url'); // 'url' or 'file'
  const [url, setUrl] = useState('');
  const [file, setFile] = useState(null);
  const [model, setModel] = useState('base');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // 설정 저장
      await axios.post(`${API_URL}/api/settings`, {
        stt_model: model
      });

      if (inputMode === 'url') {
        // YouTube URL 처리
        const response = await axios.post(`${API_URL}/api/stt`, {
          url,
          model
        });
        onJobCreated(response.data);
        setUrl('');
      } else {
        // 파일 업로드 처리
        if (!file) {
          setError('Please select a file');
          setLoading(false);
          return;
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('model', model);

        const response = await axios.post(`${API_URL}/api/stt/upload`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        onJobCreated(response.data);
        setFile(null);
        // Reset file input
        const fileInput = document.getElementById('audio-file-input');
        if (fileInput) fileInput.value = '';
      }
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
      const response = await axios.get(`${API_URL}/api/settings`);
      if (response.data.stt_model) setModel(response.data.stt_model);
    } catch (err) {
      console.error('Failed to load settings:', err);
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      const allowedExtensions = ['.m4a', '.mp3', '.wav', '.flac', '.ogg', '.aac', '.mp4', '.webm'];
      const fileExt = selectedFile.name.substring(selectedFile.name.lastIndexOf('.')).toLowerCase();

      if (!allowedExtensions.includes(fileExt)) {
        setError(`Unsupported file format. Allowed: ${allowedExtensions.join(', ')}`);
        e.target.value = '';
        return;
      }

      setFile(selectedFile);
      setError('');
    }
  };

  return (
    <div className="card">
      <h2>YouTube STT</h2>

      {/* Input Mode Toggle */}
      <div className="form-group">
        <label>Input Mode:</label>
        <div style={{ display: 'flex', gap: '10px', marginTop: '5px' }}>
          <button
            type="button"
            onClick={() => setInputMode('url')}
            style={{
              padding: '8px 16px',
              backgroundColor: inputMode === 'url' ? '#007bff' : '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            YouTube URL
          </button>
          <button
            type="button"
            onClick={() => setInputMode('file')}
            style={{
              padding: '8px 16px',
              backgroundColor: inputMode === 'file' ? '#007bff' : '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Upload File
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        {inputMode === 'url' ? (
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
        ) : (
          <div className="form-group">
            <label>Audio File:</label>
            <input
              id="audio-file-input"
              type="file"
              accept=".m4a,.mp3,.wav,.flac,.ogg,.aac,.mp4,.webm"
              onChange={handleFileChange}
              required
            />
            <small style={{ display: 'block', marginTop: '5px', color: '#666' }}>
              Supported formats: m4a, mp3, wav, flac, ogg, aac, mp4, webm
            </small>
            {file && (
              <p style={{ marginTop: '5px', color: '#28a745' }}>
                Selected: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
              </p>
            )}
          </div>
        )}

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

