import React, { useState, useEffect } from 'react';
import axios from 'axios';
import TranslationTemplateEditor from './TranslationTemplateEditor';

const TranslationForm = ({ onJobCreated }) => {
    const [inputFile, setInputFile] = useState('');
    const [targetLang, setTargetLang] = useState('ko');
    const [openWebUIUrl, setOpenWebUIUrl] = useState('');
    const [apiKey, setApiKey] = useState('');
    const [model, setModel] = useState('');
    const [loading, setLoading] = useState(false);
    const [files, setFiles] = useState([]);
    const [sttJobs, setSttJobs] = useState([]);  // Store STT jobs to get YouTube URLs
    const [isTemplateModalOpen, setIsTemplateModalOpen] = useState(false);
    const [showHelp, setShowHelp] = useState(false);

    useEffect(() => {
        fetchFiles();
        fetchSTTJobs();
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

    const fetchSTTJobs = async () => {
        try {
            const response = await axios.get('http://localhost:8000/api/jobs');
            const sttJobsList = response.data.jobs.filter(j => j.type === 'stt');
            setSttJobs(sttJobsList);
        } catch (err) {
            console.error('Failed to fetch STT jobs:', err);
        }
    };

    const getYouTubeUrlForFile = (filename) => {
        // Find STT job that generated this file
        const sttJob = sttJobs.find(job => {
            if (job.output && job.output.text === filename) {
                return true;
            }
            return false;
        });
        return sttJob?.youtube_url || null;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);

        try {
            const youtubeUrl = getYouTubeUrlForFile(inputFile);

            const response = await axios.post('http://localhost:8000/api/translate', {
                input_file: inputFile,
                target_lang: targetLang,
                openwebui_url: openWebUIUrl,
                api_key: apiKey,
                model: model,
                youtube_url: youtubeUrl  // Send YouTube URL if found
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
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h2 style={{ margin: 0 }}>Translate Text</h2>
                <button
                    onClick={() => setShowHelp(!showHelp)}
                    style={{
                        padding: '0.5rem 1rem',
                        background: 'none',
                        border: '1px solid #ddd',
                        borderRadius: '4px',
                        cursor: 'pointer'
                    }}
                >
                    {showHelp ? '닫기' : '사용 방법'}
                </button>
            </div>

            {showHelp && (
                <div style={{
                    marginBottom: '2rem',
                    padding: '1.5rem',
                    background: '#f8f9fa',
                    borderRadius: '8px',
                    border: '1px solid #e9ecef'
                }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                        <h3 style={{ margin: 0 }}>📖 사용 방법</h3>
                        <button
                            onClick={() => setShowHelp(false)}
                            style={{
                                background: 'none',
                                border: 'none',
                                fontSize: '1.2rem',
                                cursor: 'pointer',
                                color: '#6c757d',
                                padding: '0.5rem'
                            }}
                        >
                            ✕
                        </button>
                    </div>
                    <div style={{ display: 'grid', gap: '1.5rem' }}>
                        <div>
                            <h4 style={{ margin: '0 0 0.5rem 0' }}>1️⃣ 설정 입력</h4>
                            <ul style={{ margin: 0, paddingLeft: '1.5rem', color: '#495057' }}>
                                <li><strong>OpenWebUI URL</strong>: LLM 서버 주소 (예: http://localhost:3000)</li>
                                <li><strong>API Key</strong>: 인증 키</li>
                                <li><strong>Model</strong>: 사용할 모델명 (예: gpt-4)</li>
                            </ul>
                        </div>
                        <div>
                            <h4 style={{ margin: '0 0 0.5rem 0' }}>2️⃣ 파일 선택 및 번역</h4>
                            <ul style={{ margin: 0, paddingLeft: '1.5rem', color: '#495057' }}>
                                <li><strong>Input File</strong>: MinIO에 저장된 텍스트 파일을 선택합니다.</li>
                                <li><strong>Target Language</strong>: 번역할 언어를 선택합니다.</li>
                                <li><strong>Start Translation</strong>: 번역 작업을 시작합니다.</li>
                            </ul>
                        </div>
                        <div>
                            <h4 style={{ margin: '0 0 0.5rem 0' }}>3️⃣ 템플릿 설정 (고급)</h4>
                            <ul style={{ margin: 0, paddingLeft: '1.5rem', color: '#495057' }}>
                                <li><strong>⚙️ 템플릿 편집</strong> 버튼을 눌러 번역 프롬프트를 수정할 수 있습니다.</li>
                                <li><strong>System Prompt</strong>: AI 번역가의 페르소나를 설정합니다.</li>
                                <li><strong>User Prompt</strong>: 구체적인 번역 지시사항을 설정합니다. (<code>{'{text}'}</code> 필수)</li>
                            </ul>
                        </div>
                    </div>
                </div>
            )}

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
                        type="password"
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
                    <button type="button" onClick={() => setIsTemplateModalOpen(true)} className="save-btn" style={{ marginRight: '10px' }}>
                        ⚙️ 템플릿 편집
                    </button>
                    <button type="button" onClick={saveSettings} className="save-btn">
                        Save Settings
                    </button>
                    <button type="submit" disabled={loading}>
                        {loading ? 'Processing...' : 'Start Translation'}
                    </button>
                </div>
            </form>
            <TranslationTemplateEditor
                isOpen={isTemplateModalOpen}
                onClose={() => setIsTemplateModalOpen(false)}
            />
        </div>
    );
};

export default TranslationForm;
