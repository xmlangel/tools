import React, { useEffect, useState } from 'react';
import axios from 'axios';

const JobStatus = ({ job, onCompleted }) => {
    const [status, setStatus] = useState(job.status);
    const [data, setData] = useState(job);
    const [viewingText, setViewingText] = useState(null);
    const [textContent, setTextContent] = useState('');

    useEffect(() => {
        if (status === 'completed' || status === 'failed') return;

        const interval = setInterval(async () => {
            try {
                const response = await axios.get(`http://localhost:8000/api/jobs/${job.id}`);
                setStatus(response.data.status);
                setData(response.data);
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
        if (data.output_files) {
            const files = Object.values(data.output_files);
            if (files.length > 0) {
                const filename = files[0].split('/').pop().split('?')[0];
                // ID와 확장자 제거
                return filename.replace(/^\d+_/, '').replace(/\.(mp3|txt)$/, '').replace(/_/g, ' ');
            }
        }
        return null;
    };

    const handleViewText = async (url, key) => {
        try {
            // URL에서 파일명 추출
            const filename = url.split('/').pop();
            const response = await axios.get(`http://localhost:8000/api/view/${filename}`);
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

    return (
        <>
            <div className={`job-item ${status}`}>
                <div className="job-header">
                    <span className="job-id">#{data.id}</span>
                    <span className="job-type">{data.type.toUpperCase()}</span>
                    <span className={`status-badge ${status}`}>{status}</span>
                </div>
                <div className="job-details">
                    {/* YouTube URL 표시 (STT 작업인 경우) */}
                    {data.type === 'stt' && data.input_data && (
                        <p className="input-url">
                            <strong>URL:</strong> <a href={data.input_data} target="_blank" rel="noopener noreferrer">{data.input_data}</a>
                        </p>
                    )}

                    {/* 제목 표시 */}
                    {getTitle() && (
                        <p className="video-title">
                            <strong>제목:</strong> {getTitle()}
                        </p>
                    )}

                    <p className="created-at">{new Date(data.created_at).toLocaleString()}</p>

                    {/* 진행률 표시 */}
                    {status === 'processing' && (
                        <div className="progress-container">
                            <div className="progress-bar" style={{ width: `${data.progress || 0}%` }}>
                                <span className="progress-text">{data.progress || 0}%</span>
                            </div>
                        </div>
                    )}

                    {data.error_message && <p className="error">{data.error_message}</p>}
                    {status === 'completed' && data.output_files && (
                        <div className="downloads">
                            {Object.entries(data.output_files).map(([key, url]) => (
                                <div key={key} className="download-item">
                                    {(key === 'text' || key === 'translated_text') ? (
                                        <>
                                            <button onClick={() => handleViewText(url, key)} className="view-btn">
                                                View {key}
                                            </button>
                                            <a href={url} target="_blank" rel="noopener noreferrer" className="download-btn">
                                                Download {key}
                                            </a>
                                        </>
                                    ) : (
                                        <a href={url} target="_blank" rel="noopener noreferrer" className="download-btn">
                                            Download {key}
                                        </a>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* 텍스트 뷰어 모달 */}
            {viewingText && (
                <div className="modal-overlay" onClick={closeModal}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>텍스트 내용</h3>
                            <button className="close-btn" onClick={closeModal}>✕</button>
                        </div>
                        <div className="modal-body">
                            <pre className="text-content">{textContent}</pre>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

export default JobStatus;
