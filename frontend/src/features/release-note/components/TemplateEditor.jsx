import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_URL } from '../../../config';

const TemplateEditor = ({ isOpen, onClose }) => {
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
            const response = await axios.get(`${API_URL}/api/release-note/template`);
            setTemplate(response.data);
        } catch (err) {
            console.error('Failed to fetch template:', err);
        }
    };

    const handleSave = async () => {
        setLoading(true);
        try {
            await axios.post(`${API_URL}/api/release-note/template`, template);
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
            // 기본값은 백엔드에서 처리하거나 여기서 하드코딩할 수 있음.
            // 여기서는 단순히 재조회로 처리 (백엔드에 리셋 API가 없으므로)
            // 실제로는 백엔드에 리셋 로직이 필요할 수 있음.
            // 임시로 기본값 하드코딩
            setTemplate({
                system_prompt: "너는 스티브 잡스 같은 통찰력을 가진 'IT 제품 전문 마케터'야. 개발팀이 준 건조한 '기능 업데이트' 내용을, 고객이 듣고 설레할 만한 '고객 혜택 중심'의 릴리즈 노트로 바꿔줘.",
                user_prompt_template: `[변환 공식]
1. 기능(Feature): 무엇이 바뀌었나? (사실 위주)
2. 장점(Advantage): 기술적으로 무엇이 더 좋아졌나?
3. 혜택(Benefit): 결국 고객의 삶(돈/시간/감정)이 어떻게 나아졌나? (★이걸 매력적인 헤드라인으로 뽑아줘)

[입력: 개발팀 전달 사항]
{input_text}

[출력 양식]
헤드라인: (Benefit을 강조한 한 줄 카피)
상세 설명: (고객이 얻게 될 변화를 중심으로 2~3문장)
FAB 분석:
- Feature: ...
- Advantage: ...
- Benefit: ...`
            });
        }
    };

    if (!isOpen) return null;

    return (
        <div className="rn-modal-overlay" onClick={onClose}>
            <div className="rn-modal" onClick={e => e.stopPropagation()}>
                <div className="rn-modal-header">
                    <h2 className="rn-modal-title">템플릿 편집</h2>
                    <button className="rn-btn rn-btn-text" onClick={onClose}>✕</button>
                </div>

                <div className="rn-input-group" style={{ marginBottom: '1.5rem' }}>
                    <label className="rn-label">시스템 프롬프트 (AI 페르소나)</label>
                    <textarea
                        className="rn-input"
                        style={{ minHeight: '80px', resize: 'vertical' }}
                        value={template.system_prompt}
                        onChange={e => setTemplate({ ...template, system_prompt: e.target.value })}
                    />
                </div>

                <div className="rn-input-group" style={{ marginBottom: '2rem' }}>
                    <label className="rn-label">유저 프롬프트 템플릿 ({'{input_text}'}는 필수)</label>
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

export default TemplateEditor;
