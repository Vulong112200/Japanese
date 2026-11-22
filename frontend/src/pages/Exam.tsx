import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { api, type Attempt, type AttemptStart, type AttemptSummary, type ExamOverview, type ExamQuestion, type GrammarDetail, type Section } from '../api'
import { Button, ErrorBox, Loading, Panel, Tag } from '../ui'

export const SECTION_LABEL: Record<string, string> = {
  vocabulary: 'Từ vựng 文字・語彙', grammar_reading: 'Ngữ pháp・Đọc 文法・読解', listening: 'Nghe 聴解',
}
export const MONDAI_LABEL: Record<string, string> = {
  kanji_reading: '漢字読み · đọc kanji', orthography: '表記 · cách viết', contextual: '文脈規定 · chọn từ theo ngữ cảnh',
  paraphrase: '言い換え類義 · câu đồng nghĩa', grammar_form: '文の文法1 · chọn mẫu ngữ pháp',
  sentence_composition: '文の文法2 · sắp xếp câu ★', text_grammar: '文章の文法 · ngữ pháp đoạn văn',
  reading_short: '内容理解（短文）', reading_mid: '内容理解（中文）', information_retrieval: '情報検索',
  task_based: '課題理解', point_comprehension: 'ポイント理解', verbal_expression: '発話表現', quick_response: '即時応答',
}

// ?id=ATT_... in the hash keeps an attempt open across reloads (answers are auto-saved on the server).
const SOURCE_EXAM_TYPE: Record<string, string> = { official: 'official_sample', past: 'past_exam', generated: 'question_bank' }
const hashId = () => new URLSearchParams(location.hash.split('?')[1] ?? '').get('id')
const setHashId = (id: string | null) => { location.hash = id ? `#/exam?id=${id}` : '#/exam' }

export default function Exam() {
  const [id, setId] = useState<string | null>(hashId)
  useEffect(() => {
    const on = () => setId(hashId())
    addEventListener('hashchange', on)
    return () => removeEventListener('hashchange', on)
  }, [])
  return id ? <AttemptPage key={id} id={id} /> : <ExamHome />
}

// ------------------------------------------------------------------ home
function ExamHome() {
  const [ov, setOv] = useState<ExamOverview | null>(null)
  const [hist, setHist] = useState<AttemptSummary[]>([])
  const [err, setErr] = useState<unknown>(null)
  const [busy, setBusy] = useState(false)
  const [f, setF] = useState<AttemptStart>({ mode: 'practice', source: 'all', limit: 20, timing: 'none' })
  useEffect(() => {
    api.exams().then(setOv).catch(setErr)
    api.attempts().then(setHist).catch(setErr)
  }, [])

  const start = async (body: AttemptStart) => {
    setBusy(true)
    try { setHashId((await api.startAttempt(body)).attempt_id) } catch (e) { setErr(e) } finally { setBusy(false) }
  }
  if (!ov) return err ? <ErrorBox error={err} /> : <Loading />

  const types = ov.bank.filter(b => !f.section || b.section === f.section)
    .filter(b => !f.source || f.source === 'all' || SOURCE_EXAM_TYPE[f.source] === b.exam_type)
  const mondai = [...new Map(types.map(b => [b.mondai_type, b])).values()]
  const available = types.filter(b => !f.mondai_type || b.mondai_type === f.mondai_type).reduce((a, b) => a + b.n, 0)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Thi thử · Luyện đề</h1>
        <p className="text-sm text-slate-500">Chế độ thi ẩn đáp án đến khi nộp bài. Chế độ luyện tập chấm và giải thích ngay sau mỗi câu.</p>
      </div>
      {err != null && <ErrorBox error={err} />}

      <Panel title="Đề thi">
        {ov.exams.map(e => (
          <div key={e.exam_id} className="flex flex-wrap items-center gap-3">
            <div className="min-w-0 flex-1">
              <div className="jp font-medium">{e.title}</div>
              <div className="mt-1 flex flex-wrap gap-1.5 text-xs">
                {e.is_official ? <Tag tone="emerald">OFFICIAL · đáp án theo 正解</Tag>
                  : e.source_type === 'COMMUNITY_KEY' ? <Tag tone="indigo">Đề thật · đáp án cộng đồng + AI đối chiếu</Tag>
                  : e.source_type === 'AI_ANSWERED' ? <Tag tone="indigo">Đề thật · đáp án do 2 AI giải độc lập</Tag>
                  : <Tag tone="amber">AI_GENERATED</Tag>}
                <Tag>{e.question_count} câu</Tag>
                <Tag>{e.duration_minutes ? `${e.duration_minutes} phút` : 'Đề gốc không ghi thời gian'}</Tag>
                {e.verification_status !== 'verified' && <Tag tone="amber">Bản chép chờ đối chiếu ảnh gốc</Tag>}
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button kind="primary" disabled={busy} onClick={() => start({ mode: 'exam', exam_id: e.exam_id, timing: 'original' })}>Thi (giữ nguyên đề gốc)</Button>
              <Button disabled={busy} title="Áp thời gian JLPT N5 hiện hành khi làm bài; không sửa thông tin của đề gốc"
                onClick={() => start({ mode: 'exam', exam_id: e.exam_id, timing: 'current' })}>Thi tính giờ 20/40/30 phút</Button>
              <Button disabled={busy} onClick={() => start({ mode: 'practice', exam_id: e.exam_id })}>Luyện tập</Button>
            </div>
          </div>
        ))}
      </Panel>

      <Panel title="Luyện theo phần / dạng câu (Mondai)">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <Field label="Phần">
            <select value={f.section ?? ''} onChange={e => setF({ ...f, section: (e.target.value || undefined) as Section | undefined, mondai_type: undefined })} className={INPUT}>
              <option value="">Tất cả</option>
              {Object.entries(SECTION_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </Field>
          <Field label="Dạng câu">
            <select value={f.mondai_type ?? ''} onChange={e => setF({ ...f, mondai_type: e.target.value || undefined })} className={INPUT}>
              <option value="">Tất cả</option>
              {mondai.map(b => <option key={b.mondai_type} value={b.mondai_type}>{MONDAI_LABEL[b.mondai_type] ?? b.mondai_type}</option>)}
            </select>
          </Field>
          <Field label="Nguồn câu hỏi">
            <select value={f.source} onChange={e => setF({ ...f, source: e.target.value as AttemptStart['source'], mondai_type: undefined })} className={INPUT}>
              <option value="all">Tất cả</option>
              <option value="official">Chỉ đề mẫu chính thức</option>
              <option value="past">Chỉ đề thi thật các năm</option>
              <option value="generated">Chỉ câu sinh tự động (AI_GENERATED)</option>
            </select>
          </Field>
          <Field label={`Số câu (có ${available})`}>
            <input type="number" min={1} max={200} value={f.limit} onChange={e => setF({ ...f, limit: Math.max(1, Math.min(200, +e.target.value || 1)) })} className={INPUT} />
          </Field>
          <Field label="Chế độ">
            <select value={f.mode} onChange={e => setF({ ...f, mode: e.target.value as AttemptStart['mode'] })} className={INPUT}>
              <option value="practice">Luyện tập: chấm ngay từng câu</option>
              <option value="exam">Thi: chấm khi nộp bài</option>
            </select>
          </Field>
          <Field label="Thời gian">
            <div className="flex gap-2">
              <select disabled={f.mode === 'practice'} value={f.mode === 'practice' ? 'none' : f.timing}
                onChange={e => setF({ ...f, timing: e.target.value as AttemptStart['timing'] })} className={INPUT}>
                <option value="none">Không giới hạn</option>
                <option value="current">Theo JLPT (20/40/30 phút mỗi phần)</option>
                <option value="custom">Tự đặt (phút)</option>
              </select>
              {f.mode === 'exam' && f.timing === 'custom' &&
                <input type="number" min={1} max={300} aria-label="Số phút" value={f.time_limit_min ?? 10}
                  onChange={e => setF({ ...f, time_limit_min: Math.max(1, +e.target.value || 1) })} className={`${INPUT} w-20`} />}
            </div>
          </Field>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <Button kind="primary" disabled={busy || !available} onClick={() => start({
            ...f, timing: f.mode === 'practice' ? 'none' : f.timing,
            time_limit_min: f.timing === 'custom' ? f.time_limit_min ?? 10 : undefined,
          })}>Bắt đầu</Button>
          <Button disabled={busy || !ov.mistakes} onClick={() => start({ mode: 'practice', mistakes_only: true, limit: 200 })}>
            Ôn lại câu sai ({ov.mistakes})
          </Button>
        </div>
        <p className="mt-3 text-xs text-slate-500">
          Câu sinh tự động chỉ có ở phần Từ vựng (漢字読み, 表記). Chúng được tạo bằng luật từ từ vựng/kanji đã xác minh, có
          đối chiếu JMdict để không có hai đáp án đúng. Đây không phải câu hỏi JLPT chính thức.
        </p>
      </Panel>

      <Panel title="Lịch sử làm bài">
        {hist.length === 0 ? <p className="text-sm text-slate-500">Chưa có lượt nào.</p> : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-xs text-slate-500"><tr>
                <th className="py-1 pr-3">Bắt đầu</th><th className="pr-3">Bài</th><th className="pr-3">Chế độ</th>
                <th className="pr-3 text-right">Đúng</th><th className="text-right">Ước lượng</th></tr></thead>
              <tbody>
                {hist.map(h => (
                  <tr key={h.attempt_id} className="border-t border-slate-100 dark:border-slate-800">
                    <td className="py-1.5 pr-3 whitespace-nowrap tabular-nums">{h.started_at.slice(0, 16).replace('T', ' ')}</td>
                    <td className="pr-3"><a className="text-indigo-600 hover:underline dark:text-indigo-300" href={`#/exam?id=${h.attempt_id}`}>{h.title}</a></td>
                    <td className="pr-3">{h.mode === 'exam' ? 'Thi' : 'Luyện'}</td>
                    <td className="pr-3 text-right tabular-nums">{h.summary ? `${h.summary.correct}/${h.summary.total}` : <Tag tone="amber">đang làm</Tag>}</td>
                    <td className="text-right tabular-nums">{h.readiness?.total != null ? `≈${h.readiness.total}/180` : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
    </div>
  )
}

const INPUT = 'w-full rounded-lg border border-slate-300 bg-white px-2 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-800 disabled:opacity-50'

function Field({ label, children }: { label: string; children: ReactNode }) {
  return <label className="block text-sm"><span className="mb-1 block text-xs text-slate-500">{label}</span>{children}</label>
}

// ------------------------------------------------------------------ attempt (runner + result)
function AttemptPage({ id }: { id: string }) {
  const [a, setA] = useState<Attempt | null>(null)
  const [err, setErr] = useState<unknown>(null)
  useEffect(() => { api.attempt(id).then(setA).catch(setErr) }, [id])
  if (err) return <div className="space-y-3"><ErrorBox error={err} /><Button onClick={() => setHashId(null)}>← Trang thi</Button></div>
  if (!a) return <Loading />
  return a.submitted_at ? <Result a={a} /> : <Runner a={a} setA={setA} />
}

/** Seconds left in the current section. A tick from a previous section (key) is never returned, so a stale 0
 *  cannot close the next section. */
function useCountdown(remaining: number | null, key: string) {
  const [tick, setTick] = useState<{ key: string; left: number } | null>(null)
  useEffect(() => {
    if (remaining == null) return
    const deadline = Date.now() + remaining * 1000
    const t = setInterval(() => setTick({ key, left: Math.max(0, Math.round((deadline - Date.now()) / 1000)) }), 500)
    return () => clearInterval(t)
  }, [remaining, key])
  if (remaining == null) return null
  return tick?.key === key ? tick.left : remaining
}

const fmt = (s: number) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`

function Runner({ a, setA }: { a: Attempt; setA: (a: Attempt) => void }) {
  const [i, setI] = useState(0)
  const [err, setErr] = useState<unknown>(null)
  const [busy, setBusy] = useState(false)
  const exam = a.mode === 'exam'
  const sec = a.sections[a.current_section]
  const visible = useMemo(() => {
    const ids = new Set(exam ? sec.question_ids : a.sections.flatMap(s => s.question_ids))
    return a.questions.filter(q => ids.has(q.question_id))
  }, [a, exam, sec])
  const q = visible[Math.min(i, visible.length - 1)]
  const left = useCountdown(a.remaining_sec, `${a.attempt_id}:${a.current_section}`)
  const last = a.current_section >= a.sections.length - 1
  const answered = (qid: string) => !!a.answers[qid]?.answer?.length
  const unanswered = (exam ? visible : a.questions).filter(x => !answered(x.question_id)).length

  const run = useCallback(async (fn: () => Promise<Attempt>) => {
    setBusy(true)
    try { const n = await fn(); setA(n); setI(0) } catch (e) { setErr(e) } finally { setBusy(false) }
  }, [setA])
  const submit = useCallback(() => run(() => api.submit(a.attempt_id)), [run, a.attempt_id])
  const advance = useCallback(() => run(() => api.advance(a.attempt_id)), [run, a.attempt_id])

  // time is up: close the section (or submit after the last one), as in the real exam
  const fired = useRef('')
  useEffect(() => {
    const k = `${a.attempt_id}:${a.current_section}`
    if (left === 0 && fired.current !== k) {
      fired.current = k
      if (last) submit()
      else advance()
    }
  }, [left, last, submit, advance, a.attempt_id, a.current_section])

  const choose = async (qq: ExamQuestion, option: string | null, flagged = !!a.answers[qq.question_id]?.flagged) => {
    const prev = a.answers[qq.question_id]
    if (!exam && prev?.answer?.length && option !== null) return            // practice: one try per question
    const answer = option === null ? prev?.answer ?? null : [option]
    setA({ ...a, answers: { ...a.answers, [qq.question_id]: { answer, flagged, is_correct: prev?.is_correct ?? null } } })
    try {
      const r = await api.saveAnswer(a.attempt_id, qq.question_id, answer, flagged)
      if (r.question) {
        const revealed = r.question
        setA({ ...a, questions: a.questions.map(x => x.question_id === qq.question_id ? revealed : x),
          answers: { ...a.answers, [qq.question_id]: { answer, flagged, is_correct: r.is_correct ?? null } } })
      }
      setErr(null)
    } catch (e) { setErr(e); setA(a) }
  }

  const finish = () => {
    if (exam && !last) {
      if (confirm(`Kết thúc phần "${sec.name}"? ${unanswered ? `Còn ${unanswered} câu chưa làm. ` : ''}Sau khi chuyển phần sẽ không quay lại được.`)) advance()
    } else if (confirm(`Nộp bài? ${unanswered ? `Còn ${unanswered} câu chưa làm.` : 'Bạn đã làm hết các câu.'}`)) submit()
  }

  if (!q) return <Loading />
  const qIndex = visible.indexOf(q)
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0">
          <button onClick={() => setHashId(null)} className="text-sm text-indigo-600 hover:underline dark:text-indigo-300">← Trang thi (bài đã tự lưu)</button>
          <h1 className="jp truncate text-lg font-semibold">{a.title}</h1>
          <div className="flex flex-wrap gap-1.5 text-xs">
            <Tag tone={exam ? 'rose' : 'indigo'}>{exam ? 'Chế độ thi: ẩn đáp án' : 'Luyện tập'}</Tag>
            {exam && a.sections.map((s, k) => <Tag key={s.section_id} tone={k === a.current_section ? 'indigo' : 'slate'}>
              {k + 1}. {SECTION_LABEL[s.section] ?? s.name}{s.status === 'done' ? ' ✓' : ''}</Tag>)}
          </div>
        </div>
        <div className="flex items-center gap-3">
          {left != null && <div role="timer" aria-label="Thời gian còn lại của phần này"
            className={`rounded-lg px-3 py-1.5 font-mono text-lg tabular-nums ${left < 60 ? 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-200' : 'bg-slate-100 dark:bg-slate-800'}`}>
            ⏱ {fmt(left)}</div>}
          <Button kind="primary" disabled={busy} onClick={finish}>{exam && !last ? 'Kết thúc phần →' : 'Nộp bài'}</Button>
        </div>
      </div>
      {err != null && <ErrorBox error={err} />}

      <div className="grid gap-4 lg:grid-cols-[1fr_260px]">
        <QuestionCard key={q.question_id} q={q} a={a} pos={`${qIndex + 1}/${visible.length}`} onChoose={o => choose(q, o)}
          onFlag={() => choose(q, null, !a.answers[q.question_id]?.flagged)} practice={!exam} />
        <aside className="space-y-3">
          <Panel title={`Đã làm ${visible.length - visible.filter(x => !answered(x.question_id)).length}/${visible.length}`}>
            <div className="mb-3 h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
              <div className="h-full bg-indigo-500" style={{ width: `${(100 * (visible.length - visible.filter(x => !answered(x.question_id)).length)) / visible.length}%` }} />
            </div>
            <nav aria-label="Chọn câu" className="grid grid-cols-6 gap-1.5">
              {visible.map((x, k) => {
                const st = a.answers[x.question_id]
                const tone = !exam && st?.is_correct != null
                  ? (st.is_correct ? 'bg-emerald-600 text-white' : 'bg-rose-600 text-white')
                  : answered(x.question_id) ? 'bg-indigo-600 text-white' : 'bg-slate-100 dark:bg-slate-800'
                return <button key={x.question_id} onClick={() => setI(k)} aria-current={k === qIndex ? 'true' : undefined}
                  aria-label={`Câu ${k + 1}${answered(x.question_id) ? ', đã làm' : ''}${st?.flagged ? ', đã gắn cờ' : ''}`}
                  className={`relative rounded-md py-1 text-xs tabular-nums ${tone} ${k === qIndex ? 'ring-2 ring-indigo-400 ring-offset-1 dark:ring-offset-slate-900' : ''}`}>
                  {k + 1}{st?.flagged && <span className="absolute -right-0.5 -top-1 text-[10px]">🚩</span>}
                </button>
              })}
            </nav>
          </Panel>
          <div className="flex gap-2">
            <Button disabled={qIndex === 0} onClick={() => setI(qIndex - 1)}>← Trước</Button>
            <Button disabled={qIndex >= visible.length - 1} onClick={() => setI(qIndex + 1)}>Sau →</Button>
          </div>
        </aside>
      </div>
    </div>
  )
}

function Underline({ text, target }: { text: string; target?: string }) {
  const k = target ? text.indexOf(target) : -1
  if (k < 0 || !target) return <>{text}</>
  return <>{text.slice(0, k)}<u className="decoration-2 underline-offset-4">{target}</u>{text.slice(k + target.length)}</>
}

function QuestionCard({ q, a, pos, onChoose, onFlag, practice, review }: {
  q: ExamQuestion; a: Attempt; pos: string; onChoose?: (o: string) => void; onFlag?: () => void; practice?: boolean; review?: boolean
}) {
  const st = a.answers[q.question_id]
  const picked = st?.answer ?? []
  const revealed = !!q.correct_answer
  const passage = q.passage_id ? a.passages[q.passage_id] : null
  const showPage = q.image_asset_id && (q.extra.options_are_pictures || q.extra.options_are_glyph_images || q.extra.has_illustration || q.section === 'listening')
  const [rate, setRate] = useState(1)
  const audio = useRef<HTMLAudioElement>(null)
  useEffect(() => { if (audio.current) audio.current.playbackRate = rate }, [rate])
  const { audio_start: from, audio_end: to } = q.extra
  const stopAt = useRef<number | null>(null)
  const playClip = () => {
    const el = audio.current
    if (!el || from == null) return
    el.currentTime = from
    stopAt.current = to ?? null
    void el.play()
  }

  return (
    <section className="space-y-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900" aria-label={`Câu ${pos}`}>
      <div className="flex flex-wrap items-center gap-1.5 text-xs">
        <Tag tone="indigo">Câu {pos}</Tag>
        <Tag>{SECTION_LABEL[q.section] ?? q.section}{q.mondai_no ? ` · もんだい${q.mondai_no}` : ''}</Tag>
        {q.mondai_type && <Tag>{MONDAI_LABEL[q.mondai_type] ?? q.mondai_type}</Tag>}
        {q.exam_id.startsWith('BANK_')
          ? <Tag tone="amber">AI_GENERATED · không phải đề chính thức</Tag>
          : <Tag tone="emerald">Đề chính thức</Tag>}
        {q.verification_status === 'needs_review' && <Tag tone="amber">Bản chép chờ đối chiếu ảnh gốc</Tag>}
        {onFlag && <button onClick={onFlag} className="ml-auto rounded px-2 py-0.5 text-xs hover:bg-slate-100 dark:hover:bg-slate-800"
          aria-pressed={!!st?.flagged}>{st?.flagged ? '🚩 Bỏ cờ' : '⚑ Gắn cờ xem lại'}</button>}
      </div>
      {q.instruction && <p className="jp text-sm text-slate-600 dark:text-slate-300">{q.instruction}</p>}

      {q.audio_asset_id && (
        <div className="rounded-lg bg-slate-50 p-2 dark:bg-slate-800/60">
          <div className="mb-1 flex items-center justify-between text-xs text-slate-500">
            {from != null
              ? <button type="button" onClick={playClip} className="rounded-md bg-indigo-600 px-2.5 py-1 font-medium text-white hover:bg-indigo-700">
                  ▶ Nghe câu này ({fmt(Math.floor(from))}–{fmt(Math.ceil(to ?? from))})</button>
              : <span>Audio gốc (một track cho cả phần nghe, chưa có mốc thời gian câu này)</span>}
            {(practice || review) && <label className="flex items-center gap-1">Tốc độ
              <select value={rate} onChange={e => setRate(+e.target.value)} className="rounded border border-slate-300 bg-white px-1 dark:border-slate-700 dark:bg-slate-800">
                {[0.75, 0.9, 1, 1.25].map(r => <option key={r} value={r}>{r}×</option>)}
              </select></label>}
          </div>
          <audio ref={audio} controls preload="none" src={api.assetUrl(q.audio_asset_id)} className="w-full"
            onTimeUpdate={e => {
              if (stopAt.current != null && e.currentTarget.currentTime >= stopAt.current) {
                e.currentTarget.pause()
                stopAt.current = null
              }
            }} />
          {from != null && <p className="mt-1 text-xs text-slate-500">Mốc thời gian căn tự động từ bản ghi Whisper, có thể lệch vài giây.</p>}
        </div>
      )}
      {passage && <pre className="jp max-h-72 overflow-y-auto whitespace-pre-wrap rounded-lg bg-slate-50 p-3 text-[15px] leading-relaxed dark:bg-slate-800/60">{passage.text}</pre>}
      {showPage && <details open={!!(q.extra.options_are_pictures || q.extra.options_are_glyph_images)} className="text-sm">
        <summary className="cursor-pointer text-slate-500">Ảnh trang đề gốc (hình minh hoạ / lựa chọn dạng ảnh)</summary>
        <img src={api.assetUrl(q.image_asset_id!)} alt="Ảnh trang đề gốc" loading="lazy" className="mt-2 max-h-[480px] rounded border border-slate-200 dark:border-slate-700" />
      </details>}
      {q.question_text && <p className="jp text-lg leading-relaxed"><Underline text={q.question_text} target={q.extra.target} /></p>}
      {q.extra.options_audio_only && !revealed && <p className="text-xs text-slate-500">Các lựa chọn chỉ có trong audio. Nghe rồi chọn số.</p>}

      <div className="grid gap-2 sm:grid-cols-2" role="radiogroup" aria-label="Lựa chọn">
        {q.options.map(o => {
          const mine = picked.includes(o.option_id)
          const right = revealed && q.correct_answer!.includes(o.option_id)
          const tone = revealed
            ? right ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-950/40' : mine ? 'border-rose-500 bg-rose-50 dark:bg-rose-950/40' : 'border-slate-200 dark:border-slate-700'
            : mine ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-950/40' : 'border-slate-200 hover:border-indigo-300 dark:border-slate-700'
          return (
            <button key={o.option_id} role="radio" aria-checked={mine} disabled={!onChoose || (revealed && !review && practice)}
              onClick={() => onChoose?.(o.option_id)}
              className={`flex items-start gap-2 rounded-lg border-2 p-2.5 text-left transition-colors disabled:cursor-default ${tone}`}>
              <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-slate-200 text-xs font-semibold dark:bg-slate-700">{o.option_id}</span>
              <span className="min-w-0">
                <span className="jp block text-[17px]">{o.text || (q.extra.options_audio_only ? '(trong audio)' : q.extra.options_are_pictures || q.extra.options_are_glyph_images ? '(xem ảnh)' : '')}</span>
                {revealed && q.extra.option_explanations?.[o.option_id] &&
                  <span className="mt-0.5 block text-xs text-slate-600 dark:text-slate-300">{q.extra.option_explanations[o.option_id]}</span>}
              </span>
            </button>
          )
        })}
      </div>

      {revealed && (
        <div className="space-y-2 rounded-lg bg-slate-50 p-3 text-sm dark:bg-slate-800/60">
          <p><b>{!picked.length ? 'Chưa trả lời.' : st?.is_correct ? '✓ Đúng.' : '✗ Sai.'}</b> Đáp án: <b>{q.correct_answer!.join(', ')}</b></p>
          {Array.isArray(q.extra.expected_sequence) && <p>Thứ tự đúng: <b>{q.extra.expected_sequence.join(' → ')}</b></p>}
          {q.extra.expected_sequence_note && <p className="jp">{q.extra.expected_sequence_note}</p>}
          {q.extra.grammar_id && <GrammarHint id={q.extra.grammar_id} pattern={q.extra.grammar_pattern} />}
          {q.explanation_vi && <p>{q.explanation_vi}{q.explanation_origin === 'AI_GENERATED' &&
            <span className="ml-1 text-xs text-slate-500">(giải thích do AI soạn)</span>}</p>}
          {q.extra.passage_translation_vi && <details><summary className="cursor-pointer text-slate-500">Dịch bài đọc</summary>
            <p className="mt-1 whitespace-pre-wrap">{q.extra.passage_translation_vi}</p></details>}
          {q.transcript && <details><summary className="cursor-pointer text-slate-500">
            Script phần nghe{q.extra.transcript_gloss && ' (kèm romaji + dịch)'}</summary>
            {q.extra.transcript_gloss
              ? <div className="mt-1 space-y-2">{q.transcript.split('\n').map((line, i) => (
                  <div key={i}>
                    <p className="jp text-[15px]">{line}</p>
                    <p className="text-xs italic text-slate-500">{q.extra.transcript_gloss![i]?.romaji}</p>
                    <p className="text-xs text-slate-700 dark:text-slate-300">{q.extra.transcript_gloss![i]?.vi}</p>
                  </div>))}</div>
              : <pre className="jp mt-1 whitespace-pre-wrap">{q.transcript}</pre>}</details>}
        </div>
      )}
    </section>
  )
}

// ------------------------------------------------------------------ result
function Result({ a }: { a: Attempt }) {
  const r = a.result!
  const [onlyWrong, setOnlyWrong] = useState(true)
  const [busy, setBusy] = useState(false)
  const rd = r.readiness
  const list = a.questions.filter(q => !onlyWrong || r.per_question[q.question_id] !== 'correct')
  const retry = async () => {
    setBusy(true)
    try { setHashId((await api.startAttempt({ mode: 'practice', mistakes_only: true, limit: 200 })).attempt_id) } finally { setBusy(false) }
  }
  const pct = (b: { accuracy: number | null }) => (b.accuracy == null ? '—' : `${b.accuracy}%`)

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <button onClick={() => setHashId(null)} className="text-sm text-indigo-600 hover:underline dark:text-indigo-300">← Trang thi</button>
          <h1 className="jp text-lg font-semibold">Kết quả · {a.title}</h1>
          <p className="text-xs text-slate-500">Nộp lúc {a.submitted_at!.slice(0, 16).replace('T', ' ')} · {a.mode === 'exam' ? 'Chế độ thi' : 'Luyện tập'}</p>
        </div>
        <Button kind="primary" disabled={busy} onClick={retry}>Ôn lại các câu sai</Button>
      </div>

      <Panel title="Kết quả làm bài (số câu thật)">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
          {([['Tổng số câu', r.total], ['Đúng', r.correct], ['Sai', r.incorrect], ['Chưa làm', r.unanswered], ['Tỉ lệ đúng', pct(r)]] as const).map(([l, v]) => (
            <div key={l} className="rounded-lg bg-slate-50 p-3 dark:bg-slate-800/60">
              <div className="text-xs text-slate-500">{l}</div><div className="text-xl font-semibold tabular-nums">{v}</div>
            </div>))}
        </div>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <BucketTable title="Theo phần" rows={Object.entries(r.by_section).map(([k, b]) => [SECTION_LABEL[k] ?? k, b])} />
          <BucketTable title="Theo dạng câu (Mondai)" rows={r.by_mondai.map(b => [`もんだい${b.mondai_no ?? '?'} · ${MONDAI_LABEL[b.mondai_type ?? ''] ?? b.mondai_type ?? ''}`, b])} />
        </div>
        <div className="mt-3 flex flex-wrap gap-4 text-sm">
          <span>Độ chính xác phần nghe: <b>{r.listening_accuracy == null ? 'không có phần nghe' : `${r.listening_accuracy}%`}</b></span>
          {r.weak_vocabulary_lessons.length > 0 && <span>Từ vựng yếu: {r.weak_vocabulary_lessons.map(w =>
            <Tag key={w.lesson_number} tone="rose">Bài {w.lesson_number}: {w.correct}/{w.total}</Tag>)}</span>}
          {r.weak_grammar_points?.length > 0 && <span>Ngữ pháp yếu: {r.weak_grammar_points.map(w =>
            <Tag key={w.grammar_id} tone="rose"><span className="jp">{w.pattern ?? w.grammar_id}</span>: {w.correct}/{w.total}</Tag>)}</span>}
        </div>
      </Panel>

      <section className="rounded-xl border-2 border-dashed border-amber-300 bg-amber-50/60 p-4 dark:border-amber-800 dark:bg-amber-950/20" aria-label="Ước lượng mức sẵn sàng">
        <h2 className="text-sm font-semibold">{rd.label}</h2>
        <div className="mt-2 flex flex-wrap gap-6 text-sm tabular-nums">
          <span>Kiến thức + Đọc: <b>{rd.language_knowledge_reading ?? '—'}</b>/120 <span className="text-xs text-slate-500">(sàn {rd.thresholds.language_knowledge_reading})</span></span>
          <span>Nghe: <b>{rd.listening ?? '—'}</b>/60 <span className="text-xs text-slate-500">(sàn {rd.thresholds.listening})</span></span>
          <span>Tổng: <b>{rd.total ?? '—'}</b>/180 <span className="text-xs text-slate-500">(đỗ từ {rd.thresholds.total})</span></span>
          {rd.likely_pass != null && <Tag tone={rd.likely_pass ? 'emerald' : 'rose'}>{rd.likely_pass ? 'Có khả năng đạt' : 'Chưa đạt ngưỡng'}</Tag>}
        </div>
        {rd.notes.map(n => <p key={n} className="mt-1 text-xs text-slate-600 dark:text-slate-300">• {n}</p>)}
        <p className="mt-2 text-xs text-slate-500">{rd.disclaimer}</p>
      </section>

      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold">Xem lại từng câu</h2>
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={onlyWrong} onChange={e => setOnlyWrong(e.target.checked)} />Chỉ câu sai / chưa làm</label>
      </div>
      {list.length === 0 && <p className="text-sm text-slate-500">Không có câu sai. 🎉</p>}
      {list.map(q => <QuestionCard key={q.question_id} q={q} a={a} review pos={`${a.questions.indexOf(q) + 1}/${a.questions.length}`} />)}
    </div>
  )
}

export function BucketTable({ title, rows }: { title: string; rows: [string, { total: number; correct: number; incorrect: number; unanswered: number; accuracy: number | null }][] }) {
  return (
    <div>
      {title && <h3 className="mb-1 text-xs font-semibold text-slate-500">{title}</h3>}
      <table className="w-full text-sm">
        <thead className="text-left text-xs text-slate-500"><tr><th className="py-1"></th><th className="text-right">Đúng</th><th className="text-right">Sai</th><th className="text-right">Bỏ</th><th className="text-right">%</th></tr></thead>
        <tbody>{rows.map(([l, b]) => (
          <tr key={l} className="border-t border-slate-100 dark:border-slate-800">
            <td className="jp py-1 pr-2">{l}</td><td className="text-right tabular-nums">{b.correct}/{b.total}</td>
            <td className="text-right tabular-nums">{b.incorrect}</td><td className="text-right tabular-nums">{b.unanswered}</td>
            <td className="text-right tabular-nums">{b.accuracy ?? '—'}</td>
          </tr>))}</tbody>
      </table>
    </div>
  )
}

/** "Learn while reviewing": the grammar point behind a revealed question, with a link to its full page. */
function GrammarHint({ id, pattern }: { id: string; pattern?: string }) {
  const [g, setG] = useState<GrammarDetail | null>(null)
  useEffect(() => { api.grammarItem(id).then(setG).catch(() => setG(null)) }, [id])
  return (
    <div className="rounded-md border border-indigo-200 bg-indigo-50/60 p-2 dark:border-indigo-900 dark:bg-indigo-950/40">
      <p>Điểm ngữ pháp: <a href={`#/grammar?id=${id}`} className="jp font-medium hover:underline">{g?.pattern ?? pattern ?? id}</a>
        {g?.meaning_vi && <> · {g.meaning_vi}</>}</p>
      {g?.formation && <p className="jp mt-1 text-xs text-slate-600 dark:text-slate-300">Cấu trúc: {g.formation}</p>}
    </div>
  )
}
