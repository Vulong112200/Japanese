import { useEffect, useState } from 'react'
import { api, type GrammarDetail, type GrammarItem } from '../api'
import { ErrorBox, IssueList, Loading, Panel, SpeakButton, StatusBadge, Tag } from '../ui'

const ORIGIN: Record<string, string> = {
  handbook: 'Cẩm nang của bạn',
  'handbook+ai': 'Cẩm nang + AI bổ sung/sửa',
  ai: 'AI soạn (bổ sung)',
}

export default function Grammar() {
  const [items, setItems] = useState<GrammarItem[] | null>(null)
  const [q, setQ] = useState('')
  const [lesson, setLesson] = useState('')
  const [sel, setSel] = useState<string | null>(() => new URLSearchParams(location.hash.split('?')[1] ?? '').get('id'))
  const [err, setErr] = useState<unknown>(null)

  useEffect(() => {
    const t = setTimeout(() => {
      api.grammar(q, lesson ? Number(lesson) : undefined).then(setItems).catch(setErr)
    }, 200)
    return () => clearTimeout(t)
  }, [q, lesson])

  if (err) return <ErrorBox error={err} />
  const input = 'rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-900'
  const groups = new Map<string, GrammarItem[]>()
  for (const g of items ?? []) {
    const k = g.lesson_number ? `Bài ${g.lesson_number}` : 'N5 bổ sung / đối chiếu'
    groups.set(k, [...(groups.get(k) ?? []), g])
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Ngữ pháp N5</h1>
        <p className="text-sm text-slate-500">Theo Minna no Nihongo bài 1–25, cộng các điểm N5 thường gặp. Mỗi mục ghi rõ nguồn: cẩm nang của bạn hay AI bổ sung.</p>
      </div>
      <div className="flex flex-wrap gap-2">
        <input aria-label="Tìm ngữ pháp" className={`${input} min-w-0 flex-1`} placeholder="Tìm: mẫu câu, nghĩa…" value={q} onChange={e => setQ(e.target.value)} />
        <select aria-label="Bài" className={input} value={lesson} onChange={e => setLesson(e.target.value)}>
          <option value="">Tất cả bài</option>
          {Array.from({ length: 25 }, (_, i) => <option key={i + 1} value={i + 1}>Bài {i + 1}</option>)}
        </select>
      </div>
      <div className="grid gap-4 lg:grid-cols-[340px_1fr]">
        <div className="max-h-[75vh] overflow-y-auto rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
          {!items ? <Loading /> : [...groups.entries()].map(([k, gs]) => (
            <div key={k}>
              <div className="sticky top-0 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-500 dark:bg-slate-800">{k}</div>
              <ul className="divide-y divide-slate-100 dark:divide-slate-800">
                {gs.map(g => (
                  <li key={g.id}>
                    <button type="button" onClick={() => setSel(g.id)}
                      className={`w-full px-3 py-2 text-left text-sm hover:bg-slate-50 dark:hover:bg-slate-800/60 ${sel === g.id ? 'bg-indigo-50 dark:bg-indigo-950/50' : ''}`}>
                      <div className="jp font-medium">{g.pattern}</div>
                      <div className="text-xs text-slate-500">{g.meaning_vi}</div>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div>{sel ? <GrammarView id={sel} /> : <Panel><p className="text-sm text-slate-500">Chọn một mẫu ngữ pháp.</p></Panel>}</div>
      </div>
    </div>
  )
}

function GrammarView({ id }: { id: string }) {
  const [g, setG] = useState<GrammarDetail | null>(null)
  const [err, setErr] = useState<unknown>(null)
  useEffect(() => { setG(null); api.grammarItem(id).then(setG).catch(setErr) }, [id])
  if (err) return <ErrorBox error={err} />
  if (!g) return <Loading />
  const list = (xs: string[] | undefined) => xs && xs.length > 0 && <ul className="list-disc space-y-1 pl-5 text-sm">{xs.map((x, i) => <li key={i}>{x}</li>)}</ul>
  return (
    <div className="space-y-4">
      <Panel>
        <div className="flex flex-wrap items-center gap-2">
          <h2 className="jp text-2xl font-semibold">{g.pattern}</h2>
          <StatusBadge status={g.verification_status} by={g.verified_by} />
          <Tag tone={g.origin === 'ai' ? 'indigo' : 'slate'}>{ORIGIN[g.origin] ?? g.origin}</Tag>
          {g.lesson_number && <Tag>Bài {g.lesson_number}</Tag>}
        </div>
        {g.grammar_name_vi && <p className="mt-1 font-medium">{g.grammar_name_vi}</p>}
        <p className="mt-2"><b>Ý nghĩa:</b> {g.meaning_vi}</p>
        <p className="jp mt-2 rounded-lg bg-slate-50 p-2 text-sm dark:bg-slate-800/60"><b>Cấu trúc:</b> {g.formation}</p>
        {g.explanation_vi && <p className="mt-2 text-sm leading-relaxed">{g.explanation_vi}</p>}
        {g.level_note && <p className="mt-2 text-xs text-amber-700 dark:text-amber-300">{g.level_note}</p>}
      </Panel>
      <Panel title="Ví dụ">
        <ul className="space-y-3">
          {g.examples.map((ex, i) => (
            <li key={i}>
              <p className="jp text-base">{ex.jp} <SpeakButton text={ex.hiragana || ex.jp} /></p>
              {ex.hiragana && <p className="jp text-xs text-slate-500">{ex.hiragana}</p>}
              {ex.romaji && <p className="text-xs text-slate-500">{ex.romaji}</p>}
              <p className="text-sm">{ex.vi}</p>
            </li>
          ))}
        </ul>
      </Panel>
      <div className="grid gap-4 md:grid-cols-2">
        {g.usage?.length > 0 && <Panel title="Cách dùng">{list(g.usage)}</Panel>}
        {g.restrictions?.length > 0 && <Panel title="Giới hạn / lưu ý">{list(g.restrictions)}</Panel>}
        {g.common_mistakes?.length > 0 && <Panel title="Lỗi thường gặp & bẫy JLPT">{list(g.common_mistakes)}</Panel>}
        {g.similar_patterns?.length > 0 && (
          <Panel title="Mẫu tương tự">
            <ul className="space-y-1 text-sm">{g.similar_patterns.map((s, i) => <li key={i}><span className="jp font-medium">{s.pattern}</span>: {s.difference_vi}</li>)}</ul>
          </Panel>
        )}
      </div>
      {g.formality && <p className="text-xs text-slate-500">Mức độ trang trọng: {g.formality}</p>}
      {g.handbook_errors?.length > 0 && (
        <Panel title="Đã sửa so với cẩm nang gốc">
          <ul className="space-y-2 text-sm">{g.handbook_errors.map((e, i) => (
            <li key={i}><del className="jp text-rose-600">{e.quote}</del><br />{e.problem_vi} → <span className="text-emerald-700 dark:text-emerald-300">{e.correction_vi}</span></li>
          ))}</ul>
        </Panel>
      )}
      {g.issues.some(i => !i.resolved) && <Panel title="Vấn đề phát hiện"><IssueList issues={g.issues} /></Panel>}
    </div>
  )
}
