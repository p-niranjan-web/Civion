import { useState } from 'react';

/**
 * ExposureSelector — lets the user declare the environmental exposure
 * condition before running the audit, either by:
 *   1. Directly picking one of the IS 456 exposure classes, or
 *   2. Answering a short guided questionnaire that derives it.
 *
 * The resolved class is lifted up via `onChange(exposure)` and sent
 * alongside the PDF when the audit runs. Changing it and re-running
 * the audit re-extracts the document for the new exposure case.
 */

const EXPOSURE_LEVELS = ['Mild', 'Moderate', 'Severe', 'Very Severe', 'Extreme'];

const rank = (e) => EXPOSURE_LEVELS.indexOf(e);
/** Return the more severe of two exposure classes (null-safe). */
const escalate = (current, candidate) => {
  if (!current) return candidate;
  if (!candidate) return current;
  return rank(candidate) > rank(current) ? candidate : current;
};

/* ── Guided questionnaire decision tree ─────────────────────────────
   Each node: prompt + a Yes/No branch. A branch either points to the
   next question id ("next") and/or escalates the running severity
   ("set"), or terminates ("done": true) fixing the final class.
   ------------------------------------------------------------------ */
const QUESTIONS = {
  q1: {
    text: 'Is the plot within 10 km of the sea coast?',
    yes: { next: 'q2' },
    no: { next: 'q3' },
  },
  q2: {
    text:
      'Will the site directly face the sea breeze (no intervening structures between the sea and the site), or is it located within 1 km from the sea?',
    yes: { set: 'Very Severe', next: 'q3' },
    no: { next: 'q4' },
  },
  q3: {
    text:
      'Will any part of the structure be in the tidal zone (daily sea-level rise and fall over it), or in direct contact with industrial chemicals / effluent?',
    yes: { set: 'Extreme', done: true },
    no: { next: 'q4' },
  },
  q4: {
    text:
      'Will the structure be protected against the weather (sheltered from severe rain and aggressive conditions)?',
    yes: { set: 'Mild', next: 'q5' },
    no: { set: 'Severe', next: 'q5' },
  },
  q5: {
    text:
      'Will any part of the structure (foundation, basement, underground sump / tank) be in permanent contact with the ground?',
    yes: { set: 'Moderate', next: 'q6' },
    no: { next: 'q6' },
  },
  q6: {
    text:
      'Do you know of corrosion / spalling in nearby older structures, or is the site near an industrial, tannery, or fertilizer plant?',
    yes: { set: 'Very Severe', done: true },
    no: { done: true },
  },
};

const ExposureSelector = ({ value, onChange, disabled = false }) => {
  const [mode, setMode] = useState('pick'); // 'pick' | 'wizard'

  // Wizard state
  const [currentId, setCurrentId] = useState('q1');
  const [severity, setSeverity] = useState(null);
  const [history, setHistory] = useState([]); // [{ id, severity }]
  const [finished, setFinished] = useState(false);

  const resetWizard = () => {
    setCurrentId('q1');
    setSeverity(null);
    setHistory([]);
    setFinished(false);
  };

  const answer = (choice) => {
    const node = QUESTIONS[currentId];
    const branch = node[choice];
    const nextSeverity = branch.set ? escalate(severity, branch.set) : severity;

    setHistory((h) => [...h, { id: currentId, severity }]);
    setSeverity(nextSeverity);

    if (branch.done) {
      setFinished(true);
      onChange(nextSeverity || 'Moderate');
    } else {
      setCurrentId(branch.next);
    }
  };

  const goBack = () => {
    const prev = history[history.length - 1];
    if (!prev) return;
    setHistory((h) => h.slice(0, -1));
    setSeverity(prev.severity);
    setCurrentId(prev.id);
    setFinished(false);
  };

  const switchMode = (m) => {
    setMode(m);
    if (m === 'wizard') resetWizard();
  };

  return (
    <div className="exposure-selector glass-panel">
      <div className="exposure-selector-head">
        <span className="exposure-selector-title">Environmental Exposure</span>
        {value && <span className="exposure-chip">{value}</span>}
      </div>

      <div className="exposure-mode-toggle">
        <button
          type="button"
          className={mode === 'pick' ? 'active' : ''}
          onClick={() => switchMode('pick')}
          disabled={disabled}
        >
          I know it
        </button>
        <button
          type="button"
          className={mode === 'wizard' ? 'active' : ''}
          onClick={() => switchMode('wizard')}
          disabled={disabled}
        >
          Help me decide
        </button>
      </div>

      {mode === 'pick' ? (
        <select
          className="exposure-select"
          value={value || ''}
          onChange={(e) => onChange(e.target.value || null)}
          disabled={disabled}
        >
          <option value="">Select exposure condition…</option>
          {EXPOSURE_LEVELS.map((lvl) => (
            <option key={lvl} value={lvl}>
              {lvl}
            </option>
          ))}
        </select>
      ) : (
        <div className="exposure-wizard">
          {finished ? (
            <div className="exposure-wizard-result">
              <p className="exposure-wizard-result-label">Determined exposure condition</p>
              <p className="exposure-wizard-result-value">{value}</p>
              <div className="exposure-wizard-actions">
                <button type="button" className="exposure-link-btn" onClick={goBack} disabled={disabled}>
                  ← Back
                </button>
                <button type="button" className="exposure-link-btn" onClick={resetWizard} disabled={disabled}>
                  Restart
                </button>
              </div>
            </div>
          ) : (
            <>
              <p className="exposure-wizard-q">{QUESTIONS[currentId].text}</p>
              {severity && (
                <p className="exposure-wizard-running">Current: {severity}</p>
              )}
              <div className="exposure-wizard-choices">
                <button type="button" onClick={() => answer('yes')} disabled={disabled}>
                  Yes
                </button>
                <button type="button" onClick={() => answer('no')} disabled={disabled}>
                  No
                </button>
              </div>
              {history.length > 0 && (
                <button type="button" className="exposure-link-btn" onClick={goBack} disabled={disabled}>
                  ← Back
                </button>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default ExposureSelector;
