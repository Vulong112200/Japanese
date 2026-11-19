import { useEffect, useState } from 'react'
import { api, type NumberCategory } from '../api'
import { ErrorBox, Loading, Panel, SpeakButton, StartButton, readPref, writePref } from '../ui'

/** Numbers, counters, time and dates (ADR-029): rule + table per group; sound-changed forms are highlighted. */
export default function Numbers() {
  const [cats, setCats] = useState<NumberCategory[] | null>(null)
  const [err, setErr] = useState<unknown>(null)
  const [onlyIrregular, setOnlyIrregular] = useState(false)
  // practice set-up (ADR-031): chosen groups (none = all), question type, number of questions
  const [picked, setPicked] = useState<string[]>(() => readPref('num.cats', []))
  const [qType, setQType] = useState<string>(() => readPref('num.type', ''))
  const [count, setCount] = useState<number>(() => readPref('num.count', 20))
  const togglePick = (k: string) => setPicked(p => { const n = p.includes(k) ? p.filter(x => x !== k) : [...p, k]; writePref('num.cats', n); return n })
  useEffect(() => { api.numbers().then(setCats).catch(setErr) }, [])
  if (err) return <ErrorBox error={err} />
  if (!cats) return <Loading />
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Số đếm & ngày tháng N5</h1>
        <p className="text-sm text-slate-500">Mỗi nhóm có quy tắc biến âm và bảng cách đọc. Ô <span className="rounded bg-amber-100 px-1 dark:bg-amber-900/50">tô màu</span> là cách đọc đặc biệt cần nhớ riêng (cũng là các thẻ trong Ôn tập SRS → Số đếm).</p>
      </div>
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <a href="#/flashcards?entity=number" className="rounded-lg border border-slate-300 px-3 py-1.5 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800">Lật thẻ Số đếm</a>
        <label className="ml-auto flex items-center gap-1">
          <input type="checkbox" checked={onlyIrregular} onChange={e => setOnlyIrregular(e.target.checked)} /> Chỉ hiện cách đọc đặc biệt
        </label>
      </div>
      <Panel title="Luyện trắc nghiệm">
        <p className="mb-2 text-xs text-slate-500">Chọn nhóm cần ôn (không chọn = tất cả). Đọc: chọn cách đọc của 三本. Viết: cho ようか, chọn 八日.</p>
        <div className="mb-3 flex flex-wrap gap-1 text-xs">
          {cats.map(c => <button key={c.key} type="button" aria-pressed={picked.includes(c.key)} onClick={() => togglePick(c.key)}
            className={`rounded-full border px-2 py-0.5 ${picked.includes(c.key) ? 'border-sky-600 bg-sky-600 text-white' : 'border-slate-300 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800'}`}>{c.title_vi}</button>)}
          {picked.length ? <button type="button" className="px-2 py-0.5 text-slate-500 underline" onClick={() => { setPicked([]); writePref('num.cats', []) }}>Bỏ chọn</button> : null}
        </div>
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <select aria-label="Dạng câu" value={qType} onChange={e => { setQType(e.target.value); writePref('num.type', e.target.value) }}
            className="rounded-lg border border-slate-300 bg-white px-2 py-1 dark:border-slate-700 dark:bg-slate-900">
            <option value="">Đọc + Viết</option>
            <option value="kanji_reading">Chỉ Đọc (漢字読み)</option>
            <option value="orthography">Chỉ Viết (表記)</option>
          </select>
          <select aria-label="Số câu" value={count} onChange={e => { const v = Number(e.target.value); setCount(v); writePref('num.count', v) }}
            className="rounded-lg border border-slate-300 bg-white px-2 py-1 dark:border-slate-700 dark:bg-slate-900">
            {[10, 20, 50, 100].map(n => <option key={n} value={n}>{n} câu</option>)}
            <option value={500}>Tất cả</option>
          </select>
          <StartButton kind="primary" body={{ mode: 'practice', topic: 'numbers', limit: count, mondai_type: qType || undefined,
            number_categories: picked.length ? picked : undefined }}>Bắt đầu</StartButton>
        </div>
      </Panel>
      <nav className="flex flex-wrap gap-1 text-xs">
        {cats.map(c => <a key={c.key} href={`#/numbers`} onClick={e => { e.preventDefault(); document.getElementById(`num-${c.key}`)?.scrollIntoView({ behavior: 'smooth' }) }}
          className="rounded-full border border-slate-200 px-2 py-0.5 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800">{c.title_vi}</a>)}
      </nav>
      <div className="grid gap-4 lg:grid-cols-2">
        {cats.map(c => {
          const items = onlyIrregular ? c.items.filter(i => i.irregular) : c.items
          if (!items.length) return null
          return (
            <div key={c.key} id={`num-${c.key}`} className="scroll-mt-4">
              <Panel title={c.title_vi}>
                <p className="mb-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300">{c.rule_vi}</p>
                <table className="w-full text-sm">
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {items.map(i => (
                      <tr key={i.id} className={i.irregular ? 'bg-amber-50 dark:bg-amber-950/30' : ''}>
                        <td className="jp whitespace-nowrap px-2 py-1.5 text-base font-medium">{i.jp}</td>
                        <td className="jp px-2 py-1.5">
                          {i.reading} <SpeakButton text={i.reading} />
                          {i.alt_readings?.length ? <span className="block text-xs text-slate-500">cũng: {i.alt_readings.join('、')}</span> : null}
                        </td>
                        <td className="px-2 py-1.5">
                          {i.meaning_vi}
                          {i.note_vi && <span className="block text-xs text-amber-700 dark:text-amber-300">{i.note_vi}</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Panel>
            </div>
          )
        })}
      </div>
      <p className="text-xs text-slate-500">Nội dung do AI soạn, kiểm bằng luật biến âm + JMdict + 2 vòng rà soát độc lập. Phát âm bằng giọng máy của trình duyệt.</p>
    </div>
  )
}
