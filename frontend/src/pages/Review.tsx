import { useCallback, useEffect, useState } from 'react'
import { api, type Question, type QuestionDetail, type Vocab, type VocabDetail } from '../api'
import { Button, ErrorBox, IssueList, Loading, Panel, StatusBadge, Tag } from '../ui'
import { formatRaw } from './Vocabulary'

type Entity = 'vocabulary' | 'question'

export default function Review() {
  const [entity, setEntity] = useState<Entity>('vocabulary')
  const [status, setStatus] = useState('needs_review')
  const [offset, setOffset] = useState(0)
  const [list, setList] = useState<{ total: number; items: (Vocab & Question)[] } | null>(null)
  const [sel, setSel] = useState<string | null>(null)
  const [err, setErr] = useState<unknown>(null)

  const load = useCallback(() => {
    api.queue(entity, status, offset).then(setList).catch(setErr)
  }, [entity, status, offset])
  useEffect(() => { setList(null); load() }, [load])

  const keyOf = (i: Vocab & Question) => (entity === 'vocabulary' ? i.id : i.question_id)
  const next = () => {
    if (!list) return
    const idx = list.items.findIndex(i => keyOf(i) === sel)
    const n = list.items[idx + 1]
    load()
    setSel(n ? keyOf(n) : null)
  }

  if (err) return <ErrorBox error={err} />
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Duyệt dữ liệu</h1>
        <p className="text-sm text-slate-500">Chỉ người dùng mới đưa được dữ liệu vào trạng thái "Đã xác minh". Gợi ý của AI và luật tự động không tự sửa dữ liệu.</p>
      </div>
      <div className="flex flex-wrap gap-2">
        {(['vocabulary', 'question'] as Entity[]).map(e => (
          <Button key={e} kind={entity === e ? 'primary' : 'default'} onClick={() => { setEntity(e); setSel(null); setOffset(0) }}>
            {e === 'vocabulary' ? 'Từ vựng' : 'Câu hỏi đề mẫu'}
          </Button>
        ))}
        <select aria-label="Trạng thái" value={status} onChange={e => { setStatus(e.target.value); setOffset(0); setSel(null) }}
          className="rounded-lg border border-slate-300 bg-white px-2 py-1 text-sm dark:border-slate-700 dark:bg-slate-900">
          <option value="needs_review">Cần duyệt</option>
          <option value="normalized">Chưa xác minh (không lỗi)</option>
          <option value="verified">Đã xác minh</option>
          <option value="rejected">Đã loại</option>
        </select>
      </div>

      <div className="grid gap-4 lg:grid-cols-[320px_1fr]">
        <div className="rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
          {!list ? <Loading /> : (
            <>
              <div className="border-b border-slate-100 px-3 py-2 text-xs text-slate-500 dark:border-slate-800">{list.total} mục</div>
              <ul className="max-h-[65vh] divide-y divide-slate-100 overflow-y-auto dark:divide-slate-800">
                {list.items.map(i => (
                  <li key={keyOf(i)}>
                    <button type="button" onClick={() => setSel(keyOf(i))}
                      className={`flex w-full items-center justify-between gap-2 px-3 py-2 text-left text-sm hover:bg-slate-50 dark:hover:bg-slate-800/60 ${sel === keyOf(i) ? 'bg-indigo-50 dark:bg-indigo-950/50' : ''}`}>
                      <span className="jp truncate">{entity === 'vocabulary' ? `${i.word} · ${i.reading}` : `${i.question_id.replace('Q_N5S_', '')} ${i.question_text ?? '(chỉ có audio)'}`}</span>
                      {!!i.issue_count && <Tag tone="amber">{i.issue_count}</Tag>}
                    </button>
                  </li>
                ))}
              </ul>
              <div className="flex justify-between border-t border-slate-100 p-2 dark:border-slate-800">
                <Button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - 50))}>←</Button>
                <Button disabled={offset + 50 >= list.total} onClick={() => setOffset(offset + 50)}>→</Button>
              </div>
            </>
          )}
        </div>
        <div>
          {!sel ? <Panel><p className="text-sm text-slate-500">Chọn một mục để duyệt.</p></Panel>
            : entity === 'vocabulary' ? <VocabReview id={sel} onDone={next} /> : <QuestionReview id={sel} onDone={next} />}
        </div>
      </div>
    </div>
  )
}

function Actions({ entity, id, onDone, onUpdated, hasErrors }: {
  entity: Entity; id: string; onDone: () => void; onUpdated: (d: VocabDetail & QuestionDetail) => void; hasErrors: boolean
}) {
  const [note, setNote] = useState('')
  const [msg, setMsg] = useState<string | null>(null)
  const act = async (action: string, extra: object = {}) => {
    setMsg(null)
    try {
      const d = await api.review(entity, id, { action, note: note || null, ...extra })
      onUpdated(d)
      setNote('')
      if (action !== 'reextract') onDone()
    } catch (e) { setMsg(e instanceof Error ? e.message : String(e)) }
  }
  return (
    <Panel title="Quyết định">
      <label className="mb-2 block text-sm">Ghi chú (tuỳ chọn)
        <textarea value={note} onChange={e => setNote(e.target.value)} rows={2}
          className="mt-1 w-full rounded-lg border border-slate-300 bg-white p-2 text-sm dark:border-slate-700 dark:bg-slate-950" />
      </label>
      <div className="flex flex-wrap gap-2">
        <Button kind="primary" onClick={() => act('approve')} title="Xác nhận dữ liệu đúng">Duyệt ✓</Button>
        {hasErrors && <Button onClick={() => act('approve', { force: true })} title="Vẫn duyệt dù còn lỗi mức error">Duyệt dù còn lỗi</Button>}
        <Button onClick={() => act('ambiguous')}>Đánh dấu mơ hồ</Button>
        <Button onClick={() => act('reextract')}>{entity === 'vocabulary' ? 'Trích xuất lại từ RAW' : 'Yêu cầu chép lại'}</Button>
        <Button kind="danger" onClick={() => act('reject')}>Loại</Button>
      </div>
      {msg && <p role="alert" className="mt-2 text-sm text-rose-600">{msg}</p>}
    </Panel>
  )
}

const EDITABLE: [keyof Vocab, string][] = [
  ['word', 'Từ'], ['reading', 'Cách đọc (kana)'], ['romaji', 'Romaji'], ['han_viet', 'Hán-Việt'], ['meaning_vi', 'Nghĩa'],
  ['example_jp', 'Ví dụ (JP)'], ['example_romaji', 'Romaji ví dụ'], ['example_vi', 'Dịch ví dụ'],
]

function VocabReview({ id, onDone }: { id: string; onDone: () => void }) {
  const [v, setV] = useState<VocabDetail | null>(null)
  const [form, setForm] = useState<Record<string, string>>({})
  const [err, setErr] = useState<unknown>(null)
  const [saved, setSaved] = useState(false)
  useEffect(() => {
    setV(null); setSaved(false)
    api.vocabItem(id).then(d => { setV(d); setForm(Object.fromEntries(EDITABLE.map(([k]) => [k, String(d[k] ?? '')]))) }).catch(setErr)
  }, [id])
  if (err) return <ErrorBox error={err} />
  if (!v) return <Loading />

  const changed = EDITABLE.filter(([k]) => (form[k] ?? '') !== String(v[k] ?? ''))
  const applySuggestion = (code: string, suggestion: string) => {
    const field = code.replace(/^ai_/, '')
    if (EDITABLE.some(([k]) => k === field)) setForm(f => ({ ...f, [field]: suggestion }))
  }
  const save = async () => {
    const edit = Object.fromEntries(changed.map(([k]) => [k, form[k] || null]))
    const d = await api.review('vocabulary', id, { action: 'edit', note: 'Sửa trên màn hình duyệt', edit })
    setV(d); setSaved(true)
  }

  return (
    <div className="space-y-4">
      <Panel title={<span className="flex items-center gap-2">{v.id} <StatusBadge status={v.verification_status} /></span>}>
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <h3 className="mb-1 text-xs font-semibold uppercase text-slate-500">Nội dung gốc (RAW, bất biến)</h3>
            {v.raw.map(r => (
              <pre key={r.raw_id} className="jp mb-2 whitespace-pre-wrap break-words rounded-lg bg-slate-50 p-2 text-xs dark:bg-slate-800/60">
                <span className="block text-slate-500">{r.source_id} · {r.locator}</span>{formatRaw(r.content)}
              </pre>
            ))}
          </div>
          <div>
            <h3 className="mb-1 text-xs font-semibold uppercase text-slate-500">Dữ liệu chuẩn hoá (sửa được)</h3>
            <div className="space-y-2">
              {EDITABLE.map(([k, label]) => (
                <label key={k} className="block text-xs text-slate-500">{label}
                  <input value={form[k] ?? ''} onChange={e => setForm(f => ({ ...f, [k]: e.target.value }))}
                    className="jp mt-0.5 w-full rounded-md border border-slate-300 bg-white px-2 py-1 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100" />
                </label>
              ))}
              <div className="flex items-center gap-2">
                <Button disabled={!changed.length} onClick={save}>Lưu {changed.length ? `${changed.length} thay đổi` : ''}</Button>
                {saved && <span className="text-xs text-emerald-600">Đã lưu — vẫn ở "Cần duyệt" cho đến khi bạn bấm Duyệt.</span>}
              </div>
            </div>
          </div>
        </div>
      </Panel>
      <Panel title="Vấn đề & gợi ý">
        <IssueList issues={v.issues} />
        {v.issues.some(i => i.suggestion && !i.resolved) && (
          <div className="mt-2 flex flex-wrap gap-2">
            {v.issues.filter(i => i.suggestion && !i.resolved).map(i => (
              <Button key={i.issue_id} kind="ghost" onClick={() => applySuggestion(i.code, i.suggestion!)}>
                Điền gợi ý vào "{i.code.replace(/^ai_/, '')}"
              </Button>
            ))}
          </div>
        )}
      </Panel>
      <Actions entity="vocabulary" id={id} onDone={onDone} onUpdated={d => setV(d)}
        hasErrors={v.issues.some(i => !i.resolved && i.severity === 'error')} />
    </div>
  )
}

function QuestionReview({ id, onDone }: { id: string; onDone: () => void }) {
  const [q, setQ] = useState<QuestionDetail | null>(null)
  const [err, setErr] = useState<unknown>(null)
  useEffect(() => { setQ(null); api.question(id).then(setQ).catch(setErr) }, [id])
  if (err) return <ErrorBox error={err} />
  if (!q) return <Loading />
  const flags = q.extra_json as { options_audio_only?: boolean; options_are_pictures?: boolean; options_are_glyph_images?: boolean; expected_sequence_note?: string }

  return (
    <div className="space-y-4">
      <div className="grid gap-4 xl:grid-cols-2">
        <Panel title={`Ảnh trang gốc · trang ${q.source_page}`}>
          {q.page_asset_id && <img src={api.assetUrl(q.page_asset_id)} alt={`Trang ${q.source_page} của đề gốc`} className="w-full rounded-lg border border-slate-200 bg-white dark:border-slate-700" />}
          {q.passage?.image_asset_id && <img src={api.assetUrl(q.passage.image_asset_id)} alt="Bảng thông tin đi kèm" className="mt-2 w-full rounded-lg border border-slate-200 bg-white" />}
        </Panel>
        <div className="space-y-4">
          <Panel title={<span className="flex items-center gap-2">{q.question_id} <StatusBadge status={q.verification_status} /></span>}>
            <p className="text-xs text-slate-500">{q.section} · もんだい{q.mondai_no} · {q.mondai_type} · câu {q.number}</p>
            <p className="jp mt-2 text-sm text-slate-600 dark:text-slate-300">{q.instruction}</p>
            {q.passage && <pre className="jp mt-2 max-h-48 overflow-y-auto whitespace-pre-wrap rounded-lg bg-slate-50 p-2 text-sm dark:bg-slate-800/60">{q.passage.text}</pre>}
            <p className="jp mt-2 text-lg">{q.question_text ?? <i className="text-slate-500">(câu hỏi chỉ có trong audio)</i>}</p>
            <ol className="mt-2 space-y-1">
              {q.options.map(o => (
                <li key={o.option_id} className={`jp rounded-md px-2 py-1 text-sm ${q.correct_answer.includes(o.option_id) ? 'bg-emerald-50 font-semibold dark:bg-emerald-950/40' : ''}`}>
                  {o.option_id}. {o.text ?? <i className="text-slate-500">(lựa chọn dạng ảnh — xem trang gốc)</i>}
                  {q.correct_answer.includes(o.option_id) && ' ✓ 正解'}
                </li>
              ))}
            </ol>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {flags.options_audio_only && <Tag tone="amber">Lựa chọn chỉ có trong audio — ẩn ở chế độ thi</Tag>}
              {flags.options_are_pictures && <Tag tone="amber">Lựa chọn là tranh</Tag>}
              {flags.options_are_glyph_images && <Tag tone="amber">Lựa chọn là glyph dạng ảnh</Tag>}
            </div>
            {flags.expected_sequence_note && <p className="mt-2 text-xs text-slate-500">{flags.expected_sequence_note}</p>}
            {q.review_notes && <p className="mt-2 text-xs text-amber-700 dark:text-amber-300">{q.review_notes}</p>}
          </Panel>
          {q.audio_asset_id && (
            <Panel title="Audio gốc (1 track cho cả phần nghe)">
              <audio controls preload="none" src={api.assetUrl(q.audio_asset_id)} className="w-full" />
              {q.transcript && <details className="mt-2 text-sm"><summary className="cursor-pointer text-slate-500">Script (từ N5-script.pdf, chép bằng AI)</summary>
                <pre className="jp mt-1 whitespace-pre-wrap">{q.transcript}</pre></details>}
            </Panel>
          )}
          {q.explanation_vi && (
            <Panel title={<span className="flex items-center gap-2">Giải thích <Tag tone="indigo">{q.explanation_origin}</Tag></span>}>
              <p className="text-sm">{q.explanation_vi}</p>
            </Panel>
          )}
        </div>
      </div>
      <Panel title="Vấn đề"><IssueList issues={q.issues} /></Panel>
      <Actions entity="question" id={id} onDone={onDone} onUpdated={d => setQ(d)}
        hasErrors={q.issues.some(i => !i.resolved && i.severity === 'error')} />
    </div>
  )
}
