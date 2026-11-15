# DATA QUALITY REPORT

Tạo tự động lúc 2026-11-15T07:27:30+07:00.

## Độ phủ N5
- **Từ vựng**: 1253 mục (bổ sung theo danh sách JLPT N5: 158; bổ sung từ Minna (PDF Drive, OCR): 132; flashcard của bạn (CSV): 963). Có đủ 25 bài Minna. So với danh sách JLPT N5 (718 từ): toàn bộ đã có. 19 từ khớp qua dạng khác (後→後で, 結婚→結婚します…); ～がる là ngữ pháp N4.
- **Kanji**: 103/103 chữ N5 (danh sách cấp 4 JLPT cũ), đối chứng với sách Basic Kanji 120.
- **Ngữ pháp**: 135 điểm (121 điểm Minna bài 1–25 + 14 điểm N5 bổ sung/đối chiếu). Nguồn: ai: 60; handbook+ai: 75. Đã ghi nhận 20 chỗ sai hoặc thiếu trong cẩm nang gốc.

## Quy trình xác minh từ vựng
1. **Luật tự động**: kana hợp lệ, romaji ↔ kana, mã hoá, trùng lặp.
2. **Đối chiếu từ điển** (EDRDG, CC BY-SA 4.0):
   - Cách đọc, từ loại và nhóm động từ lấy từ **JMdict**. Nhóm động từ suy từ thể từ điển, không suy từ đuôi ます.
   - Hán-Việt lấy từ **KANJIDIC2**, kèm bảng bổ sung `HV_OVERRIDES` cho các chữ mà KANJIDIC2 ghi sai.
3. **Rà soát AI hai vòng độc lập**, mỗi vòng có 4 lượt đọc, phủ toàn bộ 963 mục:
   - Vòng 2 có kèm bằng chứng từ điển.
   - Sau đó người duyệt cuối (Claude) xét từng đề xuất.
4. **Áp bản sửa**: chỉ sửa lớp NORMALIZED, nguồn ở `data/normalized/corrections/vocabulary_corrections.json`.
   - Lớp RAW giữ nguyên.
   - Mỗi thay đổi ghi vào `review_actions` (`ai_correction`) kèm giá trị trước/sau.
   - Có thể hoàn tác bằng "Trích xuất lại từ RAW".
5. **Điều kiện xác minh**: chỉ đặt `verified` (`verified_by=ai`) khi mục đã qua audit **và** không còn lỗi hay cảnh báo nào từ luật hoặc từ điển.
   - Mục bạn đã sửa hoặc duyệt (`verified_by=user|pending_user`) không bị tự động thay đổi.

Đề mẫu: AI đối chiếu 29/29 đáp án 正解 với nội dung câu hỏi, kết quả **29/29 nhất quán**. Câu hỏi vẫn ở trạng thái `needs_review` cho đến khi được đối chiếu với ảnh trang gốc.

## Trạng thái từ vựng
| Trạng thái | Xác minh bởi | Số mục |
|---|---|---|
| verified | ai | 1253 |

## Bản sửa đã áp (167): han_viet 59, example_romaji 40, example_jp 14, romaji 14, word 13, reading 11, example_vi 9, meaning_vi 7
| ID | Từ | Trường | Trước (CSV gốc) | Sau | Lý do |
|---|---|---|---|---|---|
| VOC_000019 | 銀行員 | example_jp | わかりさんは 銀行員ですか。 | 田中さんは 銀行員ですか。 | 'わかりさん' không phải tên người; thay bằng tên thông dụng. |
| VOC_000019 | 銀行員 | example_romaji | Wakari-san wa ginkōin desu ka. | Tanaka-san wa ginkouin desu ka. | Khớp với câu ví dụ đã sửa. |
| VOC_000019 | 銀行員 | example_vi | Anh Wakari có phải là nhân viên ngân hàng không? | Anh Tanaka có phải là nhân viên ngân hàng không? | Khớp với câu ví dụ đã sửa. |
| VOC_000022 | エンジニア | example_jp | ギプタさんは エンジニアです。 | グプタさんは エンジニアです。 | Tên Gupta viết katakana là グプタ (nhân vật trong Minna) |
| VOC_000022 | エンジニア | example_romaji | Giputa-san wa enjinia desu. | Guputa-san wa enjinia desu. | Khớp với グプタ |
| VOC_000024 | 電気 | meaning_vi | Điện, đèn điện / Công ty điện | Điện, đèn điện | 'Công ty điện' không phải nghĩa của 電気. |
| VOC_000037 | インド | example_jp | ギプタさんは インド人です。 | グプタさんは インド人です。 | Tên Gupta viết katakana là グプタ (nhân vật trong Minna) |
| VOC_000037 | インド | example_romaji | Giputa-san wa Indo-jin desu. | Guputa-san wa Indo-jin desu. | Khớp với グプタ |
| VOC_000050 | 男の人 | han_viet | NAM NHÂN NHÂN | NAM NHÂN | Thừa một âm: 男 = NAM, 人 = NHÂN |
| VOC_000051 | 女の人 | han_viet | NỮ NHÂN NHÂN | NỮ NHÂN | Thừa một âm: 女 = NỮ, 人 = NHÂN |
| VOC_000052 | 男の子 | han_viet | NAM NHÂN TỬ | NAM TỬ | Thừa âm NHÂN: 男 = NAM, 子 = TỬ |
| VOC_000053 | 女の子 | han_viet | NỮ NHÂN TỬ | NỮ TỬ | Thừa âm NHÂN: 女 = NỮ, 子 = TỬ |
| VOC_000063 | テーブル | example_romaji | Heya no chuuuou ni teeburu ga arimasu. | Heya no chuuou ni teeburu ga arimasu. | Lỗi romaji: 中央 = chuuou |
| VOC_000072 | 喫茶店 | han_viet | NGẠT TRÀ ĐIẾM | KHIẾT TRÀ ĐIẾM | 喫 = KHIẾT (không phải NGẠT) |
| VOC_000075 | 県 | han_viet | HUYỆN / TỈNH | HUYỆN | 県 = HUYỆN; TỈNH là nghĩa, không phải âm Hán-Việt của chữ này |
| VOC_000088 | いちばん～ | han_viet | NHẤT | ∅ | Từ viết bằng kana; chữ Hán 一番 = NHẤT PHIÊN nên chỉ ghi NHẤT là thiếu |
| VOC_000095 | 東京ディズニーランド | han_viet | ĐÔNG KINH ディズニーランド | ĐÔNG KINH | Katakana không có âm Hán-Việt |
| VOC_000096 | 掛かります | example_jp | 駅から bưu điện まで 15分 かかります。 | 駅から 郵便局まで 15分 かかります。 | Lẫn tiếng Việt 'bưu điện' trong câu tiếng Nhật |
| VOC_000096 | 掛かります | example_romaji | Eki kara buu dien made juu-go-fun kakarimasu. | Eki kara yuubinkyoku made juu-go-fun kakarimasu. | Khớp với câu ví dụ đã sửa (郵便局 = yuubinkyoku) |
| VOC_000101 | 二つ | example_romaji | Mikan o futatsu kayimashita. | Mikan o futatsu kaimashita. | Lỗi romaji: 買いました = kaimashita |
| VOC_000104 | 五つ | example_romaji | Sekken o itsutsu kayimashita. | Sekken o itsutsu kaimashita. | Lỗi romaji: 買いました = kaimashita |
| VOC_000106 | 七つ | example_romaji | Pan o nanatsu kayimashita. | Pan o nanatsu kaimashita. | Lỗi romaji: 買いました = kaimashita |
| VOC_000109 | 十 | example_jp | 鞄に 本が 十 あります。 | りんごが 十 あります。 | Sách đếm bằng 冊, không dùng とお; đổi sang vật đếm được bằng ～つ |
| VOC_000109 | 十 | example_romaji | Kaban ni hon ga too arimasu. | Ringo ga too arimasu. | Khớp với câu ví dụ đã sửa |
| VOC_000109 | 十 | example_vi | Trong cặp có mười cuốn sách. | Có mười quả táo. | Khớp với câu ví dụ đã sửa |
| VOC_000110 | いくつ | example_romaji | Tamago o ikutsu kayimashita ka. | Tamago o ikutsu kaimashita ka. | Lỗi romaji: 買いました = kaimashita |
| VOC_000115 | ～枚 | example_romaji | Shatsu o san-mai kayimashita. | Shatsu o san-mai kaimashita. | Lỗi romaji: 買いました = kaimashita |
| VOC_000118 | みかん | example_romaji | Amai mikan o yottsu kayimashita. | Amai mikan o yottsu kaimashita. | Lỗi romaji: 買いました = kaimashita |
| VOC_000120 | カレー | example_vi | Tôi thích món cà rêu cay. | Tôi thích món cà ri cay. | Sai chính tả: 'cà rêu' -> 'cà ri' |
| VOC_000120 | カレー | meaning_vi | món cà rêu, cơm cà rêu (カレーライス) | món cà ri, cơm cà ri (カレーライス) | Sai chính tả: 'cà rêu' -> 'cà ri' |
| VOC_000122 | 切手 | example_romaji | Hachi-juu-yon-en no kitte o ni-mai kayimashita. | Hachi-juu-yon-en no kitte o ni-mai kaimashita. | Lỗi chính tả romaji: "kayimashita" → "kaimashita" (買いました). |
| VOC_000128 | 姉 | example_romaji | Ane wa ginkou de hatarake imasu. | Ane wa ginkou de hataraite imasu. | Romaji sai: 働いています là "hataraite imasu", không phải "hatarake imasu". |
| VOC_000147 | 簡単 | han_viet | ĐƠN GIẢN | GIẢN ĐƠN | Sai thứ tự: 簡 = GIẢN, 単 = ĐƠN. |
| VOC_000155 | 暖かい | han_viet | ÔN | NOÃN | 暖 có âm Hán-Việt là NOÃN; ÔN là của chữ 温. |
| VOC_000157 | 甘い | example_vi | Cái bánh cake này ngọt. | Chiếc bánh ga-tô này ngọt. | "bánh cake" lẫn tiếng Anh; ケーキ = bánh ga-tô / bánh ngọt. |
| VOC_000175 | すき焼き | han_viet | ∅ | THIÊU | Từ có chữ Hán 焼 = THIÊU nhưng han_viet đang để trống. |
| VOC_000176 | 刺身 | han_viet | THỨ THÂN | THÍCH THÂN | 刺 trong 刺身 đọc Hán-Việt chuẩn là THÍCH (THÍCH THÂN); THỨ là âm của 刺史. |
| VOC_000178 | 天ぷら | han_viet | THIÊN PHỤ LA | THIÊN | Từ chỉ có một chữ Hán 天 = THIÊN; ぷら là kana nên không có âm Hán-Việt. |
| VOC_000179 | 豚肉 | example_romaji | Butaniku o kayimasu. | Butaniku o kaimasu. | Lỗi chính tả romaji: "kayimasu" → "kaimasu" (買います). |
| VOC_000179 | 豚肉 | han_viet | ĐỐN NHỤC | ĐỒN NHỤC | 豚 = ĐỒN, không phải ĐỐN. |
| VOC_000194 | 迎えます | example_jp | 駅へ友達を迎えます。 | 駅へ友達を迎えに行きます。 | Trợ từ へ cần động từ chuyển động; 駅へ…迎えます sai ngữ pháp. Dùng mẫu 〜に行きます (bài 13), khớp với câu dịch. |
| VOC_000194 | 迎えます | example_romaji | Eki e tomodachi o mukaemasu. | Eki e tomodachi o mukae ni ikimasu. | Sửa theo example_jp đã chỉnh. |
| VOC_000198 | 遊びます | han_viet | GIẢI | DU | 遊 = DU; GIẢI không phải âm Hán-Việt của chữ này. |
| VOC_000200 | 買い物します | example_jp | デパートへ買い物します。 | デパートで買い物します。 | Sai trợ từ: nơi diễn ra hành động 買い物します dùng で, không dùng へ. |
| VOC_000200 | 買い物します | example_romaji | Depāto e kaimono shimasu. | Depāto de kaimono shimasu. | Sửa theo example_jp đã chỉnh (へ → で). |
| VOC_000212 | お腹が空きました | reading | おなかがあきました | おなかがすきました | 空きました trong cụm này đọc là すきました (romaji đã ghi đúng "sukimashita"), không phải あきました. |
| VOC_000216 | ご注文は？ | han_viet | TRÚNG CHÚ | CHÚ VĂN | 注 = CHÚ, 文 = VĂN; "TRÚNG CHÚ" sai. |
| VOC_000217 | 牛丼 | han_viet | NGƯU ĐỔNG | NGƯU ĐẢM | 丼 = ĐẢM; ĐỔNG không phải âm Hán-Việt của chữ này. |
| VOC_000240 | 降ります | han_viet | HÀNG | GIÁNG | 降 trong 降ります (mưa rơi) là GIÁNG; HÀNG là âm trong nghĩa "đầu hàng". |
| VOC_000243 | パソコン | example_romaji | Atarashii pasokon o kayimashita. | Atarashii pasokon o kaimashita. | Lỗi chính tả romaji: "kayimashita" → "kaimashita". |
| VOC_000267 | 降ります | han_viet | GIÁNG / HẠ | GIÁNG | Mỗi chữ Hán một âm: 降 = GIÁNG; HẠ là âm của 下, không phải của 降. |
| VOC_000285 | お寺 | example_romaji | Kyoto de otera o mimasu. | Kyouto de otera o mimasu. | 京都 = きょうと, romaji phải có trường âm: Kyouto. |
| VOC_000309 | 払います | example_romaji | Okanes o haraimasu. | Okane o haraimasu. | Lỗi chính tả romaji: "Okanes" → "Okane". |
| VOC_000328 | 先生 | meaning_vi | Bác sĩ (xưng呼 với bác sĩ), Thầy/Cô giáo | Bác sĩ (cách xưng hô với bác sĩ), Thầy/Cô giáo | Lẫn chữ Hán "呼" trong nghĩa tiếng Việt ("xưng呼" → "xưng hô"). |
| VOC_000333 | のどが痛いです | reading | のどがいたい | のどがいたいです | Cách đọc thiếu です so với từ のどが痛いです (romaji đã có "desu"). |
| VOC_000360 | 相撲 | han_viet | TƯƠNG BỘC | TƯƠNG PHÁC | 撲 = PHÁC (相撲 = TƯƠNG PHÁC); BỘC không phải âm chuẩn. |
| VOC_000373 | 手帳 | han_viet | THỦ TRƯƠNG | THỦ TRƯỚNG | 帳 đọc Hán-Việt là TRƯỚNG, không phải TRƯƠNG (張). |
| VOC_000388 | 机 | han_viet | TRƠN | KỶ | TRƠN không phải âm Hán-Việt; 机 đọc là KỶ. |
| VOC_000389 | 椅子 | han_viet | Y TỬ | Ỷ TỬ | 椅 với nghĩa 'ghế' đọc là Ỷ (椅子 = Ỷ TỬ). |
| VOC_000420 | みんなで | han_viet | CHÚNG | ∅ | Từ viết bằng kana; chữ Hán của みんな là 皆 (GIAI), CHÚNG (衆) là sai. |
| VOC_000424 | 調べます | han_viet | ĐIỀU/ĐIỆU | ĐIỀU | Mỗi chữ Hán một âm; 調 trong 調べる (điều tra) đọc là ĐIỀU. |
| VOC_000433 | 役に立ちます | reading | やくだちます | やくにたちます | Cách đọc của 役に立ちます. |
| VOC_000433 | 役に立ちます | romaji | yakudachimasu | yaku ni tachimasu | Romaji theo cách đọc やくにたちます. |
| VOC_000433 | 役に立ちます | word | 役立つ | 役に立ちます | Từ vựng Minna bài 21 là 役に立ちます (thể ます), khớp với câu ví dụ. |
| VOC_000435 | 勝ちます | word | 勝つ | 勝ちます | Cách đọc ở thể ます nên từ phải ở thể ます như trong Minna. |
| VOC_000444 | 気をつけます | word | 気をつける | 気をつけます | Cách đọc ở thể ます nên từ phải ở thể ます như trong Minna. |
| VOC_000452 | 動きます | example_vi | Đồng時計 đang chạy. | Đồng hồ chạy. | Lẫn chữ Hán 時計 trong câu tiếng Việt. |
| VOC_000452 | 動きます | word | 動く | 動きます | Cách đọc ở thể ます nên từ phải ở thể ます như trong Minna. |
| VOC_000456 | やめます | word | やめる | やめます | Cách đọc ở thể ます nên từ phải ở thể ます như trong Minna. |
| VOC_000458 | 留学します | word | 留学する | 留学します | Cách đọc ở thể ます nên từ phải ở thể ます như trong Minna. |
| VOC_000462 | むだ | example_romaji | Okanemuda ni tsukawanaide kudasai. | Okane o muda ni tsukawanaide kudasai. | Thiếu trợ từ を (o) và dấu cách: お金をむだに. |
| VOC_000463 | 首相 | han_viet | THỦ TƯƠNG | THỦ TƯỚNG | 相 trong 首相 đọc là TƯỚNG (thủ tướng). |
| VOC_000467 | 負けます | word | 負ける | 負けます | Cách đọc ở thể ます nên từ phải ở thể ます như trong Minna. |
| VOC_000473 | 放送 | han_viet | PHÁP TỐNG | PHÓNG TỐNG | 放 đọc là PHÓNG; PHÁP là 法. |
| VOC_000508 | ~目 | example_romaji | Futatsume no kado o megarimasu. | Futatsume no kado o magarimasu. | 曲がります đọc là magarimasu, không phải megarimasu. |
| VOC_000510 | お湯 | han_viet | THỦY | THANG | 湯 đọc là THANG; THỦY là 水. |
| VOC_000515 | 交差点 | example_romaji | Kousaten o migi e megarimasu. | Kousaten o migi e magarimasu. | 曲がります đọc là magarimasu. |
| VOC_000515 | 交差点 | example_vi | Rẽ右 tại ngã tư. | Rẽ phải ở ngã tư. | Lẫn chữ Hán 右 trong câu tiếng Việt. |
| VOC_000518 | 角 | example_romaji | Kado o hidari e megarimasu. | Kado o hidari e magarimasu. | 曲がります đọc là magarimasu. |
| VOC_000526 | 電気屋 | han_viet | ĐIỆN ỐC | ĐIỆN KHÍ ỐC | Thiếu âm của chữ 気 (KHÍ). |
| VOC_000528 | 法隆寺 | han_viet | PHÁP TRUNG TỰ | PHÁP LONG TỰ | 隆 đọc là LONG, không phải TRUNG. |
| VOC_000531 | 出ます | example_vi | Tiền thừa chui ra. | Tiền thừa chạy ra. | 'Chui ra' không tự nhiên khi nói về tiền thừa từ máy. |
| VOC_000531 | 出ます | meaning_vi | Chui ra, xuất hiện (tiền thừa) | Ra, chạy ra (tiền thừa) | 'Chui ra' không dùng cho tiền thừa; nghĩa trong Minna bài 23 là 'ra, chạy ra [tiền thừa]'. |
| VOC_000541 | くれます | han_viet | NGÔ | ∅ | くれます luôn viết bằng kana; chữ 呉 hầu như không dùng nên âm NGÔ gây hiểu nhầm. |
| VOC_000549 | 全部 | example_romaji | Kare wa okaane o zenbu haratte kuremashita. | Kare wa okane o zenbu haratte kuremashita. | お金 đọc là okane, không phải okaane. |
| VOC_000552 | ホームステイ | example_romaji | Hoomustei no kazoku wa watashi ni shinsetsu ni shite kuremashita. | Hoomusutei no kazoku wa watashi ni shinsetsu ni shite kuremashita. | Thiếu âm ス (su) trong hoomusutei. |
| VOC_000552 | ホームステイ | romaji | hoomustei | hoomusutei | Thiếu âm ス (su): ホームステイ = hoomusutei. |
| VOC_000553 | 自分で | example_romaji | Shokudai wa jibun de yaranakereba narimasen. | Shukudai wa jibun de yaranakereba narimasen. | 宿題 đọc là shukudai, không phải shokudai. |
| VOC_000554 | 大使館 | han_viet | ĐẠI SỬ QUÁN | ĐẠI SỨ QUÁN | 使 trong 大使館 đọc là SỨ (đại sứ quán). |
| VOC_000557 | 転勤 | reading | てんきん [～します] | てんきん | Ô cách đọc lẫn ghi chú; chỉ giữ cách đọc của 転勤. |
| VOC_000557 | 転勤 | romaji | tenkin [~shimasu] | tenkin | Romaji lẫn ghi chú; chỉ giữ romaji của てんきん. |
| VOC_000560 | どうぞお元気で | example_romaji | Kuni e kaeritemo, douzo ogenki de. | Kuni e kaettemo, douzo ogenki de. | 帰っても đọc là kaettemo, không phải kaeritemo. |
| VOC_000563 | 考えます | example_romaji | Kore kara dou suru ka kangarete imasu. | Kore kara dou suru ka kangaete imasu. | 考えて đọc là kangaete, không phải kangarete. |
| VOC_000563 | 考えます | word | 考える | 考えます | Cách đọc ở thể ます nên từ phải ở thể ます như trong Minna. |
| VOC_000564 | 年を取ります | han_viet | THỦ / TUẾ | NIÊN THỦ | Mỗi chữ Hán một âm theo thứ tự: 年 = NIÊN, 取 = THỦ. |
| VOC_000564 | 年を取ります | reading | とります [としを～] | としをとります | Ô cách đọc lẫn ghi chú; cách đọc của 年を取ります. |
| VOC_000564 | 年を取ります | romaji | torimasu [toshi o~] | toshi o torimasu | Romaji lẫn ghi chú; theo cách đọc としをとります. |
| VOC_000564 | 年を取ります | word | 取る | 年を取ります | Nghĩa 'thêm tuổi, có tuổi' là của cụm 年を取ります (Minna bài 25: [年を～] 取ります), ở thể ます. |
| VOC_000566 | 留学します | word | 留学する | 留学します | Cách đọc ở thể ます nên từ phải ở thể ます như trong Minna. |
| VOC_000567 | 億 | meaning_vi | 一億 (100 triệu) | Trăm triệu (100.000.000) | Nghĩa tiếng Việt lẫn chữ Nhật 一億. |
| VOC_000569 | 着きます | word | 着く | 着きます | Cách đọc ở thể ます nên từ phải ở thể ます như trong Minna. |
| VOC_000581 | 国 | reading | くに / おくに | くに | おくに là cách đọc của お国, không phải của 国. |
| VOC_000581 | 国 | romaji | kuni / okuni | kuni | Romaji theo cách đọc くに. |
| VOC_000582 | エスカレーター | example_romaji | Esukarātā wa ikkai desu. | Esukarētā wa ikkai desu. | レー đọc là rē, không phải rā. |
| VOC_000582 | エスカレーター | romaji | esukarātā | esukarētā | レー đọc là rē, không phải rā. |
| VOC_000585 | トイレ | han_viet | THỦ TẨY | ∅ | トイレ là từ katakana, không có chữ Hán; THỦ TẨY là của お手洗い. |
| VOC_000585 | トイレ | reading | トイレ / おてあらい | トイレ | おてあらい là từ khác (お手洗い), không phải cách đọc của トイレ. |
| VOC_000585 | トイレ | romaji | toire / otearai | toire | Romaji theo cách đọc トイレ. |
| VOC_000592 | エレベーター | example_romaji | Erebātā wa soko desu. | Erebētā wa soko desu. | ベー đọc là bē, không phải bā. |
| VOC_000592 | エレベーター | romaji | erebātā | erebētā | ベー đọc là bē, không phải bā. |
| VOC_000595 | 円 | example_romaji | Kono tokei wa hachisen yonhyaku en desu. | Kono tokei wa hassen yonhyaku en desu. | 8.000 đọc là はっせん (hassen), không phải hachisen. |
| VOC_000595 | 円 | han_viet | YÊN | VIÊN | Âm Hán-Việt của 円 là VIÊN; 'Yên' chỉ là tên đơn vị tiền tệ. |
| VOC_000598 | うち | example_vi | Số điện thoại nhà bạn là số mấy? | Số điện thoại nhà mình là số mấy? | うち chỉ nhà của người nói (nhà mình), không phải nhà của người nghe. |
| VOC_000607 | 百 | example_jp | これは ５００円です。 | これは 百円です。 | Ví dụ cũ (５００円) không chứa từ 百 |
| VOC_000607 | 百 | example_romaji | Kore wa gohyaku en desu. | Kore wa hyaku en desu. | Khớp với câu ví dụ đã sửa |
| VOC_000607 | 百 | example_vi | Cái này giá 500 Yên. | Cái này giá 100 Yên. | Khớp với câu ví dụ đã sửa |
| VOC_000620 | 美術館 | example_jp | 美術館は 月曜日 休みに なります。 | 美術館は 月曜日 休みです。 | '休みに なります' không tự nhiên ở trình độ bài 4; câu chuẩn là 休みです. |
| VOC_000620 | 美術館 | example_romaji | Bijutsukan wa Getsuyoubi yasumi ni narimasu. | Bijutsukan wa getsuyoubi yasumi desu. | Khớp với câu ví dụ đã sửa. |
| VOC_000630 | 昼 | han_viet | TRƯA | TRÚ | TRƯA là từ thuần Việt; âm Hán-Việt của 昼 là TRÚ |
| VOC_000639 | 昼休み | example_romaji | Hirusumi wa juu-ni-ji kara ichi-ji made desu. | Hiruyasumi wa juu-ni-ji kara ichi-ji made desu. | Thiếu âm tiết 'ya' (ひるやすみ) |
| VOC_000639 | 昼休み | han_viet | TRƯA HƯU | TRÚ HƯU | TRƯA là từ thuần Việt; 昼 = TRÚ |
| VOC_000639 | 昼休み | romaji | hirusumi | hiruyasumi | Thiếu âm tiết 'ya' (ひるやすみ) |
| VOC_000652 | 日曜日 | example_jp | 日曜日は 働きますん。 | 日曜日は 働きません。 | Lỗi chính tả: 働きますん → 働きません |
| VOC_000682 | 一昨日 | han_viet | NHẤT TRÁC NHẬT | NHẤT TẠC NHẬT | 昨 = TẠC, không phải TRÁC |
| VOC_000682 | 一昨日 | reading | おとtoi | おととい | Cách đọc lẫn chữ Latin (おとtoi) |
| VOC_000690 | 学校 | han_viet | HỌC GIÁO | HỌC HIỆU | 校 = HIỆU, không phải GIÁO |
| VOC_000717 | 撮ります | han_viet | TÁT | TOÁT | 撮 = TOÁT, không phải TÁT |
| VOC_000719 | 庭 | example_jp | 庭で茶を飲みます。 | 庭でお茶を飲みます。 | Thiếu お (romaji là 'ocha'; お茶 tự nhiên hơn) |
| VOC_000751 | 教えます | example_jp | わたしは　さんとうさんに　にほんごを　教えます。 | わたしは　サントスさんに　にほんごを　教えます。 | Tên riêng sai: さんとうさん → サントスさん (romaji/dịch là Santos) |
| VOC_000752 | 習います | example_jp | わたしは　いーさんに　ちゅうごくごを　習います。 | わたしは　イーさんに　ちゅうごくごを　習います。 | Tên nước ngoài phải viết katakana: イーさん |
| VOC_000757 | あげます | example_jp | わたしは　きむらに　はなを　あげます。 | わたしは　きむらさんに　はなを　あげます。 | Thiếu さん sau tên người (bản dịch là 'anh Kimura') |
| VOC_000757 | あげます | example_romaji | Watashi wa Kimura ni hana o agemasu. | Watashi wa Kimura-san ni hana o agemasu. | Khớp với câu ví dụ đã sửa (thêm -san) |
| VOC_000762 | 箸 | han_viet | TRỢ | TRỨ | 箸 (đũa) có âm Hán-Việt chuẩn là TRỨ. |
| VOC_000797 | 綺麗 | han_viet | KỲ LỆ | Ỷ LỆ | 綺 = Ỷ, không phải KỲ |
| VOC_000799 | ハンサム | example_romaji | Mirā-san wa hansomu desu. | Mirā-san wa hansamu desu. | ハンサム = hansamu, không phải hansomu |
| VOC_000799 | ハンサム | romaji | Hansomu | Hansamu | ハンサム = hansamu, không phải hansomu |
| VOC_000818 | 易しい | han_viet | DỊCH | DỊ | 易 nghĩa 'dễ' (易しい) đọc là DỊ; DỊCH là nghĩa 'trao đổi' (貿易) |
| VOC_000825 | 楽しい | han_viet | LẠC / NHẠC | LẠC | Mỗi kanji một âm; 楽 trong 楽しい (vui) là LẠC, NHẠC là nghĩa 'âm nhạc' |
| VOC_000838 | お仕事 | han_viet | SỰ CÔNG | SĨ SỰ | 仕事 = SĨ SỰ; SỰ CÔNG sai chữ và sai thứ tự |
| VOC_000847 | 日本の生活に慣れましたか | han_viet | NHẬT BẢN - SINH HOẠT - QUÁN | NHẬT BẢN SINH HOẠT QUÁN | Bỏ dấu gạch ngang thừa, mỗi kanji một âm Hán-Việt |
| VOC_000848 | もう一杯いかがですか | han_viet | NHẤT BỔI | NHẤT BÔI | 杯 = BÔI (không phải BỔI) |
| VOC_000861 | クラシック | reading | くらしく | くらしっく | Thiếu âm ngắt っ: クラシック = くらしっく |
| VOC_000870 | ローマ字 | meaning_vi | Chữ Rōmaji (chữ La-tông) | Chữ Rōmaji (chữ La-tinh) | Sai chính tả: 'La-tông' -> 'La-tinh' |
| VOC_000873 | 分かります | word | 分かる | 分かります | Cách đọc ở thể ます nên từ phải ở thể ます (theo Minna) |
| VOC_000874 | あります | word | ある | あります | Cách đọc ở thể ます nên từ phải ở thể ます (theo Minna) |
| VOC_000885 | 夫 | han_viet | CHỦ NHÂN | PHU | 夫 = PHU (CHỦ NHÂN là của 主人) |
| VOC_000885 | 夫 | reading | おっと (PHU) / しゅじん | おっと | Ô cách đọc lẫn ghi chú; 夫 đọc là おっと |
| VOC_000885 | 夫 | romaji | otto / shujin | otto | Romaji phải khớp cách đọc おっと |
| VOC_000887 | 妻 | han_viet | GIA NỘI | THÊ | 妻 = THÊ (GIA NỘI là của 家内) |
| VOC_000887 | 妻 | reading | つま (THÊ) / かない | つま | Ô cách đọc lẫn ghi chú; 妻 đọc là つま |
| VOC_000887 | 妻 | romaji | tsuma / kanai | tsuma | Romaji phải khớp cách đọc つま |
| VOC_000893 | 全然 | han_viet | HOÀN NHIÊN | TOÀN NHIÊN | 全 = TOÀN (không phải HOÀN) |
| VOC_000894 | 早く | han_viet | TẢO / TỐC | TẢO | Từ chỉ có một kanji 早 = TẢO (TỐC là của 速) |
| VOC_000920 | また今度お願いします | han_viet | KIM ĐỘ NGUỆN | KIM ĐỘ NGUYỆN | Sai chính tả Hán-Việt: 願 = NGUYỆN |
| VOC_000922 | どうぞ よろしく お願いします | han_viet | NGUỆN | NGUYỆN | Sai chính tả Hán-Việt: 願 = NGUYỆN |
| VOC_000923 | こちらこそ よろしく お願いします | han_viet | NGUỆN | NGUYỆN | Sai chính tả Hán-Việt: 願 = NGUYỆN |
| VOC_000928 | お疲れ様でした | han_viet | BÃI TƯỢNG | BÌ DẠNG | 疲 = BÌ, 様 = DẠNG |
| VOC_000933 | もう 一度 お願いします | han_viet | NHẤT ĐỘ NGUỆN | NHẤT ĐỘ NGUYỆN | Sai chính tả Hán-Việt: 願 = NGUYỆN |
| VOC_000945 | お願い します | han_viet | NGUỆN | NGUYỆN | Sai chính tả Hán-Việt: 願 = NGUYỆN |
| VOC_000950 | こんばんは | han_viet | VÃN | ∅ | Từ viết bằng kana; chữ Hán thường dùng 今晩は = KIM VÃN nên chỉ ghi VÃN là thiếu |
| VOC_000951 | こんにちは | han_viet | KIM | ∅ | Từ viết bằng kana; chữ Hán thường dùng 今日は = KIM NHẬT nên chỉ ghi KIM là thiếu |
| VOC_000953 | お気をつけて | example_romaji | Ame ga futte imasu kara, okitsukete. | Ame ga futte imasu kara, oki o tsukete. | Thiếu trợ từ を (o): お気をつけて = oki o tsukete |
| VOC_000953 | お気をつけて | romaji | Okitsukete | Oki o tsukete | Thiếu trợ từ を (o): おきをつけて |
| VOC_000961 | お気をつけください | example_romaji | Dansa ga arimasu node, oki o tsukete kudasai. | Dansa ga arimasu node, oki o tsuke kudasai. | Romaji không khớp câu ví dụ: お気をつけください |
| VOC_000961 | お気をつけください | romaji | Oki o tsukete kudasai | Oki o tsuke kudasai | Romaji không khớp: おきをつけください (không có て) |
| VOC_000962 | お世話に なります | example_romaji | Itsumo osewa ni nattorimasu. | Itsumo osewa ni natte orimasu. | Lỗi romaji: なっております = natte orimasu |
| VOC_000962 | お世話に なります | meaning_vi | Cảm ơn anh/chị luôn giúp đỡ tôi (câu chào giao tiếp công việc) | Mong được anh/chị giúp đỡ; cảm ơn anh/chị đã giúp đỡ (câu chào trong giao tiếp công việc) | お世話になります là lời chào/nhờ vả; nghĩa 'luôn giúp đỡ' là của お世話になっております. |

## Thống kê vấn đề mở
| Thực thể | Nguồn kiểm tra | Mã | Mức | Số lượng |
|---|---|---|---|---|
| question | rule | transcription_unverified | warning | 31 |
| question | ai_review | answer_key_disputed | warning | 2 |
| question | rule | options_image_only | warning | 1 |
| vocabulary | rule | duplicate_same_word | info | 110 |
| raw | rule | unstructured_format | info | 16 |
| vocabulary | rule | han_viet_without_kanji | info | 15 |
| vocabulary | rule | homograph | info | 10 |
| question | rule | audio_timestamp_missing | info | 8 |
| vocabulary | rule | latin_word | info | 1 |

## Danh sách mục từ vựng cần duyệt (error/warning)
| ID | Từ | Đọc | Hán-Việt | Nguồn | Mã | Vấn đề | Đề xuất |
|---|---|---|---|---|---|---|---|
