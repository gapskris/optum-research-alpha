import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { Search, Play, Database, ShieldAlert, Cpu, Activity, Archive, CheckCircle2, Loader2, BookOpen } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

function App() {
  const [topic, setTopic] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState([]);
  const [missionId, setMissionId] = useState(null);
  const [report, setReport] = useState(null);
  const [savedReports, setSavedReports] = useState([]);
  const [activeTab, setActiveTab] = useState('mission'); // 'mission' or 'vault'
  const [rateLimitInfo, setRateLimitInfo] = useState(null);
  
  const terminalRef = useRef(null);

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [logs]);

  useEffect(() => {
    fetchSavedReports();
  }, []);

  const fetchSavedReports = async () => {
    try {
      const response = await fetch(`${API_BASE}/reports`);
      const data = await response.json();
      setSavedReports(data);
    } catch (err) {
      console.error("Failed to fetch reports", err);
    }
  };

  const startMission = async () => {
    if (!topic) return;
    
    setIsRunning(true);
    setLogs([]);
    setReport(null);
    setMissionId(null);
    
    try {
      const response = await fetch(`${API_BASE}/run-mission`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic })
      });
      
      const { mission_id } = await response.json();
      setMissionId(mission_id);
      connectStream(mission_id);
    } catch (err) {
      setLogs(prev => [...prev, `[ERROR] Failed to connect to Command Center: ${err.message}`]);
      setIsRunning(false);
    }
  };

  const connectStream = (id) => {
    const eventSource = new EventSource(`${API_BASE}/stream/${id}`);
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.message) {
        setLogs(prev => [...prev, data.message]);
      }
      
      if (data.status === 'completed') {
        setReport(data.result);
        setIsRunning(false);
        eventSource.close();
        fetchSavedReports();
      }
      
      if (data.status === 'failed' || (data.message && data.message.includes('RateLimitError'))) {
        if (data.message && data.message.includes('RateLimitError')) {
          setRateLimitInfo("Daily Token Limit Reached. Cooldown required (~15 mins).");
        }
        setIsRunning(false);
        eventSource.close();
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
      setIsRunning(false);
    };
  };

  return (
    <div className="mission-control">
      <header>
        <h1>Optum Strategic Alpha</h1>
        <div className="subtitle">High-Fidelity Agentic Research Mission Control</div>
      </header>

      <nav style={{ display: 'flex', gap: '20px', borderBottom: '1px solid var(--border-color)', marginBottom: '10px' }}>
        <button 
          onClick={() => setActiveTab('mission')} 
          style={{ background: 'transparent', color: activeTab === 'mission' ? 'var(--accent-primary)' : 'var(--text-muted)', borderBottom: activeTab === 'mission' ? '2px solid var(--accent-primary)' : 'none', borderRadius: 0, paddingBottom: '10px' }}
        >
          Active Mission
        </button>
        <button 
          onClick={() => setActiveTab('vault')} 
          style={{ background: 'transparent', color: activeTab === 'vault' ? 'var(--accent-primary)' : 'var(--text-muted)', borderBottom: activeTab === 'vault' ? '2px solid var(--accent-primary)' : 'none', borderRadius: 0, paddingBottom: '10px' }}
        >
          The Alpha Vault
        </button>
      </nav>

      {rateLimitInfo && (
        <div style={{ background: 'var(--accent-critical)', padding: '12px', borderRadius: '8px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.9rem' }}>
          <ShieldAlert size={18} />
          <strong>Quota Alert:</strong> {rateLimitInfo}
        </div>
      )}

      {activeTab === 'mission' ? (
        <>
          <section className="card">
            <div className="launcher">
              <input 
                type="text" 
                placeholder="Enter Strategic Topic (e.g., 'Genomic Medicine 2025')..." 
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                disabled={isRunning}
              />
              <button onClick={startMission} disabled={isRunning || !topic}>
                {isRunning ? <Loader2 className="animate-spin" /> : <Play size={18} style={{ marginRight: '8px' }} />}
                {isRunning ? 'Synthesizing...' : 'Launch Mission'}
              </button>
            </div>
          </section>

          <section className="agent-grid">
            <AgentCard name="Researcher" role="Data Gathering" active={isRunning} icon={<Search size={20} />} />
            <AgentCard name="Strategist" role="Health Outcomes" active={isRunning} icon={<Activity size={20} />} />
            <AgentCard name="Consultant" role="Tech & Ops" active={isRunning} icon={<Cpu size={20} />} />
            <AgentCard name="Specialist" role="Pharmacy Benefit" active={isRunning} icon={<ShieldAlert size={20} />} />
          </section>

          <section className="terminal" ref={terminalRef}>
            {logs.length === 0 && <div style={{ color: 'var(--text-muted)' }}>Waiting for Command Input...</div>}
            {logs.map((log, idx) => (
              <div key={idx} className="log-entry">{log}</div>
            ))}
          </section>

          {report && (
            <section className="card report-viewer">
              <header style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
                <CheckCircle2 color="var(--accent-secondary)" />
                <h2 style={{ margin: 0, fontSize: '1.5rem', background: 'none', webkitTextFillColor: 'initial', color: 'white' }}>Final Strategic Alpha Report</h2>
              </header>
              <div className="markdown-container">
                <ReactMarkdown>{report}</ReactMarkdown>
              </div>
            </section>
          )}
        </>
      ) : (
        <section className="agent-grid">
          {savedReports.map((r, idx) => (
            <div key={idx} className="card" style={{ cursor: 'pointer' }} onClick={() => { setReport(r.content); setActiveTab('mission'); }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                <BookOpen size={18} color="var(--accent-primary)" />
                <div style={{ fontWeight: 'bold', fontSize: '0.9rem' }}>{r.filename}</div>
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Cached Strategic Insight</div>
            </div>
          ))}
          {savedReports.length === 0 && <div className="card">No reports archived in the Vault yet.</div>}
        </section>
      )}
    </div>
  );
}

function AgentCard({ name, role, active, icon }) {
  return (
    <div className="card agent-card">
      <div className={`pulse ${active ? 'active' : ''}`}></div>
      <div style={{ background: 'rgba(255,255,255,0.05)', padding: '10px', borderRadius: '10px' }}>
        {icon}
      </div>
      <div>
        <div style={{ fontWeight: 'bold' }}>{name}</div>
        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{role}</div>
      </div>
    </div>
  );
}

export default App;
