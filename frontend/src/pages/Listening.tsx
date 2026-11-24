import { useEffect, useState, type ReactNode } from 'react'
import { api, type AttemptStart, type ExamOverview } from '../api'
import { Button, ErrorBox, Loading, Panel, Tag } from '../ui'
import { MONDAI_LABEL } from './Exam'

// Listening hub: launches the existing attempt engine (Exam.tsx) filtered to 聴解, plus exam strategy notes.
const TYPES = ['task_based', 'point_comprehension', 'verbal_expression', 'quick_response'] as const
const SOURCE_EXAM_TYPE: Record<string, string> = { official: 'official_sample', past: 'past_exam', video: 'video_practice' }
const PAPER_TYPES = Object.values(SOURCE_EXAM_TYPE)
const INPUT = 'rounded-lg border border-slate-300 bg-white px-2 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-800'

type Tip = { title: string; body: ReactNode[] }

const MONDAI_TIPS: Tip[] = [
  {
    title: '問題1 課題理解 · 7 câu · "phải làm gì / mua gì / mang gì"',
    body: [
      <>Câu hỏi được đọc <b>trước</b> hội thoại và nhắc lại ở cuối. Lần đầu nghe, ghi ngay ra lề: <b>ai</b> (男の人 hay 女の人) và <b>làm gì</b> (なにを かいますか / どこへ いきますか / なにを もって いきますか).</>,
      <>Có <span className="jp">まず・はじめに・このあと・つぎに</span> thì câu hỏi chỉ hỏi <b>1 việc</b> trong chuỗi việc. Bám thứ tự <span className="jp">～てから・～まえに・そのあとで</span>.</>,
      <>Hội thoại hay theo kiểu: đề xuất → bị bác (<span className="jp">それは ちょっと…／それは もう あります／～なくても いいです</span>) → chốt. Chỉ chọn khi nghe câu chốt: <span className="jp">じゃあ、～に します／～て ください／～を おねがいします</span>.</>,
      <>Nghe đến đâu, gạch tranh bị loại đến đó. Cuối câu thường chỉ còn 1–2 tranh.</>,
    ],
  },
  {
    title: '問題2 ポイント理解 · 6 câu · "khi nào / ở đâu / bao nhiêu / vì sao"',
    body: [
      <>Từ để hỏi quyết định đáp án: <span className="jp">いつ・どこ・だれ・なん・いくら・どうして・どれ・なんにん・なんじ</span>. Viết nó to ra lề rồi chỉ nghe thông tin đó.</>,
      <>Gần như cả 4 lựa chọn đều được nhắc đến trong bài. Đáp án là cái <b>khớp điều kiện</b> của câu hỏi: đúng người (của anh hay của chị), đúng thời điểm (<span className="jp">きのう</span> hay <span className="jp">きょう</span>), không bị phủ định.</>,
      <>Bẫy hay gặp: thông tin bị sửa lại ngay sau đó (<span className="jp">～じゃなくて…／あ、ちがいました</span>). Đừng chốt khi mới nghe lựa chọn đầu tiên: nghe hết rồi mới chọn.</>,
      <>Số, giờ, ngày, giá: ghi số ra giấy ngay lúc nghe, đừng giữ trong đầu (xem bẫy số đếm ở dưới).</>,
    ],
  },
  {
    title: '問題3 発話表現 · 5 câu · "bạn nói gì trong tình huống này"',
    body: [
      <>Nhìn tranh, tìm <b>người có mũi tên</b>: bạn là người đó. Lựa chọn (3 câu) chỉ có trong audio, nên khi nghe hãy đánh dấu ○ / × cho từng câu.</>,
      <>Phân biệt 4 ý: nhờ người khác làm <span className="jp">～て ください</span>; đề nghị mình làm giúp <span className="jp">～ましょうか</span>; xin phép <span className="jp">～ても いいですか</span>; rủ cùng làm <span className="jp">～ませんか／～ましょう</span>.</>,
      <>Cho/nhận (授受, phần bạn hay sai): mình đưa → <span className="jp">（わたしは）～に あげます</span>. Người khác đưa mình → <span className="jp">～が（わたしに）くれます</span>; mình nhận → <span className="jp">（わたしは）～に／から もらいます</span>. Đổi chiều cho/nhận hoặc đổi <span className="jp">が／に</span> là đáp án sai.</>,
      <>Câu chào theo tình huống: <span className="jp">いただきます／ごちそうさまでした・いってきます／いってらっしゃい・ただいま／おかえりなさい・しつれいします・おさきに しつれいします・おやすみなさい・おめでとうございます・すみません・これを ください</span>.</>,
    ],
  },
  {
    title: '問題4 即時応答 · 6 câu · "đáp lại 1 câu ngắn"',
    body: [
      <>Không có tranh. Câu rất ngắn, nên xác định <b>loại câu</b> ngay từ âm cuối: hỏi (<span className="jp">～か</span>), mời (<span className="jp">～ませんか</span>), xin phép (<span className="jp">～ても いいですか</span>), cảm ơn, xin lỗi, chào.</>,
      <>Cặp đáp quen thuộc: <span className="jp">ありがとうございます → いいえ、どういたしまして・～ませんか → ええ、いいですね・～ても いいですか → はい、どうぞ／すみません、ちょっと…・いってきます → いってらっしゃい・おげんきですか → はい、げんきです</span>.</>,
      <>Bẫy: lựa chọn có từ <b>nghe giống</b> từ trong câu hỏi nhưng sai loại câu trả lời: hỏi <span className="jp">いつ</span> mà đáp nơi chốn, hỏi về người kia mà đáp về mình, sai thì quá khứ/hiện tại. Lặp lại động từ để đáp vẫn có thể đúng (<span className="jp">～ませんか → ええ、～ましょう</span>).</>,
      <>Lỡ nghe 1 lựa chọn: chọn câu tự nhiên nhất trong số còn lại, tô ngay, quên câu đó và chuẩn bị nghe câu sau.</>,
    ],
  },
]

const NUMBER_TRAPS = '1日 ついたち · 2日 ふつか · 4日 よっか ↔ 8日 ようか · 9日 ここのか · 10日 とおか · 20日 はつか · 14日/24日 じゅうよっか/にじゅうよっか · 4月 しがつ · 7月 しちがつ · 9月 くがつ · 4時 よじ · 7時 しちじ · 9時 くじ · 1分 いっぷん · 3分 さんぷん · 4分 よんぷん · 6分 ろっぷん · 8分 はっぷん · 10分 じゅっぷん · 1人 ひとり · 2人 ふたり · 4人 よにん · 300 さんびゃく · 600 ろっぴゃく · 800 はっぴゃく · 3000 さんぜん · 8000 はっせん'

const EXAM_DAY: ReactNode[] = [
  <>Cấu trúc: 4 mondai, thường 24 câu (7 + 6 + 5 + 6, có thể chênh 1–2 câu), khoảng 30 phút. Mỗi câu <b>chỉ phát 1 lần</b>. Điểm nghe tính trên thang 0–60 và phải đạt tối thiểu <b>19</b>; tổng điểm đỗ là 80/180.</>,
  <>Phần nghe làm sau cùng, sau giờ nghỉ. Hãy đi vệ sinh và uống nước trong giờ nghỉ, vì trong lúc nghe không được ra ngoài.</>,
  <><b>Tô phiếu ngay sau mỗi câu.</b> Audio chạy liên tục, hết bài không có thời gian riêng để chép đáp án. Mỗi mondai đánh số lại từ 1, và ô <span className="jp">れい</span> đã tô sẵn. Hãy kiểm tra số câu trên phiếu trước khi tô.</>,
  <>Lúc phát hướng dẫn và câu ví dụ (<span className="jp">れい</span>), bạn đã biết cách làm rồi. Hãy dùng thời gian đó để <b>xem trước tranh</b> và lựa chọn của 2–3 câu tiếp theo (問題1, 2). 問題3 chỉ có tranh, 問題4 không có gì trên đề.</>,
  <>Được viết ghi chú vào tờ đề (メモ). Ghi số, giờ, ngày, và gạch tranh bị loại.</>,
  <>Lỡ một câu thì <b>không nghĩ lại</b>: đoán, tô, rồi chuyển sang câu sau. Không bỏ trống (sai không bị trừ điểm). Nếu cứ tiếc câu cũ, bạn sẽ mất luôn câu tiếp theo.</>,
  <>Mang bút chì HB và tẩy. Ngay lúc phát hướng dẫn và câu <span className="jp">れい</span>, nếu loa nhỏ hoặc rè thì giơ tay báo giám thị liền, đừng đợi đến câu 1.</>,
]

const PLAN: ReactNode[] = [
  <>Mỗi ngày luyện 1 mondai, 10–15 câu, ở chế độ <b>Luyện tập</b>. Nghe 1 lần không dừng rồi trả lời. Sau đó đọc script (có romaji + dịch), bấm "Nghe câu này" và nghe lại trong khi nhìn script. Cuối cùng nghe lần nữa không nhìn script.</>,
  <>Chỉ dùng tốc độ 0.9× khi nghe lại để hiểu. Lúc làm bài thì luôn để 1× như thi thật.</>,
  <>Tuần cuối trước ngày thi: làm 2–3 <b>đề nghe đầy đủ</b> ở chế độ Thi, không tạm dừng, để quen nhịp 30 phút.</>,
  <>Sau mỗi lượt làm bài, bấm "Ôn câu nghe sai". Câu sai lần 2 thì chép lại câu chốt của script vào sổ.</>,
]

function Bullets({ items }: { items: ReactNode[] }) {
  return <ul className="list-disc space-y-1.5 pl-5 text-sm leading-relaxed">{items.map((x, i) => <li key={i}>{x}</li>)}</ul>
}

export default function Listening() {
  const [ov, setOv] = useState<ExamOverview | null>(null)
  const [err, setErr] = useState<unknown>(null)
  const [busy, setBusy] = useState(false)
  const [source, setSource] = useState<'all' | 'official' | 'past' | 'video'>('all')
  const [limit, setLimit] = useState(10)
  useEffect(() => { api.exams().then(setOv).catch(setErr) }, [])

  const start = async (body: AttemptStart) => {
    setBusy(true)
    try { location.hash = `#/exam?id=${(await api.startAttempt(body)).attempt_id}` } catch (e) { setErr(e) } finally { setBusy(false) }
  }
  if (!ov) return err ? <ErrorBox error={err} /> : <Loading />

  const bank = ov.bank.filter(b => b.section === 'listening' && (source === 'all' || SOURCE_EXAM_TYPE[source] === b.exam_type))
  const count = (t: string) => bank.filter(b => b.mondai_type === t).reduce((a, b) => a + b.n, 0)
  const papers = ov.exams.filter(e => PAPER_TYPES.includes(e.exam_type))

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Luyện nghe 聴解</h1>
        <p className="text-sm text-slate-500">
          Tất cả câu nghe dùng audio gốc. Ở chế độ Luyện tập, script kèm romaji và bản dịch hiện ra sau khi bạn trả lời.
          Ở chế độ Thi, script chỉ hiện sau khi nộp bài.
        </p>
      </div>
      {err != null && <ErrorBox error={err} />}

      <Panel title="Luyện theo dạng câu (Mondai)">
        <div className="mb-3 flex flex-wrap items-center gap-3 text-sm">
          <label className="flex items-center gap-2">Nguồn
            <select value={source} onChange={e => setSource(e.target.value as typeof source)} className={INPUT}>
              <option value="all">Tất cả</option>
              <option value="past">Đề thật các năm</option>
              <option value="video">Đề luyện từ video</option>
              <option value="official">Đề mẫu chính thức</option>
            </select>
          </label>
          <label className="flex items-center gap-2">Số câu
            <input type="number" min={1} max={100} value={limit} className={`${INPUT} w-20`}
              onChange={e => setLimit(Math.max(1, Math.min(100, +e.target.value || 1)))} />
          </label>
        </div>
        <div className="flex flex-wrap gap-2">
          {TYPES.map(t => (
            <Button key={t} disabled={busy || !count(t)}
              onClick={() => start({ mode: 'practice', section: 'listening', mondai_type: t, source, limit, timing: 'none' })}>
              <span className="jp">{MONDAI_LABEL[t]}</span> ({count(t)})
            </Button>))}
          <Button kind="primary" disabled={busy}
            onClick={() => start({ mode: 'practice', section: 'listening', mistakes_only: true, limit: 200, timing: 'none' })}>
            Ôn câu nghe sai
          </Button>
        </div>
      </Panel>

      <Panel title="Đề nghe đầy đủ (như thi thật)">
        <div className="space-y-3">
          {papers.map(e => (
            <div key={e.exam_id} className="flex flex-wrap items-center gap-3">
              <div className="min-w-0 flex-1">
                <div className="jp font-medium">{e.title}</div>
                <div className="mt-1 flex flex-wrap gap-1.5 text-xs">
                  {e.exam_type === 'video_practice' ? <Tag tone="amber">Đề luyện từ video YouTube · đáp án video + 2 AI đối chiếu</Tag>
                    : e.is_official ? <Tag tone="emerald">Đề mẫu chính thức</Tag> : <Tag tone="indigo">Đề thật</Tag>}
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button kind="primary" disabled={busy}
                  onClick={() => start({ mode: 'exam', exam_id: e.exam_id, section: 'listening', timing: 'current' })}>Thi phần nghe (30 phút)</Button>
                <Button disabled={busy}
                  onClick={() => start({ mode: 'practice', exam_id: e.exam_id, section: 'listening', timing: 'none' })}>Luyện tập</Button>
              </div>
            </div>))}
        </div>
      </Panel>

      <Panel title="Cách nghe từng dạng câu">
        <div className="space-y-2">
          {MONDAI_TIPS.map((t, i) => (
            <details key={t.title} open={i === 0} className="rounded-lg border border-slate-200 p-3 dark:border-slate-800">
              <summary className="jp cursor-pointer font-medium">{t.title}</summary>
              <div className="mt-2"><Bullets items={t.body} /></div>
            </details>))}
          <details className="rounded-lg border border-slate-200 p-3 dark:border-slate-800">
            <summary className="cursor-pointer font-medium">Bẫy số, giờ, ngày (biến âm)</summary>
            <p className="jp mt-2 text-sm leading-relaxed">{NUMBER_TRAPS}</p>
            <p className="mt-2 text-sm">Luyện thêm ở trang <a href="#/numbers" className="text-indigo-600 hover:underline dark:text-indigo-300">Số đếm</a>.</p>
          </details>
        </div>
      </Panel>

      <Panel title="Kinh nghiệm trong phòng thi"><Bullets items={EXAM_DAY} /></Panel>
      <Panel title="Lịch luyện nghe đến ngày thi"><Bullets items={PLAN} /></Panel>
    </div>
  )
}
