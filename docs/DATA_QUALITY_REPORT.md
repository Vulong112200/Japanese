# DATA QUALITY REPORT

Tạo tự động lúc 2026-11-14T11:55:32+07:00.

Hai lớp kiểm tra, **không lớp nào tự sửa dữ liệu**:
1. **Luật tự động** (`origin=rule`): kana hợp lệ, romaji ↔ kana, số âm Hán-Việt ↔ số kanji, mã hoá, trùng lặp, động từ thiếu thể từ điển.
2. **AI rà soát** (`origin=ai_review`, nhãn AI_GENERATED): đọc toàn bộ 963 mục, chỉ báo lỗi rõ ràng (độ tin cậy high/medium) kèm đề xuất. Lưu ở `data/normalized/ai_review/vocabulary_ai_review.json`.

Đề mẫu: AI đối chiếu 29/29 đáp án 正解 với nội dung câu hỏi — **29/29 nhất quán** (`EXAM_N5_OFFICIAL_SAMPLE.ai_review.json`). Giải thích tiếng Việt được gắn nhãn AI_GENERATED.

## Thống kê vấn đề mở
| Thực thể | Nguồn kiểm tra | Mã | Mức | Số lượng |
|---|---|---|---|---|
| vocabulary | rule | reading_not_kana | error | 5 |
| vocabulary | ai_review | ai_han_viet | warning | 35 |
| question | rule | transcription_unverified | warning | 29 |
| vocabulary | ai_review | ai_reading | warning | 22 |
| vocabulary | rule | duplicate_reading_conflict | warning | 10 |
| vocabulary | rule | han_viet_count | warning | 10 |
| vocabulary | rule | romaji_mismatch | warning | 10 |
| vocabulary | ai_review | ai_example_jp | warning | 6 |
| vocabulary | ai_review | ai_meaning_vi | warning | 3 |
| vocabulary | rule | kana_word_reading_differs | warning | 3 |
| vocabulary | ai_review | ai_example_vi | warning | 2 |
| question | rule | options_image_only | warning | 1 |
| vocabulary | rule | needs_dictionary_form | info | 153 |
| vocabulary | rule | duplicate_same_word | info | 101 |
| vocabulary | rule | han_viet_without_kanji | info | 21 |
| raw | rule | unstructured_format | info | 16 |
| question | rule | audio_timestamp_missing | info | 8 |
| vocabulary | rule | han_viet_missing | info | 1 |
| vocabulary | rule | latin_word | info | 1 |

## Danh sách mục từ vựng cần duyệt (error/warning)
| ID | Từ | Đọc | Hán-Việt | Nguồn | Mã | Vấn đề | Đề xuất |
|---|---|---|---|---|---|---|---|
| VOC_000013 | ～人 | ～じん | NHÂN | rule | duplicate_reading_conflict | Cùng từ '～人' nhưng cách đọc khác ở: VOC_000113 |  |
| VOC_000050 | 男の人 | おとこのひと | NAM NHÂN NHÂN | ai_review | ai_han_viet | [AI rà soát, độ tin cậy high] Thừa một chữ NHÂN; 男の人 chỉ có 2 kanji 男, 人. | NAM NHÂN |
| VOC_000050 | 男の人 | おとこのひと | NAM NHÂN NHÂN | rule | han_viet_count | Hán-Việt 'NAM NHÂN NHÂN' có 3 âm tiết nhưng từ có 2 chữ kanji |  |
| VOC_000051 | 女の人 | おんなのひと | NỮ NHÂN NHÂN | ai_review | ai_han_viet | [AI rà soát, độ tin cậy high] Thừa một chữ NHÂN; 女の人 chỉ có 2 kanji 女, 人. | NỮ NHÂN |
| VOC_000051 | 女の人 | おんなのひと | NỮ NHÂN NHÂN | rule | han_viet_count | Hán-Việt 'NỮ NHÂN NHÂN' có 3 âm tiết nhưng từ có 2 chữ kanji |  |
| VOC_000052 | 男の子 | おとこのこ | NAM NHÂN TỬ | ai_review | ai_han_viet | [AI rà soát, độ tin cậy high] Thừa chữ NHÂN; 男の子 gồm 男, 子. | NAM TỬ |
| VOC_000052 | 男の子 | おとこのこ | NAM NHÂN TỬ | rule | han_viet_count | Hán-Việt 'NAM NHÂN TỬ' có 3 âm tiết nhưng từ có 2 chữ kanji |  |
| VOC_000053 | 女の子 | おんなのこ | NỮ NHÂN TỬ | ai_review | ai_han_viet | [AI rà soát, độ tin cậy high] Thừa chữ NHÂN; 女の子 gồm 女, 子. | NỮ TỬ |
| VOC_000053 | 女の子 | おんなのこ | NỮ NHÂN TỬ | rule | han_viet_count | Hán-Việt 'NỮ NHÂN TỬ' có 3 âm tiết nhưng từ có 2 chữ kanji |  |
| VOC_000072 | 喫茶店 | きっさてん | NGẠT TRÀ ĐIẾM | ai_review | ai_han_viet | [AI rà soát, độ tin cậy high] Âm Hán-Việt của 喫 là KHIẾT, không phải NGẠT. | KHIẾT TRÀ ĐIẾM |
| VOC_000075 | 県 | けん | HUYỆN / TỈNH | ai_review | ai_han_viet | [AI rà soát, độ tin cậy medium] Âm Hán-Việt của 県 là HUYỆN; 'TỈNH' là nghĩa, không phải âm Hán-Việt, dễ gây nhầm. | HUYỆN |
| VOC_000095 | 東京ディズニーランド | とうきょうディズニーランド | ĐÔNG KINH ディズニーランド | rule | han_viet_count | Hán-Việt 'ĐÔNG KINH ディズニーランド' có 3 âm tiết nhưng từ có 2 chữ kanji |  |
| VOC_000096 | 掛かります | かかります | QUẢI | ai_review | ai_example_jp | [AI rà soát, độ tin cậy high] Câu ví dụ tiếng Nhật lẫn chữ tiếng Việt 'bưu điện'. | 駅から 郵便局まで 15分 かかります。 |
| VOC_000113 | ～人 | ～にん | NHÂN | rule | duplicate_reading_conflict | Cùng từ '～人' nhưng cách đọc khác ở: VOC_000013 |  |
| VOC_000120 | カレー | カレー |  | ai_review | ai_meaning_vi | [AI rà soát, độ tin cậy high] Viết sai chính tả: 'cà rêu' phải là 'cà ri' (cả trong example_vi). | món cà ri, cơm cà ri (カレーライス) / ví dụ: Tôi thích món cà ri cay. |
| VOC_000147 | 簡単 | かんたん | ĐƠN GIẢN | ai_review | ai_han_viet | [AI rà soát, độ tin cậy high] Đảo thứ tự: 簡 = GIẢN, 単 = ĐƠN. | GIẢN ĐƠN |
| VOC_000155 | 暖かい | あたたかい | ÔN | ai_review | ai_han_viet | [AI rà soát, độ tin cậy high] Âm Hán-Việt của 暖 là NOÃN; ÔN là của 温. | NOÃN |
| VOC_000178 | 天ぷら | てんぷら | THIÊN PHỤ LA | ai_review | ai_han_viet | [AI rà soát, độ tin cậy medium] Từ chỉ có 1 kanji 天 (ぷら là kana); 'PHỤ LA' không ứng với kanji nào trong từ. | THIÊN |
| VOC_000178 | 天ぷら | てんぷら | THIÊN PHỤ LA | rule | han_viet_count | Hán-Việt 'THIÊN PHỤ LA' có 3 âm tiết nhưng từ có 1 chữ kanji |  |
| VOC_000179 | 豚肉 | ぶたにく | ĐỐN NHỤC | ai_review | ai_han_viet | [AI rà soát, độ tin cậy high] Sai dấu: 豚 là ĐỒN, không phải ĐỐN. | ĐỒN NHỤC |
| VOC_000194 | 迎えます | むかえます | NGHÊNH | ai_review | ai_example_jp | [AI rà soát, độ tin cậy medium] '駅へ友達を迎えます' không tự nhiên và không khớp bản dịch 'đi đến nhà ga để đón bạn'; cần mẫu ～に行きます (Bài 13). | 駅へ友達を迎えに行きます。 |
| VOC_000198 | 遊びます | あそびます | GIẢI | ai_review | ai_han_viet | [AI rà soát, độ tin cậy high] Âm Hán-Việt của 遊 là DU, không phải GIẢI. | DU |
| VOC_000200 | 買い物します | かいものします | MÃI VẬT | ai_review | ai_example_jp | [AI rà soát, độ tin cậy high] Sai trợ từ: 'デパートへ買い物します' không đúng ngữ pháp; dùng で, hoặc へ…に行きます. | デパートで買い物します。 |
| VOC_000212 | お腹が空きました | おなかがあきました | PHÚC KHÔNG | ai_review | ai_reading | [AI rà soát, độ tin cậy high] 空きました trong cụm này đọc là すきました, không phải あきました. | おなかがすきました |
| VOC_000212 | お腹が空きました | おなかがあきました | PHÚC KHÔNG | rule | romaji_mismatch | Romaji 'Onaka ga sukimashita' không khớp cách đọc 'おなかがあきました' |  |
| VOC_000216 | ご注文は？ | ごちゅうもんは？ | TRÚNG CHÚ | ai_review | ai_han_viet | [AI rà soát, độ tin cậy high] 注文 đọc Hán-Việt là CHÚ VĂN; 'TRÚNG CHÚ' sai. | CHÚ VĂN |
| VOC_000217 | 牛丼 | ぎゅうどん | NGƯU ĐỔNG | ai_review | ai_han_viet | [AI rà soát, độ tin cậy medium] 丼 có âm Hán-Việt là TỈNH/ĐẢM; 'ĐỔNG' là phiên theo âm Nhật どん. | NGƯU TỈNH |
| VOC_000240 | 降ります | ふります | HÀNG | rule | duplicate_reading_conflict | Cùng từ '降ります' nhưng cách đọc khác ở: VOC_000267 |  |
| VOC_000267 | 降ります | おります | GIÁNG / HẠ | rule | duplicate_reading_conflict | Cùng từ '降ります' nhưng cách đọc khác ở: VOC_000240 |  |
| VOC_000328 | 先生 | せんせい | TIÊN SINH | ai_review | ai_meaning_vi | [AI rà soát, độ tin cậy high] Nghĩa tiếng Việt lẫn chữ Hán '呼' ('xưng呼'). | Bác sĩ (cách xưng hô với bác sĩ), Thầy/Cô giáo |
| VOC_000329 | 2、3日 | にさんにち | NHỊ TAM NHẬT | rule | han_viet_count | Hán-Việt 'NHỊ TAM NHẬT' có 3 âm tiết nhưng từ có 1 chữ kanji |  |
| VOC_000333 | のどが痛いです | のどがいたい | THỐNG | ai_review | ai_reading | [AI rà soát, độ tin cậy high] Cách đọc thiếu 'です' so với từ. | のどがいたいです |
| VOC_000333 | のどが痛いです | のどがいたい | THỐNG | rule | romaji_mismatch | Romaji 'nodo ga itai desu' không khớp cách đọc 'のどがいたい' |  |
| VOC_000388 | 机 | つくえ | TRƠN | ai_review | ai_han_viet | [AI rà soát, độ tin cậy high] 'TRƠN' không phải âm Hán-Việt của 机; âm đúng là CƠ (KỶ). | CƠ |
| VOC_000396 | 何 | なん | HÀ | rule | duplicate_reading_conflict | Cùng từ '何' nhưng cách đọc khác ở: VOC_000734 |  |
| VOC_000420 | みんなで | みんなで | CHÚNG | ai_review | ai_han_viet | [AI rà soát, độ tin cậy high] みんな viết bằng chữ 皆, âm Hán-Việt là GIAI; CHÚNG là âm của 衆. | GIAI |
| VOC_000433 | 役立つ | やくだちます | DỊCH LẬP | ai_review | ai_reading | [AI rà soát, độ tin cậy medium] Từ ghi ở thể từ điển nhưng cách đọc lại ở thể ます, không khớp với từ. Ngoài ra câu ví dụ dùng 役に立ちます chứ không dùng 役立つ. | やくだつ (hoặc đổi từ thành 役に立ちます / やくにたちます) |
| VOC_000435 | 勝つ | かちます | THẮNG | ai_review | ai_reading | [AI rà soát, độ tin cậy medium] Từ ghi ở thể từ điển nhưng cách đọc lại ở thể ます, không khớp với từ. | かつ |
| VOC_000444 | 気をつける | きをつけます | KHÍ | ai_review | ai_reading | [AI rà soát, độ tin cậy medium] Từ ghi ở thể từ điển nhưng cách đọc lại ở thể ます, không khớp với từ. | きをつける |
| VOC_000452 | 動く | うごきます | ĐỘNG | ai_review | ai_example_vi | [AI rà soát, độ tin cậy high] Câu dịch lẫn chữ Hán '時計' vào giữa tiếng Việt. | Đồng hồ đang chạy. |
| VOC_000452 | 動く | うごきます | ĐỘNG | ai_review | ai_reading | [AI rà soát, độ tin cậy medium] Từ ghi ở thể từ điển nhưng cách đọc lại ở thể ます, không khớp với từ. | うごく |
| VOC_000456 | やめる | やめます |  | ai_review | ai_reading | [AI rà soát, độ tin cậy medium] Từ ghi ở thể từ điển nhưng cách đọc lại ở thể ます, không khớp với từ. | やめる |
| VOC_000456 | やめる | やめます |  | rule | kana_word_reading_differs | Từ viết bằng kana nhưng khác cách đọc: やめる / やめます |  |
| VOC_000457 | アルバイト | アルバイト |  | rule | duplicate_reading_conflict | Cùng từ 'アルバイト' nhưng cách đọc khác ở: VOC_000883 |  |
| VOC_000458 | 留学する | りゅうがくします | LƯU HỌC | ai_review | ai_reading | [AI rà soát, độ tin cậy medium] Từ ghi ở thể từ điển nhưng cách đọc lại ở thể ます, không khớp với từ. | りゅうがくする |
| VOC_000467 | 負ける | まけます | PHỤ | ai_review | ai_reading | [AI rà soát, độ tin cậy medium] Từ ghi ở thể từ điển nhưng cách đọc lại ở thể ます, không khớp với từ. | まける |
| VOC_000473 | 放送 | ほうそう | PHÁP TỐNG | ai_review | ai_han_viet | [AI rà soát, độ tin cậy high] 放 đọc Hán-Việt là PHÓNG, không phải PHÁP. | PHÓNG TỐNG |
| VOC_000508 | ~目 | ~め | MỤC | rule | reading_not_kana | Cách đọc có ký tự không phải kana: ~め |  |
| VOC_000510 | お湯 | おゆ | THỦY | ai_review | ai_han_viet | [AI rà soát, độ tin cậy high] 湯 đọc Hán-Việt là THANG, không phải THỦY (THỦY là 水). | THANG |
| VOC_000515 | 交差点 | こうさてん | GIAO SAI ĐIỂM | ai_review | ai_example_vi | [AI rà soát, độ tin cậy high] Bản dịch còn sót chữ Hán 右 thay vì 'phải'. | Rẽ phải ở ngã tư. |
| VOC_000526 | 電気屋 | でんきや | ĐIỆN ỐC | rule | han_viet_count | Hán-Việt 'ĐIỆN ỐC' có 2 âm tiết nhưng từ có 3 chữ kanji |  |
| VOC_000528 | 法隆寺 | ほうりゅうじ | PHÁP TRUNG TỰ | ai_review | ai_han_viet | [AI rà soát, độ tin cậy high] 隆 đọc Hán-Việt là LONG, không phải TRUNG. | PHÁP LONG TỰ |
| VOC_000552 | ホームステイ | ホームステイ |  | rule | romaji_mismatch | Romaji 'hoomustei' không khớp cách đọc 'ホームステイ' |  |
| VOC_000563 | 考える | かんがえます | KHẢO | ai_review | ai_reading | [AI rà soát, độ tin cậy medium] Từ ghi dạng từ điển 考える nhưng cách đọc lại là dạng ます. | かんがえる (hoặc đổi word thành 考えます) |
| VOC_000564 | 取る | とります [としを～] | THỦ / TUẾ | ai_review | ai_reading | [AI rà soát, độ tin cậy medium] Từ ghi dạng từ điển 取る nhưng cách đọc là dạng ます とります. | とる (hoặc đổi word thành 取ります) |
| VOC_000566 | 留学する | りゅうがくします | LƯU HỌC | ai_review | ai_reading | [AI rà soát, độ tin cậy medium] Từ ghi dạng する nhưng cách đọc là dạng ます. | りゅうがくする (hoặc đổi word thành 留学します) |
| VOC_000569 | 着く | つきます | TRƯỚC | ai_review | ai_reading | [AI rà soát, độ tin cậy medium] Từ ghi dạng từ điển 着く nhưng cách đọc là dạng ます. | つく (hoặc đổi word thành 着きます) |
| VOC_000582 | エスカレーター | エスカレーター |  | rule | romaji_mismatch | Romaji 'esukarātā' không khớp cách đọc 'エスカレーター' |  |
| VOC_000592 | エレベーター | エレベーター |  | rule | romaji_mismatch | Romaji 'erebātā' không khớp cách đọc 'エレベーター' |  |
| VOC_000595 | 円 | えん | YÊN | ai_review | ai_han_viet | [AI rà soát, độ tin cậy medium] Âm Hán-Việt của 円(圓) là VIÊN; 'Yên' là tên gọi đơn vị tiền tệ trong tiếng Việt chứ không phải âm Hán-Việt. | VIÊN |
| VOC_000620 | 美術館 | びじゅつかん | MỸ THUẬT QUÁN | ai_review | ai_example_jp | [AI rà soát, độ tin cậy medium] '月曜日 休みに なります' không tự nhiên (nghĩa là 'trở thành ngày nghỉ'); câu chuẩn là 月曜日は休みです / 月曜日が休みです. | 美術館は 月曜日が 休みです。 |
| VOC_000630 | 昼 | ひる | TRƯA | ai_review | ai_han_viet | [AI rà soát, độ tin cậy high] 昼 đọc Hán-Việt là TRÚ; 'TRƯA' là từ thuần Việt. | TRÚ |
| VOC_000632 | 一昨日 | おととい | NHẤT TẠC NHẬT | rule | duplicate_reading_conflict | Cùng từ '一昨日' nhưng cách đọc khác ở: VOC_000682 |  |
| VOC_000639 | 昼休み | ひるやすみ | TRƯA HƯU | ai_review | ai_han_viet | [AI rà soát, độ tin cậy high] 昼 đọc Hán-Việt là TRÚ, không phải TRƯA. | TRÚ HƯU |
| VOC_000639 | 昼休み | ひるやすみ | TRƯA HƯU | rule | romaji_mismatch | Romaji 'hirusumi' không khớp cách đọc 'ひるやすみ' |  |
| VOC_000652 | 日曜日 | にちようび | NHẬT DIỆU NHẬT | ai_review | ai_example_jp | [AI rà soát, độ tin cậy high] Lỗi chính tả: '働きますん' không tồn tại, phải là 働きません. | 日曜日は 働きません。 |
| VOC_000673 | バス | ばす |  | ai_review | ai_reading | [AI rà soát, độ tin cậy medium] Từ katakana nhưng cách đọc ghi bằng hiragana (các từ ngoại lai khác đều ghi katakana). | バス |
| VOC_000681 | タクシー | たくしー |  | ai_review | ai_reading | [AI rà soát, độ tin cậy medium] Từ katakana nhưng cách đọc ghi bằng hiragana. | タクシー |
| VOC_000682 | 一昨日 | おとtoi | NHẤT TRÁC NHẬT | ai_review | ai_reading | [AI rà soát, độ tin cậy high] Cách đọc bị lỗi, lẫn romaji 'toi'. | おととい |
| VOC_000682 | 一昨日 | おとtoi | NHẤT TRÁC NHẬT | ai_review | ai_han_viet | [AI rà soát, độ tin cậy high] 昨 đọc Hán-Việt là TẠC, không phải TRÁC (dòng VOC_000632 ghi đúng). | NHẤT TẠC NHẬT |
| VOC_000682 | 一昨日 | おとtoi | NHẤT TRÁC NHẬT | rule | reading_not_kana | Cách đọc có ký tự không phải kana: おとtoi |  |
| VOC_000682 | 一昨日 | おとtoi | NHẤT TRÁC NHẬT | rule | duplicate_reading_conflict | Cùng từ '一昨日' nhưng cách đọc khác ở: VOC_000632 |  |
| VOC_000687 | スーパー | すーぱー |  | ai_review | ai_reading | [AI rà soát, độ tin cậy medium] Từ katakana nhưng cách đọc ghi bằng hiragana. | スーパー |
| VOC_000690 | 学校 | がっこう | HỌC GIÁO | ai_review | ai_han_viet | [AI rà soát, độ tin cậy medium] 校 trong 学校 đọc Hán-Việt là HIỆU (học hiệu); GIÁO là âm hiếm dùng với nghĩa khác. | HỌC HIỆU |
| VOC_000717 | 撮ります | とります | TÁT | ai_review | ai_han_viet | [AI rà soát, độ tin cậy high] 撮 đọc Hán-Việt là TOÁT, không phải TÁT. | TOÁT |
| VOC_000734 | 何 | なに / なん | HÀ | rule | duplicate_reading_conflict | Cùng từ '何' nhưng cách đọc khác ở: VOC_000396 |  |
| VOC_000751 | 教えます | おしえます | GIÁO | ai_review | ai_example_jp | [AI rà soát, độ tin cậy medium] 'さんとうさん' không phải tên Santos (Minna: サントスさん) trong khi bản dịch ghi 'anh Santos'. | わたしは　サントスさんに　にほんごを　教えます。 |
| VOC_000799 | ハンサム | ハンサム |  | rule | romaji_mismatch | Romaji 'Hansomu' không khớp cách đọc 'ハンサム' |  |
| VOC_000838 | お仕事 | おしごと | SỰ CÔNG | ai_review | ai_han_viet | [AI rà soát, độ tin cậy high] 仕事 đọc Hán-Việt là SĨ SỰ (仕=SĨ, 事=SỰ); 'SỰ CÔNG' sai. | SĨ SỰ |
| VOC_000861 | クラシック | くらしく |  | ai_review | ai_reading | [AI rà soát, độ tin cậy high] Thiếu っ nhỏ: クラシック = くらしっく. | くらしっく |
| VOC_000861 | クラシック | くらしく |  | rule | romaji_mismatch | Romaji 'kurashikku' không khớp cách đọc 'くらしく' |  |
| VOC_000861 | クラシック | くらしく |  | rule | kana_word_reading_differs | Từ viết bằng kana nhưng khác cách đọc: クラシック / くらしく |  |
| VOC_000870 | ローマ字 | ろーまじ | TỰ | ai_review | ai_meaning_vi | [AI rà soát, độ tin cậy high] Lỗi chính tả: 'La-tông' phải là 'La-tinh'. | Chữ Rōmaji (chữ La-tinh) |
| VOC_000873 | 分かる | わかります | PHÂN | ai_review | ai_reading | [AI rà soát, độ tin cậy high] Từ ở thể từ điển 分かる nhưng cách đọc lại ghi thể ます; không khớp. | わかる |
| VOC_000874 | ある | あります |  | ai_review | ai_reading | [AI rà soát, độ tin cậy high] Từ ở thể từ điển ある nhưng cách đọc ghi あります; không khớp. | ある |
| VOC_000874 | ある | あります |  | rule | kana_word_reading_differs | Từ viết bằng kana nhưng khác cách đọc: ある / あります |  |
| VOC_000883 | アルバイト | あるばいと |  | rule | duplicate_reading_conflict | Cùng từ 'アルバイト' nhưng cách đọc khác ở: VOC_000457 |  |
| VOC_000885 | 夫 | おっと (PHU) / しゅじん | CHỦ NHÂN | ai_review | ai_han_viet | [AI rà soát, độ tin cậy high] 夫 có Hán-Việt là PHU; 'CHỦ NHÂN' là của 主人, không phải của 夫. | PHU |
| VOC_000885 | 夫 | おっと (PHU) / しゅじん | CHỦ NHÂN | ai_review | ai_reading | [AI rà soát, độ tin cậy medium] Ô cách đọc lẫn Hán-Việt '(PHU)' và cách đọc của từ khác (しゅじん = 主人). | おっと |
| VOC_000885 | 夫 | おっと (PHU) / しゅじん | CHỦ NHÂN | rule | reading_not_kana | Cách đọc có ký tự không phải kana: おっと (PHU) / しゅじん |  |
| VOC_000885 | 夫 | おっと (PHU) / しゅじん | CHỦ NHÂN | rule | han_viet_count | Hán-Việt 'CHỦ NHÂN' có 2 âm tiết nhưng từ có 1 chữ kanji |  |
| VOC_000887 | 妻 | つま (THÊ) / かない | GIA NỘI | ai_review | ai_han_viet | [AI rà soát, độ tin cậy high] 妻 có Hán-Việt là THÊ; 'GIA NỘI' là của 家内, không phải của 妻. | THÊ |
| VOC_000887 | 妻 | つま (THÊ) / かない | GIA NỘI | ai_review | ai_reading | [AI rà soát, độ tin cậy medium] Ô cách đọc lẫn Hán-Việt '(THÊ)' và cách đọc của từ khác (かない = 家内). | つま |
| VOC_000887 | 妻 | つま (THÊ) / かない | GIA NỘI | rule | reading_not_kana | Cách đọc có ký tự không phải kana: つま (THÊ) / かない |  |
| VOC_000887 | 妻 | つま (THÊ) / かない | GIA NỘI | rule | han_viet_count | Hán-Việt 'GIA NỘI' có 2 âm tiết nhưng từ có 1 chữ kanji |  |
| VOC_000893 | 全然 | ぜんぜん | HOÀN NHIÊN | ai_review | ai_han_viet | [AI rà soát, độ tin cậy high] 全 là TOÀN, không phải HOÀN. | TOÀN NHIÊN |
| VOC_000894 | 早く | はやく | TẢO / TỐC | ai_review | ai_han_viet | [AI rà soát, độ tin cậy medium] 早 chỉ đọc là TẢO; TỐC là âm của chữ 速 (速く), không phải 早. | TẢO |
| VOC_000902 | ～はちょっと… | ～はちょっと… |  | rule | reading_not_kana | Cách đọc có ký tự không phải kana: ～はちょっと… |  |
| VOC_000920 | また今度お願いします | またこんどおねがいします | KIM ĐỘ NGUỆN | ai_review | ai_han_viet | [AI rà soát, độ tin cậy high] Lỗi chính tả: 'NGUỆN' phải là 'NGUYỆN' (願). | KIM ĐỘ NGUYỆN |
| VOC_000922 | どうぞ よろしく お願いします | どうぞ よろしく おねがいします | NGUỆN | ai_review | ai_han_viet | [AI rà soát, độ tin cậy high] Lỗi chính tả: 'NGUỆN' phải là 'NGUYỆN' (願). | NGUYỆN |
| VOC_000923 | こちらこそ よろしく お願いします | こちらこそ よろしく おねがいします | NGUỆN | ai_review | ai_han_viet | [AI rà soát, độ tin cậy high] Lỗi chính tả: 'NGUỆN' phải là 'NGUYỆN' (願). | NGUYỆN |
| VOC_000928 | お疲れ様でした | おつかれさまでした | BÃI TƯỢNG | ai_review | ai_han_viet | [AI rà soát, độ tin cậy high] 疲 = BÌ, 様 = DẠNG; 'BÃI TƯỢNG' sai cả hai âm. | BÌ DẠNG |
| VOC_000933 | もう 一度 お願いします | もう いちど おねがいします | NHẤT ĐỘ NGUỆN | ai_review | ai_han_viet | [AI rà soát, độ tin cậy high] Lỗi chính tả: 'NGUỆN' phải là 'NGUYỆN' (願). | NHẤT ĐỘ NGUYỆN |
| VOC_000945 | お願い します | おねがい します | NGUỆN | ai_review | ai_han_viet | [AI rà soát, độ tin cậy high] Lỗi chính tả: 'NGUỆN' phải là 'NGUYỆN' (願). | NGUYỆN |
| VOC_000953 | お気をつけて | おきをつけて | KHÍ | rule | romaji_mismatch | Romaji 'Okitsukete' không khớp cách đọc 'おきをつけて' |  |
| VOC_000961 | お気をつけください | おきをつけください | KHÍ | rule | romaji_mismatch | Romaji 'Oki o tsukete kudasai' không khớp cách đọc 'おきをつけください' |  |
