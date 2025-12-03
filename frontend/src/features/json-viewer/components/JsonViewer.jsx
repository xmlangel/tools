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
        <div className="json-viewer-container">
            <header>
                <button className="back-btn" onClick={() => navigate('/')}>← Home</button>
                <h1>JSON Viewer</h1>
                <div></div>
            </header>

            <div className="tabs">
                <button
                    className={activeTab === 'editor' ? 'active' : ''}
                    onClick={() => setActiveTab('editor')}
                >
                    Editor
                </button>
                <button
                    className={activeTab === 'viewer' ? 'active' : ''}
                    onClick={() => setActiveTab('viewer')}
                >
                    Viewer
                </button>
            </div>

            <div className="content">
                <div className="form-section">
                    {activeTab === 'editor' ? (
                        <div className="card">
                            <div className="toolbar">
                                <button className="toolbar-btn primary" onClick={handleFormat}>Format</button>
                                <button className="toolbar-btn" onClick={handleRemoveWhitespace}>Remove Whitespace</button>
                                <button className="toolbar-btn" onClick={handlePaste}>Paste</button>
                                <button className="toolbar-btn" onClick={handleClear}>Clear</button>
                                <button className="toolbar-btn" onClick={handleCopy} disabled={!input}>Copy</button>
                            </div>

                            {error && <div className="error">{error}</div>}

                            <div className="form-group">
                                <label htmlFor="json-input">JSON Input</label>
                                <textarea
                                    id="json-input"
                                    className={`json - input ${error ? 'error-border' : ''} `}
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    placeholder="Paste or type your JSON here..."
                                    spellCheck="false"
                                    rows={20}
                                />
                            </div>
                        </div>
                    ) : (
                        <div className="card">
                            <div className="toolbar">
                                <button className="toolbar-btn" onClick={handleCopy} disabled={!output}>Copy Output</button>
                            </div>

                            <div className="form-group">
                                <label htmlFor="json-output">Formatted JSON</label>
                                <pre className="json-output" id="json-output">
                                    {output || 'No output yet. Use the Editor tab to format JSON.'}
                                </pre>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default JsonViewer;
