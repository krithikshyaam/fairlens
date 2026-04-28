export default function GroupTable({ groupPositiveRates, groupAccuracies, protectedAttribute }) {
  const groups = Object.keys(groupPositiveRates).sort()
  const rates  = Object.values(groupPositiveRates)
  const maxRate = Math.max(...rates)
  const minRate = Math.min(...rates)

  return (
    <div className="card">
      <h3 className="font-bold mb-4" style={{ color: 'var(--text-primary)' }}>
        Group Breakdown — <span style={{ color: 'var(--accent)' }}>{protectedAttribute}</span>
      </h3>
      <div className="space-y-3">
        {groups.map(g => {
          const rate = groupPositiveRates[g]
          const acc  = groupAccuracies?.[g]
          const isMax = rate === maxRate
          const isMin = rate === minRate && groups.length > 1
          const barW  = maxRate > 0 ? (rate / maxRate) * 100 : 0

          return (
            <div key={g}>
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2 text-sm">
                  <span className="font-medium" style={{ color: 'var(--text-primary)' }}>{g}</span>
                  {isMax && <span className="text-xs font-bold px-1.5 py-0.5 rounded badge-low">▲ best</span>}
                  {isMin && <span className="text-xs font-bold px-1.5 py-0.5 rounded badge-high">▼ worst</span>}
                </div>
                <div className="flex items-center gap-3 text-sm">
                  <span className="font-mono font-bold" style={{ color: 'var(--text-primary)' }}>{(rate*100).toFixed(1)}%</span>
                  {acc != null && <span className="text-xs" style={{ color: 'var(--text-muted)' }}>acc {(acc*100).toFixed(0)}%</span>}
                </div>
              </div>
              <div className="h-2 rounded-full overflow-hidden" style={{ background: 'var(--bg-tertiary)' }}>
                <div className="h-full rounded-full transition-all duration-700"
                  style={{
                    width: `${barW}%`,
                    background: isMin ? 'var(--danger)' : isMax ? 'var(--success)' : 'var(--accent)'
                  }} />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
