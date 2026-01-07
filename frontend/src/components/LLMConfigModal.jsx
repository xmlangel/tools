import React, { useState, useEffect } from 'react';
import { useLLM } from '../context/LLMContext';

const LLMConfigModal = ({ isOpen, onClose }) => {
    const { configs, addConfig, updateConfig, deleteConfig } = useLLM();
    const [editingId, setEditingId] = useState(null);
    const [formData, setFormData] = useState({
        name: '',
        openwebui_url: '',
        api_key: '',
        model: ''
    });
    const [error, setError] = useState('');

    useEffect(() => {
        if (!isOpen) {
            resetForm();
        }
    }, [isOpen]);

    const resetForm = () => {
        setEditingId(null);
        setFormData({
            name: '',
            openwebui_url: '',
            api_key: '',
            model: ''
        });
        setError('');
    };

    const handleEdit = (config) => {
        setEditingId(config.id);
        setFormData({
            name: config.name,
            openwebui_url: config.openwebui_url,
            api_key: config.api_key,
            model: config.model
        });
    };

    const handleDelete = async (id) => {
        if (window.confirm('Are you sure you want to delete this configuration?')) {
            try {
                await deleteConfig(id);
            } catch (err) {
                setError('Failed to delete configuration.');
            }
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        try {
            if (editingId) {
                await updateConfig(editingId, formData);
            } else {
                await addConfig(formData);
            }
            resetForm();
        } catch (err) {
            console.error('Save configuration error:', err);
            if (err.response) {
                console.error('Error response:', err.response.status, err.response.data);
            }
            setError(err.response?.data?.detail || 'Failed to save configuration.');
        }
    };

    if (!isOpen) return null;

    return (
        <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.7)',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: 1000
        }}>
            <div style={{
                backgroundColor: 'var(--card-bg)',
                color: 'var(--text-color)',
                padding: '2rem',
                borderRadius: '8px',
                width: '600px',
                maxHeight: '80vh',
                overflowY: 'auto',
                boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)'
            }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', borderBottom: '1px solid #555', paddingBottom: '1rem' }}>
                    <h2 style={{ margin: 0 }}>LLM Settings</h2>
                    <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer', color: 'var(--text-color)' }}>&times;</button>
                </div>

                {error && <div style={{ color: '#f44336', marginBottom: '1rem', padding: '0.5rem', backgroundColor: 'rgba(244, 67, 54, 0.1)', borderRadius: '4px' }}>{error}</div>}

                <div style={{ marginBottom: '2rem' }}>
                    <h3>{editingId ? 'Edit Configuration' : 'Add New Configuration'}</h3>
                    <form onSubmit={handleSubmit}>
                        <div className="form-group">
                            <label>Name (Profile Name)</label>
                            <input
                                type="text"
                                value={formData.name}
                                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                placeholder="e.g., My GPT-4"
                                required
                                style={{ width: '100%', padding: '0.5rem', marginBottom: '1rem', backgroundColor: '#2a2a2a', border: '1px solid #555', color: 'white' }}
                            />
                        </div>
                        <div className="form-group">
                            <label>OpenWebUI URL</label>
                            <input
                                type="text"
                                value={formData.openwebui_url}
                                onChange={(e) => setFormData({ ...formData, openwebui_url: e.target.value })}
                                placeholder="http://localhost:3000"
                                required
                                style={{ width: '100%', padding: '0.5rem', marginBottom: '1rem', backgroundColor: '#2a2a2a', border: '1px solid #555', color: 'white' }}
                            />
                        </div>
                        <div className="form-group">
                            <label>API Key</label>
                            <input
                                type="password"
                                value={formData.api_key}
                                onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                                placeholder="sk-..."
                                required
                                style={{ width: '100%', padding: '0.5rem', marginBottom: '1rem', backgroundColor: '#2a2a2a', border: '1px solid #555', color: 'white' }}
                            />
                        </div>
                        <div className="form-group">
                            <label>Model</label>
                            <input
                                type="text"
                                value={formData.model}
                                onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                                placeholder="gpt-4"
                                required
                                style={{ width: '100%', padding: '0.5rem', marginBottom: '1rem', backgroundColor: '#2a2a2a', border: '1px solid #555', color: 'white' }}
                            />
                        </div>
                        <div style={{ display: 'flex', gap: '1rem' }}>
                            <button type="submit" className="save-btn" style={{ padding: '0.5rem 1rem', background: 'var(--primary-color)', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                                {editingId ? 'Update' : 'Add'}
                            </button>
                            {editingId && (
                                <button type="button" onClick={resetForm} style={{ padding: '0.5rem 1rem', background: '#6c757d', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                                    Cancel Edit
                                </button>
                            )}
                        </div>
                    </form>
                </div>

                <div>
                    <h3>Saved Configurations</h3>
                    {configs.length === 0 ? (
                        <p style={{ color: '#999' }}>No configurations saved yet.</p>
                    ) : (
                        <ul style={{ listStyle: 'none', padding: 0 }}>
                            {configs.map(config => (
                                <li key={config.id} style={{
                                    border: '1px solid #555',
                                    borderRadius: '4px',
                                    padding: '1rem',
                                    marginBottom: '0.5rem',
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    alignItems: 'center',
                                    backgroundColor: '#2a2a2a'
                                }}>
                                    <div>
                                        <strong style={{ color: 'var(--primary-color)' }}>{config.name}</strong>
                                        <div style={{ fontSize: '0.85rem', color: '#aaa' }}>
                                            {config.model} @ {config.openwebui_url}
                                        </div>
                                    </div>
                                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                                        <button onClick={() => handleEdit(config)} style={{ padding: '0.3rem 0.6rem', background: '#ffc107', color: 'black', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>Edit</button>
                                        <button onClick={() => handleDelete(config.id)} style={{ padding: '0.3rem 0.6rem', background: '#f44336', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>Delete</button>
                                    </div>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            </div>
        </div>
    );
};

export default LLMConfigModal;
