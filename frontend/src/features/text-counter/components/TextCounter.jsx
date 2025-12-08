import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './TextCounter.css';

const TextCounter = () => {
    const navigate = useNavigate();
    const [input, setInput] = useState('');
    const [stats, setStats] = useState({ total: 0, noSpace: 0 });

    useEffect(() => {
        setStats({
            total: input.length,
            noSpace: input.replace(/\s/g, '').length
        });
    }, [input]);

    const handleRemoveWhitespace = () => {
        if (!input) return;
        const noSpaceText = input.replace(/\s/g, '');
        setInput(noSpaceText);
    };

    const handleCopy = async () => {
        if (!input) return;

        try {
            await navigator.clipboard.writeText(input);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    };

    const handlePaste = async () => {
        try {
            const text = await navigator.clipboard.readText();
            setInput(text);
        } catch (err) {
            console.error('Failed to paste:', err);
        }
    };

    const handleClear = () => {
        setInput('');
    };

    return (
        <div className="text-counter-container">
            <header>
                <button className="back-btn" onClick={() => navigate('/')}>← Home</button>
                <h1>Text Counter</h1>
                <div></div>
            </header>

            <div className="content">
                <div className="form-section">
                    <div className="card">
                        <div className="toolbar">
                            <button className="toolbar-btn primary" onClick={handleRemoveWhitespace}>Remove Whitespace</button>
                            <button className="toolbar-btn" onClick={handlePaste}>Paste</button>
                            <button className="toolbar-btn" onClick={handleClear}>Clear</button>
                            <button className="toolbar-btn" onClick={handleCopy} disabled={!input}>Copy</button>

                            <div className="stats-panel">
                                <div className="stat-item">
                                    <span>공백포함:</span>
                                    <span className="stat-value">{stats.total}</span>
                                    <span>자</span>
                                </div>
                                <div className="stat-item">
                                    <span>공백제외:</span>
                                    <span className="stat-value">{stats.noSpace}</span>
                                    <span>자</span>
                                </div>
                            </div>
                        </div>

                        <div className="form-group">
                            <textarea
                                className="text-input"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder="Type or paste your text here..."
                                spellCheck="false"
                            />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default TextCounter;
