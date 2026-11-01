/* ──────────────────────────────────────────────
   Category definitions
   Each category has a display name and an array
   of keyword fragments used to match Metric names.
   ────────────────────────────────────────────── */
const CATEGORIES = [
  {
    name: 'General',
    exact: ['Concrete Type', 'Environmental Exposure', 'Cement Type'],
    keywords: [],
  },
  {
    name: 'Structural Safety',
    keywords: ['Concrete Grade', 'Min Cement Content', 'Max Cement Content', 'W/C Ratio', 'Standard Deviation', 'Characteristic Strength', 'Cover'],
  },
  {
    name: 'Construction Procedures',
    keywords: ['Mixing', 'Compaction', 'Curing', 'Slump', 'Transportation'],
  },
  {
    name: 'Materials & Limits',
    keywords: ['Water', 'Aggregate', 'Chloride'],
  },
  {
    name: 'Quality Control',
    keywords: ['Sampling'],
  },
  {
    name: 'Sulphate & Site Conditions',
    exact: ['Soil Total SO3', 'Soil Extract SO3', 'Groundwater SO3', 'Sulfate Cement Type', 'Freezing and Thawing', 'Sulphate (SO3) Content'],
    keywords: [],
  },
];

/**
 * Determine which category a metric belongs to.
 * Falls back to 'Other' if no keywords match.
 */
const categorize = (metric) => {
  for (const cat of CATEGORIES) {
    if (cat.exact && cat.exact.includes(metric)) return cat.name;
  }
  for (const cat of CATEGORIES) {
    if (cat.keywords.some((kw) => metric.includes(kw))) {
      return cat.name;
    }
  }
  return 'Other';
};

/**
 * Group an array of ledger items by category,
 * preserving original order within each group.
 */
const groupByCategory = (ledger) => {
  const groups = {};
  ledger.forEach((item) => {
    const cat = categorize(item.Metric || '');
    if (!groups[cat]) groups[cat] = [];
    groups[cat].push(item);
  });
  return groups;
};

/* ──────────────────────────────────────────────
   Ledger
   Categorised compliance parameter listing.
   ────────────────────────────────────────────── */
const Ledger = ({ auditData }) => {
  /* ── Empty state ── */
  if (!auditData) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
        </div>
        <h2>No Compliance Data</h2>
        <p>Run an audit to view the compliance ledger</p>
      </div>
    );
  }

  const groups = groupByCategory(auditData.ledger || []);

  /* Maintain a stable render order: defined categories first, then 'Other' */
  const orderedNames = [
    ...CATEGORIES.slice(0, -1).map((c) => c.name),
    'Other',
    CATEGORIES[CATEGORIES.length - 1].name,   // sulphate / site conditions stay at the bottom
  ].filter((name) => groups[name] && groups[name].length > 0);

  return (
    <div className="ledger">
      {orderedNames.map((catName) => {
        const items = groups[catName];
        return (
          <div key={catName}>
            <div className="category-header">{catName}</div>
            <div className="glass-panel table-container">
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
                  {items.map((item, idx) => {
                    const status = (item.Status || '').toLowerCase();
                    let badgeClass = 'status-badge ';
                    if (status.includes('fail')) badgeClass += 'status-fail';
                    else if (status.includes('warning')) badgeClass += 'status-warning';
                    else if (status.includes('reference')) badgeClass += 'status-reference';
                    else badgeClass += 'status-pass';

                    return (
                      <tr key={idx}>
                        <td>{item.Metric}</td>
                        <td style={{ fontFamily: 'monospace' }}>
                          {item['Extracted Value'] || item.ExtractedValue}
                          {item['Source Quote'] && status.includes('reference') && (
                            <div className="source-quote" style={{ fontSize: '12px', fontFamily: 'inherit' }}>
                              "{item['Source Quote']}"
                            </div>
                          )}
                          {item.Remark && (
                            <div className="text-secondary" style={{ fontSize: '12px', fontFamily: 'inherit' }}>
                              Remark: {item.Remark}
                            </div>
                          )}
                        </td>
                        <td className="text-secondary">
                          {item.Requirement}
                        </td>
                        <td>
                          <span className={badgeClass}>{item.Status}</span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default Ledger;
