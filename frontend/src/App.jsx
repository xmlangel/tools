import React, { useState, useEffect } from 'react';
import STTForm from './components/STTForm';
import TranslationForm from './components/TranslationForm';
import JobStatus from './components/JobStatus';
import axios from 'axios';
import './App.css';

function App() {
  const [jobs, setJobs] = useState([]);
  const [activeTab, setActiveTab] = useState('stt');
  const [loading, setLoading] = useState(true);

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
        <h1>YouTube STT & Translation</h1>
      </header>

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

export default App;
