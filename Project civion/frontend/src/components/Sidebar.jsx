import { useRef, useState } from 'react';

/**
 * Sidebar — Left panel with logo, drag-and-drop upload zone,
 * Run Audit / Download Report actions, and footer branding.
 */
const Sidebar = ({
  file,
  onFileChange,
  onRunAudit,
  loading,
  error,
  auditData,
  onDownloadReport,
  activeTab,
  setActiveTab,
}) => {
  const fileInputRef = useRef(null);
  const [dragActive, setDragActive] = useState(false);

  /* ── Drag & Drop handlers ─────────────────────────── */
  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) onFileChange(droppedFile);
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleInputChange = (e) => {
    const selected = e.target.files[0];
    if (selected) onFileChange(selected);
  };

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="logo">
        <span>CIVION</span> AI
      </div>

      {/* Subtitle */}
      <p className="sidebar-subtitle">
        Structural Compliance Engine for IS 456 Concrete Specifications
      </p>

      {/* Navigation */}
      <nav className="sidebar-nav">
        <button className={`nav-link ${activeTab === 'dashboard' ? 'active' : ''}`} onClick={() => setActiveTab('dashboard')}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>
          Dashboard
        </button>
        <button className={`nav-link ${activeTab === 'ledger' ? 'active' : ''}`} onClick={() => setActiveTab('ledger')}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>
          Compliance Ledger
        </button>
        <button className={`nav-link ${activeTab === 'traceability' ? 'active' : ''}`} onClick={() => setActiveTab('traceability')}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
          Engineering Traceability
        </button>
        <button className={`nav-link nav-premium ${activeTab === 'optimization' ? 'active' : ''}`} onClick={() => setActiveTab('optimization')}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
          Make Specs Better
        </button>
      </nav>

      {/* Upload zone */}
      <div
        className={`upload-box glass-panel ${dragActive ? 'drag-active' : ''}`}
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={handleInputChange}
          style={{ display: 'none' }}
        />

        {file ? (
          <div className="upload-selected">
            <span className="upload-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
            </span>
            <span className="upload-filename">{file.name}</span>
          </div>
        ) : (
          <div className="upload-placeholder">
            <span className="upload-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
            </span>
            <p>Drag &amp; Drop PDF or Click to Browse</p>
            <span className="upload-hint">Supports .pdf files</span>
          </div>
        )}
      </div>

      {/* Run Audit button */}
      <button
        className="btn-primary btn-full-width"
        disabled={!file || loading}
        onClick={onRunAudit}
      >
        {loading ? 'Analyzing...' : 'Run Compliance Audit'}
      </button>

      {/* Error banner */}
      {error && <div className="error-banner">{error}</div>}

      {/* Download Report button */}
      {auditData && (
        <button
          className="btn-outline btn-full-width"
          onClick={onDownloadReport}
        >
          Download PDF Report
        </button>
      )}

      {/* Spacer to push footer down */}
      <div style={{ flex: 1 }} />

      {/* Footer */}
      <p className="sidebar-footer">CIVION AI v3.0 — Production Engine</p>
    </aside>
  );
};

export default Sidebar;
