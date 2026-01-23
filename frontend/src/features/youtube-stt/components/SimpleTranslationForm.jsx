import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useLLM } from '../../../context/LLMContext';
import { API_URL } from '../../../config';

const PRESETS = {
    default: {
        label: '전문적 번역 (Professional)',
        prompt: 'You are a professional {source_lang} ({src_lang_code}) to {target_lang} ({tgt_lang_code}) translator. Your goal is to accurately convey the meaning and nuances of the original {source_lang} text while adhering to {target_lang} grammar, vocabulary, and cultural sensitivities. Produce only the {target_lang} translation, without any additional explanations or commentary.'
    },
    native: {
        label: '원어민 스타일 (Native)',
        prompt: 'You are a helpful assistant. Rewrite the input text into natural, native-like {target_lang}. If the input is already in {target_lang}, refine it to sound more authentic and easy for locals to understand. Use idioms and casual phrasing where appropriate.'
    },
    business: {
        label: '비즈니스 (Business)',
        prompt: 'You are a professional assistant. Translate or refine the text into formal, professional {target_lang}. Use appropriate business terminology and polite tone.'
    }
};

const SimpleTranslationForm = () => {
    const [inputText, setInputText] = useState('');
    const [outputText, setOutputText] = useState('');
    const [targetLang, setTargetLang] = useState('auto');
    const [srcLang, setSrcLang] = useState('auto');
    const [systemPrompt, setSystemPrompt] = useState(PRESETS.default.prompt);
    const [loading, setLoading] = useState(false);
    const [isPromptExpanded, setIsPromptExpanded] = useState(false);
    const [isTargetLangExpanded, setIsTargetLangExpanded] = useState(false);

    const [toast, setToast] = useState({ show: false, message: '' });

    const { configs, selectedConfigId, setSelectedConfigId, getSelectedConfig } = useLLM();

    const handleCopy = () => {
        if (!outputText) return;
        navigator.clipboard.writeText(outputText).then(() => {
            setToast({ show: true, message: '클립보드에 복사되었습니다.' });
            setTimeout(() => setToast({ show: false, message: '' }), 3000);
        });
    };

    const handlePresetChange = (e) => {
        const presetKey = e.target.value;
        if (presetKey && PRESETS[presetKey]) {
            setSystemPrompt(PRESETS[presetKey].prompt);
        }
    };

    // Auto-translation logic with debounce
    useEffect(() => {
        if (!inputText.trim()) {
            setOutputText('');
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
                    system_prompt: systemPrompt
                });
                setOutputText(response.data.translated_text);
            } catch (err) {
                console.error('Translation failed:', err);
                // We don't want to alert on every debounce failure, but maybe show a small error in UI
            } finally {
                setLoading(false);
            }
        }, 800); // 800ms debounce

        return () => clearTimeout(timer);
    }, [inputText, srcLang, targetLang, systemPrompt, selectedConfigId]);

    const handleTranslate = (e) => {
        if (e) e.preventDefault();
        // Manual trigger if needed, though with auto-translate it's redundant.
    };

    const getCurrentPresetLabel = () => {
        const found = Object.values(PRESETS).find(p => p.prompt === systemPrompt);
        return found ? found.label : '사용자 정의 (Custom)';
    };

    return (
        <div className="card" style={{ position: 'relative' }}>
            {toast.show && (
                <div style={{
                    position: 'absolute',
                    top: '1rem',
                    left: '50%',
                    transform: 'translateX(-50%)',
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    color: 'white',
                    padding: '0.5rem 1rem',
                    borderRadius: '4px',
                    zIndex: 1000,
                    fontSize: '0.9rem',
                    animation: 'fadeIn 0.3s, fadeOut 0.3s 2.7s'
                }}>
                    {toast.message}
                </div>
            )}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h2 style={{ margin: 0 }}>간편 텍스트 번역</h2>
            </div>

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
                {selectedConfigId && getSelectedConfig() && (
                    <div style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: '#aaa' }}>
                        ℹ️ Using: <strong style={{ color: '#4caf50' }}>{getSelectedConfig().name}</strong> (Model: {getSelectedConfig().model})
                    </div>
                )}
            </div>

            <div className="form-group">
                <div
                    onClick={() => setIsPromptExpanded(!isPromptExpanded)}
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        cursor: 'pointer',
                        userSelect: 'none',
                        marginBottom: isPromptExpanded ? '0.5rem' : '0'
                    }}
                >
                    <span style={{ marginRight: '0.5rem', fontSize: '0.8rem' }}>
                        {isPromptExpanded ? '▼' : '▶'}
                    </span>
                    <label style={{ cursor: 'pointer', margin: 0 }}>System Prompt (시스템 프롬프트)</label>
                    <span style={{ marginLeft: '0.5rem', fontSize: '0.8rem', color: '#aaa' }}>
                        {isPromptExpanded ? '' : `(현재: ${getCurrentPresetLabel()}) (클릭하여 펼치기)`}
                    </span>
                </div>

                {isPromptExpanded && (
                    <div style={{ marginTop: '0.5rem', animation: 'fadeIn 0.2s' }}>
                        <div style={{ marginBottom: '0.5rem' }}>
                            <select
                                onChange={handlePresetChange}
                                style={{ padding: '0.3rem', borderRadius: '4px', border: '1px solid #555', width: '100%', backgroundColor: '#333', color: 'white' }}
                                defaultValue="business"
                            >
                                <option value="" disabled>프리셋 선택...</option>
                                {Object.entries(PRESETS).map(([key, preset]) => (
                                    <option key={key} value={key}>{preset.label}</option>
                                ))}
                            </select>
                        </div>
                        <textarea
                            value={systemPrompt}
                            onChange={(e) => setSystemPrompt(e.target.value)}
                            placeholder="You are a professional translator..."
                            rows={3}
                            style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #555', backgroundColor: '#333', color: 'white' }}
                        />
                        <p style={{ fontSize: '0.8rem', color: '#aaa', marginTop: '0.2rem' }}>
                            번역 시 사용할 시스템 프롬프트를 직접 수정할 수 있습니다.
                        </p>
                    </div>
                )}
            </div>

            <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem' }}>
                <div style={{ flex: 1 }}>
                    <div
                        onClick={() => setIsPromptExpanded(!isPromptExpanded)}
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            cursor: 'pointer',
                            userSelect: 'none',
                            marginBottom: isPromptExpanded ? '0.5rem' : '0'
                        }}
                    >
                        <span style={{ marginRight: '0.5rem', fontSize: '0.8rem' }}>
                            {isPromptExpanded ? '▼' : '▶'}
                        </span>
                        <label style={{ cursor: 'pointer', margin: 0 }}>원본 언어</label>
                    </div>
                    <select value={srcLang} onChange={(e) => setSrcLang(e.target.value)} style={{ width: '100%', padding: '0.5rem', backgroundColor: '#333', color: 'white', border: '1px solid #555', borderRadius: '4px', marginTop: '0.5rem' }}>
                        <option value="auto">자동 감지 (Auto Detect)</option>
                        <option value="en">영어 (English)</option>
                        <option value="ko">한국어 (Korean)</option>
                        <option value="ja">일본어 (Japanese)</option>
                        <option value="zh">중국어 (Chinese)</option>
                    </select>
                </div>

                <div style={{ flex: 1 }}>
                    <div
                        onClick={() => setIsTargetLangExpanded(!isTargetLangExpanded)}
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            cursor: 'pointer',
                            userSelect: 'none',
                            marginBottom: isTargetLangExpanded ? '0.5rem' : '0'
                        }}
                    >
                        <span style={{ marginRight: '0.5rem', fontSize: '0.8rem' }}>
                            {isTargetLangExpanded ? '▼' : '▶'}
                        </span>
                        <label style={{ cursor: 'pointer', margin: 0 }}>목표 언어</label>
                    </div>
                    <select value={targetLang} onChange={(e) => setTargetLang(e.target.value)} style={{ width: '100%', padding: '0.5rem', backgroundColor: '#333', color: 'white', border: '1px solid #555', borderRadius: '4px', marginTop: '0.5rem' }}>
                        <option value="auto">자동 (Auto: En↔Ko)</option>
                        <option value="ko">한국어 (Korean)</option>
                        <option value="en">영어 (English)</option>
                        <option value="ja">일본어 (Japanese)</option>
                        <option value="zh">중국어 (Chinese)</option>
                    </select>
                </div>
            </div>

            <form onSubmit={handleTranslate}>
                <div className="form-group">
                    <label>원본 텍스트</label>
                    <textarea
                        value={inputText}
                        onChange={(e) => setInputText(e.target.value)}
                        placeholder="번역할 텍스트를 입력하세요..."
                        rows={6}
                        style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #555', backgroundColor: '#333', color: 'white' }}
                        required
                    />
                </div>

                <div style={{
                    textAlign: 'center',
                    height: '2rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    marginBottom: '1rem',
                    color: '#4caf50',
                    fontSize: '0.9rem'
                }}>
                    {loading && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <span className="spinner" style={{
                                width: '12px',
                                height: '12px',
                                border: '2px solid #4caf50',
                                borderTop: '2px solid transparent',
                                borderRadius: '50%',
                                animation: 'spin 1s linear infinite'
                            }}></span>
                            번역 중...
                        </div>
                    )}
                </div>

                <div className="form-group">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                        <label style={{ margin: 0 }}>번역 결과</label>
                        <button
                            type="button"
                            onClick={handleCopy}
                            disabled={!outputText}
                            style={{
                                background: 'transparent',
                                border: '1px solid #555',
                                color: outputText ? 'white' : '#777',
                                padding: '0.2rem 0.6rem',
                                borderRadius: '4px',
                                cursor: outputText ? 'pointer' : 'not-allowed',
                                fontSize: '0.8rem'
                            }}
                        >
                            📋 복사
                        </button>
                    </div>
                    <textarea
                        value={outputText}
                        readOnly
                        placeholder="번역 결과가 여기에 표시됩니다..."
                        rows={6}
                        style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #555', backgroundColor: '#333', color: 'white' }}
                    />
                </div>
            </form>
            {/* Inline styles for spinner */}
            <style>
                {`
                @keyframes spin {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
                .spinner {
                    width: 12px;
                    height: 12px;
                    border: 2px solid #4caf50;
                    border-top: 2px solid transparent;
                    borderRadius: 50%;
                    animation: spin 1s linear infinite;
                }
                `}
            </style>
        </div>
    );
};

export default SimpleTranslationForm;
