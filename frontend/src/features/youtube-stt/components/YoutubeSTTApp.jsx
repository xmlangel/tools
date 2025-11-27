import React, { useState, useEffect } from 'react';
import STTForm from './STTForm';
import TranslationForm from './TranslationForm';
import JobStatus from './JobStatus';
import axios from 'axios';
import '../../../App.css';

function YoutubeSTTApp({ onBack }) {
    const [jobs, setJobs] = useState([]);
    const [activeTab, setActiveTab] = useState('stt');
    const [loading, setLoading] = useState(true);
    const [showHelp, setShowHelp] = useState(false);

    // 페이지 로드 시 최근 작업 불러오기
    useEffect(() => {
        fetchJobs();
    }, []);

    const fetchJobs = async () => {
        try {
            const response = await axios.get('http://localhost:8000/api/jobs');
            setJobs(response.data.jobs || []);
        } catch (err) {
            console.error('Failed to fetch jobs:', err);
        } finally {
            setLoading(false);
        }
    };

    const addJob = (job) => {
        setJobs(prev => [job, ...prev]);
    };

    return (
        <div className="container">
            <header>
                <button className="back-btn" onClick={onBack}>← Home</button>
                <h1>YouTube STT & Translation</h1>
                <button className="help-btn" onClick={() => setShowHelp(!showHelp)}>
                    {showHelp ? '닫기' : '사용 방법'}
                </button>
            </header>

            {showHelp && (
                <div className="help-section">
                    <h3>📖 사용 방법</h3>
                    <div className="help-content">
                        <div className="help-item">
                            <h4>1️⃣ YouTube STT (음성을 텍스트로 변환)</h4>
                            <ul>
                                <li>YouTube URL을 입력합니다</li>
                                <li>Whisper 모델을 선택합니다 (large-v3 권장)</li>
                                <li>"Start STT" 버튼을 클릭합니다</li>
                                <li>진행률이 표시되며, 완료되면 텍스트 파일과 오디오 파일을 다운로드할 수 있습니다</li>
                            </ul>
                        </div>

                        <div className="help-item">
                            <h4>2️⃣ Translation (텍스트 번역)</h4>
                            <ul>
                                <li>STT 결과 파일을 선택하거나 다른 텍스트 파일을 선택합니다</li>
                                <li>목표 언어를 선택합니다</li>
                                <li>OpenWebUI 설정 (URL, API Key, Model)을 입력합니다</li>
                                <li>"Save Settings" 버튼을 클릭하면 다음번에 자동으로 불러옵니다</li>
                                <li>"Start Translation" 버튼을 클릭합니다</li>
                            </ul>
                        </div>

                        <div className="help-item">
                            <h4>💡 팁</h4>
                            <ul>
                                <li><strong>View text</strong> 버튼으로 웹에서 바로 텍스트를 확인할 수 있습니다</li>
                                <li>작업 목록은 서버에 저장되어 재시작 후에도 유지됩니다</li>
                                <li>진행률 바로 작업 상태를 실시간으로 확인할 수 있습니다</li>
                            </ul>
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
                    Translation
                </button>
            </div>

            <div className="content">
                <div className="form-section">
                    {activeTab === 'stt' ? (
                        <STTForm onJobCreated={addJob} />
                    ) : (
                        <TranslationForm onJobCreated={addJob} />
                    )}
                </div>

                <div className="jobs-section">
                    <h3>Recent Jobs</h3>
                    {loading ? (
                        <p>Loading...</p>
                    ) : jobs.length === 0 ? (
                        <p className="no-jobs">No jobs yet.</p>
                    ) : (
                        jobs.map(job => (
                            <JobStatus key={job.id} job={job} />
                        ))
                    )}
                </div>
            </div>
        </div>
    );
}

export default YoutubeSTTApp;
