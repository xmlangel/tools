import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { API_URL } from '../../../config';

const JobRow = ({ job, onCompleted }) => {
    const [status, setStatus] = useState(job.status);
    const [data, setData] = useState(job);
    const [viewingText, setViewingText] = useState(null);
    const [textContent, setTextContent] = useState('');

    useEffect(() => {
        if (!job?.id || status === 'completed' || status === 'failed' || status === 'cancelled') return;

        const interval = setInterval(async () => {
            try {
                const response = await axios.get(`${API_URL}/api/jobs/${job.id}`);
                setStatus(response.data.status);
                setData(prevData => ({
                    ...prevData,  // Keep all previous data
                    ...response.data,  // Update with new data
                    created_at: response.data.created_at || prevData.created_at,  // Preserve created_at
                    input_data: response.data.input_data || prevData.input_data  // Preserve input_data
                }));
                if (response.data.status === 'completed') {
                    onCompleted && onCompleted(response.data);
                }
            } catch (err) {
                console.error("Polling error", err);
            }
        }, 2000);

        return () => clearInterval(interval);
    }, [job.id, status]);

    // YouTube URL에서 제목 추출 (파일명에서)
    const getTitle = () => {
        if (data.output) {
            const files = Object.values(data.output);
            if (files.length > 0) {
                const filename = files[0];
                // ID와 확장자 제거
                return filename.replace(/^\d+_/, '').replace(/\.(mp3|txt)$/, '').replace(/_/g, ' ');
            }
        }
        return null;
    };

    // Format date to Korean timezone (UTC+9)
    const formatKoreanTime = (dateString) => {
        if (!dateString) return '-';

        const date = new Date(dateString);

        // Check if date is valid
        if (isNaN(date.getTime())) return '-';

        // Format as Korean timezone
        return date.toLocaleString('ko-KR', {
            timeZone: 'Asia/Seoul',
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
    };

    const handleViewText = async (filename, key) => {
        try {
            const response = await axios.get(`${API_URL}/api/view/${filename}`);
            setTextContent(response.data.content);
            setViewingText(key);
        } catch (err) {
            console.error('Failed to load text:', err);
            alert('텍스트 파일을 불러올 수 없습니다.');
        }
    };

    const closeModal = () => {
        setViewingText(null);
        setTextContent('');
    };

    const handleStop = async () => {
        if (!window.confirm('정말로 이 작업을 중지하시겠습니까?')) return;
        try {
            await axios.post(`${API_URL}/api/jobs/${job.id}/cancel`);
            setStatus('cancelled');
            alert('작업이 중지되었습니다.');
        } catch (err) {
            console.error('Failed to stop job:', err);
            alert('작업 중지에 실패했습니다.');
        }
    };

    const handleDelete = async () => {
        if (!window.confirm('정말로 이 작업을 삭제하시겠습니까?')) return;
        try {
            await axios.delete(`${API_URL}/api/jobs/${job.id}`);
            onCompleted && onCompleted({ ...job, deleted: true }); // Notify parent to remove from list
        } catch (err) {
            console.error('Failed to delete job:', err);
            alert('작업 삭제에 실패했습니다.');
        }
    };

    return (
        <>
            <tr className={`job-row ${status}`}>
                <td>#{data.id}</td>
                <td>
                    <span className={`status-badge ${status}`}>{status}</span>
                    {status === 'processing' && (
                        <div className="progress-container-mini">
                            <div className="progress-bar" style={{ width: `${data.progress || 0}%` }}></div>
                        </div>
                    )}
                </td>
                <td>
                    <div className="job-info">
                        {data.type === 'stt' && data.input_data && (
                            <div className="input-url">
                                <strong>URL: </strong>
                                <a href={data.input_data} target="_blank" rel="noopener noreferrer">
                                    {data.input_data}
                                </a>
                            </div>
                        )}
                        {getTitle() && (
                            <div className="video-title">
                                {getTitle()}
                            </div>
                        )}
                        {data.error_message && <div className="error-text">{data.error_message}</div>}
                    </div>
                </td>
                <td>{formatKoreanTime(data.created_at)}</td>
                <td>
                    <div className="action-buttons">
                        {data.youtube_url && (
                            <a href={data.youtube_url} target="_blank" rel="noopener noreferrer" className="youtube-link-btn" title="Open YouTube URL">
                                🎬
                            </a>
                        )}

                        {status === 'completed' && data.output && (
                            <>
                                {Object.entries(data.output).map(([key, filename]) => {
                                    const downloadUrl = `${API_URL}/api/download/${filename}`;
                                    // Determine the label for the button
                                    let buttonLabel = '';
                                    if (key === 'text') {
                                        buttonLabel = 'STT';
                                    } else if (key === 'translated_text' || key === 'translation') {
                                        buttonLabel = 'TR';
                                    } else if (key === 'summary') {
                                        buttonLabel = 'Summary';
                                    }

                                    return (
                                        <div key={key} className="action-group">
                                            {(key === 'text' || key === 'translated_text' || key === 'translation' || key === 'summary') ? (
                                                <>
                                                    <button onClick={() => handleViewText(filename, key)} className="view-btn-sm" title={`View ${key}`}>
                                                        {buttonLabel}
                                                    </button>
                                                    <a href={downloadUrl} target="_blank" rel="noopener noreferrer" className="download-btn-sm" title={`Download ${key}`}>
                                                        ⬇️
                                                    </a>
                                                </>
                                            ) : (
                                                <a href={downloadUrl} target="_blank" rel="noopener noreferrer" className="download-btn-sm" title={`Download ${key}`}>
                                                    ⬇️ {key === 'audio' ? '🎵' : ''}
                                                </a>
                                            )}
                                        </div>
                                    );
                                })}
                            </>
                        )}

                        {(status === 'pending' || status === 'processing') && (
                            <button onClick={handleStop} className="stop-btn-sm" title="Stop Job">
                                ⏹️
                            </button>
                        )}

                        <button onClick={handleDelete} className="delete-btn-sm" title="Delete Job">
                            🗑️
                        </button>
                    </div>
                </td>
            </tr>

            {/* 텍스트 뷰어 모달 - Portal would be better but keeping it simple for now */}
            {viewingText && (
                <tr className="modal-row">
                    <td colSpan="5">
                        <div className="modal-overlay" onClick={closeModal}>
                            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                                <div className="modal-header">
                                    <h3>텍스트 내용 ({viewingText})</h3>
                                    <button className="close-btn" onClick={closeModal}>✕</button>
                                </div>
                                <div className="modal-body">
                                    <pre className="text-content">{textContent}</pre>
                                </div>
                            </div>
                        </div>
                    </td>
                </tr>
            )}
        </>
    );
};

export default JobRow;
