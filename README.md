## Desktop application packaging

The desktop app keeps source-mode data in the repository and uses a writable
per-user data directory when installed. Build a Windows desktop bundle with:

    .\build_installer.ps1

The script builds a PyInstaller folder bundle and, when Inno Setup 6 is
installed, creates installer-output\CAISSA-JEPA-Setup.exe. Install the build
dependencies first when needed:

    & D:\chess_robot_app\.venv\Scripts\python.exe -m pip install -r requirements-build.txt

The app now has an IMPORT ZIP button. It accepts one or more ZIP archives,
extracts supported raster images safely into fen_dataset\images, prevents
path traversal and symlink extraction, avoids duplicate files by SHA-256, and
writes an import manifest at
fen_dataset\images\image_import_manifest.json. The current chess JEPA
trainer remains FEN/PGN-based; imported images are stored as a managed dataset
for the image pipeline and are not silently mixed into chess-position samples.
# CAISSA-JEPA Chess v7

**CAISSA-JEPA: Counterfactual Adversarial Imagination with Symbolic State
Anchoring for Resource-Bounded Chess Search** là ứng dụng cờ vua desktop viết
bằng Python/PySide6, có engine tự viết, dữ liệu GM, mô hình JEPA gọn nhẹ và tìm
kiếm lai JEPA-MCTS/alpha-beta. Dự án không dùng Stockfish, `python-chess`, API,
mô hình pretrained hay framework deep-learning.

## Chạy ứng dụng

```bash
python -m pip install -r requirements.txt
python main.py
```

On Windows, the repository launcher resolves the configured virtual
environment and starts the GUI from the correct project directory:

```powershell
.\run_caissa_app.ps1
```

Dữ liệu được tạo tự động trong `chess_data/chess_engine.db`. Model chỉ được tạo
và cập nhật khi người dùng bấm **TRAIN MODEL**. Nút này có thể bấm lần nữa để
dừng an toàn sau batch hiện tại.

## Quy trình dữ liệu GM hiệu quả

Nguồn mặc định là kho PGN tuần của The Week in Chess (TWIC). Công cụ tải tuần
tự từng ZIP, đọc xong một gói thì thư mục tạm và ZIP tự bị xóa. Vì vậy máy không
cần giữ đồng thời toàn bộ archive; chỉ các ván đã lọc mới tồn tại lâu dài.

```bash
python gm_data_tool.py --output gm_games --max-gb 4
```

Mặc định công cụ bắt đầu từ issue mới nhất và đi lùi tới issue 1200. Có thể giới
hạn phạm vi để thử nhanh:

```bash
python gm_data_tool.py --latest 1656 --oldest 1650 --output gm_games
```

Mỗi file TXT có tên gồm Trắng, Đen và người thắng; nội dung chứa ba dòng tóm tắt
và PGN nguyên gốc. Chỉ ván quyết định `1-0`/`0-1` mà bên thắng có title chính xác
`GM` được giữ. `download_state.json` cho phép chạy tiếp mà không nhân đôi. Tổng
TXT không vượt 4 GiB. Sau đó chọn các TXT bằng nút **IMPORT PGN**.

TWIC ghi rõ kho tuần miễn phí cho mục đích cá nhân và giữ mọi quyền. Nếu công bố
dataset/paper, cần kiểm tra và xin quyền phân phối dữ liệu; nên công bố pipeline,
hash và split thay vì phát hành lại PGN khi chưa có phép.

## Luồng engine

1. Nước người chơi được kiểm tra bằng bộ sinh nước hợp lệ có kiểm tra tự chiếu.
2. App cập nhật bàn cờ, clock 5+3, SAN, evaluation và log SQLite.
3. Nếu đang ở opening và có đúng thế cờ trong book GM cùng màu engine, app chọn
   ngẫu nhiên có trọng số trong nhóm nước mạnh (ít nhất 35% trọng số tốt nhất).
4. Nếu không có book, ngân sách thời gian được tính từ clock thật, số nước hợp
   lệ, nước bắt, chiếu, phong cấp và số quân.
5. Chưa có model đã train: iterative-deepening negamax alpha-beta chạy trong
   worker thread.
6. Có model: khoảng 52% thời gian dùng JEPA-MCTS, phần còn lại dùng alpha-beta.
   Kết quả hợp nhất theo visits, value, prior và principal move; alpha-beta phủ
   quyết khi thấy lợi thế chiến thuật rất lớn.
7. Worker trả `session_id`; kết quả cũ, kết quả sau Restart hoặc sau game-over bị
   bỏ qua. Clock UI vẫn chạy trong lúc search.

## Các thành phần tìm kiếm cổ điển

- Make/unmake lưu đầy đủ board, lượt, nhập thành, en-passant, halfmove và hash.
- Zobrist hash cập nhật gia tăng, phục vụ transposition table.
- TT lưu EXACT/LOWER/UPPER, depth, best move và chuẩn hóa mate score.
- Move ordering ưu tiên TT/PV, bắt quân, phong cấp, chiếu, killer và history.
- Iterative deepening luôn giữ nước của depth hoàn tất gần nhất.
- Quiescence chỉ mở rộng các tình huống chiến thuật để giảm horizon effect.
- Evaluation gồm vật chất và đặc trưng vị trí, trả score theo Trắng cho UI.
- Không áp dụng luật hòa 50 nước theo yêu cầu; vẫn có lặp ba lần, stalemate và
  thiếu quân.

## CAISSA-JEPA

Trạng thái tượng trưng gồm 12 plane quân, lượt đi, bốn quyền nhập thành và ô
en-passant. Nước đi gồm from/to/promotion. Online encoder dự đoán latent của thế
cờ tương lai ở horizon 1, 2 và 4; target encoder cập nhật bằng EMA.

Loss kết hợp:

- sai số dự đoán latent đa-horizon;
- counterfactual sibling ranking giữa nước GM và một nước hợp lệ khác;
- value của trạng thái hiện tại/kế tiếp;
- variance regularization chống latent collapse.

MCTS không tự tưởng tượng nước bất hợp lệ: mọi child đều do engine luật sinh và
được áp dụng tượng trưng trước khi JEPA chấm latent. Correction học từ ván thua
được dùng như prior, không ép đi nếu alpha-beta tìm thấy chiến thuật trái ngược.

Đây là prototype nghiên cứu chạy được trên CPU/RTX 5050 laptop với khoảng 8 GiB
RAM khả dụng; bản hiện tại dùng NumPy để dễ tái lập và không dùng CUDA. Tính mới
Q1 phải được chứng minh bằng systematic review, ablation và benchmark; tên và
implementation không tự tạo ra bảo đảm về novelty hay mức tạp chí.

## V7: FEN dataset và adversarial conditioning

V7 giữ v6 làm baseline bất biến, đồng thời thêm pipeline dataset FEN có thể
resume, model A-JEPA action-response và regression test MCTS/GUI. Xem
`V7_RESEARCH_PROTOCOL.md` để biết protocol và lệnh chạy.

```bash
python fen_dataset_tool.py crawl-twic --output fen_dataset --target-gb 4
python fen_dataset_tool.py verify --output fen_dataset
python train_caissa_v7.py --dataset fen_dataset \
  --model chess_data/caissa_a_jepa_v7.npz --epochs 5
python train_caissa_v7.py --architecture nnue --model-variant nnue \
  --dataset fen_dataset --model chess_data/nnue_style_baseline.npz --epochs 5
python test_core.py
python test_v7.py
```

Trên Windows, dùng runner PowerShell để xem tiến độ và resume checkpoint:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_caissa_jepa_v7.ps1 -Mode train-status
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\continue_caissa_training.ps1 -AdditionalEpochs 5
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\watch_caissa_training.ps1 -Follow
```

`continue_caissa_training.ps1` giữ lại optimizer/EMA trong checkpoint và nối tiếp
epoch; `watch_caissa_training.ps1 -Follow` đọc heartbeat trong file
`.training.json`. Nếu dataset đã thay đổi sau khi checkpoint được tạo, cần xác
nhận rõ bằng `-AllowDatasetChange`; không chạy hai lệnh train cùng lúc trên cùng
checkpoint.

```powershell
.\continue_caissa_training.ps1 -AdditionalEpochs 5 -AllowDatasetChange
```

The GUI TRAIN MODEL dropdown can start independent runs for A-JEPA H1-only,
A-JEPA H1+H2, full H1+H2+H4, no-response A-JEPA, LeJEPA with SIGReg and no
EMA teacher, Direct Policy/Value, and an NNUE-style value baseline. Alpha-Beta
is a non-trained classical engine reference. The NNUE-style entry uses sparse
side-to-move board features, a small squared-clipped-ReLU network, and the
existing alpha-beta search; it is intentionally not a Stockfish-compatible
binary `.nnue` reader. The LeJEPA entry is the chess-specific NumPy adaptation of
the predictive objective plus sketched isotropic-Gaussian regularization; it
is not a claim that the original vision implementation was copied unchanged.
Each model has its own checkpoint and `.training.json` report, while the
training monitor keeps a separate progress timeline for every selected run.
The MODEL VS MODEL screen is read-only: both agents use the same GM opening
book, colors are randomized per match, and model search begins only after the
shared opening transition. `START SERIES` keeps launching new games until
`STOP SERIES`; `CONTINUE LAST MATCHUP` reads the atomic arena checkpoint and
replays the last saved pair (and seed). If the immutable v6 checkpoint
`chess_data/caissa_jepa.npz` exists, it is available as a non-trainable arena
reference as well. The complete result history remains in
`chess_data/arena_results.jsonl`, while `chess_data/arena_checkpoint.json`
stores the restart point.

Crawler chỉ dùng public archive với HTTP Range resume, retry/backoff và
checksum/manifest. Nó tôn trọng rate limit, chính sách nguồn và không có cơ chế
vượt chặn. Chỉ publish dữ liệu hay derived dataset sau khi review license của
từng nguồn.

## Học và lịch sử

- Import chỉ lấy nước của bên thắng là GM. Các nước opening tạo book; các thế cờ
  và nước của GM trong toàn ván tạo mẫu train.
- Ván engine thắng thêm mẫu cá nhân trọng số nhỏ.
- Ván engine thua kích hoạt worker tối đa 20 giây: tìm mức giảm ít nhất 1.5 tốt
  kéo dài qua ba lượt engine, search lại và lưu nước sửa tốt hơn.
- Lịch sử có năm ván mỗi trang, trang chi tiết SAN/UCI/eval/learning.
- Bấm **XÓA** xóa ngay, không xác nhận. Foreign key cascade loại contribution,
  correction và model sample của ván; opening book được rebuild từ dữ liệu còn
  lại.

## Kiểm thử

```bash
python test_core.py
```

Test gồm perft 20/400/8902, make/unmake và Zobrist, nhập thành, en-passant,
phong cấp, mate/stalemate, PGN/SAN, SQLite cascade/rebuild, train-save-load JEPA,
MCTS hợp lệ và search lai theo thời gian.
