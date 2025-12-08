import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './JsonViewer.css';

const JsonViewer = () => {
    const navigate = useNavigate();
    const [input, setInput] = useState('');
    const [output, setOutput] = useState('');
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState('editor');

    const handleFormat = () => {
        if (!input.trim()) {
            setOutput('');
            setError(null);
            return;
        }

        try {
            const parsed = JSON.parse(input);
            const formatted = JSON.stringify(parsed, null, 2);
            setOutput(formatted);
            setError(null);
            setActiveTab('viewer'); // Auto-switch to viewer tab
        } catch (err) {
            setError(err.message);
        }
    };

    const handleRemoveWhitespace = () => {
        if (!input.trim()) {
            setOutput('');
            setError(null);
            return;
        }

        try {
            const parsed = JSON.parse(input);
            const minified = JSON.stringify(parsed);
            setOutput(minified);
            setError(null);
            setActiveTab('viewer'); // Auto-switch to viewer tab
        } catch (err) {
            setError(err.message);
        }
    };

    const handleCopy = async () => {
        const textToCopy = activeTab === 'editor' ? input : output;
        if (!textToCopy) return;

        try {
            await navigator.clipboard.writeText(textToCopy);
            alert('Copied to clipboard!');
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    };

    const handlePaste = async () => {
        try {
            const text = await navigator.clipboard.readText();
            setInput(text);
            setActiveTab('editor'); // Switch to editor when pasting
        } catch (err) {
            console.error('Failed to paste:', err);
        }
    };

    const handleClear = () => {
        setInput('');
        setOutput('');
        setError(null);
    };

    return (
        <div className="jv-container">
            <header className="jv-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <button className="jv-back-btn" onClick={() => navigate('/')}>← Home</button>
                    <h1>JSON Viewer</h1>
                </div>
            </header>

            <div className="jv-tabs">
                <button
                    className={`jv-tab-btn ${activeTab === 'editor' ? 'active' : ''}`}
                    onClick={() => setActiveTab('editor')}
                >
                    Editor
                </button>
                <button
                    className={`jv-tab-btn ${activeTab === 'viewer' ? 'active' : ''}`}
                    onClick={() => setActiveTab('viewer')}
                >
                    Viewer
                </button>
            </div>

            <div className="jv-content">
                <div className="jv-card">
                    {activeTab === 'editor' ? (
                        <>
                            <div className="jv-toolbar">
                                <button className="jv-toolbar-btn primary" onClick={handleFormat}>Format</button>
                                <button className="jv-toolbar-btn" onClick={handleRemoveWhitespace}>Remove Whitespace</button>
                                <button className="jv-toolbar-btn" onClick={handlePaste}>Paste</button>
                                <button className="jv-toolbar-btn" onClick={handleClear}>Clear</button>
                                <button className="jv-toolbar-btn" onClick={handleCopy} disabled={!input}>Copy</button>
                            </div>

                            {error && <div className="jv-error-msg">{error}</div>}

                            <textarea
                                className={`jv-textarea ${error ? 'error-border' : ''}`}
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder="Paste or type your JSON here..."
                                spellCheck="false"
                            />
                        </>
                    ) : (
                        <>
                            <div className="jv-toolbar">
                                <button className="jv-toolbar-btn" onClick={handleCopy} disabled={!output}>Copy Output</button>
                                <button className="jv-toolbar-btn" onClick={() => setActiveTab('editor')}>
                                    ✏️ Edit
                                </button>
                            </div>

                            <div className="jv-result-area">
                                <pre className="jv-result-content">
                                    {output || 'No output yet. Use the Editor tab to format JSON.'}
                                </pre>
                            </div>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};

export default JsonViewer;
