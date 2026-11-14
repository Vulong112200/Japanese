import { useEffect, useState } from 'react'
import { api, type Vocab, type VocabDetail } from '../api'
import { Button, ErrorBox, IssueList, Loading, Panel, SpeakButton, StatusBadge, Tag } from '../ui'

const PAGE = 50

export default function Vocabulary() {
  const [q, setQ] = useState('')
  const [deck, setDeck] = useState('')
  const [status, setStatus] = useState('')
  const [offset, setOffset] = useState(0)
  const [data, setData] = useState<{ total: number; items: Vocab[] } | null>(null)
  const [decks, setDecks] = useState<{ deck: string; lesson_number: number | null; n: number }[]>([])
  const [err, setErr] = useState<unknown>(null)
  const [openId, setOpenId] = useState<string | null>(null)

  useEffect(() => { api.decks().then(setDecks).catch(setErr) }, [])
  useEffect(() => {
    const t = setTimeout(() => {
      api.vocab({ q, deck, status, limit: PAGE, offset }).then(setData).catch(setErr)
    }, 200)
    return () => clearTimeout(t)
  }, [q, deck, status, offset])

  if (err) return <ErrorBox error={err} />
  const input = 'rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-900'

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Từ vựng</h1>
        <p className="text-sm text-slate-500">Nhập từ flashcard CSV của bạn. Mục "Chưa xác minh" vẫn học được; mục "Cần duyệt" có vấn đề được phát hiện.</p>
      </div>
      <div className="flex flex-wrap gap-2">
        <label className="sr-only" htmlFor="vq">Tìm kiếm</label>
        <input id="vq" className={`${input} min-w-0 flex-1`} placeholder="Tìm: kanji, kana, romaji, nghĩa, Hán-Việt…"
          value={q} onChange={e => { setQ(e.target.value); setOffset(0) }} />
        <select aria-label="Lọc theo bài" className={input} value={deck} onChange={e => { setDeck(e.target.value); setOffset(0) }}>
          <option value="">Tất cả bài</option>
          {decks.map(d => <option key={d.deck} value={d.deck}>{d.lesson_number ? `Bài ${d.lesson_number}` : d.deck} ({d.n})</option>)}
        </select>
        <select aria-label="Lọc theo trạng thái" className={input} value={status} onChange={e => { setStatus(e.target.value); setOffset(0) }}>
          <option value="">Mọi trạng thái</option>
          <option value="verified">Đã xác minh</option>
          <option value="normalized">Chưa xác minh</option>
          <option value="needs_review">Cần duyệt</option>
          <option value="rejected">Đã loại</option>
        </select>
      </div>

      {!data ? <Loading /> : (
        <>
          <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-left text-xs text-slate-500 dark:bg-slate-800/50">
                <tr><th className="px-3 py-2">Từ</th><th className="px-3 py-2">Cách đọc</th><th className="hidden px-3 py-2 md:table-cell">Hán-Việt</th>
                  <th className="px-3 py-2">Nghĩa</th><th className="hidden px-3 py-2 sm:table-cell">Bài</th><th className="px-3 py-2">Trạng thái</th></tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {data.items.map(v => (
                  <tr key={v.id} className="cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/50" onClick={() => setOpenId(v.id)}>
                    <td className="jp px-3 py-2 text-base font-medium">
                      <button type="button" className="text-left hover:underline" onClick={() => setOpenId(v.id)}>{v.word}</button>
                    </td>
                    <td className="jp px-3 py-2">{v.reading}</td>
                    <td className="hidden px-3 py-2 text-xs text-slate-500 md:table-cell">{v.han_viet}</td>
                    <td className="px-3 py-2">{v.meaning_vi}</td>
                    <td className="hidden px-3 py-2 text-slate-500 sm:table-cell">{v.lesson_number ?? v.deck.slice(0, 12)}</td>
                    <td className="px-3 py-2"><StatusBadge status={v.verification_status} /></td>
                  </tr>
                ))}
                {data.items.length === 0 && <tr><td colSpan={6} className="px-3 py-6 text-center text-slate-500">Không có kết quả.</td></tr>}
              </tbody>
            </table>
          </div>
          <div className="flex items-center justify-between text-sm text-slate-500">
            <span>{data.total ? `${offset + 1}–${Math.min(offset + PAGE, data.total)} / ${data.total}` : '0'}</span>
            <div className="flex gap-2">
              <Button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE))}>← Trước</Button>
              <Button disabled={offset + PAGE >= data.total} onClick={() => setOffset(offset + PAGE)}>Sau →</Button>
            </div>
          </div>
        </>
      )}
      {openId && <VocabDrawer id={openId} onClose={() => setOpenId(null)} />}
    </div>
  )
}

export function VocabDrawer({ id, onClose }: { id: string; onClose: () => void }) {
  const [v, setV] = useState<VocabDetail | null>(null)
  const [err, setErr] = useState<unknown>(null)
  useEffect(() => { setV(null); api.vocabItem(id).then(setV).catch(setErr) }, [id])
  useEffect(() => {
    const on = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    addEventListener('keydown', on)
    return () => removeEventListener('keydown', on)
  }, [onClose])

  return (
    <div className="fixed inset-0 z-30 flex justify-end bg-black/30" onClick={onClose}>
      <aside role="dialog" aria-modal="true" aria-label="Chi tiết từ vựng" onClick={e => e.stopPropagation()}
        className="h-full w-full max-w-lg overflow-y-auto bg-white p-5 shadow-xl dark:bg-slate-900">
        <div className="mb-4 flex justify-end"><Button kind="ghost" onClick={onClose}>Đóng ✕</Button></div>
        {err ? <ErrorBox error={err} /> : !v ? <Loading /> : (
          <div className="space-y-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="jp text-4xl font-semibold">{v.word}</span>
                <SpeakButton text={v.reading || v.word} />
              </div>
              <div className="jp mt-1 text-lg text-slate-600 dark:text-slate-300">{v.reading}</div>
              <div className="mt-1 flex flex-wrap gap-1.5 text-sm text-slate-500">
                {v.romaji && <span>{v.romaji}</span>}
                {v.han_viet && <Tag>{v.han_viet}</Tag>}
                <StatusBadge status={v.verification_status} />
              </div>
            </div>
            <p className="text-lg">{v.meaning_vi}</p>
            {v.example_jp && (
              <Panel title="Ví dụ">
                <p className="jp text-base">{v.example_jp} <SpeakButton text={v.example_jp} /></p>
                {v.example_romaji && <p className="text-sm text-slate-500">{v.example_romaji}</p>}
                {v.example_vi && <p className="mt-1 text-sm">{v.example_vi}</p>}
              </Panel>
            )}
            {v.part_of_speech === 'verb' && !v.verb_group && (
              <p className="text-xs text-slate-500">Nhóm động từ: chưa xác định (dữ liệu chỉ có thể ます; không suy đoán từ đuôi ます).</p>
            )}
            <Panel title="Vấn đề phát hiện"><IssueList issues={v.issues} /></Panel>
            <Panel title="Nguồn gốc (lớp RAW)">
              <ul className="space-y-2 text-xs">
                {v.raw.map(r => (
                  <li key={r.raw_id} className="rounded-lg bg-slate-50 p-2 dark:bg-slate-800/60">
                    <div className="mb-1 text-slate-500">{r.source_id} · {r.locator} · {r.extraction_method}</div>
                    <pre className="jp whitespace-pre-wrap break-words">{formatRaw(r.content)}</pre>
                  </li>
                ))}
              </ul>
              <p className="mt-2 text-xs text-slate-500">{v.sources.map(s => s.location).join(', ')}</p>
            </Panel>
          </div>
        )}
      </aside>
    </div>
  )
}

export function formatRaw(content: string) {
  try {
    const row = JSON.parse(content)
    return Array.isArray(row) ? row.join('\n────\n') : content
  } catch { return content }
}
