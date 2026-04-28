const METRICS = {
  demographic_parity_difference: { label: 'Demographic Parity', short: 'DPD', threshold: 0.10, better: 'lower', icon: '📊' },
  equalized_odds_difference:     { label: 'Equalized Odds',     short: 'EOD', threshold: 0.10, better: 'lower', icon: '⚖️' },
  disparate_impact_ratio:        { label: 'Disparate Impact',   short: 'DIR', threshold: 0.80, better: 'higher', icon: '🎯' },
  overall_accuracy:              { label: 'Model Accuracy',     short: 'ACC', threshold: null,  better: 'higher', icon: '✅' },
  average_odds_difference:       { label: 'Avg Odds Diff',      short: 'AOD', threshold: 0.10, better: 'lower', icon: '🔢' },
  equal_opportunity_difference:  { label: 'Equal Opportunity',  short: 'EQOD', threshold: 0.10, better: 'lower', icon: '🤝' },
  theil_index:                   { label: 'Theil Index',        short: 'TI',   threshold: 0.10, better: 'lower', icon: '📉' },
  statistical_parity_ratio:      { label: 'Statistical Parity', short: 'SPR',  threshold: 0.80, better: 'higher', icon: '📈' },
}

export default function MetricCard({ metricKey, value, compact = false }) {
  const info = METRICS[metricKey]
  if (!info) return null

  const pass = info.threshold === null ? null
    : info.better === 'lower'  ? value <= info.threshold
    : value >= info.threshold

  const displayValue = metricKey === 'overall_accuracy'
    ? `${(value * 100).toFixed(1)}%`
    : value.toFixed(4)

  const valueColor = pass === false ? 'var(--danger)' : pass === true ? 'var(--success)' : 'var(--text-primary)'

  if (compact) {
    return (
      <div className="card flex items-center justify-between gap-3 py-4">
        <div className="flex items-center gap-2">
          <span className="text-lg">{info.icon}</span>
          <div>
            <div className="text-xs font-bold" style={{ color: 'var(--text-muted)' }}>{info.short}</div>
            <div className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{info.label}</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xl font-extrabold font-mono" style={{ color: valueColor }}>{displayValue}</span>
          {pass !== null && (
            <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${pass ? 'badge-low' : 'badge-high'}`}>
              {pass ? 'PASS' : 'FAIL'}
            </span>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="card flex flex-col gap-3 hover:scale-[1.01] transition-transform">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xl">{info.icon}</span>
          <div>
            <div className="text-xs font-bold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>{info.short}</div>
            <div className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>{info.label}</div>
          </div>
        </div>
        {pass !== null && (
          <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${pass ? 'badge-low' : 'badge-high'}`}>
            {pass ? '✓ PASS' : '✗ FAIL'}
          </span>
        )}
      </div>
      <div className="text-4xl font-extrabold font-mono" style={{ color: valueColor }}>
        {displayValue}
      </div>
      {info.threshold !== null && (
        <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
          Threshold: {info.better === 'lower' ? '<' : '>'} {info.threshold}
        </div>
      )}
      {/* Mini progress bar */}
      <div className="h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--bg-tertiary)' }}>
        <div className="h-full rounded-full transition-all duration-700"
          style={{
            width: info.better === 'lower'
              ? `${Math.min(100, (value / (info.threshold * 3)) * 100)}%`
              : `${Math.min(100, value * 100)}%`,
            background: pass === false ? 'var(--danger)' : pass === true ? 'var(--success)' : '#6366f1'
          }} />
      </div>
    </div>
  )
}
