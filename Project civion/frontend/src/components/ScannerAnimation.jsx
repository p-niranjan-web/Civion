import { Fragment } from 'react';

/**
 * ScannerAnimation — Multi-stage progress stepper displayed during PDF analysis.
 * Shows 4 sequential stages with connectors and a progress bar.
 */

const STAGES = [
  { id: 1, label: 'Reading Specification' },
  { id: 2, label: 'Extracting Parameters' },
  { id: 3, label: 'Running IS 456 Audit' },
  { id: 4, label: 'Building Compliance Ledger' },
];

/* Map current stage → progress bar width % */
const PROGRESS_MAP = { 0: 0, 1: 15, 2: 40, 3: 70, 4: 92 };

const ScannerAnimation = ({ stage = 0, complete = false, fileName = '' }) => {
  const progressWidth = complete ? 100 : (PROGRESS_MAP[stage] ?? 0);

  const isDone = (id) => id < stage || complete;

  const getStageClass = (id) => {
    if (isDone(id)) return 'scanner-stage scanner-stage--complete';
    if (id === stage) return 'scanner-stage scanner-stage--active';
    return 'scanner-stage scanner-stage--pending';
  };

  const getStatusText = () => {
    if (complete) return 'Analysis complete';
    const current = STAGES.find((s) => s.id === stage);
    return current ? `${current.label}…` : '';
  };

  return (
    <div className="scanner-container">
      <div className="scanner-heading">
        <h2 className="scanner-title">Analyzing specification</h2>
        {fileName && <p className="scanner-file">{fileName}</p>}
      </div>

      <div className="scanner-stages">
        {STAGES.map((s, idx) => (
          <Fragment key={s.id}>
            <div className={getStageClass(s.id)}>
              <div className="scanner-stage-indicator">
                {isDone(s.id) ? (
                  <span className="scanner-check">✓</span>
                ) : s.id === stage ? (
                  <span className="scanner-pulse">{s.id}</span>
                ) : (
                  <span className="scanner-dot" />
                )}
              </div>
              <span className="scanner-stage-label">{s.label}</span>
            </div>
            {idx < STAGES.length - 1 && (
              <div className={`scanner-connector ${isDone(s.id) ? 'connector-complete' : ''}`} />
            )}
          </Fragment>
        ))}
      </div>

      <div className="scanner-progress-track">
        <div className="scanner-progress-fill" style={{ width: `${progressWidth}%` }} />
      </div>

      <p className="scanner-status-text">{getStatusText()}</p>
    </div>
  );
};

export default ScannerAnimation;
