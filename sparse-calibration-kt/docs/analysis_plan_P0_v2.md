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
