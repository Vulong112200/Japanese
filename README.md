# Japanese N5 Learning Hub

Ứng dụng ôn tập JLPT N5 local-first, chạy offline. Mọi dữ liệu đều truy được nguồn gốc; chỉ người dùng mới xác minh được dữ liệu.

## Cài đặt (Windows)
```powershell
cd D:\Japanese
python -m venv backend\.venv
backend\.venv\Scripts\python -m pip install fastapi uvicorn pymupdf jsonschema pytest httpx
cd frontend; npm install; npm run build; cd ..
```
Tuỳ chọn: cài `ffprobe` (FFmpeg) để đo thời lượng audio.

## Chạy
```powershell
cd D:\Japanese\backend
.venv\Scripts\python -m hub build-reference   # lần đầu: tải + dựng từ điển JMdict/KANJIDIC2 (~60 MB)
.venv\Scripts\python -m hub import        # nhập/cập nhật dữ liệu từ docs/N5 + áp bản sửa đã duyệt (an toàn khi chạy lại)
.venv\Scripts\python -m hub serve         # mở http://127.0.0.1:8000
```
Các lệnh khác:
- `python -m hub check-online`: kiểm tra truy cập các nguồn trực tuyến (chỉ HTTP).
- `python -m hub report`: tạo lại `docs/IMPORT_REPORT.md`, `SOURCE_CATALOG.md` và `DATA_QUALITY_REPORT.md`.

Phát triển giao diện: chạy `npm run dev` trong `frontend/`. Lệnh này proxy `/api` sang cổng 8000.

## Kiểm thử
```powershell
cd D:\Japanese\backend; .venv\Scripts\python -m pytest tests -q
cd D:\Japanese\frontend; npm run build    # gồm kiểm tra kiểu TypeScript
```

## Sao lưu và khôi phục
- **Toàn bộ tiến độ học và quyết định duyệt** nằm trong `data/database/hub.sqlite`.
  - Sao lưu: tắt server, rồi copy tệp này đi nơi khác.
  - Khôi phục: chép tệp đó trở lại.
- `python -m hub import` không xoá tiến độ và không mở lại các mục đã duyệt. Có kiểm thử cho điều này: `test_reimport_keeps_user_decisions`.

## Thêm dữ liệu
- **Flashcard CSV**: đặt vào `docs/N5/flashcards/`, mỗi dòng có 2 cột (mặt trước, mặt sau theo định dạng `Đọc: … / Rōmaji: … / Nghĩa: …`). Sau đó chạy `import`.
- **Tài liệu Google/NotebookLM**: tải hoặc export về `docs/N5/…`. Ứng dụng không tự đăng nhập Google.

## Dữ liệu không có trong repo
- Đề mẫu JLPT (PDF/MP3) và bản chép đề: đặt bộ đề vào `docs/N5/Exam/<thư mục>/` (N5-mondai/seikai/script/kaitou.pdf, N5Sample.mp3).
- Từ điển: tự tải bằng `build-reference`.
- `data/database/hub.sqlite`: tạo bằng `import`.

## Nguồn dữ liệu tham chiếu
JMdict và KANJIDIC2 thuộc © Electronic Dictionary Research and Development Group, giấy phép CC BY-SA 4.0 (https://www.edrdg.org/).

## Tài liệu
- `CLAUDE.md`: hướng dẫn cho các session Claude Code (cấu trúc, lệnh, quy tắc dữ liệu, quy trình rà soát).
- `docs/PROGRESS.md`: tiến độ và trạng thái module.
- `docs/ARCHITECTURE.md`: sơ đồ và các ADR.
- `docs/DATA_DICTIONARY.md`: định nghĩa dữ liệu.
- `docs/IMPORT_REPORT.md`, `docs/SOURCE_CATALOG.md`, `docs/DATA_QUALITY_REPORT.md`: báo cáo được sinh từ DB.
