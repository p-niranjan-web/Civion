import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import Ledger from './components/Ledger';
import Traceability from './components/Traceability';
import Optimization from './components/Optimization';
import ChatWindow from './components/ChatWindow';
import ScannerAnimation from './components/ScannerAnimation';

const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
  ? 'http://127.0.0.1:8000' 
  : '';

function App() {
  // Global State
  const [file, setFile] = useState(null);
  const [auditData, setAuditData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');

  // Scanner Animation State
  const [scannerStage, setScannerStage] = useState(0);
  const [scannerComplete, setScannerComplete] = useState(false);

  // Chat State
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'CIVION AI initialized. Upload a specification document to begin analysis.' }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [chatView, setChatView] = useState('split'); // 'minimized', 'split', 'fullscreen'

  // Optimization State
  const [adjustments, setAdjustments] = useState({});
  const [optimizedData, setOptimizedData] = useState(null);
  const [optLoading, setOptLoading] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState(null);

  const handleFileChange = (selectedFile) => {
    setFile(selectedFile);
    // Reset state on new file
    setAuditData(null);
    setOptimizedData(null);
    setDownloadUrl(null);
    setAdjustments({});
    setError(null);
  };

  const runAudit = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setOptimizedData(null);
    setDownloadUrl(null);
    setScannerStage(1);
    setScannerComplete(false);
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      // Simulate frontend processing stages
      const stage2Timer = setTimeout(() => setScannerStage(2), 1500);
      const stage3Timer = setTimeout(() => setScannerStage(3), 3000);
      
      const response = await fetch(`${API_BASE}/api/audit`, {
        method: 'POST',
        body: formData,
      });
      
      clearTimeout(stage2Timer);
      clearTimeout(stage3Timer);
      setScannerStage(4);
      
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Audit failed');
      }
      
      setTimeout(() => {
        setScannerComplete(true);
        setTimeout(() => {
          setAuditData(data);
          setMessages([{ role: 'assistant', content: 'Hello! I have completed the audit. Ask me any questions about the results or the specification document.' }]);
          setActiveTab('dashboard');
          setLoading(false);
          setScannerStage(0);
          
          // Initialize adjustments for failed metrics
          const metricMap = {
            "Concrete Grade": "specified_grade",
            "Min Cement Content": "specified_min_cement",
            "W/C Ratio": "specified_wc",
            "Sampling Sets": "specified_sampling_sets",
            "Aggregate Size": "max_aggregate_size_mm",
            "Mixing Time": "mixing_time_minutes",
            "Curing Days": "curing_days"
          };
          
          const initAdjs = {};
          if (data.ledger) {
            data.ledger.forEach(item => {
              if (item.Status.includes('Fail') || item.Status.includes('Warning')) {
                const key = metricMap[item.Metric];
                if (key) {
                  let req = item.Requirement.replace('Min ', '').replace('Max ', '').replace('Req ', '').trim();
                  if (req.includes(' ')) req = req.split(' ')[0];
                  initAdjs[key] = req;
                }
              }
            });
          }
          setAdjustments(initAdjs);
        }, 800);
      }, 500);

    } catch (err) {
      setError(err.message);
      setLoading(false);
      setScannerStage(0);
    }
  };

  const sendChatMessage = async () => {
    if (!chatInput.trim() || chatLoading) return;
    
    const userMsg = { role: 'user', content: chatInput };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setChatInput('');
    setChatLoading(true);
    
    try {
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: newMessages,
          audit_context: auditData?.raw_extracted_data || null
        })
      });
      
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Chat failed');
      
      setMessages([...newMessages, { role: 'assistant', content: data.response }]);
    } catch (err) {
      setMessages([...newMessages, { role: 'assistant', content: 'System Error: ' + err.message }]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleRemediate = (metric, extractedValue, requirement) => {
    const prompt = `The check for ${metric} failed. The specification has ${extractedValue} but IS 456 requires ${requirement}. What specific changes should be made to achieve compliance?`;
    setChatInput(prompt);
    if (chatView === 'minimized') setChatView('split');
  };

  const downloadReport = async () => {
    if (!auditData) return;
    try {
      const response = await fetch(`${API_BASE}/api/report/download`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(auditData)
      });
      if (!response.ok) throw new Error('Download failed');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'CIVION_Compliance_Report.pdf';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
      alert('Failed to download report.');
    }
  };

  const optimizeSpecs = async () => {
    setOptLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/optimize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          raw_data: auditData.raw_extracted_data,
          adjustments: adjustments
        })
      });
      
      if (!response.ok) throw new Error('Optimization failed');
      const data = await response.json();
      setOptimizedData(data);
      
      // Generate Rectified Report
      const reportRes = await fetch(`${API_BASE}/api/report/optimized`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          original_ledger: auditData.ledger,
          optimized_ledger: data.ledger
        })
      });
      const reportData = await reportRes.json();
      setDownloadUrl(reportData.download_url);
      
    } catch (err) {
      console.error(err);
      alert('Failed to optimize specs.');
    } finally {
      setOptLoading(false);
    }
  };

  const handleAdjustmentChange = (key, value) => {
    setAdjustments(prev => ({ ...prev, [key]: value }));
  };

  const handleDownloadOptReport = () => {
    if (downloadUrl) {
      // Create a temporary link to download the file directly
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = 'CIVION_Optimized_Specification.pdf';
      document.body.appendChild(a);
      a.click();
      a.remove();
    }
  };

  return (
    <div className="app-container">
      <Sidebar 
        file={file}
        onFileChange={handleFileChange}
        onRunAudit={runAudit}
        loading={loading}
        error={error}
        auditData={auditData}
        onDownloadReport={downloadReport}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      <main className="main-content">

        <div className="tab-content">
          {loading ? (
            <ScannerAnimation stage={scannerStage} complete={scannerComplete} />
          ) : (
            <>
              {activeTab === 'dashboard' && <Dashboard auditData={auditData} onRemediate={handleRemediate} />}
              {activeTab === 'ledger' && <Ledger auditData={auditData} />}
              {activeTab === 'traceability' && <Traceability auditData={auditData} />}
              {activeTab === 'optimization' && (
                <Optimization 
                  auditData={auditData}
                  adjustments={adjustments}
                  onAdjustmentChange={handleAdjustmentChange}
                  optimizedData={optimizedData}
                  optLoading={optLoading}
                  onOptimize={optimizeSpecs}
                  downloadUrl={downloadUrl}
                  onDownloadOptReport={handleDownloadOptReport}
                />
              )}
            </>
          )}
        </div>

        {/* Chat Window */}
        <div className={`chat-wrapper chat-${chatView}`}>
           <ChatWindow 
            messages={messages}
            chatInput={chatInput}
            onChatInputChange={setChatInput}
            chatLoading={chatLoading}
            onSendChat={sendChatMessage}
            chatView={chatView}
            onToggleMinimize={() => setChatView(chatView === 'minimized' ? 'split' : 'minimized')}
            onToggleFullscreen={() => setChatView(chatView === 'fullscreen' ? 'split' : 'fullscreen')}
          />
        </div>
      </main>
    </div>
  );
}

export default App;
