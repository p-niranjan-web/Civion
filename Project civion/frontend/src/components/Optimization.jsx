import RadialGauge from './RadialGauge';

/* ──────────────────────────────────────────────
   Metric key → Human-readable name mapping
   ────────────────────────────────────────────── */
const metricMap = {
  'Concrete Grade':    'specified_grade',
  'Min Cement Content': 'specified_min_cement',
  'W/C Ratio':         'specified_wc',
  'Sampling Sets':     'specified_sampling_sets',
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
  onAdjustmentReset,
  optimizedData,
  optLoading,
  onDownloadSummary,
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

  /* Sliders for the adjustable metrics that did not pass. They start at the value stated in the
     document; only what the user moves is sent back, nothing is auto-corrected to the IS value. */
  const raw = auditData.raw_extracted_data || {};
  const adjustable = (auditData.ledger || [])
    .filter((row) => metricMap[row.Metric] && /fail|warning/i.test(row.Status || ''))
    .map((row) => {
      const key = metricMap[row.Metric];
      let stated = Array.isArray(raw[key]) ? raw[key][raw[key].length - 1] : raw[key];
      const notStated = stated === null || stated === undefined || stated === '';
      if (notStated) {
        const m = String(row.Requirement || '').match(/\d+(\.\d+)?|M\d+/);
        stated = m ? m[0] : '';
      }
      return { key, stated, notStated };
    });
  const hasAdjustments = adjustable.length > 0;

  /* Score: use optimized score when available, else derive from counts */
  const baseScore = Math.round(
    (auditData.counts.pass / auditData.counts.total) * 100
  ) || 0;
  const displayScore = optimizedData ? optimizedData.score : baseScore;

  return (
    <div className="optimization">
      <h2 className="section-title">Summary Table</h2>

      {/* ── Score Section ── */}
      <div className="opt-score-section">
        <RadialGauge score={displayScore} size={160} />
        <div>
          <h3>Compliance Score</h3>
          <p>
            {optimizedData
              ? 'Summary table generated'
              : 'Optionally try different values below, then download the summary table'}
          </p>
        </div>
      </div>

      {/* ── Two-Column Grid ── */}
      <div className="opt-grid">
        {/* Left: Adjustment Controls */}
        <div>
          <h3>Adjustment Controls</h3>
          <p className="text-secondary">Optional. Parameters stay exactly as stated in your document unless you move a slider.</p>

          {!hasAdjustments ? (
            <p className="text-secondary">
              Nothing to adjust: every adjustable parameter already passes.
            </p>
          ) : (
            adjustable.map(({ key, stated, notStated }) => {
              const config = getSliderConfig(key);
              const changed = adjustments[key] !== undefined;
              const value = changed ? adjustments[key] : stated;
              const numericValue = value !== '' && Number.isFinite(Number(value)) ? Number(value) : config.min;

              return (
                <div key={key} className="slider-group">
                  <label>
                    {getKeyName(key)}
                    {notStated && !changed && <span className="text-secondary"> (not stated in the document)</span>}
                    {changed && (
                      <button type="button" className="btn-outline" style={{ marginLeft: 8, padding: '0 8px' }}
                              onClick={() => onAdjustmentReset(key)}>
                        Reset
                      </button>
                    )}
                  </label>

                  {config.isText ? (
                    /* Text input for grade-style values */
                    <div className="slider-wrapper">
                      <input
                        type="text"
                        className="custom-slider"
                        value={value ?? ''}
                        onChange={(e) =>
                          onAdjustmentChange(key, e.target.value)
                        }
                      />
                    </div>
                  ) : (
                    /* Range slider for numeric values */
                    <div className="slider-wrapper">
                      <div className="slider-value-bubble">{numericValue}</div>
                      <input
                        type="range"
                        className="custom-slider"
                        min={config.min}
                        max={config.max}
                        step={config.step}
                        value={numericValue}
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
            disabled={optLoading}
            onClick={onDownloadSummary}
            title="Download summary table (PDF)"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: 8, verticalAlign: 'text-bottom' }}><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
            {optLoading ? 'Preparing...' : 'Download Summary Table'}
          </button>
        </div>
      </div>

      {/* ── Optimized Compliance Matrix ── */}
      {optimizedData && optimizedData.ledger && (
        <div className="comparison-section glass-panel table-container">
          <h3 className="table-title">Summary Table</h3>
          <table>
            <thead>
              <tr>
                <th>Metric</th>
                <th>Stated Value</th>
                <th>Required Value</th>
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
