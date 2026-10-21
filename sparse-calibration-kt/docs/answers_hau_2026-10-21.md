# Trả lời sáu câu trong hướng dẫn 21/10/2026

Người trả lời: đối chiếu mã và dữ liệu trên máy đang dùng, commit gốc `f5b5d58`. Không chạy lại mô hình. Không bịa giờ GPU.

## 1. Checkpoint và tệp dự đoán của bản I

Thư mục `results/checkpoints`, `manuscript-pack/a2b/checkpoints` và `src/models` không có file trọng số (`.pt`, `.pth`, `.ckpt`). Checkpoint DKT và T-KT của bản I là **NOT RECOVERED**.

Tệp dự đoán CSV của các lần chạy cũ vẫn nằm trong `results/predictions`. A3 không chấm lại được từ checkpoint. Muốn có đối chứng `final` phải huấn luyện lại.

## 2. Vì sao fold 2 trùng fold 3

`src/three_split_constructor.py` lấy `seed = config['seeds'][fold]` và chỉ rơi về 42 khi `fold` lớn hơn số seed trong cấu hình. Nhánh đó không giải thích được dữ liệu đang có: nếu thiếu seed thì fold 3 trùng fold 0, nhưng tập người học kiểm tra của fold 0 khác fold 2 và fold 4.

Đối chiếu tập người học trong `data/processed/assist2012/splits/learner_based/fold_*/test.csv` với phép xáo của `create_learner_based_split`:

- fold 0 khớp seed xáo **42**
- fold 1 khớp seed xáo **123** (đúng `configs/assist2012.yaml`, không phải seed huấn luyện 2024)
- fold 2 và fold 3 cùng khớp seed xáo **2026**
- fold 4 khớp seed xáo **2027**
- seed 2024 và 2025 không khớp phân hoạch nào trên đĩa

`configs/assist2012.yaml` có `seeds: [42, 123, 2026]`, nên fold 2 được tạo bằng seed 2026. `scripts/create_new_folds.py` tạo fold 3 cũng bằng seed 2026 và fold 4 bằng seed 2027. Hai fold dùng chung một seed xáo, nên cùng một phân hoạch. Nhãn “seed 2025 và 2026” trong bài là nhãn lần huấn luyện gắn vào fold 2 và fold 3, không phải seed đã xáo người học.

## 3. Số 198

Đúng với median 44.5. Trên train fold 0, các KC có trong dự đoán SimpleKT: median số item là 44.5, median nhóm dense là 198 (147 KC), median nhóm sparse là 1. Số 205 là median dense của fold 2 và fold 3; median toàn bộ của fold đó là 31.5. Bản I đã in 198. Bản đang sống in 205 ở Table 8 và được sửa thành 198 trong đợt này. Các số ECE không đổi.

## 4. ASSISTments `problem_log_id` và Junyi `Log_Problem.csv`

`data/raw/assistments2012/2012-2013-data-with-predictions-4-final.csv` có 6.123.270 dòng và 6.123.270 giá trị `problem_log_id` phân biệt. Mỗi dòng là một problem log riêng, không phải một lượt làm bài bị tách thành nhiều dòng cùng `problem_log_id`.

`data/raw/junyi/Log_Problem.csv` có 16.217.311 dòng dữ liệu, không có dòng thiếu cột. Mỗi dòng có một `ucid`, một `upid` và một `is_correct`. Đó là một bản ghi một lượt làm một bài, không phải một sự kiện nhiều KC. Không có cột mã lượt làm riêng để đếm trùng.

Đây là cơ sở để L8 không áp vào hai bộ này. XES3G5M vẫn là bộ bị làm phẳng theo KC.

## 5. Giờ GPU

Máy hiện có một GPU NVIDIA GeForce RTX 3090, PyTorch 2.11.0+cu128, CUDA dùng được. Không có nhật ký số giờ GPU đã đặt trong ba tuần tới, nên không ghi một con số giờ. Cổng “dưới khoảng 100 giờ thì hoãn B4” chưa chốt bằng lịch. B4 chưa được chạy.

## 6. pyKT

Gói đã cài là `pykt-toolkit` 0.0.38. Bản này có đường xử lý theo câu hỏi: `pykt/preprocess/split_datasets_que.py` và `KTQueDataset`. Thư mục `data/raw/xes3g5m/question_level` đã có `test_quelevel.csv`, `train_valid_sequences_quelevel.csv` và `test_window_sequences_quelevel.csv`. Chưa kiểm số 7.652 câu hỏi trên toàn bộ tệp cửa sổ 2 GB, và chưa huấn luyện lại simpleKT hay DKT-event.
