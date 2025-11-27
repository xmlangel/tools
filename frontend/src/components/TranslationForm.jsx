import React, { useState, useEffect } from 'react';
import axios from 'axios';

const TranslationForm = ({ onJobCreated }) => {
    const [text, setText] = useState('');
    const [filePath, setFilePath] = useState('');
    const [apiUrl, setApiUrl] = useState('http://localhost:3000');
    const [apiKey, setApiKey] = useState('');
    const [model, setModel] = useState('llama3');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [availableFiles, setAvailableFiles] = useState([]);
    const [loadingFiles, setLoadingFiles] = useState(false);

    useEffect(() => {
        fetchFiles();
    }, []);

    const fetchFiles = async () => {
        setLoadingFiles(true);
        try {
            const response = await axios.get('http://localhost:8000/api/files');
            // .txt 파일만 필터링
            const txtFiles = (response.data.files || []).filter(file =>
                file.name.toLowerCase().endsWith('.txt')
            );
            setAvailableFiles(txtFiles);
        } catch (err) {
            console.error('Failed to fetch files:', err);
        } finally {
            setLoadingFiles(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const response = await axios.post('http://localhost:8000/api/translate', {
                text: text || null,
                file_path: filePath || null,
                api_url: apiUrl,
                api_key: apiKey,
                model: model
            });
            onJobCreated(response.data);
            setText('');
            setFilePath('');
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to start translation job');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="card">
            <h2>Translation (OpenWebUI)</h2>
            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label>Input Text (or leave empty to use file from STT):</label>
                    <textarea
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        placeholder="Enter text to translate..."
                        rows={4}
                    />
                </div>
                <div className="form-group">
                    <label>Or MinIO File Path (e.g. from STT result):</label>
                    {loadingFiles ? (
                        <p>Loading files...</p>
                    ) : availableFiles.length > 0 ? (
                        <select
                            value={filePath}
                            onChange={(e) => setFilePath(e.target.value)}
                        >
                            <option value="">-- Select a file --</option>
                            {availableFiles.map((file) => (
                                <option key={file.name} value={file.name}>
                                    {file.name} ({(file.size / 1024).toFixed(2)} KB)
                                </option>
                            ))}
                        </select>
                    ) : (
                        <p>No files available in MinIO</p>
                    )}
                </div>
                <div className="form-group">
                    <label>OpenWebUI URL:</label>
                    <input
                        type="text"
                        value={apiUrl}
                        onChange={(e) => setApiUrl(e.target.value)}
                        required
                    />
                </div>
                <div className="form-group">
                    <label>API Key:</label>
                    <input
                        type="password"
                        value={apiKey}
                        onChange={(e) => setApiKey(e.target.value)}
                        placeholder="sk-..."
                        required
                    />
                </div>
                <div className="form-group">
                    <label>Model:</label>
                    <input
                        type="text"
                        value={model}
                        onChange={(e) => setModel(e.target.value)}
                        required
                    />
                </div>
                <button type="submit" disabled={loading}>
                    {loading ? 'Starting...' : 'Start Translation'}
                </button>
                {error && <p className="error">{error}</p>}
            </form>
        </div>
    );
};

export default TranslationForm;
