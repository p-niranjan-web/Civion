import React, { useState, useEffect, useRef, useCallback } from 'react';
import RadialGauge from './RadialGauge';

/* ──────────────────────────────────────────────
   AnimatedCounter
   Smoothly counts from 0 → target over ~800ms
   using requestAnimationFrame.
   ────────────────────────────────────────────── */
const AnimatedCounter = ({ target, color }) => {
  const [displayValue, setDisplayValue] = useState(0);
  const frameRef = useRef(null);

  useEffect(() => {
    const duration = 800; // ms
    const startTime = performance.now();
    const startVal = 0;

    const step = (now) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease-out cubic for a satisfying deceleration
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(startVal + (target - startVal) * eased);
      setDisplayValue(current);

      if (progress < 1) {
        frameRef.current = requestAnimationFrame(step);
      }
    };

    frameRef.current = requestAnimationFrame(step);

    return () => {
      if (frameRef.current) cancelAnimationFrame(frameRef.current);
    };
  }, [target]);

  return (
    <div className="metric-value" style={{ color }}>
      {displayValue}
    </div>
  );
};

/* ──────────────────────────────────────────────
   Dashboard
   Main compliance dashboard with gauge, metric
   cards, and the compliance matrix table.
   ────────────────────────────────────────────── */
const Dashboard = ({ auditData, onRemediate }) => {
  /* ── Empty state ── */
  if (!auditData) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
        </div>
        <h2>Upload a Specification to Begin</h2>
        <p>Drop a PDF in the sidebar to run your first IS 456 compliance audit</p>
      </div>
    );
  }

  /* ── Derive score & interpretation ── */
  const counts = auditData.counts;
  const score = Math.round((counts.pass / counts.total) * 100) || 0;

  const getInterpretation = (s) => {
    if (s < 40) return 'Critical — Immediate attention required';
    if (s < 70) return 'Moderate — Several issues need resolution';
    if (s < 90) return 'Good — Minor adjustments recommended';
    return 'Excellent — Specification meets IS 456 standards';
  };

  /* ── Metric card definitions ── */
  const metrics = [
    { label: 'Total Checks', value: counts.total, color: '#ffffff', border: '#ffffff' },
    { label: 'Passed',       value: counts.pass,  color: '#00e676', border: '#00e676' },
    { label: 'Failed',       value: counts.fail,  color: '#ff5252', border: '#ff5252' },
    { label: 'Warnings',     value: counts.warning, color: '#ffab40', border: '#ffab40' },
  ];

  return (
    <div className="dashboard">
      {/* ── Header: Gauge + Summary ── */}
      <div className="dashboard-header">
        <RadialGauge score={score} size={160} />
        <div className="dashboard-summary">
          <h2>Overall Compliance</h2>
          <p>{getInterpretation(score)}</p>
        </div>
      </div>

      {/* ── Metric Cards ── */}
      <div className="metrics-grid">
        {metrics.map((m) => (
          <div
            key={m.label}
            className="metric-card glass-panel metric-card-animated"
            style={{ borderTop: `3px solid ${m.border}` }}
          >
            <div className="metric-title">{m.label}</div>
            <AnimatedCounter target={m.value} color={m.color} />
          </div>
        ))}
      </div>

      {/* ── Compliance Matrix Table ── */}
      <div className="glass-panel table-container">
        <h3 className="table-title">Compliance Matrix</h3>
        <table>
          <thead>
            <tr>
              <th>Metric</th>
              <th>Extracted Value</th>
              <th>Requirement</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {auditData.ledger.map((item, idx) => {
              const status = (item.Status || '').toLowerCase();
              const isFail    = status.includes('fail');
              const isWarning = status.includes('warning');

              let rowClass = '';
              if (isFail) rowClass = 'row-fail';
              else if (isWarning) rowClass = 'row-warning';

              // Normalise badge class
              let badgeClass = 'status-badge ';
              if (isFail) badgeClass += 'status-fail';
              else if (isWarning) badgeClass += 'status-warning';
              else badgeClass += 'status-pass';

              return (
                <tr key={idx} className={rowClass}>
                  <td>{item.Metric}</td>
                  <td>{item['Extracted Value'] || item.ExtractedValue}</td>
                  <td>{item.Requirement}</td>
                  <td>
                    <span className={badgeClass}>{item.Status}</span>
                  </td>
                  <td>
                    {isFail || isWarning ? (
                      <button
                        className="remediate-btn"
                        onClick={() =>
                          onRemediate(
                            item.Metric,
                            item['Extracted Value'] || item.ExtractedValue,
                            item.Requirement
                          )
                        }
                      >
                        Ask AI →
                      </button>
                    ) : (
                      '—'
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Dashboard;
