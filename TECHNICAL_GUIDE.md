# Hướng dẫn kỹ thuật CAISSA-JEPA

Tài liệu này đi theo luồng code của `main.py` và giải thích các cụm hàm mới quan
trọng. Tên hàm được giữ nguyên tiếng Việt để đối chiếu trực tiếp với source.

## 1. Từ nước người chơi đến nước engine

`mousePressEvent`/`mouseMoveEvent`/`mouseReleaseEvent` chuyển click hoặc drag thành
hai index. `move_piece` kiểm tra lượt, gọi bộ luật, tạo snapshot trước nước đi,
SAN, position key và trạng thái opening. Sau khi `ap_dung_nuoc_di`, hàm cập nhật
quyền nhập thành, en-passant, clock, lượt, repetition key, evaluation và
`game_records`.

Nếu ván chưa kết thúc và tới lượt engine, `bat_dau_search_engine` chạy theo thứ
tự: GM opening book → correction hợp lệ → tính ngân sách → tạo `engineworker`
trong `QThread`. `nhan_ket_qua_engine` chỉ nhận đúng `search_session_id`, kiểm tra
game/lượt lần cuối rồi gọi lại `move_piece`.

## 2. Trạng thái, sinh nước và hoàn tác

`vitriengine.__init__` sao chép board 64 ô, lượt, bốn quyền nhập thành,
en-passant, halfmove và repetition counts. `lay_tat_ca_nuoc_di_hop_le` lấy pseudo
moves theo từng quân, áp dụng từng nước bằng `thuc_hien_nuoc_di`, loại nước để vua
mình bị chiếu, rồi `hoan_tac_nuoc_di`.

Move là tuple `(from_index, to_index, promotion_piece)`. Vì promotion nằm trong
move nên bốn lựa chọn Q/R/B/N là bốn nhánh khác nhau. Undo record giữ quân bị bắt,
rook castling, pawn en-passant, quyền nhập thành, halfmove, turn và Zobrist cũ;
việc hoàn tác vì thế không suy luận ngược và trả trạng thái chính xác.

## 3. Evaluation

`tinh_evaluation` cộng vật chất, piece-square/hoạt động quân, pawn structure,
mobility, center, king safety và phase. Điểm nội bộ dùng centipawn và dương cho
Trắng. `tinh_evaluation_theo_luot` đổi dấu theo side-to-move để negamax chỉ cần
một công thức. UI chia 100 và giới hạn hình học thanh evaluation, nhưng giữ score
thật trong lịch sử.

## 4. Negamax, alpha-beta và iterative deepening

`negamax(depth, alpha, beta, ply)` dùng đối xứng
`score(position) = -score(child)`. Alpha là bảo đảm tốt nhất của bên hiện tại;
khi score đạt beta, phần còn lại không thể thay đổi quyết định của cha nên bị
cắt. `tim_nuoc_di_tot_nhat` chạy depth 1, 2, 3…; chỉ công bố kết quả của depth đã
hoàn tất. Nếu `kiem_tra_dung_search` thấy hết giờ/stop event, exception chuyên
dụng thoát nhanh qua mọi tầng và undo vẫn chạy trong `finally`.

## 5. Quiescence và horizon effect

Tại depth 0, `quiescence` không dừng ngay ở một thế đang trao đổi quân. Nó lấy
stand-pat evaluation rồi tiếp tục các nước bắt/phong cấp/chiếu quan trọng tới khi
thế chiến thuật ổn định hoặc chạm giới hạn. Điều này tránh đánh giá sai vì nhìn
dừng đúng trước khi hậu bị bắt.

## 6. Zobrist và transposition table

`khoi_tao_zobrist` tạo bảng random cố định cho quân–ô, lượt, castling và
en-passant. `tinh_zobrist_hash` dùng cho khởi tạo/test; `thuc_hien_nuoc_di` XOR
thành phần cũ/mới để cập nhật gia tăng. Undo phục hồi hash đã lưu.

TT được probe trong `negamax`; entry đủ depth có cờ `EXACT`, `LOWER`, `UPPER` để
trả score hoặc siết cửa sổ. `score_vao_tt`/`score_tu_tt` chuẩn hóa mate score theo
ply. `luu_transposition` giới hạn 150.000 entry. Vị trí đang lặp không tái sử dụng
TT để tránh trộn giá trị phụ thuộc lịch sử.

## 7. Move ordering

`diem_sap_xep_nuoc_di` và `sap_xep_nuoc_di` xếp TT/PV trước, rồi promotion,
MVV-LVA capture, check, killer và history. `cap_nhat_killer_history` chỉ học quiet
move gây beta cutoff. Ordering không đổi correctness nhưng đưa nước mạnh lên đầu
để alpha-beta cắt nhiều nhánh hơn. Kết quả trả depth, nodes, qnodes, NPS, TT hits,
TT size, cutoffs và PV.

## 8. Quản lý thời gian và thread

`tinh_do_phuc_tap_position` đo branching factor, capture, promotion, check và số
quân từ trạng thái thật. `tinh_ngan_sach_search` kết hợp độ phức tạp với thời gian
còn lại, increment và số nước dự kiến, luôn chừa biên chống rơi cờ.

`engineworker` không chạm widget. Nó nhận snapshot độc lập và phát dictionary qua
Signal. `cap_nhat_clock` chạy QTimer 50 ms trong GUI thread nên đồng hồ vẫn giảm.
`dung_search_engine`, stop event và session ID ngăn kết quả cũ áp dụng sau
Restart. `closeEvent` yêu cầu mọi worker dừng và chờ hữu hạn.

## 9. PGN/SAN và dữ liệu GM

`pgnparser.doc_headers` đọc tag; bộ làm sạch bỏ comment `{}`, NAG `$`, move number
và variation lồng `()`. `tao_san` tạo SAN từ legal move và `san_thanh_move` so SAN
đã chuẩn hóa với toàn bộ nước hợp lệ. Parser hỗ trợ disambiguation, O-O/O-O-O,
capture, en-passant, promotion, check và mate. `fen_thanh_snapshot` hỗ trợ các test
và PGN có FEN.

`importworker.doc_tung_game` stream file thay vì nạp cả 4 GiB. `la_title_gm`
tokenize title và chỉ chấp nhận token `GM`. Worker bỏ hòa, bỏ ván GM thua, parse
toàn ván thắng và chỉ lấy record có `side == winner_color`. SHA-256 của metadata
và chuỗi move chống nhập trùng.

## 10. Opening book

`contributions` là dữ liệu có nguồn gốc theo từng game. `rebuild_opening_book`
tổng hợp lại bảng materialized từ contribution còn tồn tại; GM có trọng số ưu
tiên. `chon_nuoc_opening_book` chỉ chạy khi trạng thái thật còn là opening, chỉ
lấy row có `gm_count > 0` và đúng màu engine. Nó giữ nhóm đạt ít nhất 35% trọng
số cao nhất rồi random có trọng số để opening mạnh nhưng đa dạng. Midgame/endgame
không dùng nước PGN trực tiếp.

## 11. Mô hình CAISSA-JEPA

`caissajepa.ma_hoa_snapshot` tạo vector symbolic: 12×64 quân, lượt, castling và
8 vị trí en-passant. `ma_hoa_action` mã hóa from/to/promotion. `encode` tạo latent
64 chiều; online encoder nhận gradient, target encoder chỉ cập nhật EMA.

`predict` nhận latent hiện tại + action và dự đoán latent horizon 1/2/4.
`train_batch` tính multi-horizon latent loss, value loss, counterfactual sibling
margin và variance anti-collapse. Gradient tanh/cosine được viết bằng NumPy;
`adam_update` tối ưu tham số predictor/encoder/value. `save` ghi file tạm rồi
replace nguyên tử; `load` chỉ đọc array, không pickle.

`trainworker.tao_training_sample` xác minh move mẫu vẫn hợp lệ và chọn một legal
sibling khác làm counterfactual. `chay` đọc SQLite theo batch 32, ba epoch, phát
loss/progress và lưu cuối mỗi epoch. Không có code train tự chạy ở startup; chỉ
`bat_dau_train_model` tạo worker khi bấm nút.

## 12. JEPA-MCTS và hợp nhất alpha-beta

`caissamcts.expand` sinh child từ bộ luật tượng trưng, áp predictor lên từng nước
để tạo prior. `select_child` dùng PUCT; ở node đối thủ, dấu Q đổi để mô phỏng
minimax. `run_simulation` áp move thật trên engine state, dùng terminal exact hoặc
JEPA value ở leaf, rồi backprop giá trị theo góc nhìn root.

`engineworker.chay` chỉ tải model nếu file tồn tại và `trained_steps > 0`. MCTS
nhận khoảng 52% ngân sách, alpha-beta nhận phần còn lại. `chon_hybrid_move` kết
hợp visit share 0.55, value 0.25, prior 0.20, bonus alpha/PV và correction. Nếu
alpha score tuyệt đối ít nhất 8 tốt, nước chiến thuật của alpha-beta thắng quyền
quyết định.

## 13. Học sau ván

`luu_game_hien_tai` thêm contribution trọng số nhỏ cho nước engine; chỉ ván engine
thắng mới thêm model sample cá nhân. GM samples vẫn là nguồn ưu tiên trong book.

Nếu engine thua, `learningworker.tim_sai_lam` đổi evaluation về góc nhìn engine,
tìm giảm ít nhất 1.5 tốt không hồi phục qua tối đa ba lượt engine tiếp. `chay`
chọn tối đa ba lỗi, chia trần 20 giây, search lại và chỉ lưu correction nếu nước
mới khác nước cũ và tốt hơn ít nhất 0.35. Correction được dùng làm preferred move
ở lần gặp sau, không thay thế luật hay tactical search.

## 14. SQLite và xóa lịch sử

`chessdatabase.tao_database` bật WAL, foreign keys và tạo `games`,
`contributions`, `opening_book`, `corrections`, `model_samples` cùng index.
`luu_game` INSERT OR IGNORE theo source hash. Các hàm `them_*` ghi provenance gắn
`game_id`. `lay_history` chỉ hiển thị ván PLAYED.

`xoa_game` xóa ngay row PLAYED. Foreign key `ON DELETE CASCADE` xóa contribution,
sample và correction đúng ván; sau đó `rebuild_opening_book` tính lại từ dữ liệu
còn lại. Vì vậy xóa một ván không ảnh hưởng bản ghi gốc của ván khác.

## 15. UI lịch sử, clock và điều khiển

`ve_hai_clock` luôn đặt engine trên và người chơi dưới ở cạnh phải; màu quân phụ
thuộc lựa chọn đầu ván. `doi_clock_thanh_text` dùng `ceil` theo 100 ms để hiển thị
đầy đủ phần mười giây. Nước hợp lệ cộng 3000 ms; nước sai không gọi hàm cộng.

`ve_control_panel` tạo ba nút Lịch sử/Import/Train và status worker.
`ve_history_list` hiển thị năm ván/trang; `ve_history_detail` hiển thị 24 ply/trang
với SAN, UCI, eval và dấu học. `xu_ly_history_click` xử lý XÓA trực tiếp không có
overlay xác nhận.

## 16. Công cụ dữ liệu rời

`gm_data_tool.find_latest_issue` đọc archive TWIC; `process_archive` tải đúng một
ZIP vào `TemporaryDirectory`, giải nén PGN trong RAM, lọc và ghi từng TXT. Khi
hàm kết thúc, ZIP/gói tạm bị xóa tự động. `select_winning_gm` yêu cầu kết quả quyết
định và title GM ở đúng bên thắng. `download_state.json` lưu issue/hash đã xử lý;
`current_output_size` và kiểm tra trước mỗi write bảo đảm không vượt 4 GiB.

## 17. Phạm vi kiểm chứng

`test_core.py` kiểm tra perft, hash/undo, castling, ô castling bị tấn công,
en-passant hợp lệ và en-passant làm lộ vua, bốn promotion, mate, stalemate, mate
in one, bắt hậu miễn phí, PGN variations/NAG, strict GM-winner import, SQLite
cascade, JEPA finite loss/save/load, MCTS legal move và hybrid worker.

UI responsiveness/clock được bảo vệ bằng kiến trúc thread và session, nhưng trước
khi phát hành nên chạy thêm GUI soak test thực trên máy Windows/Linux đích. Đối
với paper, cần benchmark Elo hoặc SPRT, nhiều seed, ablation từng loss/routing,
baseline có cùng node/time budget và systematic literature review cập nhật.
