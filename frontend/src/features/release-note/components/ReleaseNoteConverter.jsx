import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import './ReleaseNote.css';
import TemplateEditor from './TemplateEditor';
import { useLLM } from '../../../context/LLMContext';
import { API_URL } from '../../../config';

const ReleaseNoteConverter = () => {
    const navigate = useNavigate();
    const [inputText, setInputText] = useState('');
    const [result, setResult] = useState('');
    const [loading, setLoading] = useState(false);
    const [isTemplateModalOpen, setIsTemplateModalOpen] = useState(false);
    const [showHelp, setShowHelp] = useState(false);
    const [activeTab, setActiveTab] = useState('editor');

    const { configs, selectedConfigId, setSelectedConfigId, getSelectedConfig } = useLLM();

    const handleConvert = async () => {
        if (!inputText.trim()) {
            alert('변환할 텍스트를 입력해주세요.');
            return;
        }

        const selectedConfig = getSelectedConfig();
        if (!selectedConfig) {
            alert('Please select an LLM configuration first.');
            return;
        }

        setLoading(true);
        try {
            const response = await axios.post(`${API_URL}/api/release-note/convert`, {
                input_text: inputText,
                openwebui_url: selectedConfig.openwebui_url,
                api_key: selectedConfig.api_key,
                model: selectedConfig.model
            });
            setResult(response.data.result);
            setActiveTab('viewer'); // Auto-switch to viewer
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
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <button className="rn-back-btn" onClick={() => navigate('/')}>← Home</button>
                    <h1>릴리즈 노트 변환기</h1>
                    <button className="rn-help-btn" onClick={() => setShowHelp(!showHelp)}>
                        {showHelp ? '닫기' : '사용 방법'}
                    </button>
                </div>
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
                            <h4>1️⃣ 설정 선택</h4>
                            <ul>
                                <li>우측 상단의 <strong>LLM Settings</strong>에서 LLM 설정을 추가하세요.</li>
                                <li><strong>Editor</strong> 탭의 툴바에서 사용할 설정을 선택하세요.</li>
                            </ul>
                        </div>
                        <div className="rn-help-item">
                            <h4>2️⃣ 텍스트 입력 및 변환</h4>
                            <ul>
                                <li><strong>Editor</strong> 탭에서 기능 업데이트 내용을 입력합니다.</li>
                                <li><strong>✨ 변환하기</strong> 버튼을 클릭하면 AI가 고객 친화적인 릴리즈 노트로 변환합니다.</li>
                                <li><strong>⚙️ 템플릿</strong> 버튼으로 AI 프롬프트를 수정할 수 있습니다.</li>
                            </ul>
                        </div>
                        <div className="rn-help-item">
                            <h4>3️⃣ 결과 활용</h4>
                            <ul>
                                <li>변환이 완료되면 자동으로 <strong>Viewer</strong> 탭으로 이동합니다.</li>
                                <li><strong>📋 복사</strong> 버튼으로 결과를 클립보드에 복사하여 사용합니다.</li>
                            </ul>
                        </div>
                    </div>
                </div>
            )}

            <div className="rn-tabs">
                <button
                    className={`rn-tab-btn ${activeTab === 'editor' ? 'active' : ''}`}
                    onClick={() => setActiveTab('editor')}
                >
                    Editor
                </button>
                <button
                    className={`rn-tab-btn ${activeTab === 'viewer' ? 'active' : ''}`}
                    onClick={() => setActiveTab('viewer')}
                >
                    Viewer
                </button>
            </div>

            <div className="rn-content">
                <div className="rn-card">
                    {activeTab === 'editor' ? (
                        <>
                            <div className="rn-toolbar">
                                <select
                                    className="rn-settings-select"
                                    value={selectedConfigId || ''}
                                    onChange={(e) => setSelectedConfigId(Number(e.target.value))}
                                >
                                    <option value="" disabled>Select LLM Configuration...</option>
                                    {configs.map(config => (
                                        <option key={config.id} value={config.id}>
                                            {config.name} ({config.model})
                                        </option>
                                    ))}
                                </select>
                                <button className="rn-toolbar-btn primary" onClick={handleConvert} disabled={loading}>
                                    {loading ? '✨ 변환 중...' : '✨ 변환하기'}
                                </button>
                                <button className="rn-toolbar-btn" onClick={() => setIsTemplateModalOpen(true)}>
                                    ⚙️ 템플릿
                                </button>
                                <button className="rn-toolbar-btn" onClick={() => loadExample(1)}>예제 1</button>
                                <button className="rn-toolbar-btn" onClick={() => loadExample(2)}>예제 2</button>
                                <button className="rn-toolbar-btn" onClick={() => setInputText('')}>Clear</button>
                            </div>
                            <textarea
                                className="rn-textarea"
                                placeholder="여기에 개발팀이 전달한 기능 업데이트 내용을 입력하세요..."
                                value={inputText}
                                onChange={(e) => setInputText(e.target.value)}
                            />
                        </>
                    ) : (
                        <>
                            <div className="rn-toolbar">
                                <button className="rn-toolbar-btn" onClick={copyToClipboard} disabled={!result}>
                                    📋 복사
                                </button>
                                <button className="rn-toolbar-btn" onClick={() => setActiveTab('editor')}>
                                    ✏️ 수정하기
                                </button>
                            </div>
                            <div className="rn-result-area">
                                {result ? (
                                    <div className="rn-result-content">
                                        <ReactMarkdown>{result}</ReactMarkdown>
                                    </div>
                                ) : (
                                    <div style={{ color: 'var(--rn-text-secondary)', textAlign: 'center', marginTop: '2rem' }}>
                                        아직 변환된 결과가 없습니다.<br />
                                        Editor 탭에서 텍스트를 입력하고 변환 버튼을 눌러주세요.
                                    </div>
                                )}
                            </div>
                        </>
                    )}
                </div>
            </div>

            <TemplateEditor
                isOpen={isTemplateModalOpen}
                onClose={() => setIsTemplateModalOpen(false)}
            />
        </div>
    );
};

export default ReleaseNoteConverter;
