import { useState, useEffect } from 'react';

/**
 * RadialGauge — SVG circular progress indicator.
 * Renders a track ring + animated progress arc with dynamic color
 * based on the score threshold (red < 40, amber 40-69, green >= 70).
 */
const RadialGauge = ({ score = 0, size = 180, strokeWidth = 10, label }) => {
  const [animatedOffset, setAnimatedOffset] = useState(null);

  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const targetOffset = circumference - (score / 100) * circumference;

  // Determine color from score thresholds
  const getColor = (s) => {
    if (s < 40) return '#ff2d55';
    if (s < 70) return '#ffb800';
    return '#00e87a';
  };

  const color = getColor(score);

  // Trigger the stroke-dashoffset animation after mount
  useEffect(() => {
    // Start fully offset (empty ring)
    setAnimatedOffset(circumference);

    const timer = setTimeout(() => {
      setAnimatedOffset(targetOffset);
    }, 50);

    return () => clearTimeout(timer);
  }, [score, circumference, targetOffset]);

  return (
    <div className="radial-gauge">
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        style={{ transform: 'rotate(-90deg)' }}
      >
        {/* Track ring */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth={strokeWidth}
        />

        {/* Progress ring */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={animatedOffset !== null ? animatedOffset : circumference}
          style={{
            transition: 'stroke-dashoffset 1.2s ease-out',
            filter: `drop-shadow(0 0 12px ${color}40)`,
          }}
        />
      </svg>

      {/* Center text overlay */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: size,
          height: size,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          pointerEvents: 'none',
        }}
      >
        <span style={{ fontSize: size * 0.22, fontWeight: 700, color }}>
          {score}
          <span style={{ fontSize: size * 0.12, fontWeight: 500 }}>%</span>
        </span>

        {label && (
          <span
            style={{
              fontSize: size * 0.08,
              color: 'var(--text-secondary)',
              marginTop: 4,
            }}
          >
            {label}
          </span>
        )}
      </div>
    </div>
  );
};

export default RadialGauge;
