export default function GeminiBox({ explanation }) {
  if (!explanation) return null
  return (
    <div className="rounded-2xl p-5 relative overflow-hidden"
      style={{ background: 'linear-gradient(135deg, rgba(99,102,241,0.08), rgba(139,92,246,0.08))', border: '1px solid rgba(99,102,241,0.2)' }}>
      <div className="absolute top-0 right-0 w-32 h-32 rounded-full opacity-10 blur-2xl"
        style={{ background: 'radial-gradient(circle, #6366f1, transparent)' }} />
      <div className="flex items-center gap-2 mb-3">
        <div className="w-7 h-7 rounded-lg flex items-center justify-center text-white text-sm font-bold shadow-md"
          style={{ background: 'linear-gradient(135deg, #4285f4, #9b59b6)' }}>G</div>
        <span className="font-bold text-sm" style={{ color: 'var(--text-primary)' }}>Gemini AI Explanation</span>
        <span className="text-xs ml-auto px-2 py-0.5 rounded-full"
          style={{ background: 'var(--bg-tertiary)', color: 'var(--text-muted)' }}>AI-generated</span>
      </div>
      <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{explanation}</p>
    </div>
  )
}
