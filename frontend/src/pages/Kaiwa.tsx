import { useEffect, useState } from 'react'
import { api, type KaiwaDetail, type KaiwaItem } from '../api'
import { ErrorBox, IssueList, Loading, Panel, SpeakButton, StatusBadge, Tag } from '../ui'

const TOPICS: Record<string, string> = {
  self_intro: 'Giới thiệu bản thân',
  greetings: 'Chào hỏi',
  shopping: 'Mua sắm',
  directions: 'Hỏi đường',
  transportation: 'Phương tiện đi lại',
  restaurant: 'Gọi món ăn',
  daily_routine: 'Sinh hoạt hằng ngày',
  work_school: 'Công việc và trường học',
  time_dates: 'Giờ giấc, ngày tháng',
}

export default function Kaiwa() {
  const [items, setItems] = useState<KaiwaItem[] | null>(null)
  const [sel, setSel] = useState<string | null>(() => new URLSearchParams(location.hash.split('?')[1] ?? '').get('id'))
  const [err, setErr] = useState<unknown>(null)
  useEffect(() => { api.kaiwa().then(setItems).catch(setErr) }, [])

  if (err) return <ErrorBox error={err} />
  const groups = new Map<string, KaiwaItem[]>()
  for (const k of items ?? []) groups.set(k.topic, [...(groups.get(k.topic) ?? []), k])

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Hội thoại (Kaiwa)</h1>
        <p className="text-sm text-slate-500">Học bổ trợ theo 9 chủ đề, chỉ dùng từ vựng và ngữ pháp N5 đã xác minh. Không phải một phần của đề thi JLPT.</p>
      </div>
      <div className="grid gap-4 lg:grid-cols-[320px_1fr]">
        <div className="max-h-[75vh] overflow-y-auto rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
          {!items ? <Loading /> : [...groups.entries()].map(([topic, ks]) => (
            <div key={topic}>
              <div className="sticky top-0 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-500 dark:bg-slate-800">{TOPICS[topic] ?? topic}</div>
              <ul className="divide-y divide-slate-100 dark:divide-slate-800">
                {ks.map(k => (
                  <li key={k.id}>
                    <button type="button" onClick={() => setSel(k.id)} aria-current={sel === k.id ? 'true' : undefined}
                      className={`w-full px-3 py-2 text-left text-sm hover:bg-slate-50 dark:hover:bg-slate-800/60 ${sel === k.id ? 'bg-indigo-50 dark:bg-indigo-950/50' : ''}`}>
                      <div className="font-medium">{k.title_vi}</div>
                      <div className="text-xs text-slate-500">{k.line_count} lượt lời</div>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div>{sel ? <KaiwaView id={sel} /> : <Panel><p className="text-sm text-slate-500">Chọn một hội thoại.</p></Panel>}</div>
      </div>
    </div>
  )
}

function KaiwaView({ id }: { id: string }) {
  const [k, setK] = useState<KaiwaDetail | null>(null)
  const [err, setErr] = useState<unknown>(null)
  const [showKana, setShowKana] = useState(true)
  const [showVi, setShowVi] = useState(true)
  useEffect(() => { setK(null); api.kaiwaItem(id).then(setK).catch(setErr) }, [id])
  if (err) return <ErrorBox error={err} />
  if (!k) return <Loading />
  const toggle = 'rounded-lg border border-slate-300 px-2 py-1 text-xs hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800'
  return (
    <div className="space-y-4">
      <Panel>
        <div className="flex flex-wrap items-center gap-2">
          <h2 className="text-lg font-semibold">{k.title_vi}</h2>
          <StatusBadge status={k.verification_status} by={k.verified_by} />
          <Tag tone="indigo">AI soạn</Tag>
          <Tag>{TOPICS[k.topic] ?? k.topic}</Tag>
        </div>
        {k.situation_vi && <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{k.situation_vi}</p>}
        <div className="mt-3 flex gap-2">
          <button type="button" className={toggle} aria-pressed={showKana} onClick={() => setShowKana(!showKana)}>
            {showKana ? 'Ẩn' : 'Hiện'} hiragana</button>
          <button type="button" className={toggle} aria-pressed={showVi} onClick={() => setShowVi(!showVi)}>
            {showVi ? 'Ẩn' : 'Hiện'} bản dịch</button>
        </div>
      </Panel>
      <Panel title="Hội thoại">
        <ol className="space-y-3">
          {k.lines.map((ln, i) => (
            <li key={i} className="grid grid-cols-[5.5rem_1fr] gap-2">
              <span className="jp pt-0.5 text-sm font-semibold text-indigo-700 dark:text-indigo-300">{ln.speaker}</span>
              <div>
                <p className="jp text-base">{ln.jp} <SpeakButton text={ln.hiragana || ln.jp} /></p>
                {showKana && <p className="jp text-xs text-slate-500">{ln.hiragana}</p>}
                {showVi && <p className="text-sm">{ln.vi}</p>}
              </div>
            </li>
          ))}
        </ol>
      </Panel>
      <div className="grid gap-4 md:grid-cols-2">
        {k.vocab.length > 0 && (
          <Panel title="Từ vựng">
            <ul className="space-y-1 text-sm">{k.vocab.map(v => (
              <li key={v.ref}><span className="jp font-medium">{v.word}</span> <span className="jp text-slate-500">({v.reading})</span>: {v.meaning_vi}</li>
            ))}</ul>
          </Panel>
        )}
        {k.grammar.length > 0 && (
          <Panel title="Ngữ pháp">
            <ul className="space-y-1 text-sm">{k.grammar.map(g => (
              <li key={g.id}><a className="jp text-indigo-700 underline dark:text-indigo-300" href={`#/grammar?id=${g.id}`}>{g.pattern}</a></li>
            ))}</ul>
          </Panel>
        )}
      </div>
      {k.issues.some(i => !i.resolved) && <Panel title="Vấn đề phát hiện"><IssueList issues={k.issues} /></Panel>}
    </div>
  )
}
