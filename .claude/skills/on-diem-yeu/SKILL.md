---
name: on-diem-yeu
description: Tổng hợp điểm yếu ngữ pháp JLPT N5 của người học theo kết quả gần nhất (điểm đã làm đúng lại thì giảm/bỏ), báo cáo bài nên học lại, và soạn thêm câu ôn khi một điểm yếu đã hết câu mới. Dùng khi người dùng nói "ôn điểm yếu", "tổng hợp điểm yếu", "tôi yếu chỗ nào", "tạo bộ đề điểm yếu", hoặc gõ /on-diem-yeu.
---

# Ôn điểm yếu ngữ pháp (ADR-033)

Bài ôn điểm yếu do app tự tính lại mỗi lần mở trang: trang Thi thử, khung **"Ôn điểm yếu ngữ pháp (tự cập nhật)"**, endpoint `POST /api/attempts {"mode":"practice","weak_points":true}`. Skill này làm những việc app không tự làm được: phân tích và giải thích cho người học, rồi **soạn thêm câu** khi kho câu của một điểm yếu đã cạn.

## Luật tính (code: `backend/hub/learning/analytics.py` `weak_points`; chọn câu: `backend/hub/api.py` `_weak_drill`)
- **Nguồn dữ liệu:** câu trả lời cuối cùng của các câu có `grammar_id`, lấy từ lượt đã nộp và câu trả lời ở chế độ luyện tập (được chấm và khoá ngay khi trả lời).
- **Số câu ôn của một điểm:** `2 + số lần sai có trọng số`, tối đa 5. Trọng số của một lần sai giảm một nửa sau mỗi 7 ngày.
- **Sau lần sai cuối cùng:** đúng 1 câu thì số câu ôn giảm một nửa ("Đang tiến bộ"); đúng 2 câu liền thì bỏ điểm đó khỏi bài ôn ("Đã ổn").
- **Thứ tự chọn câu trong một điểm:** câu lần gần nhất làm sai trước, rồi câu chưa làm, rồi câu làm đã lâu nhất. Không lấy câu thuộc bài đọc.
- **Câu đề thật:** kèm tối đa 10 câu ngữ pháp đề thật (文法1/2) mà lần trả lời gần nhất còn sai.
- Đổi hằng số (`WEAK_*` trong `analytics.py`) thì phải sửa test `test_weak_points_recency_and_recovery` và `test_weak_point_drill_follows_recent_answers`.

## Các bước
1. **Lấy số liệu.** Server phải đang chạy (`http://127.0.0.1:8000`; nếu không chạy thì dùng `backend/.venv/Scripts/pythonw.exe backend/scripts/launch.py`).
   ```bash
   curl -s http://127.0.0.1:8000/api/stats/weak-points
   ```
   Kết quả là `points[]` gồm `grammar_id, pattern, lesson_number, wrong, total, streak, need, status, fresh, available`, cùng `past_mistakes` và `total`.
   Muốn xem kết quả đề gần nhất (theo phần và theo mondai) thì đọc `GET /api/attempts` và `GET /api/stats/analytics`. Chỉ đọc. Không tạo lượt làm bài trong DB thật; nếu lỡ tạo thì xoá lượt chưa nộp và chưa có câu trả lời.

2. **Báo cáo cho người học** (tiếng Việt, ngắn):
   - Bảng các điểm "Đang yếu" và "Đang tiến bộ": mẫu ngữ pháp, bài, số lần sai/tổng, số câu sẽ ôn.
   - Danh sách các điểm vừa chuyển sang "Đã ổn", để người học thấy mình đã tiến bộ.
   - **Bài nên học lại:** gom các điểm `weak` theo `lesson_number`. Bài nào có ≥ 2 điểm yếu, hoặc có điểm có `need` ≥ 4, thì ghi trước.
   - Hướng dẫn: vào **Thi thử**, khung **Ôn điểm yếu ngữ pháp**, bấm **Làm bài ôn điểm yếu**.

3. **Soạn thêm câu khi kho cạn.** Điều kiện: một điểm có `need > fresh`, tức số câu chưa làm hoặc đang sai ít hơn số câu cần ôn. Nếu không có điểm nào như vậy thì dừng ở bước 2.
   - **Soạn:** chạy 1–2 agent, mỗi agent nhận một nhóm điểm, số câu mỗi điểm khoảng `need - fresh + 1`. Định dạng giống `data/normalized/grammar_questions/grammar_questions.json` (`entries[]`): `question_id` dạng `Q_GQW_<YYYYMMDD>_<NN>`, `grammar_id`, `mondai_type` (`grammar_form` | `sentence_composition`), `question_text`, `options` (4), `answer` (1–4), `star_position`, `expected_sequence`, `explanation_vi`, `option_explanations` (đủ "1"–"4"), `audited: true`, `excluded: false`, `review_log`.
     - Câu 文法1 có đúng 1 chỗ `（　　）`.
     - Câu ★ có đúng 3 ô `＿＿` và 1 ô `★`, và `answer = expected_sequence[star_position-1]`.
     - Chỉ dùng kanji N5 (lấy bằng `SELECT kanji FROM kanji WHERE verification_status='verified'`). Mỗi câu chỉ có 1 đáp án đúng. Không chép câu người học đã làm.
     - Đưa cho agent các câu người học đã sai của điểm đó (`question_text`, đáp án đã chọn) để biết họ nhầm ở đâu.
   - **Kiểm luật:** `backend/.venv/Scripts/python -X utf8 .claude/skills/on-diem-yeu/scripts/check_questions.py <file>` phải in `questions with issues: 0`.
   - **Giải mù:** 2 agent độc lập, mỗi agent nhận bản đề không có đáp án (một bản xáo thứ tự), trả về `{qid: {answer, seq, alt, issue}}`. Chỉ nhận câu khi đáp án gốc = A = B, và với câu ★ thì `seq` của cả hai phải trùng `expected_sequence`. Câu không khớp: nếu do solver chọn nhầm ô ★ thì giải mù lại bằng solver mới và ghi `note`; nếu câu thật sự có hơn một đáp án thì sửa câu rồi giải mù lại, hoặc đặt `excluded: true`.
   - **Ghi bằng chứng:** thêm vào `data/normalized/ai_review/grammar_questions_review.json` các khoá `solver_a, solver_b, seq_a, seq_b, alt_a, alt_b, issue_a, issue_b` (thêm `note` nếu có).
   - **Ghi bộ đề:** file mới `data/normalized/grammar_questions/sets/weak_<YYYYMMDD>.json`, nội dung `{exam_id: "SET_N5_GRAMMAR_WEAK_<YYYYMMDD>", title, note, entries}`. Không sửa bộ cũ, vì lịch sử làm bài tham chiếu tới chúng.
   - **Nhập và kiểm tra:** `cd backend && .venv/Scripts/python -X utf8 -m hub import`, sau đó `.venv/Scripts/python -m pytest tests -q`.
   - **Khởi động lại server:** tắt các tiến trình `hub serve`, chạy lại `launch.py`, gọi lại `/api/stats/weak-points` và kiểm tra `fresh` đã tăng.
   - Cập nhật `docs/PROGRESS.md`, rồi commit (tiếng Việt, theo CLAUDE.md §7).

## Đừng
- Đừng đánh dấu `verified` khi chưa có đủ 2 lời giải mù khớp đáp án.
- Đừng sửa tay `attempt_answers` hay `review_log` để "làm sạch" điểm yếu. Điểm yếu chỉ biến mất khi người học làm đúng.
- Đừng đưa vào bài ôn những câu chép từ đề JLPT thật (`copied_from_past_exam`).
