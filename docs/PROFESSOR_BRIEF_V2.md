# CAISSA-JEPA: bản trao đổi nghiên cứu với giáo sư

## Cập nhật mới nhất — V2.9 đã cho kết quả phát triển âm/mixed (02/10/2026)

V2.9 hoàn tất 60/60 fit và 160 block ghép cặp (320 ván) trên Connect4-6x7 và
Reversi6. So với task-value-dynamics trong cùng planner minimax hai ply, điểm
ghép cặp của JEPA là **−0,1375** ở Connect4, **+0,0125** ở Reversi6 và **−0,0625**
trung bình macro, trên 20 cụm seed checkpoint. Cổng đề cử đã khóa thất bại;
không có forfeits/censors, hai ghế JEPA được cân bằng, và CPU planner chỉ cao
hơn 2,5%/0,5% ở hai game. Khoảng tin cậy là exploratory, chưa hiệu chỉnh bội,
và chỉ có điều kiện trên các seed/lịch đã chọn. Mọi ván bắt đầu từ trạng thái
khởi đầu chuẩn nên kết quả chưa đại diện cho phân phối tình huống rộng.

Kết luận trung thực: recipe ba epoch không cho thấy JEPA tốt hơn baseline;
đây là bằng chứng chống lại cấu hình đã thử, không phải bác bỏ JEPA nói chung.
Không tiếp tục tăng epoch đơn thuần. Reviewer độc lập không tìm thấy vấn đề
P1/P2 trong artifact; họ đề xuất giả thuyết có thể kiểm tra rằng loss dự đoán
latent trên reply-set có thể gây xung đột với gradient policy/value trên
encoder dùng chung. Bước kế tiếp được đóng phạm vi thành một diagnostic không
cập nhật trọng số; chỉ nếu gate định trước đạt mới viết protocol riêng cho
conflict-projected JEPA. Gradient surgery và gradient routing đã có prior art,
nên đây chưa phải novelty claim. Xem [method note](METHOD_V210_GRADIENT_DIAGNOSTIC.md),
[roadmap](../ROADMAP.md), [analysis JSON](validation/V29_DEVELOPMENT_MATCH_ANALYSIS_V01.json)
và [related work](RELATED_WORK.md).

V2.10 completed a no-update, train-only gradient diagnostic using 20 frozen
JEPA checkpoints, 300 roots per game and seed, and ten disjoint batches of 30.
The independent audit verified all 400 seed/game/batch cells, 12,000 roots,
zero invalid roots, source and panel hashes, and a maximum gradient-sum
decomposition error of 5.2e-18. The predeclared gradient-conflict screen failed
in both games: median encoder cosine was -0.029 in Connect4 and -0.040 in
Reversi6; both seed-cluster 95% intervals included zero, and persistent-conflict
seeds were 13/20 and 12/20 (threshold: 15/20). Therefore the gradient-conflict
explanation is rejected for this candidate; no projection intervention is
justified. This is a mechanism diagnostic, not a JEPA strength or superiority
result. See [full diagnostic artifact](validation/V210_GRADIENT_DIAGNOSTIC_DEV01.json),
[frozen method note](METHOD_V210_GRADIENT_DIAGNOSTIC.md), and
[independent audit](V210_GRADIENT_DIAGNOSTIC_REVIEW_01.md).

## Lịch sử V2.9 — phép thử underfit trước khi có kết quả

V2.8 đã hoàn tất so sánh phát triển nhưng chưa cho thấy JEPA vượt task-value-
dynamics. Thử nghiệm đã đóng băng tiếp theo chỉ đổi thời lượng huấn luyện từ
một lên ba epoch cho ba nhánh ghép cặp, dùng 20 seed, train split DEV09 đã audit
và một lịch thi đấu phát triển mới. Grant chỉ cho phép fit development/train.
Hai pilot tài nguyên dừng trước khởi tạo model vì RAM khả dụng ở process
preflight chỉ 1,17 GB và 1,32 GB, dưới ngưỡng 2 GB. Một fit JEPA ba epoch chỉ dùng đo tài nguyên đã hoàn tất (65,6 giây, peak working set 859 MB); panel V2.9 qua supervisor đã hoàn tất 60/60 fit, 0 lỗi; match phát triển 160 block/320 ván hiện đang chạy và chưa xem outcome giữa chừng. 20 test V2.9 và 96 test V2.8 pass trong Python 3.11.9 / NumPy 2.4.6 đúng lockfile. Supervisor Job Object đã qua review độc lập; giới hạn commit 1,3 GB và CPU 4 giờ là rào bảo vệ, chưa được hiệu chuẩn từ peak commit/CPU thực đo. Đây là phép thử giả thuyết
underfit; thay đổi thời lượng tự nó không phải novelty thuật toán. Ngưỡng
pass/fail tự động được ghi trong
`V29_THREE_EPOCH_DEVELOPMENT_AMENDMENT_01.md`. Kể cả pass, kết quả chỉ đề cử
cho một nghiên cứu model-selection riêng, không chứng minh superiority hay
mức sẵn sàng Q1.

## Bản cập nhật hiện hành — V2.8, 02/10/2026

**Trạng thái trung thực:** panel phát triển V2.8 đã hoàn tất 60 fit (20 seed × 3
arm, một epoch) và 160 block đối sánh (320 ván) trên Connect4-6x7 và Reversi6.
Đây là kết quả phát triển/mô hình-lựa-chọn, không phải xác nhận. JEPA chưa cho
thấy ưu thế trước baseline task/value-dynamics. Điểm JEPA trừ 0.5, trung bình
đều hai game, là −0.0188; khoảng tin cậy t 95% theo 20 cụm seed là
[−0.0825, 0.0450]. Trước direct-exact-leaf, mức này là +0.0875
[−0.0095, 0.1845], nhưng lợi thế chỉ xuất hiện trên Connect4 (+0.1875),
còn Reversi6 là −0.0125. Các khoảng này có điều kiện trên hai match seed đã
lên lịch trong mỗi ô và không ước lượng riêng bất định do lấy mẫu seed/tình
huống trận. Vì vậy chưa có căn cứ kết luận JEPA tốt hơn.
Kết quả đầy đủ, hash và compute theo arm ở
[báo cáo development](validation/V28_DEVELOPMENT_MATCH_ANALYSIS_V01.json).

Các baseline dùng chung two-ply minimax và giới hạn 2 giây/500.000 transition
mỗi lượt; compute thực tế vẫn khác theo nhánh tìm kiếm và độ dài game, nên phải
báo riêng. Các thí nghiệm V1–V2.5 cũng chưa xác nhận ưu thế JEPA và được giữ
nguyên như bằng chứng âm. Không sử dụng dữ liệu bên thứ ba; DEV09 là self-play
do dự án tạo. Dữ liệu vẫn ở local, `training_approved` vẫn false, locked-final
chưa được mở.

**Câu hỏi nghiên cứu hiện hành:** trong game hai người, luân phiên lượt, quan sát đầy
đủ, xác định và tổng bằng không với legal actions/terminal rules rõ ràng, liệu mục
tiêu JEPA dự đoán latent của các nhánh phản hồi hợp lệ có cải thiện quyết định của
planner max–min dưới cùng dữ liệu và ngân sách tính toán so với task/value prediction
và direct policy/value? Đối thủ trong planner là phản hồi hợp lệ xấu nhất; đây không
phải dự báo hành vi của một đối thủ cụ thể, kỳ vọng theo policy chưa hiệu chuẩn, hay
bảo đảm equilibrium/exploitability.

**Phần có thể đóng góp nếu được chứng minh:** không phải “JEPA dự đoán tương lai”,
“nhiều game dùng một codebase”, hay “planner có latent”. MuZero, Athénan và LAMIR đã
đặt chuẩn cao cho learned-model planning/game-theoretic search; MA-JEPA và các JEPA
policy/world-model gần đây đã dùng conditioning theo hành động. Giả thuyết hẹp cần
kiểm tra là objective JEPA đem lại lợi thế quyết định tăng thêm trước baseline
task-prediction ghép cặp công bằng trong panel game đã khóa. Transfer sang
game/variant chưa huấn luyện là mục tiêu riêng, chưa được protocol hiện tại chứng minh.
Ma trận nguồn và khác biệt domain nằm ở [review related work](RELATED_WORK.md).

**Bước nghiên cứu kế tiếp:** kiểm tra giả thuyết một epoch còn underfit bằng panel
ba epoch đã ghép cặp cho tất cả arm; đây là thay đổi thời lượng duy nhất và cần
amendment/schedule/grant phiên bản mới trước khi fit. Sau đó dùng schedule
development mới và selection split đã audit để quyết định có giữ recipe. Nếu JEPA
không cải thiện trước task/value-dynamics ở cả hai game với compute đo được hợp lý,
phải thiết kế lại hoặc thu hẹp claim. V08 vẫn khóa cho tới khi recipe, estimand,
primary metric, multiplicity, practical margin, censor policy, power và stopping
rule được đóng băng, kiểm tra độc lập và đăng ký trước. Không đọc locked results để
điều chỉnh model.

**Đánh giá hiện thời:** đây là một negative/mixed result hữu ích để chọn hướng tiếp
theo, chưa phải bản thảo Q1 triển vọng. Novelty risk vẫn cao: policy-aware minimax
model learning và latent-space value alignment đã xuất hiện trong prior art 2026;
chỉ có thể bảo vệ đóng góp hẹp sau khi đối chiếu kỹ hơn và đo lợi thế tăng thêm của
JEPA trước task-prediction. Góp ý giáo sư nên tập trung vào việc liệu lợi thế
decision-level đủ ý nghĩa trong game luật đã biết, hay hướng phù hợp hơn là sample
efficiency/held-out variant transfer. Q1 là mục tiêu chất lượng, không phải cam kết
được nhận.

> **Bổ sung ngày 30/09/2026:** Đã đọc toàn văn KLENT (ICML 2026 accepted). Phương pháp này học policy và Q trực tiếp từ self-play, không dùng search trong training; báo cáo đạt 50% win rate trung bình ở 75M simulator evaluations so với 300M của Gumbel AlphaZero (3 seeds, 5 games, 6-block ResNet). Đây là kết quả của bài báo, không phải kết quả CAISSA, và simulator calls không tương đương compute đo trên phần cứng. V2 cần có KLENT-style regularized policy/Q baseline riêng bên cạnh minimax-Q; KLENT tối ưu regularized self-play, không phải nhãn worst-case minimax. Repo code chính thức hiện không công bố license, nên chưa dùng code; có thể triển khai clean-room từ phương trình trong paper và audit fidelity. Hiện chưa có V2.7 training hay bằng chứng JEPA thắng baseline.

> **Cập nhật nghiên cứu 30/09/2026:** deep search phát hiện thêm prior art trực tiếp về state abstraction trong Markov game zero-sum (AAAI 2025), transfer policy-value giữa nhiều game/variant (TMLR 2023), path-consistency regularization cho AlphaZero (ICML 2022), và một phương pháp model-free hiệu quả trên năm board games (ICML 2026 accepted), bên cạnh Athénan. Vì vậy, latent compression, minimax-sufficient abstraction, cross-game transfer, latent consistency, hay sample efficiency đều không thể tự đứng làm novelty claim. Candidate complete-reply-set JEPA + minimax action-ordering vẫn chưa đóng băng và chưa được xác minh là khác biệt đủ; trước training cần benchmark công bằng với Athénan/tree-value, minimax-Q/abstraction, policy-value transfer, PCZero, model-free regularized policy optimization và task-prediction. Hiện chưa có training V2.7, checkpoint, hay bằng chứng JEPA hơn baseline. Chi tiết nguồn trong [prior-art re-audit](V27_PRIOR_ART_REAUDIT_20260930.md).

**Cập nhật: 30/09/2026 — bản trao đổi với giáo sư.** V1 và các grid V2–V2.5
đều chưa vượt cổng đề cử. V2.5 là so sánh đầy đủ, đã audit độc lập, nhưng
không cho thấy JEPA vượt baseline: mức exact gần như bằng không và planner
hybrid dùng latent kém hơn. **Chưa chứng minh JEPA tốt hơn baseline; tài liệu
này phù hợp để xin góp ý về pivot nghiên cứu, chưa phải bản thảo Q1.** Q1 là
mục tiêu chất lượng, không phải cam kết được nhận.

**Định vị V2.7 ban đầu (nay đã được rà soát lại):** V2.6 không qua cổng chi phí/độ phủ của nhãn minimax:
game nhỏ dễ giải chính xác, còn Connect4-8x8 giữa ván phần lớn hết ngân sách
solver. Tôi đề xuất đánh giá một hướng riêng: dữ liệu self-play tự sinh và
paired matches trên ít nhất hai họ game khó hơn, so sánh JEPA với direct
policy/value, task-prediction và decoded-feature prediction dưới cùng dữ liệu,
compute và planner. Chỉ số khi ấy là kết quả trước một opponent suite cố định;
nó không đồng nghĩa minimax, exploitability hay Nash. TD-JEPA (ICLR 2026) đã có
predictor latent đa bước có điều kiện theo policy, nên thêm action phản hồi của
đối thủ chưa đủ tạo novelty. Hướng này hiện mới là proposal: chưa đóng băng
method, chưa tạo dữ liệu, chưa train và chưa có kết quả dương. Xem
[V2.7 research positioning](V27_RESEARCH_POSITIONING.md). Câu hỏi xin ý kiến
giáo sư ở giai đoạn này là liệu estimand “bounded-budget performance against a
fixed, held-out opponent suite” có giá trị nghiên cứu đủ rõ, và cần thêm prior
art nào trước khi quyết định có triển khai không.

Một pilot feasibility nhỏ chạy96 trận (8 seed × 3 cặp policy × 2 chỗ ngồi) trên
Connect4 gravity 8×8 và Reversi8 trong5.207 giây. Heuristic tự viết thắng
random cả16/16 trận trong mỗi game; đây là bằng chứng opponent bank hiện tại
quá yếu, không phải bằng chứng model mạnh. Kết quả, seed, seat và hash bàn cờ:
[receipt V2.7](validation/V27_MATCH_FEASIBILITY_01.json). Bước tiếp theo là
opponent search độc lập và kiểm tra luật; chưa tạo self-play dataset hay train.

**Cập nhật tiếp theo:** đã có một đối thủ alpha-beta giới hạn depth 3/500
node mỗi nước trên bộ luật bitboard tham chiếu do dự án tự viết. 12 trajectory
có seed trên ba cấu hình game khớp legal actions, trạng thái cuối và utility
với adapter chính; đây chỉ là kiểm tra nội bộ, không phải referee bên ngoài.
Pilot v2 có fingerprint 32 trận và chạy86.69 giây; search thắng center/random
4/4 mẫu mỗi cặp/game nhưng N=2 seed. Reversi v2 self-play để quân âm thắng
4/4 và có116 node-cap hits. Sau đó tôi thêm canonicalization D4 cùng chuẩn hóa
player-to-move. Unit test xác nhận các phép quay/lật/đổi màu cùng ánh xạ về một
trạng thái canonical và kiểm tra nhánh bốn canonical maps đồng hạng ở bàn đầu.
Pilot v3 cùng lịch chạy51.19 giây, giảm còn68 cap hits; tuy vậy self-play lần
này quân dương/đi trước thắng trên cả hai seed duy nhất (bốn receipt rows có
hai bản sao seat-swap). V2 trước đó quân âm thắng trên cả hai seed duy nhất.
Các chỗ ngồi đảo dấu giữa hai phiên bản cho thấy ngân hàng opponent vẫn chưa
được hiệu chuẩn; hai seed không tách được first-move advantage khỏi bất đối
xứng policy/RNG. Vì vậy
chưa dùng để sinh dữ liệu nghiên cứu.

**Rà soát novelty mới:** Deep Latent Competition đã mô hình hóa tương tác latent
cạnh tranh giữa hai người, dự đoán góc nhìn/hành động đối thủ và self-play tưởng
tượng trong game đua xe. Preprint MA-JEPA (27/09/2026) đã dùng JEPA với predictor
điều kiện theo trạng thái và hành động đồng thời của nhiều agent trong cooperative
SMAC. Dù hai domain này khác game luân phiên, fully observable, zero-sum mà đề tài
nhắm tới, chúng khiến claim “JEPA đầu tiên có action/opponent conditioning” không
thể bảo vệ. Novelty hiện ở mức rủi ro nghiêm trọng/chưa xác minh. Candidate hẹp
cho tìm kiếm tiếp là dự đoán toàn bộ tập legal replies và bảo toàn thứ tự hành
động minimax dưới compute budget công bằng; chưa đóng băng, chưa có bằng chứng
đã là phương pháp mới. Chi tiết và receipts:
[V2.7 positioning](V27_RESEARCH_POSITIONING.md), receipts
[01](validation/V27_SEARCH_OPPONENT_01.json),
[02](validation/V27_SEARCH_OPPONENT_02.json),
[03](validation/V27_SEARCH_OPPONENT_03.json),
[04](validation/V27_SEARCH_OPPONENT_04.json).

Rà soát nguồn sâu hơn còn tìm thấy minimax-Q neural learners và AAR/AI: agent
RTS liên quan dùng learned transition, leaf evaluation, action ranking cùng
minimax search. Quan trọng hơn, Athénan (JMLR 2026) thuộc chính lớp hai người,
perfect-information, zero-sum mà dự án nhắm tới: phương pháp này học value từ
các state trong search tree và dùng minimax; báo cáo kết quả trên Go, Hex,
Othello, Arimaa và game khác. Đây là baseline phi-JEPA trực tiếp cần được đưa
vào so sánh, không chỉ một bài liên quan xa. Bất kỳ candidate nào dự đoán toàn
bộ nhánh hợp lệ cũng phải chứng minh nó bổ sung hơn tree-value learning ở cùng
state/action/compute budget. Vì vậy ngay cả “học thứ tự hành động minimax” cũng
có tiền lệ gần; nghiên cứu AAMAS 2023 [*Minimax Strikes Back*](https://www.lamsade.dauphine.fr/~cazenave/papers/MinimaxStrikesBack_AAMAS.pdf)
còn so Athénan trực tiếp với Polygames/AlphaZero và báo cáo chi phí tạo
state-data thấp hơn khoảng296 lần theo thiết lập của bài. Candidate chỉ đáng
triển khai nếu có phân biệt toán học rõ và
cổng độ phủ teacher không chọn lọc vị trí. Báo cáo đối chiếu từng công trình,
claim limit và điều kiện dừng nằm trong
[V2.7 prior-art re-audit](V27_PRIOR_ART_REAUDIT_20260930.md). Pilot chuẩn hóa
Reversi chỉ vượt đối thủ sanity 4/4 trên hai seed; lệch ghế tự đấu đảo từ quân
âm thắng trên cả hai seed duy nhất sang quân dương thắng trên cả hai seed duy
nhất (bốn receipt rows mỗi phiên bản có seat-swap lặp), nên hiện không chứng
minh sức mạnh hay đã sửa được bias. Full regression đạt330 test; reviewer độc
lập không tìm thấy lỗi chặn commit và các chỉnh sửa về số ván duy nhất/test
tie-map đã được áp dụng. Tuy nhiên không có model,
dataset, checkpoint hoặc kết quả JEPA mới.

## Kết quả V2.5 mới nhất

| Đánh giá development | Raw-tail JEPA | Baseline mạnh nhất | Chênh lệch regret (dương có lợi JEPA) | Kết luận |
| --- | ---: | ---: | ---: | --- |
| Exact-state | 0.202446 | Direct 0.203775 | +0.001329; bootstrap mô tả 95% [−0.023899, 0.026938] | Dưới cổng +0.05; Connect4 tốt hơn nhưng Reversi kém hơn; chỉ1/3 seed ủng hộ |
| Hybrid latent planning | 0.268340 | Direct 0.203775 | −0.064565; 95% [−0.126889, −0.005814] | JEPA hybrid kém hơn direct; cũng kém recurrent policy/value (0.250596) |

Cổng cơ chế cũng thất bại: raw-tail không cải thiện đồng thời hai game và ít
nhất hai seed so với raw-mean/raw-scaled; scalar-tail đạt backed-up oracle MSE
0.529363, tốt hơn raw-tail 0.545679. Vì vậy chênh lệch exact nhỏ không thể
được quy cho phần JEPA-tail. Các khoảng là mô tả adaptive development trên209
root tái sử dụng và3 seed, không phải khoảng xác nhận đã hiệu chỉnh cho việc
thử nhiều thiết kế.

Grid hoàn tất42/42 cell:17.556 quyết định learned,836 control, không lỗi/censor/
collapse. Audit độc lập kiểm tra2.016 tensor,480 plan và toàn bộ source/data/hash;
không thấy overlap train-development. Reversi được so với mã nguồn độc lập MIT
trên100 trajectory cho mỗi cỡ4×4 và6×6:183.612 so sánh trajectory,392 fixture,
0 sai khác. Điều này chỉ xác nhận luật ở trạng thái kiểm tra, không xác thực
nhãn minimax. Tổng thời gian cell4.899 giây và peak RSS200.802.304 byte.

Kết quả chi tiết: [V2.5 report](V25_GRID05_RESULTS.md); protocol đóng băng:
[METHOD_V25](METHOD_V25.md). Post-run search cho thấy prior art trực tiếp về
consistency trên Go/Gomoku, transfer giữa board-game variants, và simulator
learning theo game-theoretic robustness; xem
[research update](V25_POSTRUN_RESEARCH_UPDATE.md). Hướng tiếp theo chỉ là giả
thuyết thiết kế: kiểm tra lợi ích sample-efficiency/transfer trên **game
variant bị giữ nguyên cả luật**, với policy/value-only, MuZero-style, rule-aware
và JEPA baselines được tuning công bằng. Chưa có V2.6 được khóa hay bằng chứng
JEPA tốt hơn.

Nghiên cứu transfer gần nhất đã thử nhiều game/variant bằng mạng policy-value,
nên chuyển game không tự nó là claim mới. Một công trình ECAI mới dùng JEPA để
cải thiện zero-shot generalization trong ProcGen và visual control; domain đó là
single-agent, luật cố định, không phải đối kháng hai người với luật biến thể.
Bộ Ludii được bài transfer kia dùng có license CC BY-NC-ND 4.0 ở repository
chính thức; dự án chưa tải hay dùng Ludii. Nếu
tiếp tục, ưu tiên luật procedural do dự án tự triển khai hoặc nguồn có quyền
train và chia sẻ rõ ràng.

## Hồ sơ nghiên cứu trước đó (lịch sử)

Các mục dưới đây giữ lại quá trình V2 trước V2.5; chúng không thay cho kết quả
mới nhất ở trên.

## Câu hỏi và đóng góp cần chứng minh

Giả thuyết có thể bác bỏ: biểu diễn dự đoán trạng thái latent tương lai, có điều
kiện theo hành động của cả hai bên, cải thiện lập kế hoạch dưới ngân sách tính
toán giới hạn; lợi ích còn giữ được trên nhiều game trong một lớp xác định.
Phạm vi hiện tại là game hai người, luân phiên, quan sát đầy đủ, chuyển tiếp xác
định và tổng bằng không. Không suy rộng sang thông tin ẩn hoặc game ngẫu nhiên.

V2 dùng Connect4 bàn 4×5 và Reversi 6×6, với các nhánh hành động hợp lệ của cả
hai bên. Planner lấy **minimax** qua hai lượt, không lấy kỳ vọng theo policy
đối thủ và không học hành vi một đối thủ cụ thể. Chỉ số chính là regret của
nước đi so với oracle, trung bình cân bằng hai game; thấp hơn tốt hơn. Đây là
chất lượng quyết định tại vị trí, chưa phải Elo, tỷ lệ thắng cả trận hay exploitability.
Xem [benchmark](BENCHMARK_V2_SPEC.md) và [phương pháp V2](METHOD_V2.md).

## Bằng chứng đã hoàn tất

| Giai đoạn | Quan sát có thể kiểm chứng | Diễn giải |
| --- | --- | --- |
| [Pilot V1](TWO_PLAYER_PILOT_20260929.md) | 21 lần chạy, 3 seed, 68 vị trí. Các biến thể learned exact-state đều đạt regret 0 trên lịch đánh giá quá dễ. | Không phân biệt được phương pháp; dừng mở rộng pilot này. |
| [Grid01](V2_GRID01_RESULTS.md) | 36 lần chạy; 209 vị trí development. Projected JEPA: regret 0.249145; value-dynamics: 0.247664. Chênh lệch có lợi cho JEPA là −0.001481; khoảng bootstrap 95% [−0.049433, 0.048714]. | JEPA không hơn baseline mạnh nhất; không vượt cổng đề cử. |
| [Grid02](V21_GRID02_RESULTS.md) | 60 lần chạy, cùng 209 vị trí; mọi nhóm nhận augmentation đối xứng hợp lệ. Raw JEPA: 0.207425; value-dynamics: 0.212250. Lợi ích +0.004826; khoảng 95% [−0.039003, 0.044845]. | Tín hiệu nhỏ, chưa đủ: dưới ngưỡng 0.05, không hơn decoded ở cả hai game, khoảng chứa 0. |
| [Grid03 / V2.2](V22_GRID03_RESULTS.md) | 72 lần chạy. Nhánh ít nhãn: raw JEPA 0.293339, direct 0.283917. Lợi ích −0.009422; khoảng 95% [−0.075730, 0.047922]. | JEPA kém direct ở cả hai game; giả thuyết lợi thế khi hạn chế nhãn chưa được hỗ trợ. |
| [Chẩn đoán train V2.3](V23_FIT_DIAGNOSTIC.md) | 18 lần chạy, 160 epoch, hai dung lượng, 72 checkpoint được kiểm chứng. Mọi nhóm còn cải thiện từ80→160; tăng dung lượng giúp cả3 nhóm/all3 seed. | Ngân sách và dung lượng ảnh hưởng rõ. Direct có train S thấp hơn JEPA ở mọi cặp seed/dung lượng; đây không phải đánh giá sức chơi mới. |

Các khoảng trên là mô tả development sau điều chỉnh phương pháp, không hiệu
chỉnh cho quá trình thử nhiều thiết kế. Ba seed không biến hàng trăm vị trí thành
hàng trăm lần huấn luyện độc lập. Mức cải thiện chung sau augmentation không
được quy riêng cho JEPA. Lợi ích ở nhánh exact-state cũng chưa chứng minh rollout
latent tốt: cần đọc riêng nhánh hybrid, hiện còn yếu trên Reversi. Ablation bỏ
action phản hồi có điểm exact tốt trong Grid02, nên đóng góp đặc thù của
opponent conditioning vẫn chưa được xác lập.

## V2.2 đã kiểm tra điều gì?

[Protocol V2.2](METHOD_V22.md) đã khóa trước fitting: kiểm tra JEPA khi hạn chế
quyền truy cập nhãn oracle, giữ cùng các chuyển tiếp quan sát được cho mọi nhóm.
Chọn 25% root huấn luyện bằng hash cố định; nhãn được mở theo toàn bộ closure
hai lượt và nhất quán trên các trạng thái đối xứng tương đương. **25% root không
phải 25% nhãn trạng thái.** Nhánh 100% là phân tích độ nhạy đã định trước.

Ma trận gồm 72 lần chạy: hai mức nhãn, sáu nhóm, hai learning rate và ba seed.
Các đối chứng là direct policy/value, value-dynamics, decoded dynamics và
EMA-value trên các successor chưa có nhãn; raw-no-response chỉ dùng để phân
tích cơ chế. Lịch lấy mẫu, augmentation, số cập nhật và dữ liệu được ghép cặp.
Đây chưa phải so sánh bằng nhau về FLOP hoạt động.

Toàn bộ 30.096 quyết định learned và 836 quyết định control hoàn tất, không có
lỗi, censor hay cảnh báo collapse. Bốn khoảng so sánh primary đều chứa 0.
Nhánh đủ nhãn cho raw JEPA 0.205867 so với direct 0.224788, nhưng dùng learning
rate chọn từ nhánh ít nhãn: không được diễn giải là thắng các baseline đã
tuning độc lập trên đủ nhãn, hoặc dùng để thay kết luận primary âm.
Ngay trong bảng đủ nhãn, direct ở learning rate 0.001 đạt 0.196598, thấp hơn
raw JEPA; đây chỉ là kiểm tra mô tả, không phải đổi cách chọn primary.

Ngưỡng đề cử đã khóa yêu cầu: raw JEPA giảm regret ít nhất 0.05 so với
đối chứng mạnh nhất đã tuning; hơn từng đối chứng ở cả hai game; có lợi ở ít
nhất 2/3 seed ghép cặp; không collapse và không bỏ qua run hoặc quyết định lỗi.
Learning rate chọn ở nhánh ít nhãn được giữ nguyên cho nhánh đủ nhãn. Không đổi
mức nhãn hoặc hạ ngưỡng sau khi xem kết quả. Vượt cổng này mới cho phép đề xuất
replication bằng mask/seed độc lập, rồi selection và confirmation riêng.

Dữ liệu tự sinh đã có oracle từ trước: thí nghiệm chỉ mô phỏng quyền truy cập
nhãn, **không chứng minh tiết kiệm chi phí tạo nhãn thực tế**. Trainer nhận file
train đã xóa nhãn ẩn và file development riêng; không mở lại ngân hàng train
đầy đủ. Audit kiểm tra luật, transition, overlap theo đối xứng, mask và hash.
Checkpoint gắn source/config/data fingerprint; selection/final chưa được dùng
để dự đoán. [Review trước fitting](V22_PREFIT_REVIEW.md) ghi các kiểm tra cụ thể.

## Tính mới và nội dung cần trao đổi

Rủi ro trùng ý tưởng cao: [MuZero](https://arxiv.org/abs/1911.08265) đã lập kế
hoạch latent trên nhiều board game; [SPR](https://arxiv.org/abs/2007.05929) đã
dùng dự đoán biểu diễn EMA nhiều bước; [EfficientZero](https://arxiv.org/abs/2111.00210)
đã kết hợp consistency và learned planning. [RePAIR](https://arxiv.org/html/2606.11860)
là prior art trực tiếp về biểu diễn cờ vua và JEPA auxiliary; kết quả reconstruction
của họ không phải chứng minh sức chơi. Vì vậy, ghép JEPA với action hai người
hoặc đổi tên workflow chưa tạo thành tính mới. Phạm vi đọc từng nguồn và điểm
khác biệt được ghi trong [review predictive models](V2_PREDICTIVE_RESEARCH.md),
[review evaluation](V2_GAME_EVALUATION_RESEARCH.md) và
[đối chiếu nghiên cứu tiếp theo](V23_RESEARCH_OPTIONS.md).

**Đã sẵn sàng để giáo sư đánh giá:** câu hỏi có thể bác bỏ, benchmark có độ khó
phân biệt, đối chứng rõ, kết quả âm được giữ nguyên và một thí nghiệm hẹp có
cổng quyết định trước. Cần trao đổi xem label efficiency trong minimax có đủ
giá trị khoa học, và bằng chứng cơ chế nào phân biệt latent prediction với
reconstruction hoặc scalar self-distillation.

**Chưa sẵn sàng để công bố:** chưa có ưu thế JEPA được xác nhận, chưa có transfer
game giữ lại, chưa có kết quả sức chơi toàn hệ thống hoặc replication độc lập.
Một bài báo mạnh cần bổ sung các bằng chứng đó, kiểm tra luật bằng tham chiếu
độc lập phù hợp, phân tích compute và một claim mới hẹp nhưng có thể bảo vệ.
Nếu lợi ích biến mất trước EMA-value/decoded hoặc khi đổi mask, cần bác bỏ
giải thích JEPA-specific và giữ kết quả âm trong hồ sơ nghiên cứu.

## Hướng V2.6 đang nghiên cứu, chưa khóa protocol

Deep search cho thấy transfer policy/value giữa board-game variants, JEPA
visual OOD trong RL, predictive state consistency trong board games và
adversarial simulator learning đều có prior art. Hai review độc lập cũng nhắc
rằng trong game Markov đầy đủ trạng thái, minimax đã xét nước đi nối tiếp của
cả hai bên; điều đó không đồng nghĩa học hành vi của một đối thủ cụ thể.

V2.6 sẽ chỉ tiếp tục nếu có thể kiểm tra công bằng câu hỏi hẹp hơn: liệu
action-conditioned JEPA trên chuyển tiếp luân phiên giúp giảm regret minimax
trên luật held-out theo số transition đã thấy, so với cùng encoder được huấn
luyện bằng policy/value, MuZero-style task prediction và dự đoán đặc trưng trạng
thái. Metric chính dự kiến là AULC regret trên variant held-out theo measured
training compute, với search/inference budget ghép cặp; AULC theo transition
exposure là phụ để phân tích sample efficiency. Chưa khóa margin, cỡ mẫu hay
model. Variant-size holdout chỉ
hỗ trợ claim within-family, không phải cross-game transfer. Trước fitting phải
đạt gate về luật procedural tự sở hữu, split theo variant/trajectory/symmetry,
root khó, oracle cost và cân bằng ngân sách baseline. Mã hiện có dùng input đã
padding 198 đặc trưng/65 action slots cho board đến8×8, và mỗi fit V2.5 đã thấy
cả Connect4-4×5 lẫn Reversi6; điều này cho phép thử bounded trên variant trong
giới hạn đó, nhưng chưa chứng minh held-out transfer. Nếu exact solver rẻ hơn
hoặc JEPA không thắng các learned control
đã tuning công bằng, sẽ dừng claim phương pháp tích cực; mọi kết quả âm vẫn giữ.

## Quyết định sau chẩn đoán mới

Vòng so sánh tiếp theo sẽ dùng mức hidden/latent128/64 và160 epoch chung cho
mọi nhóm liên quan; đây là điểm vận hành hữu hạn, không phải tuyên bố hội tụ.
Trước khi chạy grid kiến trúc, một phép đo train đã được định trước sẽ kiểm tra
giới hạn của transition cộng tuyến tính: nó không thể đảo thứ tự hai latent
ở từng tọa độ khi thay hành động. Có phản ví dụ và cận sai số, nhưng mức liên
quan trên các biểu diễn đã học vẫn chưa đo. [Protocol probe](METHOD_V24_ORDER_PROBE.md)
giữ các checkpoint cố định và không đọc development/final. Ý tưởng dùng vài
minimum-probe ngẫu nhiên đã bị hoãn sau phản ví dụ; không đưa tên mới cho loss
đó rồi coi là đóng góp. Nếu đổi transition, baseline phải được tăng cường tương ứng.

Phép đo V2.4 sau đó đã hoàn tất và qua audit độc lập: cả4 ngưỡng chính và4
ngưỡng nonterminal đều không đạt. Cận sai số chỉ bằng khoảng0,02–0,28% sai số
H1 ở các nhóm chính, dù coverage68–72%. Chưa chứng minh được giới hạn này là
nút thắt; lower bound nhỏ cũng không chứng minh predictor hiện tại đủ tốt.

Thiết kế V2.5 mới tập trung vào sai số lớn nhất trong một tập phản hồi hợp lệ
đầy đủ, so sánh với mean-only, scalar-tail, decoded-tail, recurrent policy/value
và một control phân bổ gradient. Cùng kiến trúc/compute opportunity,42cell
hữu hạn. [Method](METHOD_V25.md) đã được phản biện trước code; chưa có kết quả
V2.5. WAKER, VAML, TD-JEPA và EfficientZero là prior art quan trọng, nên chưa
được gọi hướng này là nguyên lý mới hoặc kết quả triển vọng đã xác nhận.

Lần chạy V2.5 đầu tiên dừng vì lỗi kỹ thuật ở bộ giám sát RAM: ba cell hoàn
thành, cell4 bị lỗi và38 cell chưa chạy. Nguyên nhân được tái hiện độc lập;
đây vẫn là lần chạy không kết luận. Amendment chỉ sửa monitor, sau đó lần
retry mới đã hoàn tất42 cell và cho kết quả âm nêu ở đầu tài liệu. Cả hai lần
chạy và chi phí đều được giữ lại. [Bản định vị phương pháp](V25_RESEARCH_POSITIONING.md)
tách cận minimax có điều kiện khỏi các claim cần chứng minh.

**Đề nghị thảo luận với giáo sư:** liệu pivot sang câu hỏi JEPA có giúp tăng
sample efficiency khi chuyển sang game variant hoàn toàn held-out có giá trị
khoa học, và nhóm nào là baseline công bằng nhất. Nếu nghiên cứu sâu hơn không
tìm thấy một claim hẹp có novelty bảo vệ được, dự án nên chuyển sang bài
benchmark/phân tích negative results thay vì tiếp tục đổi loss đến khi có một
điểm thắng development.

## Cập nhật feasibility V2.6 — 2026-09-29

Định vị sâu hơn cho thấy chuyển giao giữa board-game variants, planning với
latent dynamics và action-conditioned prediction đều có prior art đáng kể; do
đó V2.6 chỉ là giả thuyết kiểm định JEPA có tăng chất lượng quyết định trên
variant luật held-out dưới ngân sách đo được hay không. Phản biện protocol độc
lập không tìm thấy blocker khái niệm sau khi bổ sung công thức AULC đầy đủ và
reserve cho optimizer/checkpoint. Smoke test interface cho Connect4-5x5 và
Reversi8 đạt trên tập mẫu nhỏ đối chiếu với reference rules do dự án tự viết;
đây không phải kiểm định độc lập bên ngoài. Chưa tạo V2.6 labels, chưa huấn
luyện, và chưa có bằng chứng JEPA thắng. Chi tiết cùng giới hạn nằm trong
`METHOD_V26.md` và receipt `validation/V26_INTERFACE_SMOKE_01.json`.
Đo cost sơ bộ cho exact minimax trên Connect4-4x5 chỉ giải được2/5 root
không-terminal trong ngân sách100k nodes/1s. Đây là mẫu nhỏ, không ước lượng
tỷ lệ tổng thể, nhưng cho thấy không thể âm thầm bỏ root khó sau khi thấy chi
phí oracle; timeout phải được tính vào gate coverage đã định trước. Receipt:
`validation/V26_ORACLE_FEASIBILITY_01.json`.
Một alpha-beta reference solver do dự án viết tiếp theo giải được4/5 root trên
cùng mẫu thay vì2/5 của negamax thuần trong1 giây/root. Các giá trị exact đã
đối chiếu trên root giải xong; tuy vậy một root vẫn timeout và mẫu nhỏ chưa
đạt gate coverage. Đây là tiến bộ engineering cho oracle, không phải kết quả
JEPA.
Feasibility hiện có khoảng trống giữa hai regime: Connect4-4x5 dễ gán nhãn
nhưng exact search giải hầu hết root; Connect4 8x8 khó hơn nhưng exact oracle
chỉ giải được1/10 root trong1 giây. Do đó phương pháp V2.6 chưa vào training;
cần tìm oracle/metric khả thi không loại root khó, hoặc pivot sang self-play với
match evaluation paired và cùng compute.
Một survey tái lập bằng seed cố định cho thấy Connect4-4x5 exact-label được
17/24 root, trong đó13 root có action outcome khác nhau; Reversi6/8 endgame
được giải8/8 nhưng exact search rẻ, nên không phải benchmark planning chính
tốt. Chưa có training V2.6 hay kết quả model nào.
