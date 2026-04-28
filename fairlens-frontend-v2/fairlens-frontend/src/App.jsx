import { useState } from 'react'
import { useTheme } from './ThemeContext'
import LandingPage from './components/LandingPage'
import UploadScreen from './components/UploadScreen'
import ResultsScreen from './components/ResultsScreen'
import MitigationScreen from './components/MitigationScreen'

const STEPS = ['Upload', 'Analysis', 'Mitigation']

export default function App() {
  const [view, setView] = useState('landing')  // 'landing' | 'app'
  const [step, setStep] = useState(0)
  const [analysis, setAnalysis] = useState(null)
  const [mitigation, setMitigation] = useState(null)
  const [uploadConfig, setUploadConfig] = useState(null)
  const { dark, toggle } = useTheme()

  function handleStart() { setView('app') }

  function handleAnalysisDone(result, config) {
    setAnalysis(result)
    setUploadConfig(config)
    setStep(1)
  }

  function handleMitigationDone(result) {
    setMitigation(result)
    setStep(2)
  }

  function reset() {
    setStep(0); setAnalysis(null); setMitigation(null); setUploadConfig(null)
  }

  function goHome() {
    reset(); setView('landing')
  }

  if (view === 'landing') return <LandingPage onStart={handleStart} />

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg-primary)' }}>

      {/* ── App Navbar ── */}
      <header className="sticky top-0 z-50 border-b" style={{ background: 'var(--bg-secondary)', borderColor: 'var(--border)' }}>
        <div className="max-w-6xl mx-auto px-6 py-3 flex items-center justify-between">
          <button onClick={goHome} className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold shadow-md">⚖</div>
            <div>
              <div className="font-bold leading-none text-sm" style={{ color: 'var(--text-primary)' }}>FairLens</div>
              <div className="text-xs leading-none" style={{ color: 'var(--text-muted)' }}>AI Bias Detection</div>
            </div>
          </button>

          {/* Step progress */}
          <nav className="flex items-center gap-1.5">
            {STEPS.map((label, i) => (
              <div key={label} className="flex items-center gap-1.5">
                <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-all duration-300
                  ${i === step ? 'text-white shadow-md' : i < step ? 'text-indigo-600' : ''}`}
                  style={i === step
                    ? { background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }
                    : i < step
                      ? { background: 'var(--accent-light)' }
                      : { background: 'var(--bg-tertiary)', color: 'var(--text-muted)' }}>
                  <span className="w-4 h-4 rounded-full flex items-center justify-center text-xs border border-current font-bold">
                    {i < step ? '✓' : i + 1}
                  </span>
                  {label}
                </div>
                {i < STEPS.length - 1 && (
                  <div className="w-4 h-px" style={{ background: i < step ? 'var(--accent)' : 'var(--border)' }} />
                )}
              </div>
            ))}
          </nav>

          <div className="flex items-center gap-2">
            <button onClick={toggle}
              className="w-8 h-8 rounded-xl flex items-center justify-center text-base transition-all hover:scale-110"
              style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border)' }}>
              {dark ? '☀️' : '🌙'}
            </button>
            <button onClick={reset} className="btn-secondary text-xs py-1.5 px-3">
              ↩ New
            </button>
          </div>
        </div>
      </header>

      {/* ── Main ── */}
      <main className="max-w-6xl mx-auto px-6 py-8 page-enter">
        {step === 0 && <UploadScreen onDone={handleAnalysisDone} />}
        {step === 1 && analysis && (
          <ResultsScreen
            analysis={analysis}
            uploadConfig={uploadConfig}
            onMitigate={handleMitigationDone}
            onReset={reset}
          />
        )}
        {step === 2 && mitigation && (
          <MitigationScreen
            mitigation={mitigation}
            analysisId={analysis.analysis_id}
            onReset={reset}
          />
        )}
      </main>
    </div>
  )
}
