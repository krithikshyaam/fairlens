const ROWS = [
  { key: 'demographic_parity_difference', label: 'Demographic Parity Difference', better: 'lower',  threshold: 0.10 },
  { key: 'equalized_odds_difference',     label: 'Equalized Odds Difference',     better: 'lower',  threshold: 0.10 },
  { key: 'disparate_impact_ratio',        label: 'Disparate Impact Ratio',         better: 'higher', threshold: 0.80 },
  { key: 'average_odds_difference',       label: 'Average Odds Difference',        better: 'lower',  threshold: 0.10 },
  { key: 'equal_opportunity_difference',  label: 'Equal Opportunity Difference',   better: 'lower',  threshold: 0.10 },
  { key: 'theil_index',                   label: 'Theil Index',                    better: 'lower',  threshold: 0.10 },
  { key: 'overall_accuracy',             label: 'Overall Accuracy',               better: 'higher', threshold: null, isPercent: true },
]

function fmt(key, val, isPercent) {
  if (!val && val !== 0) return '—'
  return isPercent ? `${(val*100).toFixed(1)}%` : val.toFixed(4)
}

export default function BeforeAfterTable({ before, after }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr style={{ borderBottom: '2px solid var(--border)' }}>
            {['Metric','Before','After','Change'].map(h => (
              <th key={h} className={`py-3 text-xs font-bold uppercase tracking-wider ${h==='Metric'?'text-left pr-4':'text-center px-3'}`}
                style={{ color: 'var(--text-muted)' }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {ROWS.map(({ key, label, better, threshold, isPercent }) => {
            const bv = before[key] ?? 0
            const av = after[key]  ?? 0
            const diff = av - bv
            const improved = better === 'lower' ? diff < 0 : diff > 0
            const sign = diff > 0 ? '+' : ''

            return (
              <tr key={key} style={{ borderBottom: '1px solid var(--border)' }}
                className="transition-colors hover:bg-opacity-50"
                onMouseEnter={e => e.currentTarget.style.background='var(--bg-tertiary)'}
                onMouseLeave={e => e.currentTarget.style.background='transparent'}>
                <td className="py-3 pr-4 font-medium" style={{ color: 'var(--text-secondary)' }}>
                  {label}
                  {threshold && <span className="ml-1.5 text-xs" style={{ color: 'var(--text-muted)' }}>({better==='lower'?'<':'>'}{threshold})</span>}
                </td>
                <td className="py-3 px-3 text-center font-mono" style={{ color: 'var(--text-secondary)' }}>{fmt(key,bv,isPercent)}</td>
                <td className="py-3 px-3 text-center font-mono font-bold" style={{ color: 'var(--text-primary)' }}>{fmt(key,av,isPercent)}</td>
                <td className="py-3 pl-3 text-center">
                  <span className={`inline-flex items-center gap-1 font-mono text-xs font-bold px-2.5 py-1 rounded-full
                    ${improved ? 'badge-low' : Math.abs(diff)<0.001 ? '' : 'badge-high'}`}
                    style={Math.abs(diff)<0.001 ? { background:'var(--bg-tertiary)', color:'var(--text-muted)' } : {}}>
                    {improved ? '▼' : Math.abs(diff)<0.001 ? '─' : '▲'}
                    {' '}{sign}{fmt(key,diff,isPercent)}
                  </span>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
