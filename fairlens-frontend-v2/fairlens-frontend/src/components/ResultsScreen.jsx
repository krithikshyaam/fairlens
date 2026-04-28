import { useState } from 'react'
import MetricCard from './MetricCard'
import SHAPChart from './SHAPChart'
import GroupTable from './GroupTable'
import GeminiBox from './GeminiBox'
import { mitigateDataset, downloadReport } from '../api'

const STRATEGIES = [
  { id: 'threshold_optimizer', label: 'Threshold Optimizer', type: 'Post-processing', icon: '🎯', desc: 'Per-group decision thresholds. Fast, no retraining.' },
  { id: 'reweighing',          label: 'Reweighing',          type: 'Pre-processing',  icon: '⚖️', desc: 'Reweights samples so all groups influence equally.' },
  { id: 'correlation_removal', label: 'Correlation Removal', type: 'Pre-processing',  icon: '✂️', desc: 'Drops features correlated with protected attributes.' },
]

const CORE_METRICS    = ['demographic_parity_difference','equalized_odds_difference','disparate_impact_ratio','overall_accuracy']
const EXTENDED_METRICS = ['average_odds_difference','equal_opportunity_difference','theil_index','statistical_parity_ratio']

export default function ResultsScreen({ analysis, uploadConfig, onMitigate, onReset }) {
  const [strategy, setStrategy]     = useState('threshold_optimizer')
  const [mitigating, setMitigating] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [error, setError]           = useState(null)
  const [showExtended, setShowExtended] = useState(false)

  const m = analysis.metrics
  const primaryAttr = analysis.protected_attributes[0]

  async function handleMitigate() {
    setMitigating(true); setError(null)
    try {
      const result = await mitigateDataset({
        analysisId: analysis.analysis_id,
        strategy,
        targetColumn: uploadConfig.targetColumn,
        protectedAttributes: uploadConfig.protectedAttributes,
        positiveLabel: uploadConfig.positiveLabel,
      })
      onMitigate(result)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
      setMitigating(false)
    }
  }

  async function handleReport() {
    setDownloading(true)
    try { await downloadReport({ analysisId: analysis.analysis_id, includeMitigation: false }) }
    catch {}
    setDownloading(false)
  }

  return (
    <div className="space-y-6 page-enter">

      {/* ── Summary banner ── */}
      <div className="card">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <div className="flex items-center gap-3 mb-1 flex-wrap">
              <h2 className="text-xl font-extrabold" style={{ color: 'var(--text-primary)' }}>{analysis.dataset_name}</h2>
              <span className={`badge-${m.bias_severity}`}>{m.bias_severity} bias</span>
            </div>
            <div className="text-sm flex flex-wrap gap-x-4 gap-y-1 mt-2" style={{ color: 'var(--text-muted)' }}>
              <span>🎯 Target: <b style={{ color: 'var(--text-primary)' }}>{analysis.target_column}</b></span>
              <span>🔒 Protected: <b style={{ color: 'var(--text-primary)' }}>{analysis.protected_attributes.join(', ')}</b></span>
              <span>🤖 Model: <b style={{ color: 'var(--text-primary)' }}>{analysis.model_type}</b></span>
              <span>📊 Rows: <b style={{ color: 'var(--text-primary)' }}>{analysis.data_profile.row_count.toLocaleString()}</b></span>
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={handleReport} disabled={downloading} className="btn-secondary text-sm py-2 px-4">
              {downloading ? '⏳' : '📄'} Report
            </button>
            <button onClick={onReset} className="btn-secondary text-sm py-2 px-4">↩ New</button>
          </div>
        </div>
      </div>

      {/* ── Core metrics ── */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-bold" style={{ color: 'var(--text-primary)' }}>Core Fairness Metrics</h3>
          <button onClick={() => setShowExtended(v => !v)}
            className="text-xs font-semibold px-3 py-1.5 rounded-lg transition-all"
            style={{ background: 'var(--accent-light)', color: 'var(--accent)' }}>
            {showExtended ? 'Hide' : 'Show'} Extended Metrics
          </button>
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {CORE_METRICS.map(k => <MetricCard key={k} metricKey={k} value={m[k]} />)}
        </div>
      </div>

      {/* ── Extended metrics (togglable) ── */}
      {showExtended && (
        <div className="page-enter">
          <h3 className="font-bold mb-3" style={{ color: 'var(--text-primary)' }}>Extended Metrics</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {EXTENDED_METRICS.map(k => <MetricCard key={k} metricKey={k} value={m[k] ?? 0} compact />)}
          </div>
        </div>
      )}

      {/* ── Gemini ── */}
      <GeminiBox explanation={analysis.gemini_explanation} />

      {/* ── Group table + SHAP ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GroupTable
          groupPositiveRates={m.group_positive_rates}
          groupAccuracies={m.group_accuracies}
          protectedAttribute={primaryAttr}
        />
        <SHAPChart features={analysis.feature_importances} />
      </div>

      {/* ── Dataset profile ── */}
      <div className="card">
        <h3 className="font-bold mb-4" style={{ color: 'var(--text-primary)' }}>Dataset Profile</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: 'Rows', value: analysis.data_profile.row_count.toLocaleString() },
            { label: 'Columns', value: analysis.data_profile.column_count },
            { label: 'Class balance', value: Object.entries(analysis.data_profile.class_balance).map(([k,v]) => `${k}: ${v}`).join(' / ') },
            { label: 'Protected detected', value: analysis.data_profile.protected_attributes.join(', ') || '—' },
          ].map(({ label, value }) => (
            <div key={label} className="rounded-xl p-3" style={{ background: 'var(--bg-tertiary)' }}>
              <div className="text-xs font-bold uppercase tracking-wider mb-1" style={{ color: 'var(--text-muted)' }}>{label}</div>
              <div className="text-sm font-semibold break-words" style={{ color: 'var(--text-primary)' }}>{value}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Mitigation ── */}
      <div className="card">
        <h3 className="font-bold mb-1" style={{ color: 'var(--text-primary)' }}>Apply Bias Mitigation</h3>
        <p className="text-sm mb-5" style={{ color: 'var(--text-secondary)' }}>
          Choose a strategy and FairLens will reduce bias while preserving accuracy.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-5">
          {STRATEGIES.map(s => (
            <button key={s.id} onClick={() => setStrategy(s.id)}
              className="text-left p-4 rounded-xl border-2 transition-all hover:-translate-y-0.5"
              style={{
                borderColor: strategy === s.id ? 'var(--accent)' : 'var(--border)',
                background: strategy === s.id ? 'var(--accent-light)' : 'var(--bg-secondary)',
              }}>
              <div className="text-2xl mb-2">{s.icon}</div>
              <div className="font-bold text-sm mb-0.5" style={{ color: 'var(--text-primary)' }}>{s.label}</div>
              <div className="text-xs font-semibold mb-1.5" style={{ color: 'var(--accent)' }}>{s.type}</div>
              <div className="text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{s.desc}</div>
            </button>
          ))}
        </div>
        {error && (
          <div className="rounded-xl px-4 py-3 text-sm mb-4 flex items-center gap-2"
            style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.25)', color: 'var(--danger)' }}>
            ⚠️ {error}
          </div>
        )}
        <button onClick={handleMitigate} disabled={mitigating} className="btn-primary">
          {mitigating ? (
            <><svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
            </svg> Applying...</>
          ) : `🛠️ Apply ${STRATEGIES.find(s=>s.id===strategy)?.label}`}
        </button>
      </div>
    </div>
  )
}
