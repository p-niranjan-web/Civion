/**
 * ScannerAnimation — Multi-stage progress stepper displayed during PDF analysis.
 * Shows 4 sequential stages with animated connectors and a progress bar.
 */

const STAGES = [
  { id: 1, label: 'Scanning PDF Structure', icon: '1' },
  { id: 2, label: 'Extracting Parameters', icon: '2' },
  { id: 3, label: 'Running IS 456 Audit', icon: '3' },
  { id: 4, label: 'Generating Compliance Matrix', icon: '4' },
];

/* Map current stage → progress bar width % */
const PROGRESS_MAP = { 0: 0, 1: 20, 2: 45, 3: 70, 4: 90 };

const ScannerAnimation = ({ stage = 0, complete = false }) => {
  const progressWidth = complete ? 100 : (PROGRESS_MAP[stage] ?? 0);

  const getStageClass = (stageId) => {
    if (stageId < stage || complete) return 'scanner-stage scanner-stage--complete';
    if (stageId === stage && !complete) return 'scanner-stage scanner-stage--active';
    return 'scanner-stage scanner-stage--pending';
  };

  const getStatusText = () => {
    if (complete) return 'Analysis Complete';
    const current = STAGES.find((s) => s.id === stage);
    return current ? current.label : '';
  };

  return (
    <div className="scanner-container">
      {/* Stage indicators */}
      <div className="scanner-stages">
        {STAGES.map((s, idx) => (
          <div key={s.id} className={getStageClass(s.id)}>
            {/* Indicator circle */}
            <div className="scanner-indicator">
              {s.id < stage || complete ? (
                <span className="scanner-check">✓</span>
              ) : s.id === stage && !complete ? (
                <span className="scanner-pulse">{s.icon}</span>
              ) : (
                <span className="scanner-dot" />
              )}
            </div>

            {/* Label */}
            <span className="scanner-label">{s.label}</span>

            {/* Connector line (skip last stage) */}
            {idx < STAGES.length - 1 && (
              <div
                className={`scanner-connector ${
                  s.id < stage || complete ? 'scanner-connector--filled' : ''
                }`}
              />
            )}
          </div>
        ))}
      </div>

      {/* Progress bar */}
      <div className="scanner-progress-track">
        <div
          className="scanner-progress-fill"
          style={{
            width: `${progressWidth}%`,
            transition: 'width 0.6s ease-out',
          }}
        />
      </div>

      {/* Status text */}
      <p className="scanner-status-text">{getStatusText()}</p>
    </div>
  );
};

export default ScannerAnimation;
