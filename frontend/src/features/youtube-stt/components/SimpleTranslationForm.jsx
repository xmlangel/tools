import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useLLM } from '../../../context/LLMContext';
import { API_URL } from '../../../config';

const MODES = {
    TEXT: 'text',
    DOCUMENTS: 'documents'
};

const LANGUAGES = [
    { code: 'auto', nameSrc: '자동 감지', nameTgt: '자동 (En↔Ko)' },
    { code: 'ko', name: '한국어' },
    { code: 'en', name: '영어' },
    { code: 'ja', name: '일본어' },
    { code: 'zh', name: '중국어' }
];

const PRESETS = {
    default: {
        label: '전문적 번역 (Professional)',
        prompt: 'You are a professional {source_lang} ({src_lang_code}) to {target_lang} ({tgt_lang_code}) translator. Your goal is to accurately convey the meaning and nuances of the original {source_lang} text while adhering to {target_lang} grammar, vocabulary, and cultural sensitivities. Produce only the {target_lang} translation, without any additional explanations or commentary.'
    }
};

const SimpleTranslationForm = ({ onJobCreated }) => {
    const [mode, setMode] = useState(MODES.TEXT);
    const [inputText, setInputText] = useState('');
    const [outputText, setOutputText] = useState('');
    const [srcLang, setSrcLang] = useState('auto');
    const [targetLang, setTargetLang] = useState('auto');
    const [loading, setLoading] = useState(false);
    const [isFullScreen, setIsFullScreen] = useState(false);
    const [toast, setToast] = useState({ show: false, message: '' });
    const [uploadedFile, setUploadedFile] = useState(null);

    const { configs, selectedConfigId, setSelectedConfigId, getSelectedConfig, getTranslationDefaultConfig } = useLLM();
    const fileInputRef = useRef(null);

    // Auto-select translation default config on mount
    useEffect(() => {
        const transDefault = getTranslationDefaultConfig();
        if (transDefault && configs.length > 0) {
            setSelectedConfigId(transDefault.id);
        }
    }, [configs.length]);

    // Auto-translation for TEXT mode
    useEffect(() => {
        if (mode !== MODES.TEXT || !inputText.trim()) {
            if (mode === MODES.TEXT) setOutputText('');
            return;
        }

        const selectedConfig = getSelectedConfig();
        if (!selectedConfig) return;

        const timer = setTimeout(async () => {
            setLoading(true);
            try {
                const response = await axios.post(`${API_URL}/api/translate/simple`, {
                    text: inputText,
                    target_lang: targetLang,
                    src_lang: srcLang,
                    provider: selectedConfig.provider,
                    api_url: selectedConfig.api_url,
                    api_key: selectedConfig.api_key,
                    model: selectedConfig.model,
                    system_prompt: PRESETS.default.prompt
                });
                setOutputText(response.data.translated_text);

                // Trigger Recent Jobs update
                if (response.data.job && onJobCreated) {
                    onJobCreated(response.data.job);
                }
            } catch (err) {
                console.error('Translation failed:', err);
            } finally {
                setLoading(false);
            }
        }, 800);

        return () => clearTimeout(timer);
    }, [inputText, srcLang, targetLang, mode, selectedConfigId]);

    const handleFileUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setUploadedFile(file);
        const selectedConfig = getSelectedConfig();
        if (!selectedConfig) {
            alert('LLM 설정을 먼저 선택해주세요.');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('target_lang', targetLang);
        formData.append('src_lang', srcLang);
        formData.append('provider', selectedConfig.provider);
        formData.append('api_url', selectedConfig.api_url);
        formData.append('api_key', selectedConfig.api_key);
        formData.append('model', selectedConfig.model);
        formData.append('system_prompt', PRESETS.default.prompt);

        setLoading(true);
        try {
            const response = await axios.post(`${API_URL}/api/translate/file`, formData);
            setOutputText(response.data.translated_text);
            // Show extracted original text too
            setInputText(response.data.original_text);

            // Trigger Recent Jobs update
            if (response.data.job && onJobCreated) {
                onJobCreated(response.data.job);
            }
        } catch (err) {
            console.error('File translation failed:', err);
            let errorMessage = '파일 번역에 실패했습니다';

            if (err.response?.data?.detail) {
                const detail = err.response.data.detail;
                if (typeof detail === 'string') {
                    errorMessage += `: ${detail}`;
                } else if (Array.isArray(detail)) {
                    // FastAPI validation errors
                    const msg = detail.map(d => `${d.loc.join('.')}: ${d.msg}`).join(', ');
                    errorMessage += `: ${msg}`;
                } else {
                    errorMessage += `: ${JSON.stringify(detail)}`;
                }
            } else {
                errorMessage += `: ${err.message}`;
            }
            alert(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    const handleCopy = () => {
        if (!outputText) return;
        navigator.clipboard.writeText(outputText).then(() => {
            setToast({ show: true, message: '클립보드에 복사되었습니다.' });
            setTimeout(() => setToast({ show: false, message: '' }), 3000);
        });
    };

    const clearInput = () => {
        setInputText('');
        setOutputText('');
        setUploadedFile(null);
        if (fileInputRef.current) fileInputRef.current.value = '';
    };

    return (
        <div style={{ width: '100%', color: '#eee', padding: '0 20px' }}>
            {/* Mode Select Tabs */}
            <div style={{ display: 'flex', gap: '8px', marginBottom: '12px', borderBottom: '1px solid #444', paddingBottom: '8px' }}>
                <button
                    onClick={() => { setMode(MODES.TEXT); clearInput(); }}
                    style={{ ...tabBtnStyle, color: mode === MODES.TEXT ? 'var(--primary-color)' : '#aaa', borderBottom: mode === MODES.TEXT ? '2px solid var(--primary-color)' : 'none' }}
                >
                    <span style={{ marginRight: '6px' }}>⌨️</span> 텍스트
                </button>
                <button
                    onClick={() => { setMode(MODES.DOCUMENTS); clearInput(); }}
                    style={{ ...tabBtnStyle, color: mode === MODES.DOCUMENTS ? 'var(--primary-color)' : '#aaa', borderBottom: mode === MODES.DOCUMENTS ? '2px solid var(--primary-color)' : 'none' }}
                >
                    <span style={{ marginRight: '6px' }}>📄</span> 문서
                </button>
            </div>

            {/* LLM Config Select (Compact) */}
            <div style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span style={{ fontSize: '0.9rem', color: '#aaa' }}>LLM:</span>
                <select
                    value={selectedConfigId || ''}
                    onChange={(e) => setSelectedConfigId(Number(e.target.value))}
                    style={{ background: '#222', border: '1px solid #444', color: 'white', padding: '4px 8px', borderRadius: '4px', fontSize: '0.9rem' }}
                >
                    {configs.map(config => (
                        <option key={config.id} value={config.id}>{config.name} ({config.model})</option>
                    ))}
                </select>
            </div>

            {/* Side-by-Side Container */}
            <div style={{ display: 'flex', gap: '0', backgroundColor: '#1e1e1e', borderRadius: '8px', overflow: 'hidden', border: '1px solid #333', minHeight: '650px' }}>

                {/* Left Side: Input */}
                <div style={{ flex: 1, borderRight: '1px solid #333', display: 'flex', flexDirection: 'column' }}>
                    {/* Source Lang Bar */}
                    <div style={langBarStyle}>
                        {LANGUAGES.slice(0, 5).map(lang => (
                            <button
                                key={lang.code}
                                onClick={() => setSrcLang(lang.code)}
                                style={{ ...langBtnStyle, color: srcLang === lang.code ? 'var(--primary-color)' : '#eee' }}
                            >
                                {lang.nameSrc || lang.name}
                            </button>
                        ))}
                    </div>

                    {/* Input Content */}
                    <div style={{ position: 'relative', flex: 1, padding: '16px', display: 'flex', flexDirection: 'column' }}>
                        {mode === MODES.TEXT || inputText ? (
                            <textarea
                                value={inputText}
                                onChange={(e) => setInputText(e.target.value)}
                                placeholder="텍스트 입력"
                                style={textAreaStyle}
                            />
                        ) : (
                            <div style={uploadBoxStyle} onClick={() => fileInputRef.current.click()}>
                                <input
                                    type="file"
                                    ref={fileInputRef}
                                    onChange={handleFileUpload}
                                    style={{ display: 'none' }}
                                    accept=".pdf,.txt,.md"
                                />
                                <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📁</div>
                                <div style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>파일 선택</div>
                                <div style={{ color: '#aaa', marginTop: '8px' }}>
                                    컴퓨터에서 .pdf, .txt, .md 파일을 찾아보세요
                                </div>
                            </div>
                        )}
                        {uploadedFile && (
                            <div style={{ marginTop: '16px', padding: '8px', background: '#333', borderRadius: '4px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontSize: '0.9rem' }}>📎 {uploadedFile.name}</span>
                                <button onClick={clearInput} style={{ background: 'none', border: 'none', color: '#ff6b6b', cursor: 'pointer' }}>✕</button>
                            </div>
                        )}
                        {inputText && mode === MODES.TEXT && (
                            <button onClick={clearInput} style={{ position: 'absolute', top: '16px', right: '16px', background: 'none', border: 'none', color: '#aaa', cursor: 'pointer', fontSize: '1.2rem', zIndex: 10 }}>&times;</button>
                        )}
                        {mode === MODES.TEXT && (
                            <div style={{ position: 'absolute', bottom: '16px', left: '16px', color: '#666', fontSize: '0.8rem' }}>
                                {inputText.length} / 5000
                            </div>
                        )}
                    </div>
                </div>

                {/* Right Side: Output */}
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', backgroundColor: '#2b2d31' }}>
                    {/* Target Lang Bar */}
                    <div style={langBarStyle}>
                        {LANGUAGES.slice(0, 5).map(lang => (
                            <button
                                key={lang.code}
                                onClick={() => setTargetLang(lang.code)}
                                style={{ ...langBtnStyle, color: targetLang === lang.code ? 'var(--primary-color)' : '#eee' }}
                            >
                                {lang.nameTgt || lang.name}
                            </button>
                        ))}
                    </div>

                    {/* Output Content */}
                    <div style={{ position: 'relative', flex: 1, padding: '16px' }}>
                        {loading ? (
                            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                                <div className="spinner"></div>
                            </div>
                        ) : (
                            <div style={{ ...textAreaStyle, color: outputText ? 'white' : '#777', cursor: 'text', userSelect: 'text', whiteSpace: 'pre-wrap' }}>
                                {outputText || '번역 결과'}
                            </div>
                        )}

                        {/* Output Actions */}
                        <div style={{ position: 'absolute', bottom: '16px', right: '16px', display: 'flex', gap: '12px' }}>
                            <button onClick={handleCopy} style={actionBtnStyle} title="복사">📋</button>
                            <button onClick={() => setIsFullScreen(true)} style={actionBtnStyle} title="전체화면">⤢</button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Full Screen Modal */}
            {isFullScreen && (
                <div style={fullScreenOverlayStyle}>
                    <div style={fullScreenHeaderStyle}>
                        <h2 style={{ margin: 0, color: 'var(--primary-color)' }}>전체화면 번역 결과</h2>
                        <div style={{ display: 'flex', gap: '12px' }}>
                            <button onClick={handleCopy} style={primaryBtnStyle}>📋 결과 복사</button>
                            <button onClick={() => setIsFullScreen(false)} style={closeBtnStyle}>&times;</button>
                        </div>
                    </div>
                    <div style={fullScreenContentStyle}>
                        {outputText}
                    </div>
                </div>
            )}

            {/* Toast Notification */}
            {toast.show && (
                <div style={toastStyle}>{toast.message}</div>
            )}

            {/* Spinner Styles */}
            <style>
                {`
                @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
                .spinner {
                    width: 24px; height: 24px;
                    border: 3px solid rgba(100, 108, 255, 0.3);
                    border-top: 3px solid var(--primary-color);
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                }
                @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
                `}
            </style>
        </div>
    );
};

// Styles
const tabBtnStyle = {
    background: 'none', border: 'none', padding: '8px 16px', cursor: 'pointer',
    fontSize: '0.95rem', fontWeight: '500', transition: 'all 0.2s', outline: 'none'
};

const langBarStyle = {
    display: 'flex', alignItems: 'center', height: '48px',
    borderBottom: '1px solid #333', padding: '0 8px', gap: '4px'
};

const langBtnStyle = {
    background: 'none', border: 'none', padding: '4px 12px', cursor: 'pointer',
    fontSize: '0.85rem', fontWeight: '500', borderRadius: '4px', outline: 'none'
};

const textAreaStyle = {
    width: '100%', height: '100%', background: 'none', border: 'none',
    color: 'white', resize: 'none', fontSize: '1.2rem', lineHeight: '1.5',
    outline: 'none', overflowY: 'auto', textAlign: 'left'
};

const uploadBoxStyle = {
    height: '100%', display: 'flex', flexDirection: 'column',
    justifyContent: 'center', alignItems: 'center', cursor: 'pointer',
    border: '2px dashed #444', borderRadius: '12px', padding: '40px',
    transition: 'all 0.2s', backgroundColor: 'rgba(255,255,255,0.02)'
};

const actionBtnStyle = {
    background: 'rgba(255,255,255,0.05)', border: '1px solid #444', color: '#aaa', cursor: 'pointer',
    fontSize: '1.1rem', padding: '6px', borderRadius: '6px', transition: 'all 0.2s'
};

const fullScreenOverlayStyle = {
    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.95)', zIndex: 2000,
    display: 'flex', flexDirection: 'column', padding: '2rem', animation: 'fadeIn 0.3s'
};

const fullScreenHeaderStyle = {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    marginBottom: '1.5rem', borderBottom: '1px solid #333', paddingBottom: '1rem'
};

const fullScreenContentStyle = {
    flex: 1, overflowY: 'auto', fontSize: '1.25rem', lineHeight: '1.8',
    color: '#eee', padding: '1.5rem', backgroundColor: '#1a1a1a',
    borderRadius: '8px', whiteSpace: 'pre-wrap', border: '1px solid #333', textAlign: 'left'
};

const primaryBtnStyle = {
    background: 'var(--primary-color)', color: 'white', border: 'none',
    padding: '10px 20px', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold'
};

const closeBtnStyle = {
    background: 'none', border: '1px solid #555', color: 'white',
    fontSize: '2rem', cursor: 'pointer', lineHeight: 1, padding: '0 12px', borderRadius: '6px'
};

const toastStyle = {
    position: 'fixed', bottom: '2rem', left: '50%', transform: 'translateX(-50%)',
    backgroundColor: 'rgba(0,0,0,0.9)', color: 'white', padding: '10px 20px',
    borderRadius: '8px', zIndex: 3000, animation: 'fadeIn 0.3s', border: '1px solid #444'
};

export default SimpleTranslationForm;
