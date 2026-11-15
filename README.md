# Japanese N5 Learning Hub

Ứng dụng ôn tập JLPT N5 local-first, chạy offline. Mọi dữ liệu đều truy được nguồn gốc; chỉ người dùng mới xác minh được dữ liệu.

## Cài đặt (Windows)
```powershell
cd D:\Japanese
python -m venv backend\.venv
backend\.venv\Scripts\python -m pip install fastapi uvicorn pymupdf jsonschema pytest httpx
cd frontend; npm install; npm run build; cd ..
```
Tuỳ chọn:
- Cài `ffprobe` (FFmpeg) để đo thời lượng audio.
- OCR cho PDF scan:
  1. Chạy `winget install UB-Mannheim.TesseractOCR`.
  2. Tải `jpn`, `jpn_vert`, `vie`, `eng` `.traineddata` từ https://github.com/tesseract-ocr/tessdata_best vào `data/reference/tessdata/`.
  3. Chạy `backend\.venv\Scripts\python -m pip install numpy pillow`.

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

## Hướng dẫn sử dụng
Mở http://127.0.0.1:8000 sau khi chạy `hub serve`. Thanh menu trên cùng có các trang dưới đây.

**1. Bắt đầu mỗi ngày ở Tổng quan**
- Khung **"Học gì tiếp"** gợi ý việc nên làm dựa trên dữ liệu học thật của bạn, theo thứ tự ưu tiên: thẻ đến hạn → câu từng làm sai → điểm ngữ pháp yếu → thi thử → thẻ mới.
- Đặt **mục tiêu ngày** (số lượt ôn thẻ + câu trả lời) ngay tại khung mục tiêu. Streak được tính cả những ngày chỉ làm bài.

**2. Học kiến thức**

| Trang | Dùng để |
|---|---|
| Từ vựng | Tra 1.253 từ: lọc theo bài Minna 1–25, xem ví dụ, Hán-Việt, nhóm động từ |
| Ngữ pháp | Xem 135 mẫu: cách dùng, ví dụ, lỗi thường gặp. Nút **Luyện** mở bài tập riêng cho mẫu đó |
| Kanji | Xem 103 chữ: âm On/Kun, Hán-Việt, từ ví dụ |
| Hội thoại | Đọc 27 bài theo 9 chủ đề. Bật/tắt hiragana và bản dịch; ▶ đọc từng câu bằng giọng máy |

**3. Ôn bằng thẻ (Ôn tập SRS)**
- Chọn loại thẻ: từ vựng (2 chiều), ngữ pháp, kanji.
- Lật thẻ rồi tự chấm Quên / Khó / Được / Dễ. Lịch ôn (SM-2) tự giãn cách.
- Mỗi ngày làm hết thẻ đến hạn trước, sau đó mới học thẻ mới.

**4. Luyện và kiểm tra (Thi thử)**

*Luyện theo phần / dạng câu:*
1. Chọn **Phần** (Từ vựng / Ngữ pháp–Đọc hiểu / Nghe) và **Dạng câu** (もんだい).
2. Chọn **Nguồn**:
   - đề mẫu chính thức;
   - đề thật các năm;
   - câu sinh tự động (từ vựng, ngữ pháp 文の文法, bài đọc 文章の文法/読解 do AI soạn).
3. Chọn số câu và chế độ:
   - **Luyện tập**: chấm và giải thích ngay sau mỗi câu, có bản dịch bài đọc và script nghe;
   - **Thi**: chỉ chấm khi nộp.
- Bài đọc có nhiều câu thì luôn được lấy đủ cả bài.
- **Ôn câu sai**: chỉ lấy những câu bạn từng làm sai.

*Làm đề hoàn chỉnh (khung "Đề thi"):*
- Có 1 đề mẫu chính thức và 6 đề thật các năm (2012–2024).
- Hai cách làm:
  - **Thi (giữ nguyên đề gốc)**: theo cấu trúc và thời gian gốc;
  - **Thi tính giờ 20/40/30 phút**: theo giờ JLPT hiện hành.
- Phần nghe: bấm **▶ Nghe câu này** để phát đúng đoạn audio của câu đó (tự dừng cuối câu). Thanh audio đầy đủ vẫn dùng được.
- Khi làm bài: gắn cờ câu cần xem lại, điều hướng bằng lưới số câu bên phải. Hết giờ một phần thì tự chuyển sang phần sau.

*Kết quả:*
- Xem điểm theo phần và theo dạng câu, điểm ngữ pháp yếu (có nút Luyện), và **ước lượng mức sẵn sàng**.
- Ước lượng này không phải điểm JLPT chính thức (thang 120/60, ngưỡng đỗ 80 và 38/19).

**5. Theo dõi (Thống kê)**
- Hoạt động 30 ngày, tổng thời gian học (ước tính).
- Tỉ lệ nhớ SRS theo loại thẻ.
- Lịch sử thi theo phần, dạng câu yếu, điểm ngữ pháp yếu, câu sai từ 2 lần trở lên.

**Lộ trình gợi ý:**
- Mỗi ngày: SRS khoảng 20 phút → luyện 10–20 câu theo dạng câu yếu → đọc 1 bài hội thoại.
- Mỗi tuần: 1 đề thật ở chế độ **Thi tính giờ**, rồi luyện lại các câu sai.

**Nhãn dữ liệu:**
- `AI_GENERATED`: câu do AI soạn hoặc sinh bằng luật, không phải đề JLPT chính thức. Đã kiểm bằng luật + 2 AI giải độc lập.
- Đề thật các năm: bản cộng đồng, đáp án cộng đồng được đối chiếu với 2 AI.
- Màn **Duyệt dữ liệu**: bạn tự sửa/duyệt một mục. Mục đã duyệt thì lần nhập sau không ghi đè.

## Sao lưu và khôi phục
- **Toàn bộ tiến độ học và quyết định duyệt** nằm trong `data/database/hub.sqlite`.
- Ở Tổng quan, khung **"Sao lưu dữ liệu"**:
  - **Tải bản sao lưu**: tải về tệp `.sqlite`.
  - **Khôi phục**: chọn tệp đã tải. Bản hiện tại được tự lưu vào `data/database/backups/` trước khi bị ghi đè.
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
