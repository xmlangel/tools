import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import STTForm from './STTForm';
import TranslationForm from './TranslationForm';
import SimpleTranslationForm from './SimpleTranslationForm';
import JobRow from './JobRow';
import axios from 'axios';
import '../../../App.css';
import { API_URL } from '../../../config';

function YoutubeSTTApp() {
    const navigate = useNavigate();
    const [searchParams, setSearchParams] = useSearchParams();
    const activeTab = searchParams.get('tab') || 'stt';

    // Helper to safely set tab
    const setActiveTab = (tab) => {
        setSearchParams({ tab });
    };

    const [jobs, setJobs] = useState([]);
    const [jobTab, setJobTab] = useState('stt');
    const [loading, setLoading] = useState(true);
    const [showHelp, setShowHelp] = useState(false);

    // 페이지 로드 시 최근 작업 불러오기
    useEffect(() => {
        fetchJobs();
    }, []);

    const fetchJobs = async () => {
        try {
            const response = await axios.get(`${API_URL}/api/jobs`);
            setJobs(response.data.jobs || []);
        } catch (err) {
            console.error('Failed to fetch jobs:', err);
        } finally {
            setLoading(false);
        }
    };

    const addJob = (job) => {
        setJobs(prev => [job, ...prev]);
        // Auto-switch tab to show the new job
        if (job.type === 'translate') {
            setJobTab('translate');
        } else if (job.type === 'stt') {
            setJobTab('stt');
        }
    };

    const handleJobUpdate = (updatedJob) => {
        if (updatedJob.deleted) {
            setJobs(prev => prev.filter(j => j.id !== updatedJob.id));
        } else {
            setJobs(prev => prev.map(j => j.id === updatedJob.id ? updatedJob : j));
        }
    };

    return (
        <div className="container">
            <header>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <button className="back-btn" onClick={() => navigate('/')}>← Home</button>
                    <h1>YouTube STT & Translation</h1>
                    <button className="help-btn" onClick={() => setShowHelp(!showHelp)}>
                        {showHelp ? '닫기' : '사용 방법'}
                    </button>
                </div>
            </header>

            {showHelp && (
                <div className="help-section" style={{ backgroundColor: '#3a3a3a', color: 'rgba(255, 255, 255, 0.87)', border: '1px solid #555' }}>
                    <h3 style={{ color: 'white', borderBottom: '1px solid #555' }}>📖 사용 방법</h3>
                    <div className="help-content" style={{ textAlign: 'left' }}>
                        <div className="help-item">
                            <h4 style={{ color: '#646cff' }}>1️⃣ YouTube STT (음성을 텍스트로 변환)</h4>
                            <ul style={{ color: '#ccc' }}>
                                <li>YouTube URL을 입력합니다</li>
                                <li>Whisper 모델을 선택합니다:
                                    <ul style={{ color: '#aaa' }}>
                                        <li><strong>tiny</strong>: 가장 빠름, 정확도 낮음 (테스트용)</li>
                                        <li><strong>base</strong>: 빠름, 기본 정확도</li>
                                        <li><strong>small</strong>: 균형잡힌 속도와 정확도</li>
                                        <li><strong>medium</strong>: 느림, 높은 정확도</li>
                                        <li><strong>large-v3</strong>: 가장 느림, 최고 정확도 (권장)</li>
                                    </ul>
                                </li>
                                <li>"Start STT" 버튼을 클릭합니다</li>
                                <li>진행률이 표시되며, 완료되면 텍스트 파일과 오디오 파일을 다운로드할 수 있습니다</li>
                            </ul>
                            <p style={{ fontSize: '0.85rem', color: '#aaa', marginTop: '0.5rem', backgroundColor: '#2a2a2a', padding: '0.5rem', borderRadius: '4px' }}>
                                💡 <strong>기술 정보:</strong> OpenAI의 Whisper 모델을 사용하여 음성을 텍스트로 변환합니다.
                                YouTube 영상에서 오디오를 추출하고 Whisper가 자동으로 음성을 인식합니다.
                            </p>
                        </div>

                        <div className="help-item">
                            <h4 style={{ color: '#646cff' }}>2️⃣ Translation (텍스트 번역)</h4>
                            <ul style={{ color: '#ccc' }}>
                                <li>STT 결과 파일을 선택하거나 다른 텍스트 파일을 선택합니다</li>
                                <li>목표 언어를 선택합니다 (한국어, 영어, 일본어, 중국어)</li>
                                <li>우측 상단의 <strong>LLM Settings</strong>에서 LLM 설정을 추가하고 선택합니다.</li>
                                <li>"Start Translation" 버튼을 클릭합니다</li>
                            </ul>
                            <p style={{ fontSize: '0.85rem', color: '#aaa', marginTop: '0.5rem', backgroundColor: '#2a2a2a', padding: '0.5rem', borderRadius: '4px' }}>
                                💡 <strong>기술 정보:</strong> OpenWebUI를 통해 LLM(대규모 언어 모델)에 접근하여 번역합니다.
                                텍스트를 청크로 나누어 순차적으로 번역하며, 문맥을 고려한 자연스러운 번역을 제공합니다.
                            </p>
                        </div>

                        <div className="help-item">
                            <h4 style={{ color: '#646cff' }}>💡 팁</h4>
                            <ul style={{ color: '#ccc' }}>
                                <li><strong>View text</strong> 버튼으로 웹에서 바로 텍스트를 확인할 수 있습니다</li>
                                <li><strong>🎬 아이콘</strong>을 클릭하면 원본 YouTube 영상으로 이동합니다</li>
                                <li><strong>⏹️ 버튼</strong>으로 진행 중인 작업을 중지할 수 있습니다</li>
                                <li><strong>🗑️ 버튼</strong>으로 작업 기록을 삭제할 수 있습니다</li>
                                <li>작업 목록은 서버에 저장되어 재시작 후에도 유지됩니다</li>
                                <li>진행률 바로 작업 상태를 실시간으로 확인할 수 있습니다</li>
                            </ul>
                        </div>

                        <div className="help-item">
                            <h4 style={{ color: '#646cff' }}>🔄 작업 흐름</h4>
                            <p style={{ fontSize: '0.9rem', lineHeight: '1.6', color: '#ccc' }}>
                                1. YouTube URL 입력 → 2. 오디오 다운로드 → 3. Whisper로 STT 처리 →
                                4. 텍스트 파일 저장 → 5. (선택) 텍스트 파일 선택 → 6. LLM으로 번역 →
                                7. 번역된 텍스트 저장
                            </p>
                        </div>
                    </div>
                </div>
            )}

            <div className="tabs">
                <button
                    className={activeTab === 'stt' ? 'active' : ''}
                    onClick={() => setActiveTab('stt')}
                >
                    YouTube STT
                </button>
                <button
                    className={activeTab === 'translate' ? 'active' : ''}
                    onClick={() => setActiveTab('translate')}
                >
                    Translation (File)
                </button>
                <button
                    className={activeTab === 'simple-translate' ? 'active' : ''}
                    onClick={() => setActiveTab('simple-translate')}
                >
                    Simple Translation
                </button>
            </div>

            <div className="content">
                <div className="form-section">
                    {activeTab === 'stt' ? (
                        <STTForm onJobCreated={addJob} />
                    ) : activeTab === 'translate' ? (
                        <TranslationForm onJobCreated={addJob} />
                    ) : (
                        <SimpleTranslationForm />
                    )}
                </div>

                <div className="jobs-section">
                    <h3>Recent Jobs</h3>

                    <div className="job-tabs">
                        <button
                            className={`job-tab ${jobTab === 'stt' ? 'active' : ''}`}
                            onClick={() => setJobTab('stt')}
                        >
                            YouTube STT
                        </button>
                        <button
                            className={`job-tab ${jobTab === 'translate' ? 'active' : ''}`}
                            onClick={() => setJobTab('translate')}
                        >
                            Translation
                        </button>
                    </div>

                    {loading ? (
                        <p>Loading...</p>
                    ) : jobs.filter(job => job.type === jobTab).length === 0 ? (
                        <p className="no-jobs">No {jobTab === 'stt' ? 'STT' : 'Translation'} jobs yet.</p>
                    ) : (
                        <table className="jobs-table">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Status</th>
                                    <th>Input / Title</th>
                                    <th>Created At</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {jobs
                                    .filter(job => job.type === jobTab)
                                    .map(job => (
                                        <JobRow key={job.id} job={job} onCompleted={handleJobUpdate} />
                                    ))
                                }
                            </tbody>
                        </table>
                    )}
                </div>
            </div>
        </div>
    );
}

export default YoutubeSTTApp;
