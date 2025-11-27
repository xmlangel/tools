import React, { useState } from 'react';
import YoutubeSTTApp from './features/youtube-stt/components/YoutubeSTTApp';
import './App.css';

function App() {
  const [currentTool, setCurrentTool] = useState(null);

  const tools = [
    {
      id: 'youtube-stt',
      title: 'YouTube STT & Translation',
      description: 'YouTube 영상을 텍스트로 변환하고 번역합니다.',
      icon: '🎥'
    },
    // 추후 다른 툴 추가 가능
    // { id: 'image-gen', title: 'Image Generator', description: '...', icon: '🎨' }
  ];

  if (currentTool === 'youtube-stt') {
    return <YoutubeSTTApp onBack={() => setCurrentTool(null)} />;
  }

  return (
    <div className="app-container">
      <header className="main-header">
        <h1>My AI Tools</h1>
        <p>Select a tool to start working</p>
      </header>

      <div className="tool-grid">
        {tools.map(tool => (
          <div key={tool.id} className="tool-card" onClick={() => setCurrentTool(tool.id)}>
            <div className="tool-icon">{tool.icon}</div>
            <h3>{tool.title}</h3>
            <p>{tool.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
