import { useTheme } from '../ThemeContext'

const FEATURES = [
  { icon: '🔍', title: 'Detect Hidden Bias', desc: 'Compute Demographic Parity, Equalized Odds, Disparate Impact, Theil Index and more across all protected groups.' },
  { icon: '🧠', title: 'SHAP Explainability', desc: 'Identify exactly which features drive discriminatory predictions with feature-level SHAP importance charts.' },
  { icon: '🛠️', title: '3 Mitigation Strategies', desc: 'Reweighing, Threshold Optimizer, and Correlation Removal — apply in one click and see results instantly.' },
  { icon: '✨', title: 'Gemini AI Explanations', desc: 'Google Gemini translates complex bias findings into plain English any stakeholder can understand.' },
  { icon: '📄', title: 'PDF Audit Reports', desc: 'Download compliance-ready audit reports with before/after metrics for regulatory documentation.' },
  { icon: '📂', title: '6 File Formats', desc: 'Upload CSV, TSV, JSON, Parquet, Excel (.xlsx), or Feather files. FairLens handles the rest.' },
]

const STEPS = [
  { n: '01', title: 'Upload Dataset', desc: 'Drop any CSV, Excel, or Parquet file. FairLens auto-detects protected attributes.' },
  { n: '02', title: 'Detect Bias', desc: 'Get 8 fairness metrics, SHAP charts, and a Gemini-powered plain-English explanation.' },
  { n: '03', title: 'Apply Mitigation', desc: 'Choose a strategy, apply it in one click, and see before vs after comparisons.' },
  { n: '04', title: 'Download Report', desc: 'Export a compliance-ready PDF audit report for your team or regulators.' },
]

const METRICS = [
  { label: 'Datasets Audited', value: '5K+' },
  { label: 'Bias Metrics', value: '8' },
  { label: 'Mitigation Strategies', value: '3' },
  { label: 'File Formats', value: '6' },
]

export default function LandingPage({ onStart }) {
  const { dark, toggle } = useTheme()

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg-primary)' }}>

      {/* ── Navbar ── */}
      <nav className="sticky top-0 z-50 border-b" style={{ background: 'var(--bg-secondary)', borderColor: 'var(--border)' }}>
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg shadow-lg">⚖</div>
            <div>
              <div className="font-bold text-lg leading-none" style={{ color: 'var(--text-primary)' }}>FairLens</div>
              <div className="text-xs leading-none" style={{ color: 'var(--text-muted)' }}>AI Bias Detection</div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={toggle} className="w-9 h-9 rounded-xl flex items-center justify-center text-lg transition-all hover:scale-110"
              style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border)' }}>
              {dark ? '☀️' : '🌙'}
            </button>
            <button onClick={onStart} className="btn-primary text-sm py-2 px-5">
              Launch App →
            </button>
          </div>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="relative overflow-hidden py-24 px-6">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-0 left-1/4 w-96 h-96 rounded-full opacity-20 blur-3xl"
            style={{ background: 'radial-gradient(circle, #6366f1, transparent)' }} />
          <div className="absolute bottom-0 right-1/4 w-80 h-80 rounded-full opacity-15 blur-3xl"
            style={{ background: 'radial-gradient(circle, #8b5cf6, transparent)' }} />
        </div>
        <div className="relative max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium mb-8"
            style={{ background: 'var(--accent-light)', color: 'var(--accent)', border: '1px solid var(--accent)' }}>
            <span>🏆</span> Google Solution Challenge 2026
          </div>
          <h1 className="text-5xl sm:text-6xl font-extrabold mb-6 leading-tight">
            <span style={{ color: 'var(--text-primary)' }}>Detect & Fix</span><br />
            <span className="gradient-text">AI Bias Instantly</span>
          </h1>
          <p className="text-xl mb-10 max-w-2xl mx-auto leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
            FairLens audits your ML models and datasets for hidden discrimination —
            then fixes it. Built for teams who need fairness, not just compliance checkboxes.
          </p>
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <button onClick={onStart} className="btn-primary text-base px-8 py-4">
              ⚖️ Start Free Audit
            </button>
            <a href="#how-it-works"
              className="btn-secondary text-base px-8 py-4">
              See how it works ↓
            </a>
          </div>
        </div>
      </section>

      {/* ── Stats ── */}
      <section className="py-12 px-6 border-y" style={{ borderColor: 'var(--border)', background: 'var(--bg-tertiary)' }}>
        <div className="max-w-4xl mx-auto grid grid-cols-2 sm:grid-cols-4 gap-6">
          {METRICS.map(({ label, value }) => (
            <div key={label} className="text-center">
              <div className="text-4xl font-extrabold gradient-text">{value}</div>
              <div className="text-sm mt-1 font-medium" style={{ color: 'var(--text-muted)' }}>{label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Features ── */}
      <section className="py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-extrabold mb-3" style={{ color: 'var(--text-primary)' }}>
              Everything you need to ship fair AI
            </h2>
            <p className="text-lg" style={{ color: 'var(--text-secondary)' }}>
              From raw data to compliance-ready PDF report in under 60 seconds.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map(({ icon, title, desc }) => (
              <div key={title} className="card group cursor-default">
                <div className="text-3xl mb-4">{icon}</div>
                <h3 className="font-bold text-base mb-2" style={{ color: 'var(--text-primary)' }}>{title}</h3>
                <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How it works ── */}
      <section id="how-it-works" className="py-20 px-6" style={{ background: 'var(--bg-tertiary)' }}>
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-extrabold mb-3" style={{ color: 'var(--text-primary)' }}>How FairLens works</h2>
            <p style={{ color: 'var(--text-secondary)' }}>Four steps from upload to fair model.</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {STEPS.map(({ n, title, desc }) => (
              <div key={n} className="card flex gap-5">
                <div className="text-3xl font-extrabold gradient-text flex-shrink-0 w-12">{n}</div>
                <div>
                  <h3 className="font-bold mb-1" style={{ color: 'var(--text-primary)' }}>{title}</h3>
                  <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="py-20 px-6 text-center">
        <div className="max-w-2xl mx-auto">
          <h2 className="text-3xl font-extrabold mb-4" style={{ color: 'var(--text-primary)' }}>
            Ready to audit your AI?
          </h2>
          <p className="text-lg mb-8" style={{ color: 'var(--text-secondary)' }}>
            Upload any dataset. Get results in seconds. No signup required.
          </p>
          <button onClick={onStart} className="btn-primary text-lg px-10 py-4 mx-auto justify-center">
            ⚖️ Launch FairLens Free
          </button>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t py-8 px-6" style={{ borderColor: 'var(--border)', background: 'var(--bg-secondary)' }}>
        <div className="max-w-6xl mx-auto flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-sm font-bold">⚖</div>
            <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>FairLens</span>
            <span className="text-sm" style={{ color: 'var(--text-muted)' }}>— Google Solution Challenge 2026</span>
          </div>
          <div className="text-sm" style={{ color: 'var(--text-muted)' }}>
            Built with FastAPI · React · Google Gemini · Cloud Run
          </div>
        </div>
      </footer>
    </div>
  )
}
