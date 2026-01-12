import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_URL } from '../../../config';

const SummaryTemplateForm = () => {
    const [template, setTemplate] = useState({
        system_prompt: '',
        user_prompt_template: ''
    });
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');

    useEffect(() => {
        fetchTemplate();
    }, []);

    const fetchTemplate = async () => {
        try {
            const response = await axios.get(`${API_URL}/api/summary/template`);
            setTemplate(response.data);
        } catch (err) {
            console.error('Failed to fetch summary template:', err);
            setMessage('Failed to load template.');
        }
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setTemplate(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setMessage('');

        try {
            await axios.post(`${API_URL}/api/summary/template`, template);
            setMessage('Template saved successfully!');
            setTimeout(() => setMessage(''), 3000);
        } catch (err) {
            console.error('Failed to save template:', err);
            setMessage('Failed to save template.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="card">
            <h2>요약 템플릿 설정 (Summary Template)</h2>
            <p className="description" style={{ color: '#ccc', fontSize: '0.9rem', marginBottom: '1rem' }}>
                STT 작업 완료 후 자동으로 실행될 요약의 프롬프트를 설정합니다.
            </p>

            {message && (
                <div style={{
                    padding: '10px',
                    marginBottom: '15px',
                    borderRadius: '4px',
                    backgroundColor: message.includes('Failed') ? '#ff6b6b33' : '#4caf5033',
                    color: message.includes('Failed') ? '#ff6b6b' : '#4caf50',
                    border: `1px solid ${message.includes('Failed') ? '#ff6b6b' : '#4caf50'}`
                }}>
                    {message}
                </div>
            )}

            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label htmlFor="system_prompt">System Prompt</label>
                    <textarea
                        id="system_prompt"
                        name="system_prompt"
                        value={template.system_prompt}
                        onChange={handleChange}
                        rows={10}
                        style={{ width: '100%', fontFamily: 'monospace', padding: '10px', backgroundColor: '#2a2a2a', color: '#fff', border: '1px solid #555' }}
                        placeholder="Enter system prompt..."
                    />
                    <small style={{ color: '#888' }}>
                        AI의 페르소나와 요약 규칙을 정의합니다.
                    </small>
                </div>

                <div className="form-group" style={{ marginTop: '1.5rem' }}>
                    <label htmlFor="user_prompt_template">User Prompt Template</label>
                    <textarea
                        id="user_prompt_template"
                        name="user_prompt_template"
                        value={template.user_prompt_template}
                        onChange={handleChange}
                        rows={10}
                        style={{ width: '100%', fontFamily: 'monospace', padding: '10px', backgroundColor: '#2a2a2a', color: '#fff', border: '1px solid #555' }}
                        placeholder="Enter user prompt template..."
                    />
                    <small style={{ color: '#888' }}>
                        사용자 입력과 함께 전달될 프롬프트입니다. <code>{'{text}'}</code> 플레이스홀더가 반드시 포함되어야 합니다.
                    </small>
                </div>

                <div className="button-group" style={{ marginTop: '2rem' }}>
                    <button type="submit" disabled={loading} className="save-btn" style={{ width: '100%' }}>
                        {loading ? 'Saving...' : 'Save Template'}
                    </button>
                </div>
            </form>
        </div>
    );
};

export default SummaryTemplateForm;
