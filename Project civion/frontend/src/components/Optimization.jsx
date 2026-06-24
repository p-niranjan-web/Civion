import React from 'react';
import RadialGauge from './RadialGauge';

/* ──────────────────────────────────────────────
   Metric key → Human-readable name mapping
   ────────────────────────────────────────────── */
const metricMap = {
  'Concrete Grade':    'specified_grade',
  'Min Cement Content': 'specified_min_cement',
  'W/C Ratio':         'specified_wc',
  'Sampling Sets':     'specified_sampling_sets',
  'Aggregate Size':    'max_aggregate_size_mm',
  'Mixing Time':       'mixing_time_minutes',
  'Curing Days':       'curing_days',
};

/** Reverse-lookup: backend key → display name */
const getKeyName = (key) => {
  const found = Object.entries(metricMap).find(([, v]) => v === key);
  return found ? found[0] : key;
};

/**
 * Return { min, max, step, isText } for a given
 * adjustment key so we can render the right input.
 */
const getSliderConfig = (key) => {
  switch (key) {
    case 'specified_min_cement':
      return { min: 200, max: 500, step: 10 };
    case 'specified_wc':
    case 'max_wc':
      return { min: 0.3, max: 0.7, step: 0.01 };
    case 'max_aggregate_size_mm':
      return { min: 10, max: 40, step: 5 };
    case 'mixing_time_minutes':
      return { min: 1, max: 10, step: 1 };
    case 'curing_days':
      return { min: 3, max: 28, step: 1 };
    case 'specified_sampling_sets':
      return { min: 1, max: 20, step: 1 };
    case 'specified_grade':
      return { isText: true };
    default:
      return { isText: true };
  }
};

/* ──────────────────────────────────────────────
   Optimization
   Premium optimization panel with adjustment
   sliders, gauge, comparison table, and download.
   ────────────────────────────────────────────── */
const Optimization = ({
  auditData,
  adjustments,
  onAdjustmentChange,
  optimizedData,
  optLoading,
  onOptimize,
  downloadUrl,
  onDownloadOptReport,
}) => {
  /* ── Empty state ── */
  if (!auditData) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
        </div>
        <h2>Run an Audit First</h2>
        <p>Upload and audit a specification to unlock the optimization engine</p>
      </div>
    );
  }

  const adjustmentKeys = Object.keys(adjustments || {});
  const hasAdjustments = adjustmentKeys.length > 0;

  /* Score: use optimized score when available, else derive from counts */
  const baseScore = Math.round(
    (auditData.counts.pass / auditData.counts.total) * 100
  ) || 0;
  const displayScore = optimizedData ? optimizedData.score : baseScore;

  return (
    <div className="optimization">
      <h2 className="section-title">Structural Optimization Engine</h2>

      {/* ── Score Section ── */}
      <div className="opt-score-section">
        <RadialGauge score={displayScore} size={160} />
        <div>
          <h3>Compliance Score</h3>
          <p>
            {optimizedData
              ? 'Optimized specification generated'
              : 'Adjust parameters below to reach 100% compliance'}
          </p>
        </div>
      </div>

      {/* ── Two-Column Grid ── */}
      <div className="opt-grid">
        {/* Left: Adjustment Controls */}
        <div>
          <h3>Adjustment Controls</h3>

          {!hasAdjustments ? (
            <p className="text-secondary">
              No failed metrics to optimize. Your specification is fully compliant.
            </p>
          ) : (
            adjustmentKeys.map((key) => {
              const config = getSliderConfig(key);
              const value = adjustments[key];

              return (
                <div key={key} className="slider-group">
                  <label>{getKeyName(key)}</label>

                  {config.isText ? (
                    /* Text input for grade-style values */
                    <div className="slider-wrapper">
                      <input
                        type="text"
                        className="custom-slider"
                        value={value}
                        onChange={(e) =>
                          onAdjustmentChange(key, e.target.value)
                        }
                      />
                    </div>
                  ) : (
                    /* Range slider for numeric values */
                    <div className="slider-wrapper">
                      <div className="slider-value-bubble">{value}</div>
                      <input
                        type="range"
                        className="custom-slider"
                        min={config.min}
                        max={config.max}
                        step={config.step}
                        value={value}
                        onChange={(e) =>
                          onAdjustmentChange(key, Number(e.target.value))
                        }
                      />
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* Right: Actions & Download */}
        <div>
          <button
            className="premium-btn"
            disabled={optLoading || !hasAdjustments}
            onClick={onOptimize}
          >
            {optLoading ? 'Optimizing...' : 'Make the Specs Better'}
          </button>

          {downloadUrl && (
            <div className="download-card glass-panel">
              <h4>Rectified Specification Ready</h4>
              <button
                className="btn-outline btn-full-width"
                onClick={onDownloadOptReport}
              >
                Download Rectified PDF
              </button>
            </div>
          )}
        </div>
      </div>

      {/* ── Optimized Compliance Matrix ── */}
      {optimizedData && optimizedData.ledger && (
        <div className="comparison-section glass-panel table-container">
          <h3 className="table-title">Optimized Compliance Matrix</h3>
          <table>
            <thead>
              <tr>
                <th>Metric</th>
                <th>Extracted Value</th>
                <th>Requirement</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {optimizedData.ledger.map((item, idx) => {
                const status = (item.Status || '').toLowerCase();
                let badgeClass = 'status-badge ';
                if (status.includes('fail')) badgeClass += 'status-fail';
                else if (status.includes('warning')) badgeClass += 'status-warning';
                else badgeClass += 'status-pass';

                return (
                  <tr key={idx}>
                    <td>{item.Metric}</td>
                    <td>{item['Extracted Value'] || item.ExtractedValue}</td>
                    <td>{item.Requirement}</td>
                    <td>
                      <span className={badgeClass}>{item.Status}</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* ── Disclaimer ── */}
      <p className="disclaimer">
        This optimization engine provides engineering recommendations based on
        IS 456:2000 requirements. All output must be reviewed and validated by a
        qualified structural engineer before use in construction. The tool does
        not replace professional engineering judgment.
      </p>
    </div>
  );
};

export default Optimization;
