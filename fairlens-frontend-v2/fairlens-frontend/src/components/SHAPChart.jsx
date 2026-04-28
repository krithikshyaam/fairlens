import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { useTheme } from '../ThemeContext'

const COLORS = { increases_bias: '#ef4444', reduces_bias: '#10b981', neutral: '#94a3b8' }

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="card text-sm px-4 py-3 !shadow-xl">
      <div className="font-bold mb-1" style={{ color: 'var(--text-primary)' }}>{d.feature}</div>
      <div style={{ color: 'var(--text-secondary)' }}>Mean |SHAP|: <span className="font-mono font-bold">{d.shap_value.toFixed(5)}</span></div>
      <div className="text-xs mt-1 font-medium" style={{ color: COLORS[d.direction] }}>{d.direction.replace(/_/g,' ')}</div>
    </div>
  )
}

export default function SHAPChart({ features }) {
  const { dark } = useTheme()
  const data = [...features].sort((a,b) => b.shap_value - a.shap_value).slice(0,12)
    .map(f => ({ ...f, label: f.feature.length > 22 ? f.feature.slice(0,20)+'…' : f.feature }))
    .reverse()

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-5">
        <h3 className="font-bold" style={{ color: 'var(--text-primary)' }}>SHAP Feature Importances</h3>
        <div className="flex items-center gap-3 text-xs" style={{ color: 'var(--text-muted)' }}>
          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-red-400 inline-block"/>increases bias</span>
          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-slate-400 inline-block"/>neutral</span>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={data.length * 36 + 20}>
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 24, top: 4, bottom: 4 }}>
          <XAxis type="number" tick={{ fontSize: 11, fill: dark ? '#94a3b8' : '#64748b' }} tickFormatter={v => v.toFixed(3)} />
          <YAxis type="category" dataKey="label" tick={{ fontSize: 12, fill: dark ? '#cbd5e1' : '#374151' }} width={165} />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: dark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.03)' }} />
          <Bar dataKey="shap_value" radius={[0,5,5,0]}>
            {data.map((e,i) => <Cell key={i} fill={COLORS[e.direction] || COLORS.neutral} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
