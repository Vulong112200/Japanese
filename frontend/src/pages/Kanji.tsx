import { useEffect, useMemo, useState } from 'react'
import { api, type KanjiItem } from '../api'
import { Button, ErrorBox, Loading, Panel, SpeakButton, StatusBadge, Tag } from '../ui'

export default function Kanji() {
  const [items, setItems] = useState<KanjiItem[] | null>(null)
  const [sel, setSel] = useState<KanjiItem | null>(null)
  const [mode, setMode] = useState<'list' | 'quiz'>('list')
  const [err, setErr] = useState<unknown>(null)
  useEffect(() => { api.kanji().then(setItems).catch(setErr) }, [])
  if (err) return <ErrorBox error={err} />
  if (!items) return <Loading />
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h1 className="text-xl font-semibold">Kanji N5 ({items.length} chữ)</h1>
          <p className="text-sm text-slate-500">Âm on/kun và số nét theo KANJIDIC2; từ ví dụ lấy từ kho từ vựng đã xác minh.</p>
        </div>
        <div className="flex gap-2">
          <Button kind={mode === 'list' ? 'primary' : 'default'} onClick={() => setMode('list')}>Danh sách</Button>
          <Button kind={mode === 'quiz' ? 'primary' : 'default'} onClick={() => setMode('quiz')}>Luyện đọc</Button>
        </div>
      </div>
      {mode === 'quiz' ? <Quiz items={items} /> : (
        <div className="grid gap-4 lg:grid-cols-[1fr_380px]">
          <div className="grid grid-cols-5 gap-2 sm:grid-cols-8 md:grid-cols-10">
            {items.map(k => (
              <button key={k.id} type="button" onClick={() => setSel(k)} title={`${k.han_viet} — ${k.meaning_vi}`}
                className={`jp aspect-square rounded-lg border text-2xl hover:border-indigo-400 ${sel?.id === k.id ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-950/50' : 'border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900'}`}>
                {k.kanji}
              </button>
            ))}
          </div>
          <div>{sel ? <KanjiCard k={sel} /> : <Panel><p className="text-sm text-slate-500">Chọn một chữ.</p></Panel>}</div>
        </div>
      )}
    </div>
  )
}

function KanjiCard({ k }: { k: KanjiItem }) {
  return (
    <Panel>
      <div className="flex items-start gap-4">
        <div className="jp text-7xl leading-none">{k.kanji}</div>
        <div className="space-y-1 text-sm">
          <div className="text-lg font-semibold">{k.han_viet}</div>
          <div>{k.meaning_vi}</div>
          <div className="text-slate-500">{k.stroke_count} nét</div>
          <StatusBadge status={k.verification_status} by={k.verified_by} />
        </div>
      </div>
      <dl className="jp mt-3 grid grid-cols-[70px_1fr] gap-1 text-sm">
        <dt className="text-slate-500">On</dt><dd>{k.onyomi.join('、') || '—'}</dd>
        <dt className="text-slate-500">Kun</dt><dd>{k.kunyomi.join('、') || '—'}</dd>
      </dl>
      <h3 className="mt-3 text-xs font-semibold uppercase text-slate-500">Từ ví dụ</h3>
      <ul className="mt-1 space-y-1 text-sm">
        {k.example_words.map((w, i) => (
          <li key={i} className="flex items-center gap-2">
            <span className="jp font-medium">{w.word}</span><span className="jp text-slate-500">【{w.reading}】</span>
            <span>{w.meaning_vi}</span><SpeakButton text={w.reading} />
            {!w.vocab_id && <Tag>ngoài kho từ vựng</Tag>}
          </li>
        ))}
      </ul>
    </Panel>
  )
}

function shuffle<T>(xs: T[]): T[] {
  const a = [...xs]
  for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]] }
  return a
}

/** Reading quiz: an example word is shown, choose its reading. Distractors are readings of other example words. */
function Quiz({ items }: { items: KanjiItem[] }) {
  const pool = useMemo(() => items.flatMap(k => k.example_words.map(w => ({ ...w, kanji: k }))), [items])
  const [n, setN] = useState(0)
  const [score, setScore] = useState({ right: 0, total: 0 })
  const [picked, setPicked] = useState<string | null>(null)
  const q = useMemo(() => {
    const target = pool[Math.floor(Math.random() * pool.length)]
    const others = shuffle(pool.filter(w => w.reading !== target.reading)).slice(0, 3).map(w => w.reading)
    return { target, options: shuffle([target.reading, ...others]) }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [n, pool])
  const answer = (opt: string) => {
    if (picked) return
    setPicked(opt)
    setScore(s => ({ right: s.right + (opt === q.target.reading ? 1 : 0), total: s.total + 1 }))
  }
  return (
    <Panel title={`Đọc đúng ${score.right}/${score.total}`}>
      <div className="text-center">
        <div className="jp my-4 text-5xl">{q.target.word}</div>
        <div className="mx-auto grid max-w-md grid-cols-2 gap-2">
          {q.options.map(o => {
            const state = picked && (o === q.target.reading ? 'bg-emerald-600 text-white' : o === picked ? 'bg-rose-600 text-white' : '')
            return <button key={o} type="button" onClick={() => answer(o)}
              className={`jp rounded-xl border border-slate-300 px-3 py-3 text-lg dark:border-slate-700 ${state || 'hover:bg-slate-50 dark:hover:bg-slate-800'}`}>{o}</button>
          })}
        </div>
        {picked && (
          <div className="mt-4 space-y-2 text-sm">
            <p>{q.target.word}【{q.target.reading}】: {q.target.meaning_vi} · chữ <span className="jp">{q.target.kanji.kanji}</span> ({q.target.kanji.han_viet})</p>
            <Button kind="primary" onClick={() => { setPicked(null); setN(x => x + 1) }}>Câu tiếp</Button>
          </div>
        )}
      </div>
    </Panel>
  )
}
