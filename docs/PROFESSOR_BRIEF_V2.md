# CAISSA-JEPA: bản trao đổi nghiên cứu với giáo sư

**Cập nhật: 29/09/2026.** V1 và ba grid V2–V2.2 đã hoàn tất; cả ba grid không
vượt cổng đề cử. Dự án đã có nền tảng kiểm chứng và bằng chứng âm
có thể thảo luận nghiêm túc. **Chưa chứng minh JEPA tốt hơn baseline, chưa sẵn
sàng gửi bài Q1.** Q1 là mục tiêu chất lượng nghiên cứu, không phải cam kết được nhận.

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
