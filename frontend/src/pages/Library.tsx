import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { api, type Source } from '../api'
import { Button, ErrorBox, Loading, Panel, Tag } from '../ui'

const ACCESS: Record<string, [string, 'emerald' | 'amber' | 'rose' | 'slate' | 'indigo']> = {
  local: ['Tệp cục bộ', 'emerald'],
  accessible: ['Truy cập được', 'emerald'],
  requires_auth: ['Cần đăng nhập', 'amber'],
  manual_export: ['Cần export thủ công', 'amber'],
  unreachable: ['Không truy cập được', 'rose'],
  unchecked: ['Chưa kiểm tra', 'slate'],
}

function fmtSize(n: number | null) {
  if (!n) return ''
  return n > 1 << 20 ? `${(n / (1 << 20)).toFixed(1)} MB` : `${Math.round(n / 1024)} KB`
}

export default function Library() {
  const [q, setQ] = useState('')
  const [type, setType] = useState('')
  const [items, setItems] = useState<Source[] | null>(null)
  const [err, setErr] = useState<unknown>(null)
  const [busy, setBusy] = useState<string | null>(null)
  const [msg, setMsg] = useState<string | null>(null)

  const load = useCallback(() => { api.sources(q, type).then(setItems).catch(setErr) }, [q, type])
  useEffect(() => { const t = setTimeout(load, 200); return () => clearTimeout(t) }, [load])

  const run = async (label: string, fn: () => Promise<unknown>) => {
    setBusy(label); setMsg(null)
    try { await fn(); setMsg(`${label}: xong`); load() } catch (e) { setMsg(`${label}: ${e instanceof Error ? e.message : e}`) } finally { setBusy(null) }
  }

  const add = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const f = new FormData(e.currentTarget)
    const form = e.currentTarget
    await run('Đăng ký URL', () => api.addSource({
      url: f.get('url'), name: f.get('name'), source_type: f.get('source_type'), reliability: f.get('reliability'),
    }))
    form.reset()
  }

  if (err) return <ErrorBox error={err} />
  const types = items ? [...new Set(items.map(s => s.source_type))].sort() : []
  const input = 'rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-900'

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h1 className="text-xl font-semibold">Thư viện nguồn</h1>
          <p className="text-sm text-slate-500">Mọi dữ liệu đều truy được về một nguồn. Tệp gốc chỉ được đọc, không bị sửa.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button disabled={!!busy} onClick={() => run('Quét thư mục', api.scan)}>Quét thư mục cục bộ</Button>
          <Button disabled={!!busy} onClick={() => run('Kiểm tra URL', api.checkOnline)} title="Chỉ kiểm tra truy cập, không tải nội dung">Kiểm tra truy cập URL</Button>
          <a className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800" href="/api/sources/export" download>Xuất metadata JSON</a>
        </div>
      </div>
      {(busy || msg) && <p role="status" className="text-sm text-slate-600 dark:text-slate-300">{busy ? `${busy}…` : msg}</p>}

      <div className="flex flex-wrap gap-2">
        <input aria-label="Tìm nguồn" className={`${input} min-w-0 flex-1`} placeholder="Tìm theo tên, URL, mục đích…" value={q} onChange={e => setQ(e.target.value)} />
        <select aria-label="Loại nguồn" className={input} value={type} onChange={e => setType(e.target.value)}>
          <option value="">Mọi loại</option>
          {types.map(t => <option key={t}>{t}</option>)}
        </select>
      </div>

      {!items ? <Loading /> : (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs text-slate-500 dark:bg-slate-800/50">
              <tr><th className="px-3 py-2">Nguồn</th><th className="px-3 py-2">Loại / độ tin cậy</th><th className="px-3 py-2">Truy cập</th>
                <th className="px-3 py-2">Xử lý</th><th className="px-3 py-2 text-right">Bản ghi</th><th className="px-3 py-2"></th></tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {items.map(s => {
                const [al, at] = ACCESS[s.access_status ?? 'unchecked'] ?? [s.access_status ?? '', 'slate']
                return (
                  <tr key={s.source_id} className="align-top">
                    <td className="max-w-md px-3 py-2">
                      <div className="font-medium">{s.url ? <a href={s.url} target="_blank" rel="noreferrer" className="hover:underline">{s.name}</a> : s.name}</div>
                      <div className="text-xs text-slate-500">{s.source_id}{s.page_count ? ` · ${s.page_count} trang` : ''}{s.duration_seconds ? ` · ${Math.round(s.duration_seconds)} giây` : ''}{s.size_bytes ? ` · ${fmtSize(s.size_bytes)}` : ''}</div>
                      {s.purpose && <div className="text-xs text-slate-600 dark:text-slate-400">{s.purpose}</div>}
                      {s.notes && <div className="text-xs text-slate-500">{s.notes}</div>}
                      {s.error && <div className="text-xs text-rose-600">{s.error}</div>}
                    </td>
                    <td className="px-3 py-2"><div>{s.source_type}</div><Tag tone={s.reliability === 'OFFICIAL' ? 'indigo' : 'slate'}>{s.reliability}</Tag></td>
                    <td className="px-3 py-2"><Tag tone={at}>{al}</Tag></td>
                    <td className="px-3 py-2 text-xs">{s.processing_status}</td>
                    <td className="px-3 py-2 text-right tabular-nums">{s.record_count || ''}</td>
                    <td className="px-3 py-2">
                      {(s.source_id.startsWith('SRC_LOCAL_FC_') || s.source_id.startsWith('SRC_LOCAL_N5_')) &&
                        <Button kind="ghost" disabled={!!busy} onClick={() => run(`Xử lý lại ${s.source_id}`, () => api.reprocess(s.source_id))}>Xử lý lại</Button>}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      <Panel title="Đăng ký nguồn trực tuyến">
        <form onSubmit={add} className="grid gap-2 md:grid-cols-[2fr_1.5fr_1fr_1fr_auto]">
          <input name="url" type="url" required placeholder="https://…" aria-label="URL" className={input} />
          <input name="name" required placeholder="Tên nguồn" aria-label="Tên nguồn" className={input} />
          <select name="source_type" aria-label="Loại" className={input}>
            {['website', 'google_drive', 'google_doc', 'notebooklm', 'youtube', 'other'].map(t => <option key={t}>{t}</option>)}
          </select>
          <select name="reliability" aria-label="Độ tin cậy" className={input} defaultValue="EDUCATIONAL">
            {['OFFICIAL', 'PRIMARY', 'EDUCATIONAL', 'SUPPLEMENTARY', 'AI_GENERATED', 'USER_CREATED'].map(t => <option key={t}>{t}</option>)}
          </select>
          <Button type="submit" kind="primary" disabled={!!busy}>Đăng ký</Button>
        </form>
        <p className="mt-2 text-xs text-slate-500">Đăng ký chỉ lưu URL; không tự động trích xuất nội dung từ website bên thứ ba.</p>
      </Panel>
    </div>
  )
}
