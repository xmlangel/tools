import React from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import YoutubeSTTApp from './features/youtube-stt/components/YoutubeSTTApp';
import ReleaseNoteConverter from './features/release-note/components/ReleaseNoteConverter';
import JsonViewer from './features/json-viewer/components/JsonViewer';
import LoginPage from './features/auth/LoginPage';
import { AuthProvider, useAuth } from './context/AuthContext';
import RequireAuth from './components/RequireAuth';
import './App.css';

function HomePage() {
  const { logout } = useAuth();
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
        <div className="header-content">
          <h1>My AI Tools</h1>
          <button onClick={logout} className="logout-button">Logout</button>
        </div>
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
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={
          <RequireAuth>
            <HomePage />
          </RequireAuth>
        } />
        <Route path="/youtube-stt" element={
          <RequireAuth>
            <YoutubeSTTApp />
          </RequireAuth>
        } />
        <Route path="/release-note" element={
          <RequireAuth>
            <ReleaseNoteConverter />
          </RequireAuth>
        } />
        <Route path="/json-viewer" element={
          <RequireAuth>
            <JsonViewer />
          </RequireAuth>
        } />
      </Routes>
    </AuthProvider>
  );
}

export default App;
