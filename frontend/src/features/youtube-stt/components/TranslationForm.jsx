import React, { useState, useEffect } from 'react';
import axios from 'axios';
import TranslationTemplateEditor from './TranslationTemplateEditor';
import { useLLM } from '../../../context/LLMContext';
import { API_URL } from '../../../config';

const TranslationForm = ({ onJobCreated }) => {
    const [inputFile, setInputFile] = useState('');
    const [targetLang, setTargetLang] = useState('ko');
    const [srcLang, setSrcLang] = useState('auto');
    const [loading, setLoading] = useState(false);
    const [files, setFiles] = useState([]);
    const [sttJobs, setSttJobs] = useState([]);  // Store STT jobs to get YouTube URLs
    const [isTemplateModalOpen, setIsTemplateModalOpen] = useState(false);
    const [showHelp, setShowHelp] = useState(false);

    const { configs, selectedConfigId, setSelectedConfigId, getSelectedConfig } = useLLM();

    useEffect(() => {
        fetchFiles();
        fetchSTTJobs();
    }, []);

    // Auto-select default config
    useEffect(() => {
        if (!selectedConfigId && configs.length > 0) {
            const defaultConfig = configs.find(c => c.is_default);
            if (defaultConfig) {
                setSelectedConfigId(defaultConfig.id);
            }
        }
    }, [configs, selectedConfigId, setSelectedConfigId]);

    const fetchFiles = async () => {
        try {
            const response = await axios.get(`${API_URL}/api/files`);
            const txtFiles = response.data.files.filter(f => f.name.endsWith('.txt'));
            setFiles(txtFiles);
        } catch (err) {
            console.error('Failed to fetch files:', err);
        }
    };

    const fetchSTTJobs = async () => {
        try {
            const response = await axios.get(`${API_URL}/api/jobs`);
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

    const handleFileUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        // Check file extension/type if strictly needed, but backend handles it.
        const formData = new FormData();
        formData.append('file', file);

        setLoading(true);
        try {
            const response = await axios.post(`${API_URL}/api/upload`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            });

            alert('File uploaded successfully!');

            // Refresh file list and select the new file
            await fetchFiles();
            setInputFile(response.data.filename);

        } catch (err) {
            console.error('Upload failed:', err);
            alert('Failed to upload file: ' + (err.response?.data?.detail || err.message));
        } finally {
            setLoading(false);
            // Clear the input value so the same file can be selected again if needed
            e.target.value = null;
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        const selectedConfig = getSelectedConfig();
        if (!selectedConfig) {
            alert('Please select an LLM configuration first.');
            return;
        }

        setLoading(true);

        try {
            const youtubeUrl = getYouTubeUrlForFile(inputFile);

            const response = await axios.post(`${API_URL}/api/translate`, {
                input_file: inputFile,
                target_lang: targetLang,
                src_lang: srcLang,
                provider: selectedConfig.provider,
                api_url: selectedConfig.api_url,
                api_key: selectedConfig.api_key,
                model: selectedConfig.model,
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

    const [viewingFile, setViewingFile] = useState(null);
    const [fileContent, setFileContent] = useState('');

    const handlePreview = async () => {
        if (!inputFile) {
            alert('Please select a file first.');
            return;
        }

        try {
            const response = await axios.get(`${API_URL}/api/view/${inputFile}`);
            setFileContent(response.data.content);
            setViewingFile(inputFile);
        } catch (err) {
            alert('Failed to load file content: ' + (err.response?.data?.detail || err.message));
        }
    };

    const closePreview = () => {
        setViewingFile(null);
        setFileContent('');
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
                    background: '#3a3a3a',
                    borderRadius: '8px',
                    border: '1px solid #555',
                    color: 'rgba(255, 255, 255, 0.87)'
                }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                        <h3 style={{ margin: 0, color: 'white' }}>📖 사용 방법</h3>
                        <button
                            onClick={() => setShowHelp(false)}
                            style={{
                                background: 'none',
                                border: 'none',
                                fontSize: '1.2rem',
                                cursor: 'pointer',
                                color: 'rgba(255, 255, 255, 0.6)',
                                padding: '0.5rem'
                            }}
                        >
                            ✕
                        </button>
                    </div>
                    <div style={{ display: 'grid', gap: '1.5rem', textAlign: 'left' }}>
                        <div>
                            <h4 style={{ margin: '0 0 0.5rem 0', color: '#646cff' }}>1️⃣ 설정 선택</h4>
                            <ul style={{ margin: 0, paddingLeft: '1.5rem', color: '#ccc' }}>
                                <li>우측 상단의 <strong>LLM Settings</strong>에서 LLM 설정을 추가하세요.</li>
                                <li>아래 드롭다운에서 사용할 설정을 선택하세요.</li>
                            </ul>
                        </div>
                        <div>
                            <h4 style={{ margin: '0 0 0.5rem 0', color: '#646cff' }}>2️⃣ 파일 선택 및 번역</h4>
                            <ul style={{ margin: 0, paddingLeft: '1.5rem', color: '#ccc' }}>
                                <li><strong>Input File</strong>: MinIO에 저장된 텍스트 파일을 선택합니다.</li>
                                <li><strong>👁️ Preview</strong>: 선택한 파일의 내용을 미리 확인할 수 있습니다.</li>
                                <li><strong>Target Language</strong>: 번역할 언어를 선택합니다.</li>
                                <li><strong>Start Translation</strong>: 번역 작업을 시작합니다.</li>
                            </ul>
                        </div>
                        <div>
                            <h4 style={{ margin: '0 0 0.5rem 0', color: '#646cff' }}>3️⃣ 템플릿 설정 (고급)</h4>
                            <ul style={{ margin: 0, paddingLeft: '1.5rem', color: '#ccc' }}>
                                <li><strong>⚙️ 템플릿 편집</strong> 버튼을 눌러 번역 프롬프트를 수정할 수 있습니다.</li>
                                <li><strong>System Prompt</strong>: AI 번역가의 페르소나를 설정합니다.</li>
                                <li><strong>User Prompt</strong>: 구체적인 번역 지시사항을 설정합니다. (<code>{'{text}'}</code> 필수)</li>
                            </ul>
                        </div>
                    </div>
                </div>
            )}

            <form onSubmit={handleSubmit}>
                <div className="form-group" style={{ marginBottom: '1.5rem', padding: '1rem', background: '#2a2a2a', borderRadius: '8px', border: '1px solid #555' }}>
                    <label>LLM Configuration</label>
                    <select
                        value={selectedConfigId || ''}
                        onChange={(e) => setSelectedConfigId(Number(e.target.value))}
                        style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #555', backgroundColor: '#333', color: 'white' }}
                    >
                        <option value="" disabled>Select LLM Configuration...</option>
                        {configs.map(config => (
                            <option key={config.id} value={config.id}>
                                {config.name} ({config.model})
                            </option>
                        ))}
                    </select>
                    {configs.length === 0 && (
                        <p style={{ fontSize: '0.8rem', color: '#ff6b6b', marginTop: '0.5rem' }}>
                            No LLM configurations found. Please add one in the settings.
                        </p>
                    )}
                </div>

                <div className="form-group">
                    <label>Input File (from MinIO)</label>
                    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                        <select
                            value={inputFile}
                            onChange={(e) => setInputFile(e.target.value)}
                            required
                            style={{ flex: 1 }}
                        >
                            <option value="">Select a file...</option>
                            {files.map(file => (
                                <option key={file.name} value={file.name}>{file.name}</option>
                            ))}
                        </select>

                        {/* File Upload Input */}
                        <label
                            className="save-btn"
                            style={{
                                cursor: 'pointer',
                                margin: 0,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                padding: '0.5rem 1rem',
                                fontSize: '0.9rem'
                            }}
                            title="Upload new file to MinIO"
                        >
                            📤 Upload
                            <input
                                type="file"
                                onChange={handleFileUpload}
                                style={{ display: 'none' }}
                                accept=".txt,.md,.vtt,.srt" // Suggest text-related files
                            />
                        </label>

                        <button
                            type="button"
                            onClick={handlePreview}
                            className="view-btn"
                            disabled={!inputFile}
                            style={{
                                padding: '0.5rem 0.8rem', // Adjusted padding
                                color: inputFile ? '#4caf50' : '#666',
                                borderColor: inputFile ? '#4caf50' : '#666',
                                cursor: inputFile ? 'pointer' : 'not-allowed',
                                display: 'flex',
                                alignItems: 'center'
                            }}
                            title="Preview file content"
                        >
                            👁️
                        </button>
                    </div>
                </div>

                <div style={{ display: 'flex', gap: '1rem' }}>
                    <div className="form-group" style={{ flex: 1 }}>
                        <label>Source Language</label>
                        <select value={srcLang} onChange={(e) => setSrcLang(e.target.value)}>
                            <option value="auto">자동 감지 (Auto Detect)</option>
                            <option value="en">영어</option>
                            <option value="ko">한국어</option>
                            <option value="ja">일본어</option>
                            <option value="zh">중국어</option>
                        </select>
                    </div>

                    <div className="form-group" style={{ flex: 1 }}>
                        <label>Target Language</label>
                        <select value={targetLang} onChange={(e) => setTargetLang(e.target.value)}>
                            <option value="ko">Korean</option>
                            <option value="en">English</option>
                            <option value="ja">Japanese</option>
                            <option value="zh">Chinese</option>
                        </select>
                    </div>
                </div>

                <div className="button-group">
                    <button type="button" onClick={() => setIsTemplateModalOpen(true)} className="save-btn" style={{ marginRight: '10px' }}>
                        ⚙️ 템플릿 편집
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

            {/* File Preview Modal */}
            {viewingFile && (
                <div className="modal-overlay" onClick={closePreview}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>File Preview: {viewingFile}</h3>
                            <button className="close-btn" onClick={closePreview}>✕</button>
                        </div>
                        <div className="modal-body">
                            <pre className="text-content">{fileContent}</pre>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default TranslationForm;
