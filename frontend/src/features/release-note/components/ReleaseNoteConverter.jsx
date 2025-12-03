import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import './ReleaseNote.css';
import TemplateEditor from './TemplateEditor';

const ReleaseNoteConverter = () => {
    const navigate = useNavigate();
    const [inputText, setInputText] = useState('');
    const [result, setResult] = useState('');
    const [loading, setLoading] = useState(false);
    const [settings, setSettings] = useState({
        openwebui_url: '',
        api_key: '',
        model: ''
    });
    const [isTemplateModalOpen, setIsTemplateModalOpen] = useState(false);
    const [showHelp, setShowHelp] = useState(false);

    useEffect(() => {
        loadSettings();
    }, []);

    // ... (loadSettings, handleSettingsChange, handleConvert, loadExample, copyToClipboard functions remain same)

    const loadSettings = async () => {
        try {
            const response = await axios.get('http://localhost:8000/api/settings');
            setSettings({
                openwebui_url: response.data.openwebui_url || '',
                api_key: response.data.api_key || '',
                model: response.data.model || ''
            });
        } catch (err) {
            console.error('Failed to load settings:', err);
        }
    };

    const handleSettingsChange = (e) => {
        setSettings({
            ...settings,
            [e.target.name]: e.target.value
        });
    };

    const handleConvert = async () => {
        if (!inputText.trim()) {
            alert('변환할 텍스트를 입력해주세요.');
            return;
        }
        if (!settings.openwebui_url || !settings.api_key || !settings.model) {
            alert('설정(URL, API Key, Model)을 모두 입력해주세요.');
            return;
        }

        setLoading(true);
        try {
            const response = await axios.post('http://localhost:8000/api/release-note/convert', {
                input_text: inputText,
                openwebui_url: settings.openwebui_url,
                api_key: settings.api_key,
                model: settings.model
            });
            setResult(response.data.result);
        } catch (err) {
            alert('변환 실패: ' + (err.response?.data?.detail || err.message));
        } finally {
            setLoading(false);
        }
    };

    const loadExample = (type) => {
        if (type === 1) {
            setInputText("PG 오류 메세지를 GPT가 정상적으로 해석하여 저장 못 하는 이슈 수정");
        } else if (type === 2) {
            setInputText("PG 결제 시 면세 가격 입력 필드 연동");
        }
    };

    const copyToClipboard = () => {
        if (!result) return;
        navigator.clipboard.writeText(result);
        alert('클립보드에 복사되었습니다.');
    };

    return (
        <div className="rn-container">
            <header className="rn-header">
                <button className="rn-back-btn" onClick={() => navigate('/')}>← Home</button>
                <h1>릴리즈 노트 변환기</h1>
                <button className="rn-help-btn" onClick={() => setShowHelp(!showHelp)}>
                    {showHelp ? '닫기' : '사용 방법'}
                </button>
            </header>

            {showHelp && (
                <div className="rn-help-section">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                        <h3 style={{ margin: 0 }}>📖 사용 방법</h3>
                        <button
                            onClick={() => setShowHelp(false)}
                            style={{
                                background: 'none',
                                border: 'none',
                                fontSize: '1.2rem',
                                cursor: 'pointer',
                                color: 'var(--rn-text-secondary)',
                                padding: '0.5rem'
                            }}
                        >
                            ✕
                        </button>
                    </div>
                    <div className="rn-help-content">
                        <div className="rn-help-item">
                            <h4>1️⃣ 설정 입력</h4>
                            <ul>
                                <li><strong>OpenWebUI URL</strong>: LLM 서버 주소 (예: http://localhost:3000)</li>
                                <li><strong>API Key</strong>: 인증 키</li>
                                <li><strong>Model</strong>: 사용할 모델명 (예: gpt-4)</li>
                            </ul>
                        </div>
                        <div className="rn-help-item">
                            <h4>2️⃣ 텍스트 입력 및 변환</h4>
                            <ul>
                                <li>왼쪽 <strong>개발자 원본 텍스트</strong> 창에 기능 업데이트 내용을 입력합니다.</li>
                                <li><strong>✨ 변환하기</strong> 버튼을 클릭하면 AI가 고객 친화적인 릴리즈 노트로 변환합니다.</li>
                                <li><strong>⚙️ 템플릿 편집</strong>에서 AI 프롬프트를 수정할 수 있습니다.</li>
                            </ul>
                        </div>
                        <div className="rn-help-item">
                            <h4>3️⃣ 결과 활용</h4>
                            <ul>
                                <li>오른쪽 <strong>변환 결과</strong> 창에서 변환된 내용을 확인합니다.</li>
                                <li><strong>📋 복사</strong> 버튼으로 결과를 클립보드에 복사하여 사용합니다.</li>
                            </ul>
                        </div>
                    </div>
                </div>
            )}

            <div className="rn-settings-panel">
                <div className="rn-settings-grid">
                    <div className="rn-input-group">
                        <label className="rn-label">OpenWebUI URL</label>
                        <input
                            type="text"
                            className="rn-input"
                            name="openwebui_url"
                            value={settings.openwebui_url}
                            onChange={handleSettingsChange}
                            placeholder="http://localhost:3000"
                        />
                    </div>
                    <div className="rn-input-group">
                        <label className="rn-label">API Key</label>
                        <input
                            type="password"
                            className="rn-input"
                            name="api_key"
                            value={settings.api_key}
                            onChange={handleSettingsChange}
                            placeholder="sk-..."
                        />
                    </div>
                    <div className="rn-input-group">
                        <label className="rn-label">Model</label>
                        <input
                            type="text"
                            className="rn-input"
                            name="model"
                            value={settings.model}
                            onChange={handleSettingsChange}
                            placeholder="gpt-4"
                        />
                    </div>
                </div>
            </div>

            <main className="rn-main-content">
                {/* Left Column */}
                <div className="rn-column">
                    <div className="rn-card">
                        <div className="rn-card-header">
                            <h2 className="rn-card-title">📝 개발자 원본 텍스트</h2>
                            <div style={{ display: 'flex', gap: '0.5rem' }}>
                                <button className="rn-btn rn-btn-text" onClick={() => loadExample(1)}>예제 1</button>
                                <button className="rn-btn rn-btn-text" onClick={() => loadExample(2)}>예제 2</button>
                            </div>
                        </div>
                        <textarea
                            className="rn-textarea"
                            placeholder="여기에 개발팀이 전달한 기능 업데이트 내용을 입력하세요..."
                            value={inputText}
                            onChange={(e) => setInputText(e.target.value)}
                        />
                    </div>
                    <div className="rn-controls">
                        <button className="rn-btn rn-btn-secondary" onClick={() => setIsTemplateModalOpen(true)}>
                            ⚙️ 템플릿 편집
                        </button>
                        <button className="rn-btn rn-btn-primary" onClick={handleConvert} disabled={loading}>
                            {loading ? '✨ 변환 중...' : '✨ 변환하기'}
                        </button>
                    </div>
                </div>

                {/* Right Column */}
                <div className="rn-column">
                    <div className="rn-card">
                        <div className="rn-card-header">
                            <h2 className="rn-card-title">🎁 변환 결과</h2>
                            <button className="rn-btn rn-btn-text" onClick={copyToClipboard} disabled={!result}>
                                📋 복사
                            </button>
                        </div>
                        <div className="rn-textarea rn-result-area">
                            {result ? (
                                <div className="rn-result-content">
                                    <ReactMarkdown>{result}</ReactMarkdown>
                                </div>
                            ) : (
                                <div style={{ color: 'var(--rn-text-secondary)', textAlign: 'center', marginTop: '2rem' }}>
                                    아직 변환된 결과가 없습니다.<br />
                                    왼쪽에서 텍스트를 입력하고 변환 버튼을 눌러주세요.
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </main>

            <TemplateEditor
                isOpen={isTemplateModalOpen}
                onClose={() => setIsTemplateModalOpen(false)}
            />
        </div>
    );
};

export default ReleaseNoteConverter;
