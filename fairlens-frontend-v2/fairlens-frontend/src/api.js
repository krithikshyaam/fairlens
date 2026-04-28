import axios from 'axios'

const BASE = ''   // Vite proxy handles /analyze, /mitigate, /report

// ── POST /analyze ──────────────────────────────────────────────────────────
export async function analyzeDataset({ file, targetColumn, protectedAttributes, positiveLabel }) {
  const form = new FormData()
  form.append('file', file)
  form.append('target_column', targetColumn)
  form.append('protected_attributes', JSON.stringify(protectedAttributes))
  form.append('positive_label', positiveLabel)

  const { data } = await axios.post(`${BASE}/analyze`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

// ── POST /mitigate ─────────────────────────────────────────────────────────
export async function mitigateDataset({ analysisId, strategy, targetColumn, protectedAttributes, positiveLabel }) {
  const { data } = await axios.post(`${BASE}/mitigate`, {
    analysis_id: analysisId,
    strategy,
    target_column: targetColumn,
    protected_attributes: protectedAttributes,
    positive_label: positiveLabel,
  })
  return data
}

// ── POST /report ───────────────────────────────────────────────────────────
export async function downloadReport({ analysisId, includeMitigation }) {
  const response = await axios.post(
    `${BASE}/report`,
    { analysis_id: analysisId, include_mitigation: includeMitigation },
    { responseType: 'blob' }
  )
  const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
  const link = document.createElement('a')
  link.href = url
  link.download = `fairlens_audit_${analysisId.slice(0, 8)}.pdf`
  link.click()
  window.URL.revokeObjectURL(url)
}
