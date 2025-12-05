import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useLLM } from '../../../context/LLMContext';

const SimpleTranslationForm = () => {
    const [inputText, setInputText] = useState('');
    const [outputText, setOutputText] = useState('');
    const [targetLang, setTargetLang] = useState('auto');
    const [systemPrompt, setSystemPrompt] = useState('');
    const [loading, setLoading] = useState(false);

    const { configs, selectedConfigId, setSelectedConfigId, getSelectedConfig } = useLLM();

    const PRESETS = {
        default: {
            label: '기본 (Default)',
            prompt: 'You are a professional translator. Translate the following text into {target_lang} naturally.'
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

    useEffect(() => {
        loadDefaultTemplate();
    }, []);

    const loadDefaultTemplate = async () => {
        try {
            // Fetch default template to pre-fill system prompt if empty
            const templateResponse = await axios.get('http://localhost:8000/api/template');
            if (templateResponse.data.system_prompt) {
                setSystemPrompt(templateResponse.data.system_prompt);
            }
        } catch (err) {
            console.error('Failed to load default template:', err);
        }
    };

    const handlePresetChange = (e) => {
        const presetKey = e.target.value;
        if (presetKey && PRESETS[presetKey]) {
            setSystemPrompt(PRESETS[presetKey].prompt);
        }
    };

    const handleTranslate = async (e) => {
        e.preventDefault();
        if (!inputText.trim()) return;

        const selectedConfig = getSelectedConfig();
        if (!selectedConfig) {
            alert('Please select an LLM configuration first.');
            return;
        }

        setLoading(true);
        try {
            const response = await axios.post('http://localhost:8000/api/translate/simple', {
                text: inputText,
                target_lang: targetLang,
                openwebui_url: selectedConfig.openwebui_url,
                api_key: selectedConfig.api_key,
                model: selectedConfig.model,
                system_prompt: systemPrompt
            });
            setOutputText(response.data.translated_text);
        } catch (err) {
            console.error('Translation failed:', err);
            alert('Translation failed: ' + (err.response?.data?.detail || err.message));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="card">
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
                <label>System Prompt (시스템 프롬프트)</label>
                <div style={{ marginBottom: '0.5rem' }}>
                    <select
                        onChange={handlePresetChange}
                        style={{ padding: '0.3rem', borderRadius: '4px', border: '1px solid #555', width: '100%', backgroundColor: '#333', color: 'white' }}
                        defaultValue=""
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

                <div className="form-group">
                    <label>목표 언어</label>
                    <select value={targetLang} onChange={(e) => setTargetLang(e.target.value)} style={{ width: '100%', padding: '0.5rem', backgroundColor: '#333', color: 'white', border: '1px solid #555' }}>
                        <option value="auto">자동 (Auto: En↔Ko)</option>
                        <option value="ko">한국어</option>
                        <option value="en">영어</option>
                        <option value="ja">일본어</option>
                        <option value="zh">중국어</option>
                    </select>
                </div>

                <button type="submit" disabled={loading} style={{ width: '100%', marginBottom: '1.5rem' }}>
                    {loading ? '번역 중...' : '번역하기'}
                </button>

                <div className="form-group">
                    <label>번역 결과</label>
                    <textarea
                        value={outputText}
                        readOnly
                        placeholder="번역 결과가 여기에 표시됩니다..."
                        rows={6}
                        style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #555', backgroundColor: '#333', color: 'white' }}
                    />
                </div>
            </form>
        </div>
    );
};

export default SimpleTranslationForm;
