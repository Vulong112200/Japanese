import { useCallback, useEffect, useState } from 'react'
import { api, type Card } from '../api'
import { Button, ErrorBox, Loading, Panel, SpeakButton, StatusBadge } from '../ui'

const RATINGS = [
  { id: 'again', label: 'Lại', key: '1', cls: 'bg-rose-600 hover:bg-rose-500' },
  { id: 'hard', label: 'Khó', key: '2', cls: 'bg-amber-600 hover:bg-amber-500' },
  { id: 'good', label: 'Được', key: '3', cls: 'bg-emerald-600 hover:bg-emerald-500' },
  { id: 'easy', label: 'Dễ', key: '4', cls: 'bg-sky-600 hover:bg-sky-500' },
] as const

function readPref<T>(k: string, d: T): T {
  try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d } catch { return d }
}
function writePref(k: string, v: unknown) {
  try { localStorage.setItem(k, JSON.stringify(v)) } catch { /* storage blocked */ }
}

export default function Flashcards() {
  const [direction, setDirection] = useState<'jp_vi' | 'vi_jp'>(() => readPref('srs.direction', 'jp_vi'))
  const [newLimit, setNewLimit] = useState<number>(() => readPref('srs.newLimit', 20))
  const [queue, setQueue] = useState<Card[] | null>(null)
  const [shown, setShown] = useState(false)
  const [done, setDone] = useState(0)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<unknown>(null)

  const load = useCallback(() => {
    setQueue(null); setShown(false)
    api.due(direction, newLimit).then(setQueue).catch(setErr)
  }, [direction, newLimit])
  useEffect(() => { load() }, [load])

  const card = queue?.[0]
  const answer = useCallback(async (rating: string) => {
    if (!card || busy) return
    setBusy(true)
    try {
      const updated = await api.answer(card.card_id, rating)
      setDone(n => n + 1)
      // "again" cards come back in this session (due in 10 min) — requeue at the end
      setQueue(q => (q ? [...q.slice(1), ...(rating === 'again' ? [{ ...card, ...updated }] : [])] : q))
      setShown(false)
    } catch (e) { setErr(e) } finally { setBusy(false) }
  }, [card, busy])

  useEffect(() => {
    const on = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement)?.tagName === 'SELECT') return
      if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); setShown(true) }
      const r = RATINGS.find(r => r.key === e.key)
      if (r && shown) answer(r.id)
    }
    addEventListener('keydown', on)
    return () => removeEventListener('keydown', on)
  }, [shown, answer])

  if (err) return <ErrorBox error={err} />
  const front = card && (direction === 'jp_vi'
    ? <span className="jp text-5xl font-semibold">{card.word}</span>
    : <span className="text-2xl font-medium">{card.meaning_vi}</span>)

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-xl font-semibold">Ôn tập SRS</h1>
        <div className="flex items-center gap-2 text-sm">
          <select aria-label="Chiều ôn" className="rounded-lg border border-slate-300 bg-white px-2 py-1 dark:border-slate-700 dark:bg-slate-900"
            value={direction} onChange={e => { const v = e.target.value as 'jp_vi' | 'vi_jp'; setDirection(v); writePref('srs.direction', v) }}>
            <option value="jp_vi">Nhật → Việt</option>
            <option value="vi_jp">Việt → Nhật</option>
          </select>
          <label className="flex items-center gap-1">Thẻ mới/ngày
            <input type="number" min={0} max={200} value={newLimit} aria-label="Số thẻ mới mỗi ngày"
              className="w-16 rounded-lg border border-slate-300 bg-white px-2 py-1 dark:border-slate-700 dark:bg-slate-900"
              onChange={e => { const v = Math.max(0, Math.min(200, Number(e.target.value) || 0)); setNewLimit(v); writePref('srs.newLimit', v) }} />
          </label>
        </div>
      </div>

      {!queue ? <Loading /> : !card ? (
        <Panel>
          <p className="text-center">{done ? `Xong! Bạn đã ôn ${done} lượt trong phiên này.` : 'Không có thẻ đến hạn và đã hết hạn mức thẻ mới hôm nay.'}</p>
          <div className="mt-3 flex justify-center"><Button onClick={load}>Tải lại</Button></div>
        </Panel>
      ) : (
        <>
          <div className="flex justify-between text-xs text-slate-500">
            <span>Còn {queue.length} thẻ · đã ôn {done}</span>
            <span>{card.lesson_number ? `Bài ${card.lesson_number}` : card.deck} · {card.status === 'new' ? 'thẻ mới' : `khoảng ${card.interval_days} ngày`}</span>
          </div>
          <section className="rounded-2xl border border-slate-200 bg-white p-6 text-center shadow-sm dark:border-slate-800 dark:bg-slate-900" aria-live="polite">
            {card.verification_status !== 'verified' && (
              <div className="mb-3 flex justify-center"><StatusBadge status={card.verification_status} /></div>
            )}
            <div className="flex min-h-28 items-center justify-center">{front}</div>
            {!shown ? (
              <div className="mt-6"><Button kind="primary" onClick={() => setShown(true)}>Hiện đáp án (Space)</Button></div>
            ) : (
              <div className="mt-4 space-y-2 border-t border-slate-100 pt-4 dark:border-slate-800">
                <div className="jp text-2xl">{direction === 'vi_jp' && <span className="mr-2 font-semibold">{card.word}</span>}{card.reading}
                  <SpeakButton text={card.reading || card.word} /></div>
                <div className="text-sm text-slate-500">{[card.romaji, card.han_viet].filter(Boolean).join(' · ')}</div>
                {direction === 'jp_vi' && <div className="text-xl">{card.meaning_vi}</div>}
                {card.example_jp && (
                  <div className="mx-auto max-w-md rounded-lg bg-slate-50 p-3 text-left text-sm dark:bg-slate-800/60">
                    <p className="jp">{card.example_jp}</p>
                    {card.example_vi && <p className="text-slate-500">{card.example_vi}</p>}
                  </div>
                )}
              </div>
            )}
          </section>
          {shown && (
            <div className="grid grid-cols-4 gap-2">
              {RATINGS.map(r => (
                <button key={r.id} type="button" disabled={busy} onClick={() => answer(r.id)}
                  className={`rounded-xl py-3 text-sm font-semibold text-white disabled:opacity-50 ${r.cls}`}>
                  {r.label} <span className="opacity-70">({r.key})</span>
                </button>
              ))}
            </div>
          )}
          <p className="text-center text-xs text-slate-500">Phím tắt: Space hiện đáp án · 1–4 chấm điểm. Nhãn "Chưa xác minh"/"Cần duyệt" = dữ liệu chưa được bạn duyệt.</p>
        </>
      )}
    </div>
  )
}
