import React, { useState } from 'react';
import { Routes, Route, Link, Outlet } from 'react-router-dom';
import YoutubeSTTApp from './features/youtube-stt/components/YoutubeSTTApp';
import ReleaseNoteConverter from './features/release-note/components/ReleaseNoteConverter';
import JsonViewer from './features/json-viewer/components/JsonViewer';
import LoginPage from './features/auth/LoginPage';
import { AuthProvider, useAuth } from './context/AuthContext';
import RequireAuth from './components/RequireAuth';
import './App.css';

import { LLMProvider } from './context/LLMContext';
import LLMConfigModal from './components/LLMConfigModal';

const Layout = () => {
  const { logout } = useAuth();
  const [isLLMModalOpen, setIsLLMModalOpen] = useState(false);

  return (
    <>
      <div style={{ position: 'fixed', top: '1rem', right: '1rem', display: 'flex', gap: '1rem', zIndex: 1000 }}>
        <button
          onClick={() => setIsLLMModalOpen(true)}
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '0.9rem',
            fontWeight: 'bold'
          }}
        >
          LLM Settings
        </button>
        <button
          onClick={logout}
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: '#dc3545',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '0.9rem',
            fontWeight: 'bold'
          }}
        >
          Logout
        </button>
      </div>
      <LLMConfigModal isOpen={isLLMModalOpen} onClose={() => setIsLLMModalOpen(false)} />
      <div className="app-content">
        <Outlet />
      </div>
    </>
  );
};

function HomePage() {
  const tools = [
    {
      id: 'youtube-stt',
      path: '/youtube-stt',
      title: 'YouTube STT & Translation',
      description: 'YouTube 영상을 텍스트로 변환하고 번역합니다.',
      icon: '🎥'
    },
    {
      id: 'release-note',
      path: '/release-note',
      title: '릴리즈 노트 변환기',
      description: '개발자 언어를 고객이 설레는 카피로 변환합니다.',
      icon: '📝'
    },
    {
      id: 'json-viewer',
      path: '/json-viewer',
      title: 'JSON Viewer',
      description: 'JSON 데이터를 포맷팅하고 검증합니다.',
      icon: '🔍'
    }
  ];

  return (
    <div className="app-container">
      <header className="main-header">
        <h1>My AI Tools</h1>
        <p>Select a tool to start working</p>
      </header>

      <div className="tool-grid">
        {tools.map(tool => (
          <Link key={tool.id} to={tool.path} className="tool-card">
            <div className="tool-icon">{tool.icon}</div>
            <h3>{tool.title}</h3>
            <p>{tool.description}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <LLMProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<RequireAuth><Layout /></RequireAuth>}>
            <Route path="/" element={<HomePage />} />
            <Route path="/youtube-stt" element={<YoutubeSTTApp />} />
            <Route path="/release-note" element={<ReleaseNoteConverter />} />
            <Route path="/json-viewer" element={<JsonViewer />} />
          </Route>
        </Routes>
      </LLMProvider>
    </AuthProvider>
  );
}

export default App;
