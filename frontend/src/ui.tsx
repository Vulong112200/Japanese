import type { ReactNode } from 'react'
import type { Issue, Status } from './api'

const STATUS: Record<string, [string, string]> = {
  verified: ['Đã xác minh', 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-200'],
  normalized: ['Chưa xác minh', 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200'],
  needs_review: ['Cần duyệt', 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200'],
  rejected: ['Đã loại', 'bg-slate-200 text-slate-600 dark:bg-slate-800 dark:text-slate-400'],
  extracted: ['Đã trích', 'bg-sky-100 text-sky-800 dark:bg-sky-900/40 dark:text-sky-200'],
  raw: ['RAW', 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'],
}

export function StatusBadge({ status, by }: { status: Status | string; by?: string | null }) {
  const [base, cls] = STATUS[status] ?? [status, 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300']
  const label = status === 'verified' && by ? `${base} · ${by === 'user' ? 'bạn' : 'AI + từ điển'}` : base
  const title = status === 'verified' && by === 'ai'
    ? 'Đã qua 2 vòng rà soát AI độc lập, đối chiếu JMdict/KANJIDIC2 và các luật kiểm tra tự động' : undefined
  return <span title={title} className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium whitespace-nowrap ${cls}`}>{label}</span>
}

export function Tag({ children, tone = 'slate' }: { children: ReactNode; tone?: 'slate' | 'indigo' | 'amber' | 'rose' | 'emerald' }) {
  const tones = {
    slate: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
    indigo: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/50 dark:text-indigo-200',
    amber: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200',
    rose: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200',
    emerald: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-200',
  }
  return <span className={`inline-flex rounded px-1.5 py-0.5 text-xs font-medium ${tones[tone]}`}>{children}</span>
}

export function Panel({ title, children, action }: { title?: ReactNode; children: ReactNode; action?: ReactNode }) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      {(title || action) && (
        <div className="mb-3 flex items-center justify-between gap-2">
          <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-200">{title}</h2>
          {action}
        </div>
      )}
      {children}
    </section>
  )
}

export function Button({ children, onClick, kind = 'default', disabled, type = 'button', title }: {
  children: ReactNode; onClick?: () => void; kind?: 'default' | 'primary' | 'danger' | 'ghost'; disabled?: boolean
  type?: 'button' | 'submit'; title?: string
}) {
  const kinds = {
    default: 'border border-slate-300 bg-white hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:hover:bg-slate-700',
    primary: 'bg-indigo-600 text-white hover:bg-indigo-500',
    danger: 'bg-rose-600 text-white hover:bg-rose-500',
    ghost: 'hover:bg-slate-100 dark:hover:bg-slate-800',
  }
  return (
    <button type={type} title={title} disabled={disabled} onClick={onClick}
      className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${kinds[kind]}`}>
      {children}
    </button>
  )
}

const SEV: Record<Issue['severity'], string> = {
  error: 'border-rose-300 bg-rose-50 dark:border-rose-800 dark:bg-rose-950/40',
  warning: 'border-amber-300 bg-amber-50 dark:border-amber-800 dark:bg-amber-950/30',
  info: 'border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-800/50',
}

export function IssueList({ issues }: { issues: Issue[] }) {
  const open = issues.filter(i => !i.resolved)
  if (!open.length) return <p className="text-sm text-slate-500">Không có vấn đề mở.</p>
  return (
    <ul className="space-y-2">
      {open.map(i => (
        <li key={i.issue_id} className={`rounded-lg border p-2 text-sm ${SEV[i.severity]}`}>
          <div className="flex flex-wrap items-center gap-1.5">
            <Tag tone={i.severity === 'error' ? 'rose' : i.severity === 'warning' ? 'amber' : 'slate'}>{i.severity}</Tag>
            <Tag tone={i.origin === 'ai_review' ? 'indigo' : 'slate'}>{i.origin === 'ai_review' ? 'AI rà soát' : i.origin === 'user' ? 'Người dùng' : 'Luật tự động'}</Tag>
            <code className="text-xs text-slate-500">{i.code}</code>
          </div>
          <p className="mt-1">{i.message}</p>
          {i.suggestion && <p className="mt-1 text-slate-600 dark:text-slate-300">Đề xuất: <span className="jp font-medium">{i.suggestion}</span></p>}
        </li>
      ))}
    </ul>
  )
}

export function Loading() {
  return <p className="p-4 text-sm text-slate-500" role="status">Đang tải…</p>
}

export function ErrorBox({ error }: { error: unknown }) {
  return <p role="alert" className="rounded-lg border border-rose-300 bg-rose-50 p-3 text-sm text-rose-800 dark:border-rose-800 dark:bg-rose-950/40 dark:text-rose-200">
    Lỗi: {error instanceof Error ? error.message : String(error)} — kiểm tra backend (python -m hub) đang chạy.
  </p>
}

/** Browser speech synthesis. Clearly labelled: NOT original audio. */
export function speak(text: string) {
  try {
    const u = new SpeechSynthesisUtterance(text)
    u.lang = 'ja-JP'
    u.rate = 0.9
    speechSynthesis.cancel()
    speechSynthesis.speak(u)
  } catch { /* unsupported browser */ }
}

export function SpeakButton({ text }: { text: string }) {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) return null
  return (
    <button type="button" onClick={() => speak(text)} title="Phát âm bằng giọng máy của trình duyệt (không phải audio gốc)"
      className="rounded-md px-1.5 py-0.5 text-sm text-slate-500 hover:bg-slate-100 hover:text-slate-800 dark:hover:bg-slate-800 dark:hover:text-slate-100"
      aria-label={`Phát âm ${text} (giọng máy)`}>
      🔊<span className="ml-1 text-[10px] align-middle">giọng máy</span>
    </button>
  )
}
