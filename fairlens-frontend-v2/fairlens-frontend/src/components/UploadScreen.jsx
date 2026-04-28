import { useState, useRef } from 'react'
import { analyzeDataset } from '../api'

const PRESETS = [
  { label: 'Kaggle Survey 2018', emoji: '📊', file: 'kaggle_survey_2018_synthetic.csv', target: 'compensation_high', protected: ['Q1_gender','Q2_age','Q3_country'], positive: 'high' },
  { label: 'COMPAS Recidivism', emoji: '⚖️', file: 'compas.csv', target: 'two_year_recid', protected: ['race','sex'], positive: '1' },
]

const LOADING_MSGS = [
  '🔍 Profiling dataset...',
  '🔧 Encoding features...',
  '🤖 Training model...',
  '📐 Computing fairness metrics...',
  '🧠 Running SHAP analysis...',
  '✨ Generating Gemini explanation...',
]

export default function UploadScreen({ onDone }) {
  const [file, setFile] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [targetColumn, setTargetColumn] = useState('')
  const [protectedInput, setProtectedInput] = useState('')
  const [positiveLabel, setPositiveLabel] = useState('1')
  const [loading, setLoading] = useState(false)
  const [loadingIdx, setLoadingIdx] = useState(0)
  const [error, setError] = useState(null)
  const fileRef = useRef()

  function handleFile(f) {
    if (!f) return
    setFile(f); setError(null)
  }

  function applyPreset(p) {
    setTargetColumn(p.target)
    setProtectedInput(p.protected.join(', '))
    setPositiveLabel(p.positive)
  }

  async function handleSubmit() {
    if (!file) return setError('Please upload a dataset file.')
    if (!targetColumn.trim()) return setError('Target column is required.')
    const pa = protectedInput.split(',').map(s => s.trim()).filter(Boolean)
    if (!pa.length) return setError('At least one protected attribute is required.')

    setLoading(true); setError(null); setLoadingIdx(0)
    const interval = setInterval(() => setLoadingIdx(i => (i + 1) % LOADING_MSGS.length), 1400)

    try {
      const result = await analyzeDataset({
        file,
        targetColumn: targetColumn.trim(),
        protectedAttributes: pa,
        positiveLabel: positiveLabel.trim() || '1',
      })
      clearInterval(interval)
      onDone(result, { targetColumn: targetColumn.trim(), protectedAttributes: pa, positiveLabel: positiveLabel.trim() || '1' })
    } catch (err) {
      clearInterval(interval)
      const msg = err.response?.data?.detail || err.message || 'Unknown error'
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg))
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6 page-enter">
      <div className="text-center py-4">
        <h1 className="text-3xl font-extrabold mb-2" style={{ color: 'var(--text-primary)' }}>
          Run a Bias Audit
        </h1>
        <p className="text-base" style={{ color: 'var(--text-secondary)' }}>
          Upload your dataset — FairLens detects hidden discrimination in seconds.
        </p>
      </div>

      {/* Drop zone */}
      <div
        onClick={() => !loading && fileRef.current.click()}
        onDragOver={e => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={e => { e.preventDefault(); setDragging(false); handleFile(e.dataTransfer.files[0]) }}
        className={`rounded-2xl border-2 border-dashed p-10 text-center cursor-pointer transition-all duration-200
          ${dragging ? 'scale-[1.01]' : ''}
          ${file ? 'border-emerald-400' : 'hover:border-indigo-400'}`}
        style={{
          background: file ? 'var(--bg-tertiary)' : dragging ? 'var(--accent-light)' : 'var(--bg-secondary)',
          borderColor: file ? '#34d399' : dragging ? 'var(--accent)' : 'var(--border)',
        }}
      >
        <input ref={fileRef} type="file" accept=".csv,.tsv,.json,.parquet,.xlsx,.xls,.feather" className="hidden"
          onChange={e => handleFile(e.target.files[0])} />
        {file ? (
          <div className="space-y-2">
            <div className="text-4xl">✅</div>
            <div className="font-bold text-base" style={{ color: 'var(--text-primary)' }}>{file.name}</div>
            <div className="text-sm" style={{ color: 'var(--text-muted)' }}>{(file.size/1024).toFixed(1)} KB · Click to change</div>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="text-4xl">📁</div>
            <div className="font-semibold" style={{ color: 'var(--text-primary)' }}>Drop your dataset here</div>
            <div className="text-sm" style={{ color: 'var(--text-muted)' }}>
              CSV · TSV · JSON · Parquet · Excel · Feather
            </div>
          </div>
        )}
      </div>

      {/* Presets */}
      <div>
        <div className="text-xs font-bold uppercase tracking-widest mb-3" style={{ color: 'var(--text-muted)' }}>
          Quick presets
        </div>
        <div className="grid grid-cols-2 gap-3">
          {PRESETS.map(p => (
            <button key={p.label} onClick={() => applyPreset(p)}
              className="flex items-center gap-3 p-3 rounded-xl text-left transition-all hover:-translate-y-0.5"
              style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border)' }}>
              <span className="text-2xl">{p.emoji}</span>
              <div>
                <div className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{p.label}</div>
                <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Auto-fill config</div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Config */}
      <div className="card space-y-4">
        <h2 className="font-bold text-base" style={{ color: 'var(--text-primary)' }}>Configuration</h2>

        <div>
          <label className="block text-sm font-semibold mb-1.5" style={{ color: 'var(--text-secondary)' }}>
            Target column <span className="text-red-500">*</span>
          </label>
          <input type="text" value={targetColumn} onChange={e => setTargetColumn(e.target.value)}
            placeholder="e.g. compensation_high" className="input-field" />
        </div>

        <div>
          <label className="block text-sm font-semibold mb-1.5" style={{ color: 'var(--text-secondary)' }}>
            Protected attributes <span className="text-red-500">*</span>
          </label>
          <input type="text" value={protectedInput} onChange={e => setProtectedInput(e.target.value)}
            placeholder="e.g. Q1_gender, Q2_age, Q3_country" className="input-field" />
          <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>Comma-separated column names</p>
        </div>

        <div>
          <label className="block text-sm font-semibold mb-1.5" style={{ color: 'var(--text-secondary)' }}>
            Positive label
          </label>
          <input type="text" value={positiveLabel} onChange={e => setPositiveLabel(e.target.value)}
            placeholder="e.g. high or 1" className="input-field" />
        </div>
      </div>

      {error && (
        <div className="rounded-xl px-4 py-3 text-sm flex items-start gap-2"
          style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.3)', color: 'var(--danger)' }}>
          ⚠️ {error}
        </div>
      )}

      <button onClick={handleSubmit} disabled={loading || !file} className="btn-primary w-full justify-center text-base py-4">
        {loading ? (
          <>
            <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
            </svg>
            {LOADING_MSGS[loadingIdx]}
          </>
        ) : '⚖️ Run Bias Analysis'}
      </button>
    </div>
  )
}
