import { useEffect, useState } from 'react'
import { api, type Dashboard as D } from '../api'
import { Button, ErrorBox, fmtDuration, Loading, Panel, StartButton } from '../ui'

const CARD_STATUS: [string, string, string][] = [
  ['new', 'Mới', 'bg-slate-300 dark:bg-slate-600'],
  ['learning', 'Đang học', 'bg-sky-500'],
  ['reviewing', 'Đang ôn', 'bg-indigo-500'],
  ['mastered', 'Thuộc', 'bg-emerald-500'],
  ['needs_attention', 'Cần chú ý', 'bg-rose-500'],
]

function Stat({ label, value, hint }: { label: string; value: number | string; hint?: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <div className="text-xs text-slate-500">{label}</div>
      <div className="mt-1 text-2xl font-semibold tabular-nums">{value}</div>
      {hint && <div className="mt-1 text-xs text-slate-500">{hint}</div>}
    </div>
  )
}

function StackBar({ data, total }: { data: Record<string, number>; total: number }) {
  return (
    <div>
      <div className="flex h-3 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800" role="img"
        aria-label={CARD_STATUS.map(([k, l]) => `${l}: ${data[k] ?? 0}`).join(', ')}>
        {CARD_STATUS.map(([k, , c]) => (data[k] ? <div key={k} className={c} style={{ width: `${(data[k] / total) * 100}%` }} /> : null))}
      </div>
      <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-600 dark:text-slate-300">
        {CARD_STATUS.map(([k, l, c]) => (
          <li key={k} className="flex items-center gap-1.5"><span className={`h-2 w-2 rounded-full ${c}`} />{l} <b className="tabular-nums">{data[k] ?? 0}</b></li>
        ))}
      </ul>
    </div>
  )
}

function GoalCard({ d, onSaved }: { d: D; onSaved: (goal: number) => void }) {
  const [edit, setEdit] = useState<string | null>(null)
  const [err, setErr] = useState('')
  const pct = Math.min(100, Math.round((d.done_today / d.daily_goal) * 100))
  const save = async () => {
    const n = Number(edit)
    if (!Number.isInteger(n) || n < 5 || n > 500) { setErr('Từ 5 đến 500'); return }
    try { onSaved((await api.saveSettings({ daily_goal: n })).daily_goal); setEdit(null); setErr('') } catch (e) { setErr(String(e)) }
  }
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center justify-between text-xs text-slate-500">
        <span>Mục tiêu hôm nay</span>
        {edit === null && <button type="button" className="hover:underline" onClick={() => setEdit(String(d.daily_goal))}>Sửa</button>}
      </div>
      {edit === null
        ? <div className="mt-1 text-2xl font-semibold tabular-nums">{d.done_today}<span className="text-base text-slate-500">/{d.daily_goal}</span></div>
        : <form className="mt-1 flex items-center gap-1" onSubmit={e => { e.preventDefault(); save() }}>
          <input type="number" min={5} max={500} value={edit} onChange={e => setEdit(e.target.value)} aria-label="Số lượt học mỗi ngày"
            className="w-20 rounded-md border border-slate-300 bg-white px-2 py-1 text-sm dark:border-slate-700 dark:bg-slate-800" autoFocus />
          <Button type="submit" kind="primary">Lưu</Button>
          <Button onClick={() => { setEdit(null); setErr('') }}>Huỷ</Button>
        </form>}
      {err && <p role="alert" className="text-xs text-rose-600">{err}</p>}
      <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800" role="progressbar"
        aria-valuenow={d.done_today} aria-valuemin={0} aria-valuemax={d.daily_goal} aria-label="Tiến độ mục tiêu hôm nay">
        <div className={pct >= 100 ? 'h-full bg-emerald-500' : 'h-full bg-indigo-500'} style={{ width: `${pct}%` }} />
      </div>
      <div className="mt-1 text-xs text-slate-500">
        {pct >= 100 ? 'Đã đạt mục tiêu ✓' : 'Lượt ôn thẻ + câu trả lời'} · {fmtDuration(d.study_seconds_today)} (ước tính)
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [d, setD] = useState<D | null>(null)
  const [err, setErr] = useState<unknown>(null)
  useEffect(() => { api.dashboard().then(setD).catch(setErr) }, [])
  if (err) return <ErrorBox error={err} />
  if (!d) return <Loading />

  const sum = (m: Record<string, number>) => Object.values(m).reduce((a, b) => a + b, 0)
  const dueVocab = (d.due_now.jp_vi ?? 0) + (d.due_now.vi_jp ?? 0)
  const dueGrammar = d.due_by_entity.grammar ?? 0
  const dueKanji = d.due_by_entity.kanji ?? 0
  const due = dueVocab + dueGrammar + dueKanji
  const accuracy = d.reviews_today ? Math.round((d.correct_today / d.reviews_today) * 100) : null

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h1 className="text-xl font-semibold">Tổng quan · JLPT {d.level}</h1>
          <p className="text-sm text-slate-500">Số liệu lấy trực tiếp từ cơ sở dữ liệu học tập của bạn.</p>
        </div>
        <a href="#/flashcards" className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500">
          {due ? `Ôn ${due} thẻ đến hạn` : 'Học thẻ mới'}
        </a>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat label="Chuỗi ngày học" value={`${d.streak_days} ngày`} />
        <GoalCard d={d} onSaved={g => setD({ ...d, daily_goal: g })} />
        <Stat label="Thẻ đến hạn" value={due} hint={`Từ vựng ${dueVocab} · Ngữ pháp ${dueGrammar} · Kanji ${dueKanji}`} />
        <Stat label="Lượt ôn thẻ hôm nay" value={d.reviews_today} hint={accuracy !== null ? `Nhớ đúng ${accuracy}%` : 'Chưa ôn hôm nay'} />
      </div>

      <Panel title="Học gì tiếp" action={<a href="#/analytics" className="text-sm text-indigo-600 hover:underline dark:text-indigo-300">Xem thống kê →</a>}>
        {d.recommendations.length === 0
          ? <p className="text-sm text-slate-500">Không có việc gợi ý: hôm nay không có thẻ đến hạn, câu sai hay điểm ngữ pháp yếu.</p>
          : <ol className="divide-y divide-slate-100 text-sm dark:divide-slate-800">
            {d.recommendations.map(r => (
              <li key={r.kind} className="flex flex-wrap items-center justify-between gap-2 py-2">
                <div>
                  <div className="jp font-medium">{r.title}</div>
                  <div className="text-xs text-slate-500">{r.reason}</div>
                </div>
                {r.start
                  ? <StartButton body={r.start}>Bắt đầu</StartButton>
                  : <a href={r.href} className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800">Mở</a>}
              </li>))}
          </ol>}
        <p className="mt-2 text-xs text-slate-500">Gợi ý tính từ dữ liệu học của bạn (thẻ đến hạn, câu sai gần nhất, điểm ngữ pháp yếu, lần thi gần nhất).</p>
      </Panel>

      <div className="grid gap-4 md:grid-cols-2">
        <Panel title="Mức độ thuộc (thẻ SRS)">
          <div className="space-y-4">
            {([['Từ vựng (JP→VI)', d.cards_by_status, 'vocabulary'], ['Ngữ pháp', d.cards_by_entity.grammar, 'grammar'],
              ['Kanji', d.cards_by_entity.kanji, 'kanji']] as const).map(([l, m, e]) => (
              <div key={e}>
                <a href={`#/flashcards?entity=${e}`} className="mb-1 block text-sm font-medium hover:underline">{l}</a>
                <StackBar data={m} total={sum(m) || 1} />
              </div>))}
          </div>
          <p className="mt-3 text-xs text-slate-500">"Thuộc" yêu cầu ≥3 lần nhớ liên tiếp và khoảng ôn ≥21 ngày — không bao giờ sau 1 lần trả lời.</p>
        </Panel>
        <Panel title="Chất lượng dữ liệu">
          <dl className="grid grid-cols-2 gap-2 text-sm">
            <dt className="text-slate-500">Từ vựng cần duyệt</dt><dd className="tabular-nums font-medium">{d.vocabulary_by_status.needs_review ?? 0}</dd>
            <dt className="text-slate-500">Từ vựng chưa xác minh</dt><dd className="tabular-nums font-medium">{d.vocabulary_by_status.normalized ?? 0}</dd>
            <dt className="text-slate-500">Câu hỏi đề mẫu cần duyệt</dt><dd className="tabular-nums font-medium">{d.questions_by_status.needs_review ?? 0}</dd>
            <dt className="text-slate-500">Vấn đề mở (lỗi / cảnh báo)</dt><dd className="tabular-nums font-medium">{d.open_issues.error ?? 0} / {d.open_issues.warning ?? 0}</dd>
          </dl>
          <a href="#/review" className="mt-3 inline-block text-sm text-indigo-600 hover:underline dark:text-indigo-300">Mở màn hình duyệt →</a>
        </Panel>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Panel title="Thi thử" action={<a href="#/exam" className="text-sm text-indigo-600 hover:underline dark:text-indigo-300">Mở trang thi →</a>}>
          <dl className="grid grid-cols-2 gap-2 text-sm">
            <dt className="text-slate-500">Lượt đã nộp</dt><dd className="tabular-nums font-medium">{d.exam.attempts_submitted}</dd>
            <dt className="text-slate-500">Lượt gần nhất</dt>
            <dd className="font-medium">{d.exam.last
              ? <a href={`#/exam?id=${d.exam.last.attempt_id}`} className="hover:underline">{d.exam.last.correct}/{d.exam.last.total} câu ({d.exam.last.accuracy ?? 0}%)</a>
              : 'Chưa có'}</dd>
            <dt className="text-slate-500">Câu sai chờ ôn</dt><dd className="tabular-nums font-medium">{d.exam.mistakes_pending}</dd>
            <dt className="text-slate-500">Ngân hàng câu hỏi</dt><dd className="tabular-nums font-medium">{d.exam.bank_questions}</dd>
          </dl>
        </Panel>
        <Panel title="Kiến thức N5 đã xác minh">
          <dl className="grid grid-cols-2 gap-2 text-sm">
            {([['Từ vựng', d.vocabulary_by_status, '#/vocabulary'], ['Ngữ pháp', d.grammar_by_status, '#/grammar'],
              ['Kanji', d.kanji_by_status, '#/kanji']] as const).map(([l, m, href]) => (
              <div key={l} className="contents">
                <dt><a href={href} className="text-slate-500 hover:underline">{l}</a></dt>
                <dd className="tabular-nums font-medium">{m.verified ?? 0}/{Object.values(m).reduce((a, b) => a + b, 0)}</dd>
              </div>))}
          </dl>
        </Panel>
      </div>

      <Panel title="Ngữ pháp cần ôn" action={<a href="#/flashcards?entity=grammar" className="text-sm text-indigo-600 hover:underline dark:text-indigo-300">Ôn thẻ ngữ pháp →</a>}>
        {d.weak_grammar_points.length === 0
          ? <p className="text-sm text-slate-500">Chưa có gợi ý: làm <a href="#/exam" className="text-indigo-600 hover:underline dark:text-indigo-300">bài thi thử hoặc luyện tập</a> có phần ngữ pháp (文の文法) để biết điểm nào còn sai.</p>
          : <>
            <ul className="divide-y divide-slate-100 text-sm dark:divide-slate-800">
              {d.weak_grammar_points.map(w => (
                <li key={w.grammar_id} className="flex items-center justify-between gap-2 py-1.5">
                  <a href={`#/grammar?id=${w.grammar_id}`} className="jp hover:underline">{w.pattern ?? w.grammar_id}</a>
                  <span className="flex shrink-0 items-center gap-2">
                    <span className="tabular-nums text-slate-500">đúng {w.correct}/{w.total}</span>
                    <StartButton body={{ mode: 'practice', grammar_id: w.grammar_id, limit: 10 }}>Luyện</StartButton>
                  </span>
                </li>
              ))}
            </ul>
            <p className="mt-2 text-xs text-slate-500">Tính theo lần trả lời gần nhất của mỗi câu trong các lượt đã nộp; làm đúng lại thì điểm đó tự biến mất.</p>
          </>}
      </Panel>

      <Panel title="Bài có tỉ lệ quên cao nhất">
        {d.weak_lessons.length === 0
          ? <p className="text-sm text-slate-500">Chưa đủ dữ liệu: cần có lượt trả lời "Lại" trong phần ôn tập.</p>
          : <ul className="divide-y divide-slate-100 text-sm dark:divide-slate-800">
            {d.weak_lessons.map(w => (
              <li key={w.deck} className="flex items-center justify-between py-1.5">
                <span>{w.lesson_number ? `Bài ${w.lesson_number}` : w.deck}</span>
                <span className="tabular-nums text-slate-500">quên {w.wrong} / {w.wrong + w.right} lượt</span>
              </li>
            ))}
          </ul>}
      </Panel>

      <BackupPanel />
    </div>
  )
}

function BackupPanel() {
  const [msg, setMsg] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  async function restore(file: File) {
    if (!confirm(`Khôi phục từ "${file.name}"? Toàn bộ dữ liệu hiện tại sẽ được thay bằng bản sao lưu (bản hiện tại được tự lưu lại trước).`)) return
    setBusy(true)
    try {
      const r = await api.restore(file)
      setMsg(`Đã khôi phục: ${r.counts.srs_cards} thẻ, ${r.counts.review_log} lượt ôn, ${r.counts.exam_attempts} lượt thi.`
        + (r.pre_restore_backup ? ` Bản trước khi khôi phục: data/database/backups/${r.pre_restore_backup}.` : ''))
    } catch (e) {
      setMsg(`Không khôi phục được: ${e instanceof Error ? e.message : String(e)}`)
    } finally {
      setBusy(false)
    }
  }
  return (
    <Panel title="Sao lưu dữ liệu">
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <a href={api.backupUrl} download className="rounded-lg bg-indigo-600 px-3 py-1.5 text-white hover:bg-indigo-500">Tải bản sao lưu</a>
        <label className="cursor-pointer rounded-lg border border-slate-300 px-3 py-1.5 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800">
          {busy ? 'Đang khôi phục…' : 'Khôi phục từ file…'}
          <input type="file" accept=".sqlite,.db" className="sr-only" disabled={busy}
            onChange={e => { const f = e.target.files?.[0]; e.target.value = ''; if (f) void restore(f) }} />
        </label>
      </div>
      {msg && <p className="mt-2 text-sm" role="status">{msg}</p>}
      <p className="mt-2 text-xs text-slate-500">Bản sao lưu là toàn bộ cơ sở dữ liệu (tiến độ SRS, lịch sử thi, cài đặt, chỉnh sửa của bạn). Sau khi khôi phục bản cũ, chạy <code>hub import</code> để cập nhật nội dung học mới; tiến độ được giữ nguyên.</p>
    </Panel>
  )
}
