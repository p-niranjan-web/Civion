import React from 'react';

/* ──────────────────────────────────────────────
   Traceability
   Source-quote mapping table linking every
   extracted parameter back to its origin in the
   uploaded specification document.
   ────────────────────────────────────────────── */
const Traceability = ({ auditData }) => {
  /* ── Empty state ── */
  if (!auditData) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
        </div>
        <h2>No Traceability Data</h2>
        <p>Run an audit to view source traceability</p>
      </div>
    );
  }

  const traceability = auditData.traceability;

  if (!traceability || traceability.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
        </div>
        <h2>No Traceability Data</h2>
        <p>No source quotes were extracted for this audit</p>
      </div>
    );
  }

  return (
    <div className="traceability">
      <div className="glass-panel table-container">
        <h3 className="table-title">Engineering Traceability</h3>
        <p className="table-subtitle">
          Each extracted parameter is mapped to its source text in the uploaded specification.
        </p>
        <table>
          <thead>
            <tr>
              <th>Parameter</th>
              <th>Extracted Value</th>
              <th>Source Quote</th>
            </tr>
          </thead>
          <tbody>
            {traceability.map((item, idx) => {
              const quote = item['Source Quote'] || item.SourceQuote || '';
              const isEmpty =
                !quote || quote === 'No quote extracted';

              return (
                <tr key={idx}>
                  <td style={{ fontWeight: 600 }}>
                    {item.Parameter}
                  </td>
                  <td className="value-mono">
                    {item['Extracted Value'] || item.ExtractedValue}
                  </td>
                  <td className={isEmpty ? 'text-dim' : 'source-quote'}>
                    {isEmpty ? '—' : `"${quote}"`}
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

export default Traceability;
