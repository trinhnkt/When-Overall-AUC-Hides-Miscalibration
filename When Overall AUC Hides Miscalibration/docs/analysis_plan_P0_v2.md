# Kế hoạch phân tích P0 v2

Khóa trước mọi lần chạy của đợt bổ sung 21/10/2026. Nguồn yêu cầu: `Check list/20.10/Huong_dan_thuc_nghiem_bo_sung_NCS_Trinh_P0_IJIET_v2.pdf`. Câu trả lời đã biết nằm ở `docs/answers_hau_2026-10-21.md`.

Thay đổi sau commit này ghi vào mục Deviations, kèm ngày và lý do. Không thêm biến thể ngoài bảng này để tìm một kết quả.

## Estimand chính

- Đại lượng: ΔECE = ECE_sparse − ECE_dense của DKT trên ASSISTments 2012.
- ECE: 15 bin đều độ rộng, hàm `compute_ece` trong `src/calibration_eval.py`.
- Giao thức: `best_valid × chunk`.
- Dòng dùng: chỉ `no_history = 0`.
- Đi kèm: ΔECE* của bản I giữ làm mức tham chiếu, không gọi là khoảng tin cậy. Hiệu cùng cỡ = ECE_sparse − trung vị ECE_dense ở đúng N_sparse. Khoảng phân vị 95% bằng bootstrap theo người học, chỉ trên fold 0, B = 2000, R = 200 trong mỗi lần lặp.
- Mô tả: trung bình ± độ lệch chuẩn trên bốn phân hoạch. Không gộp bốn phân hoạch thành một khoảng tin cậy.
- Seed bộ sinh số cho bootstrap và rút cùng cỡ: 20261021.

## Phân tích phụ

Ba chế độ chấm `full`, `chunk`, `slide` và hai cách chọn checkpoint `final`, `best_valid`. ECE_sweep và ước lượng Kumar và cộng sự (2019). M = 10 và M = 20. Chia bin đều khối lượng. Biến thể giữ dòng `no_history` với p = 0.5. M = 15 đều độ rộng vẫn là cấu hình chính.

## Quy tắc loại dòng

Chỉ loại dòng `no_history = 1`. Báo số dòng bị loại theo nhóm và theo mô hình.

## Quyết định T-KT, ghi trước B1

Giữ T-KT và sửa thành **T-KT-c**: mặt nạ nhân quả, mặt nạ padding, `PAD = 2 * n_kcs`. Không thêm BOS, không dịch thêm, không thêm mã hóa vị trí trong lần sửa này. Nếu UT-A1 đến UT-A7 không đạt sau hai lần sửa thì bỏ T-KT và dùng simpleKT (pyKT) làm Transformer duy nhất. Chưa huấn luyện T-KT-c.

## Trạng thái trước lần chạy

Checkpoint bản I: NOT RECOVERED. Vì vậy A3 không chấm lại được và A4 phải huấn luyện lại cả `final` lẫn `best_valid`. Chưa chạy ma trận đó. Quy tắc R1–R4 chưa áp vào câu kết luận.

## Quy tắc kết luận R1–R8

- R1. Ở giao thức chính, ΔECE* > 0, hiệu cùng cỡ > 0 và khoảng 95% của hiệu này không chứa 0. Được giữ kết luận chính và thêm khoảng tin cậy, chỉ cho ASSISTments 2012 và định nghĩa KC hiện tại. Sửa tóm tắt và IV.B. Ở V.D, thay câu chưa kiểm bằng kết quả.
- R2. Hiệu cùng cỡ > 0 nhưng khoảng chứa 0, hoặc ΔECE* > 0 mà hiệu cùng cỡ ≤ 0. Chỉ nêu chênh lệch quan sát. Viết lại tóm tắt, IV.B, VI và thư.
- R3. Tương phản chỉ còn ở `final × full`, mất ở `best_valid` hoặc `chunk`. Phát hiện chính mới là hiệu chỉnh trên KC hiếm phụ thuộc giao thức. Viết lại tóm tắt, câu trả lời và kết luận. Đổi tiêu đề chỉ sau khi thầy duyệt.
- R4. Tương phản mất ở mọi giao thức. Bài là chẩn đoán âm tính trên dữ liệu đã xét. Thầy quyết định có nộp ngay không.
- R5. XES3G5M qua cổng và cùng dấu, đạt R1. Được nói lặp lại trên hai bộ đã xét, vẫn giới hạn theo định nghĩa KC.
- R6. XES3G5M qua cổng nhưng khác dấu hoặc không có tương phản. Khác biệt theo bộ dữ liệu. Không tuyên bố xu thế chung.
- R7. XES3G5M không qua cổng trước hạn. Giữ cách xử lý XES của bản đang sống. Không rút số một cách âm thầm.
- R8. Số T-KT-c khác nhiều so với T-KT bản đang sống. Thay toàn bộ số T-KT. Ghi số cũ chịu lỗi huấn luyện. Không so hai bộ số như hai mô hình.

Chỉ dòng SUPPORTED trong `docs/claim_evidence.csv` được viết thành phát hiện chính.

## Deviations

- 21/10/2026. Chưa chạy A3–A5 vì không còn checkpoint và lần huấn luyện đầy đủ chưa được khởi động trong đợt lập mã. Không có số mới để điền.
- 21/10/2026, cùng ngày, sau khi đối chiếu lại hướng dẫn. Bắt đầu hàng đợi A3–A4: DKT, ASSISTments 2012, năm lần chạy (fold 0–4, seed 42, 2024, 2025, 2026, 2027), cả `final` và `best_valid`, rồi chấm `full`, `chunk`, `slide`. Vì không còn checkpoint, `final × full` là lần huấn luyện mới và không được kỳ vọng tái lập 0,0602 trong sai số 0,0005. Chưa sang mức B. Chưa sửa bản thảo.
- 22/10/2026. B1 đã chạy sau khi UT-A1–UT-A7 in PASS. T-KT-c trên ASSISTments 2012, năm lần chạy, `best_valid × chunk`, patience 8, tối đa 50 epoch. Collate của DKT vẫn đệm bằng 0. T-KT-c dùng collate riêng với `PAD = 2 * n_kcs`. Bản thảo chưa sửa.
- 22/10/2026. B3: huấn luyện lại simpleKT chính thức trên ASSISTments, năm lần chạy, cùng cấu hình trong `scripts/p0_retrain_official_simplekt.py`. Tệp CSV và checkpoint tháng 5 giữ nguyên. ECE bốn phân hoạch trên mọi dòng lệch dưới 0,005 so với 0,0203/0,0884. Bản thảo chưa sửa.
- 22/10/2026. B2: DKT trên Junyi, năm lần chạy, `best_valid × chunk`. Tương phản là medium–dense. Số bản I 0,0389/0,2513 giữ nguyên vì đó là giao thức cũ. Bản thảo chưa sửa.
- 22/10/2026. B4: UT-B8 FAIL vì question-level có 7651 câu hỏi, trong khi catalogue có 7652. Mã 6232 không có lượt làm. Không huấn luyện XES. R7. Bản thảo chưa sửa.
- 22/10/2026. C1: thêm fold 5 của ASSISTments, seed xáo 2028, seed khởi tạo 42, một lần cho DKT, T-KT-c và simpleKT, `best_valid × chunk`. Fold 3 vẫn là bản sao của fold 2. Fold 5 không đưa vào trung bình bốn phân hoạch. Bản thảo chưa sửa.
- 22/10/2026. C2: ablation TKT_PE trên ASSISTments fold 0, seed khởi tạo 42, `best_valid × chunk`. Không thay T-KT-c. Bản thảo chưa sửa.
- 22/10/2026. C3: simpleKT chính thức trên Junyi, năm lần chạy, `best_valid × chunk`. Tương phản là medium–dense. Không thay cặp DKT cũ 0,0389/0,2513. Không huấn luyện simpleKT trên XES. Bản thảo chưa sửa.
