import React, { useState, useEffect } from 'react';
import axios from 'axios';

const TranslationForm = ({ onJobCreated }) => {
    const [inputFile, setInputFile] = useState('');
    const [targetLang, setTargetLang] = useState('ko');
    const [openWebUIUrl, setOpenWebUIUrl] = useState('');
    const [apiKey, setApiKey] = useState('');
    const [model, setModel] = useState('');
    const [loading, setLoading] = useState(false);
    const [files, setFiles] = useState([]);

    useEffect(() => {
        fetchFiles();
        loadSettings();
    }, []);

    const loadSettings = async () => {
        try {
            const response = await axios.get('http://localhost:8000/api/settings');
            if (response.data.openwebui_url) setOpenWebUIUrl(response.data.openwebui_url);
            if (response.data.api_key) setApiKey(response.data.api_key);
            if (response.data.model) setModel(response.data.model);
        } catch (err) {
            console.error('Failed to load settings:', err);
        }
    };

    const saveSettings = async () => {
        try {
            await axios.post('http://localhost:8000/api/settings', {
                openwebui_url: openWebUIUrl,
                api_key: apiKey,
                model: model
            });
            alert('설정이 저장되었습니다.');
        } catch (err) {
            console.error('Failed to save settings:', err);
            alert('설정 저장에 실패했습니다.');
        }
    };

    const fetchFiles = async () => {
        try {
            const response = await axios.get('http://localhost:8000/api/files');
            const txtFiles = response.data.files.filter(f => f.name.endsWith('.txt'));
            setFiles(txtFiles);
        } catch (err) {
            console.error('Failed to fetch files:', err);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);

        try {
            const response = await axios.post('http://localhost:8000/api/translate', {
                input_file: inputFile,
                target_lang: targetLang,
                openwebui_url: openWebUIUrl,
                api_key: apiKey,
                model: model
            });

            onJobCreated(response.data);
            alert('Translation job started!');
        } catch (err) {
            alert('Error: ' + (err.response?.data?.detail || 'Failed to start translation job'));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="card">
            <h2>Translate Text</h2>
            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label>Input File (from MinIO)</label>
                    <select value={inputFile} onChange={(e) => setInputFile(e.target.value)} required>
                        <option value="">Select a file...</option>
                        {files.map(file => (
                            <option key={file.name} value={file.name}>{file.name}</option>
                        ))}
                    </select>
                </div>

                <div className="form-group">
                    <label>Target Language</label>
                    <select value={targetLang} onChange={(e) => setTargetLang(e.target.value)}>
                        <option value="ko">Korean</option>
                        <option value="en">English</option>
                        <option value="ja">Japanese</option>
                        <option value="zh">Chinese</option>
                    </select>
                </div>

                <div className="form-group">
                    <label>OpenWebUI URL</label>
                    <input
                        type="text"
                        value={openWebUIUrl}
                        onChange={(e) => setOpenWebUIUrl(e.target.value)}
                        placeholder="http://localhost:3000"
                        required
                    />
                </div>

                <div className="form-group">
                    <label>API Key</label>
                    <input
                        type="text"
                        value={apiKey}
                        onChange={(e) => setApiKey(e.target.value)}
                        placeholder="sk-..."
                        required
                    />
                </div>

                <div className="form-group">
                    <label>Model</label>
                    <input
                        type="text"
                        value={model}
                        onChange={(e) => setModel(e.target.value)}
                        placeholder="gpt-4"
                        required
                    />
                </div>

                <div className="button-group">
                    <button type="button" onClick={saveSettings} className="save-btn">
                        Save Settings
                    </button>
                    <button type="submit" disabled={loading}>
                        {loading ? 'Processing...' : 'Start Translation'}
                    </button>
                </div>
            </form>
        </div>
    );
};

export default TranslationForm;
