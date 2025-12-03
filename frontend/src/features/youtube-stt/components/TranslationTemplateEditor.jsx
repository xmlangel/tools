import React, { useState, useEffect } from 'react';
import axios from 'axios';

const TranslationTemplateEditor = ({ isOpen, onClose }) => {
    const [template, setTemplate] = useState({
        system_prompt: '',
        user_prompt_template: ''
    });
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (isOpen) {
            fetchTemplate();
        }
    }, [isOpen]);

    const fetchTemplate = async () => {
        try {
            const response = await axios.get('http://localhost:8000/api/translate/template');
            setTemplate(response.data);
        } catch (err) {
            console.error('Failed to fetch template:', err);
        }
    };

    const handleSave = async () => {
        setLoading(true);
        try {
            await axios.post('http://localhost:8000/api/translate/template', template);
            alert('템플릿이 저장되었습니다.');
            onClose();
        } catch (err) {
            alert('템플릿 저장 실패: ' + err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleReset = async () => {
        if (window.confirm('기본 템플릿으로 초기화하시겠습니까?')) {
            setTemplate({
                system_prompt: "You are a professional translator. Translate the following text into Korean naturally.",
                user_prompt_template: `다음 텍스트를 한국어로 번역해줘. 문맥을 고려해서 자연스럽게 번역하고, 번역된 결과만 출력해. 설명이나 잡담은 하지 마.

[텍스트 시작]
{text}
[텍스트 끝]`
            });
        }
    };

    if (!isOpen) return null;

    return (
        <div className="rn-modal-overlay" onClick={onClose}>
            <div className="rn-modal" onClick={e => e.stopPropagation()}>
                <div className="rn-modal-header">
                    <h2 className="rn-modal-title">번역 템플릿 편집</h2>
                    <button className="rn-btn rn-btn-text" onClick={onClose}>✕</button>
                </div>

                <div className="rn-input-group" style={{ marginBottom: '1.5rem' }}>
                    <label className="rn-label">시스템 프롬프트 (System Prompt)</label>
                    <textarea
                        className="rn-input"
                        style={{ minHeight: '80px', resize: 'vertical' }}
                        value={template.system_prompt}
                        onChange={e => setTemplate({ ...template, system_prompt: e.target.value })}
                    />
                </div>

                <div className="rn-input-group" style={{ marginBottom: '2rem' }}>
                    <label className="rn-label">유저 프롬프트 템플릿 ({'{text}'}는 필수)</label>
                    <textarea
                        className="rn-input"
                        style={{ minHeight: '300px', resize: 'vertical', fontFamily: 'monospace' }}
                        value={template.user_prompt_template}
                        onChange={e => setTemplate({ ...template, user_prompt_template: e.target.value })}
                    />
                </div>

                <div className="rn-controls" style={{ justifyContent: 'space-between' }}>
                    <button className="rn-btn rn-btn-text" onClick={handleReset}>
                        기본값 복원
                    </button>
                    <div style={{ display: 'flex', gap: '1rem' }}>
                        <button className="rn-btn rn-btn-secondary" onClick={onClose}>
                            취소
                        </button>
                        <button className="rn-btn rn-btn-primary" onClick={handleSave} disabled={loading}>
                            {loading ? '저장 중...' : '저장하기'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default TranslationTemplateEditor;
