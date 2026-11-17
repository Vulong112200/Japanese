import { useCallback, useEffect, useState } from 'react'
import { api, type Card, type SrsEntity } from '../api'
import { Button, ErrorBox, Loading, Panel, SpeakButton, StatusBadge, readPref, writePref } from '../ui'

const RATINGS = [
  { id: 'again', label: 'Lại', key: '1', cls: 'bg-rose-600 hover:bg-rose-500' },
  { id: 'hard', label: 'Khó', key: '2', cls: 'bg-amber-600 hover:bg-amber-500' },
  { id: 'good', label: 'Được', key: '3', cls: 'bg-emerald-600 hover:bg-emerald-500' },
  { id: 'easy', label: 'Dễ', key: '4', cls: 'bg-sky-600 hover:bg-sky-500' },
] as const
// Ôn tổng hợp (ADR-027): only "Quên" is written back to SRS; "Nhớ" leaves the schedule alone
const CRAM_RATINGS = [
  { id: 'again', label: 'Quên', key: '1', cls: 'bg-rose-600 hover:bg-rose-500' },
  { id: 'good', label: 'Nhớ', key: '3', cls: 'bg-emerald-600 hover:bg-emerald-500' },
] as const
const CRAM_SOURCES = [['studied', 'Từ đã học'], ['weak', 'Từ hay quên'], ['all', 'Tất cả']] as const

function shuffled<T>(a: T[]): T[] {
  const b = [...a]
  for (let i = b.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1));[b[i], b[j]] = [b[j], b[i]] }
  return b
}
const numOrNull = (v: string) => (v === '' ? null : Math.max(1, Number(v) || 1))

const ENTITIES: [SrsEntity, string][] = [['vocabulary', 'Từ vựng'], ['grammar', 'Ngữ pháp'], ['kanji', 'Kanji'], ['number', 'Số đếm']]
const hashEntity = () => {
  const e = new URLSearchParams(location.hash.split('?')[1] ?? '').get('entity')
  return ENTITIES.some(([k]) => k === e) ? (e as SrsEntity) : null
}

export default function Flashcards() {
  const [entity, setEntity] = useState<SrsEntity>(() => hashEntity() ?? readPref('srs.entity', 'vocabulary'))
  const [vocabDirection, setDirection] = useState<'jp_vi' | 'vi_jp'>(() => readPref('srs.direction', 'jp_vi'))
  const direction = entity === 'vocabulary' ? vocabDirection : 'jp_vi'   // grammar/kanji: one direction (ADR-021)
  const [newLimit, setNewLimit] = useState<number>(() => readPref('srs.newLimit', 20))
  const [mode, setMode] = useState<'srs' | 'cram'>(() => readPref('srs.mode', 'srs'))
  const [lessonFrom, setLessonFrom] = useState<number | null>(() => readPref('srs.lessonFrom', null))
  const [lessonTo, setLessonTo] = useState<number | null>(() => readPref('srs.lessonTo', null))
  const [shuffle, setShuffle] = useState<boolean>(() => readPref('srs.shuffle', false))
  const [cramSource, setCramSource] = useState<string>(() => readPref('srs.cramSource', 'studied'))
  const [cramN, setCramN] = useState<number>(() => readPref('srs.cramN', 50))
  const [queue, setQueue] = useState<Card[] | null>(null)
  const [shown, setShown] = useState(false)
  const [done, setDone] = useState(0)
  const [forgot, setForgot] = useState(0)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<unknown>(null)
  const cram = mode === 'cram'
  const ratings = cram ? CRAM_RATINGS : RATINGS

  const load = useCallback(() => {
    setQueue(null); setShown(false); setDone(0); setForgot(0)
    const p = { direction, entity, lesson_from: lessonFrom, lesson_to: lessonTo }
    const req = cram ? api.cram({ ...p, source: cramSource, n: cramN })
      : api.due({ ...p, new_limit: newLimit, shuffle: shuffle ? 'true' : undefined }).then(q => (shuffle ? shuffled(q) : q))
    req.then(setQueue).catch(setErr)
  }, [direction, newLimit, entity, cram, lessonFrom, lessonTo, shuffle, cramSource, cramN])
  useEffect(() => { load() }, [load])

  const card = queue?.[0]
  const answer = useCallback(async (rating: string) => {
    if (!card || busy) return
    setBusy(true)
    try {
      // cram "Nhớ" is not an on-schedule review: not sent to SM-2, only clears the "Từ hay quên" mark
      const updated = cram && rating !== 'again' ? (await api.recalled(card.card_id), {}) : await api.answer(card.card_id, rating)
      setDone(n => n + 1)
      if (rating === 'again') setForgot(n => n + 1)
      // "again" cards come back in this session (due in 10 min) — requeue at the end
      setQueue(q => (q ? [...q.slice(1), ...(rating === 'again' ? [{ ...card, ...updated }] : [])] : q))
      setShown(false)
    } catch (e) { setErr(e) } finally { setBusy(false) }
  }, [card, busy, cram])

  useEffect(() => {
    const on = (e: KeyboardEvent) => {
      if (['SELECT', 'INPUT'].includes((e.target as HTMLElement)?.tagName)) return
      if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); setShown(true) }
      const r = ratings.find(r => r.key === e.key)
      if (r && shown) answer(r.id)
    }
    addEventListener('keydown', on)
    return () => removeEventListener('keydown', on)
  }, [shown, answer, ratings])

  if (err) return <ErrorBox error={err} />
  const front = card && (
    entity === 'grammar' ? <span className="jp text-3xl font-semibold">{card.pattern}</span>
      : entity === 'kanji' ? <span className="jp text-7xl font-semibold">{card.kanji}</span>
        : entity === 'number' ? <span><span className="jp block text-5xl font-semibold">{card.jp}</span><span className="mt-2 block text-sm text-slate-500">{card.category_vi}</span></span>
        : direction === 'jp_vi' ? <span className="jp text-5xl font-semibold">{card.word}</span>
          : <span className="text-2xl font-medium">{card.meaning_vi}</span>)

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-xl font-semibold">Ôn tập SRS</h1>
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <select aria-label="Loại thẻ" className="rounded-lg border border-slate-300 bg-white px-2 py-1 dark:border-slate-700 dark:bg-slate-900"
            value={entity} onChange={e => { const v = e.target.value as SrsEntity; setEntity(v); writePref('srs.entity', v) }}>
            {ENTITIES.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
          </select>
          {entity === 'vocabulary' && <select aria-label="Chiều ôn" className="rounded-lg border border-slate-300 bg-white px-2 py-1 dark:border-slate-700 dark:bg-slate-900"
            value={direction} onChange={e => { const v = e.target.value as 'jp_vi' | 'vi_jp'; setDirection(v); writePref('srs.direction', v) }}>
            <option value="jp_vi">Nhật → Việt</option>
            <option value="vi_jp">Việt → Nhật</option>
          </select>}
          <select aria-label="Chế độ" className="rounded-lg border border-slate-300 bg-white px-2 py-1 dark:border-slate-700 dark:bg-slate-900"
            value={mode} onChange={e => { const v = e.target.value as 'srs' | 'cram'; setMode(v); writePref('srs.mode', v) }}>
            <option value="srs">Theo lịch SRS</option>
            <option value="cram">Ôn tổng hợp</option>
          </select>
        </div>
      </div>
      <div className="flex flex-wrap items-center justify-end gap-2 text-sm">
        {(entity === 'vocabulary' || entity === 'grammar') && <label className="flex items-center gap-1">Bài
          <input type="number" min={1} value={lessonFrom ?? ''} placeholder="đầu" aria-label="Từ bài" className="w-16 rounded-lg border border-slate-300 bg-white px-2 py-1 dark:border-slate-700 dark:bg-slate-900"
            onChange={e => { const v = numOrNull(e.target.value); setLessonFrom(v); writePref('srs.lessonFrom', v) }} />–
          <input type="number" min={1} value={lessonTo ?? ''} placeholder="cuối" aria-label="Đến bài" className="w-16 rounded-lg border border-slate-300 bg-white px-2 py-1 dark:border-slate-700 dark:bg-slate-900"
            onChange={e => { const v = numOrNull(e.target.value); setLessonTo(v); writePref('srs.lessonTo', v) }} />
        </label>}
        {cram ? <>
          <select aria-label="Nguồn thẻ" className="rounded-lg border border-slate-300 bg-white px-2 py-1 dark:border-slate-700 dark:bg-slate-900"
            value={cramSource} onChange={e => { setCramSource(e.target.value); writePref('srs.cramSource', e.target.value) }}>
            {CRAM_SOURCES.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
          </select>
          <label className="flex items-center gap-1">Số thẻ
            <input type="number" min={1} max={500} value={cramN} aria-label="Số thẻ mỗi lượt" className="w-16 rounded-lg border border-slate-300 bg-white px-2 py-1 dark:border-slate-700 dark:bg-slate-900"
              onChange={e => { const v = Math.max(1, Math.min(500, Number(e.target.value) || 1)); setCramN(v); writePref('srs.cramN', v) }} />
          </label>
        </> : <>
          <select aria-label="Thứ tự" className="rounded-lg border border-slate-300 bg-white px-2 py-1 dark:border-slate-700 dark:bg-slate-900"
            value={shuffle ? 'random' : 'lesson'} onChange={e => { const v = e.target.value === 'random'; setShuffle(v); writePref('srs.shuffle', v) }}>
            <option value="lesson">Theo bài</option>
            <option value="random">Ngẫu nhiên</option>
          </select>
          <label className="flex items-center gap-1">Thẻ mới/ngày
            <input type="number" min={0} max={500} value={newLimit} aria-label="Số thẻ mới mỗi ngày" className="w-16 rounded-lg border border-slate-300 bg-white px-2 py-1 dark:border-slate-700 dark:bg-slate-900"
              onChange={e => { const v = Math.max(0, Math.min(500, Number(e.target.value) || 0)); setNewLimit(v); writePref('srs.newLimit', v) }} />
          </label>
        </>}
      </div>

      {!queue ? <Loading /> : !card ? (
        <Panel>
          <p className="text-center">{cram
            ? (done ? `Xong lượt! Nhớ ${done - forgot} · Quên ${forgot} (thẻ quên đã được đưa lại vào lịch SRS).` : 'Không có thẻ nào khớp bộ lọc. "Từ đã học" chỉ gồm thẻ bạn đã học ở chế độ SRS.')
            : (done ? `Xong! Bạn đã ôn ${done} lượt trong phiên này.` : 'Không có thẻ đến hạn và đã hết hạn mức thẻ mới hôm nay.')}</p>
          <div className="mt-3 flex justify-center"><Button onClick={load}>{cram ? 'Lượt mới' : 'Tải lại'}</Button></div>
        </Panel>
      ) : (
        <>
          <div className="flex justify-between text-xs text-slate-500">
            <span>Còn {queue.length} thẻ · {cram ? `nhớ ${done - forgot} · quên ${forgot}` : `đã ôn ${done}`}</span>
            <span>{card.lesson_number ? `Bài ${card.lesson_number}` : card.deck ?? card.category_vi ?? ''} · {card.status === 'new' ? 'thẻ mới' : `khoảng ${card.interval_days} ngày`}</span>
          </div>
          <section className="rounded-2xl border border-slate-200 bg-white p-6 text-center shadow-sm dark:border-slate-800 dark:bg-slate-900" aria-live="polite">
            {card.verification_status !== 'verified' && (
              <div className="mb-3 flex justify-center"><StatusBadge status={card.verification_status} /></div>
            )}
            <div className="flex min-h-28 items-center justify-center">{front}</div>
            {!shown ? (
              <div className="mt-6"><Button kind="primary" onClick={() => setShown(true)}>Hiện đáp án (Space)</Button></div>
            ) : entity === 'grammar' ? (
              <div className="mt-4 space-y-2 border-t border-slate-100 pt-4 text-left dark:border-slate-800">
                <div className="text-center text-xl">{card.meaning_vi}</div>
                {card.grammar_name_vi && <div className="text-center text-sm text-slate-500">{card.grammar_name_vi}</div>}
                <p className="jp text-sm"><span className="text-slate-500">Cách dùng: </span>{card.formation}</p>
                {card.examples?.map((x, i) => (
                  <div key={i} className="rounded-lg bg-slate-50 p-3 text-sm dark:bg-slate-800/60">
                    <p className="jp">{x.jp} <SpeakButton text={x.jp} /></p>
                    <p className="text-slate-500">{x.vi}</p>
                  </div>
                ))}
                <a href={`#/grammar?id=${card.entity_id}`} className="block text-center text-sm text-indigo-600 hover:underline dark:text-indigo-300">Xem chi tiết điểm ngữ pháp →</a>
              </div>
            ) : entity === 'kanji' ? (
              <div className="mt-4 space-y-2 border-t border-slate-100 pt-4 dark:border-slate-800">
                <div className="text-xl">{card.han_viet && <b className="mr-2 uppercase">{card.han_viet}</b>}{card.meaning_vi}</div>
                <div className="jp text-sm text-slate-600 dark:text-slate-300">
                  {card.onyomi?.length ? <span className="mr-3">音: {card.onyomi.join('、')}</span> : null}
                  {card.kunyomi?.length ? <span>訓: {card.kunyomi.join('、')}</span> : null}
                </div>
                {card.example_words?.length ? (
                  <ul className="mx-auto max-w-md rounded-lg bg-slate-50 p-3 text-left text-sm dark:bg-slate-800/60">
                    {card.example_words.slice(0, 4).map(w => (
                      <li key={w.word}><span className="jp font-medium">{w.word}</span> <span className="jp text-slate-500">({w.reading})</span> {w.meaning_vi}</li>
                    ))}
                  </ul>
                ) : null}
              </div>
            ) : (
              <div className="mt-4 space-y-2 border-t border-slate-100 pt-4 dark:border-slate-800">
                <div className="jp text-2xl">{direction === 'vi_jp' && <span className="mr-2 font-semibold">{card.word}</span>}{card.reading}
                  <SpeakButton text={card.reading || card.word || ''} /></div>
                <div className="text-sm text-slate-500">{[card.romaji, card.han_viet].filter(Boolean).join(' · ')}</div>
                {direction === 'jp_vi' && <div className="text-xl">{card.meaning_vi}</div>}
                {card.alt_readings?.length ? <div className="jp text-xs text-slate-500">Cũng đọc: {card.alt_readings.join('、')}</div> : null}
                {card.note_vi && <div className="text-sm text-amber-700 dark:text-amber-300">{card.note_vi}</div>}
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
            <div className={`grid gap-2 ${cram ? 'grid-cols-2' : 'grid-cols-4'}`}>
              {ratings.map(r => (
                <button key={r.id} type="button" disabled={busy} onClick={() => answer(r.id)}
                  className={`rounded-xl py-3 text-sm font-semibold text-white disabled:opacity-50 ${r.cls}`}>
                  {r.label} <span className="opacity-70">({r.key})</span>
                </button>
              ))}
            </div>
          )}
          <p className="text-center text-xs text-slate-500">Phím tắt: Space hiện đáp án · {cram ? '1 Quên · 3 Nhớ' : '1–4 chấm điểm'}. Nhãn "Chưa xác minh"/"Cần duyệt" = dữ liệu chưa được bạn duyệt.</p>
        </>
      )}
    </div>
  )
}
