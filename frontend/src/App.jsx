import React from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import YoutubeSTTApp from './features/youtube-stt/components/YoutubeSTTApp';
import JsonViewer from './features/json-viewer/components/JsonViewer';
import './App.css';

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
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/youtube-stt" element={<YoutubeSTTApp />} />
      <Route path="/json-viewer" element={<JsonViewer />} />
    </Routes>
  );
}

export default App;
