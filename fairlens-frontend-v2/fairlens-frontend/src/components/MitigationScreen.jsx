import { useState } from 'react'
import BeforeAfterTable from './BeforeAfterTable'
import GeminiBox from './GeminiBox'
import { downloadReport } from '../api'

const STRATEGY_INFO = {
  reweighing:           { label: 'Reweighing',          type: 'Pre-processing',  icon: '⚖️' },
  threshold_optimizer:  { label: 'Threshold Optimizer', type: 'Post-processing', icon: '🎯' },
  correlation_removal:  { label: 'Correlation Removal', type: 'Pre-processing',  icon: '✂️' },
}

export default function MitigationScreen({ mitigation, analysisId, onReset }) {
  const [downloading, setDownloading] = useState(false)
  const [downloaded,  setDownloaded]  = useState(false)

  const b   = mitigation.before_metrics
  const a   = mitigation.after_metrics
  const imp = mitigation.improvement_summary
  const info = STRATEGY_INFO[mitigation.strategy] || { label: mitigation.strategy, type: '', icon: '🛠️' }

  const dpd_improved = (imp.demographic_parity_difference ?? 0) > 0.02
  const severity_improved = b.bias_severity !== a.bias_severity

  async function handleDownload() {
    setDownloading(true)
    try { await downloadReport({ analysisId, includeMitigation: true }); setDownloaded(true) }
    catch {}
    setDownloading(false)
  }

  const summaryCards = [
    { label: 'DPD reduced by', value: (imp.demographic_parity_difference??0).toFixed(4), positive: (imp.demographic_parity_difference??0)>0 },
    { label: 'DIR improved by', value: (imp.disparate_impact_ratio??0).toFixed(4), positive: (imp.disparate_impact_ratio??0)>0 },
    { label: 'Before severity', value: b.bias_severity.toUpperCase(), sev: b.bias_severity },
    { label: 'After severity',  value: a.bias_severity.toUpperCase(),  sev: a.bias_severity },
  ]

  return (
    <div className="space-y-6 page-enter">

      {/* ── Result banner ── */}
      <div className="rounded-2xl p-6 relative overflow-hidden"
        style={{
          background: dpd_improved
            ? 'linear-gradient(135deg, rgba(16,185,129,0.08), rgba(5,150,105,0.05))'
            : 'linear-gradient(135deg, rgba(245,158,11,0.08), rgba(217,119,6,0.05))',
          border: `1px solid ${dpd_improved ? 'rgba(16,185,129,0.3)' : 'rgba(245,158,11,0.3)'}`,
        }}>
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2 flex-wrap">
              <span className="text-2xl">{info.icon}</span>
              <h2 className="text-xl font-extrabold" style={{ color: 'var(--text-primary)' }}>{info.label} Applied</h2>
              <span className="text-xs font-bold px-3 py-1 rounded-full"
                style={{ background: 'var(--accent-light)', color: 'var(--accent)' }}>{info.type}</span>
            </div>
            <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
              {dpd_improved
                ? `✅ Bias successfully reduced. DPD improved by ${(imp.demographic_parity_difference??0).toFixed(4)}.`
                : `⚠️ Marginal improvement. Consider trying a different strategy.`}
              {severity_improved && ` Severity: ${b.bias_severity} → ${a.bias_severity}.`}
            </p>
          </div>
          <div className="flex gap-2 flex-shrink-0">
            <button onClick={onReset} className="btn-secondary text-sm py-2 px-4">↩ New Analysis</button>
            <button onClick={handleDownload} disabled={downloading} className="btn-primary text-sm py-2 px-4">
              {downloading ? '⏳' : downloaded ? '✅' : '📄'} {downloading ? 'Generating…' : downloaded ? 'Downloaded' : 'Download PDF'}
            </button>
          </div>
        </div>
      </div>

      {/* ── Summary cards ── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {summaryCards.map(({ label, value, positive, sev }) => (
          <div key={label} className="card text-center">
            <div className="text-xs font-bold uppercase tracking-wider mb-2" style={{ color: 'var(--text-muted)' }}>{label}</div>
            <div className="text-2xl font-extrabold"
              style={{ color: sev === 'high' ? 'var(--danger)' : sev === 'medium' ? 'var(--warning)' : sev === 'low' ? 'var(--success)' : positive ? 'var(--success)' : 'var(--text-primary)' }}>
              {positive && !sev ? '+' : ''}{value}
            </div>
          </div>
        ))}
      </div>

      {/* ── Before / After table ── */}
      <div className="card">
        <h3 className="font-bold mb-5" style={{ color: 'var(--text-primary)' }}>Fairness Metrics — Before vs After</h3>
        <BeforeAfterTable before={b} after={a} />
      </div>

      {/* ── Group rate comparison ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {[{ label: 'Before', rates: b.group_positive_rates, color: '#ef4444' },
          { label: 'After',  rates: a.group_positive_rates, color: '#10b981' }].map(({ label, rates, color }) => (
          <div key={label} className="card">
            <h3 className="font-bold mb-4" style={{ color: 'var(--text-primary)' }}>
              Group Positive Rates — <span style={{ color }}>{label}</span>
            </h3>
            <div className="space-y-3">
              {Object.entries(rates).sort((x,y) => y[1]-x[1]).map(([g,r]) => (
                <div key={g}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="font-medium truncate" style={{ color: 'var(--text-primary)' }}>{g}</span>
                    <span className="font-mono font-bold ml-2" style={{ color }}>{(r*100).toFixed(1)}%</span>
                  </div>
                  <div className="h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--bg-tertiary)' }}>
                    <div className="h-full rounded-full transition-all duration-700" style={{ width:`${r*100}%`, background: color }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* ── Gemini ── */}
      <GeminiBox explanation={mitigation.gemini_explanation} />

      {/* ── Download CTA ── */}
      <div className="rounded-2xl p-8 text-center text-white"
        style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}>
        <div className="text-3xl mb-3">📄</div>
        <h3 className="text-xl font-extrabold mb-2">Download Full Audit Report</h3>
        <p className="text-indigo-200 text-sm mb-6 max-w-md mx-auto">
          Compliance-ready PDF with dataset profile, all metrics, SHAP importances, before/after comparison, and Gemini summary.
        </p>
        <button onClick={handleDownload} disabled={downloading}
          className="bg-white font-bold px-8 py-3 rounded-xl transition-all hover:bg-indigo-50 disabled:opacity-60"
          style={{ color: '#6366f1' }}>
          {downloading ? 'Generating PDF…' : downloaded ? '✅ Downloaded' : '⬇️ Download PDF Report'}
        </button>
      </div>
    </div>
  )
}
