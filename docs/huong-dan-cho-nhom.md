# Hướng dẫn cho cả nhóm — Dự án Dự đoán giá nhà (IT5315E)

Tài liệu 1 trang để mọi thành viên nắm mục tiêu, biết đọc gì, chạy gì, và
chuẩn bị gì cho buổi bảo vệ. Chi tiết luôn nằm ở file gốc — đây chỉ là bản đồ.

---

## 1. Mục tiêu

**Câu hỏi kinh doanh:** *"Với đặc điểm và vị trí của một căn nhà, giá thị
trường ước tính là bao nhiêu, và mức độ tin cậy của ước tính đó ra sao?"*

Nhóm đóng vai bộ phận phân tích định giá của một sàn bất động sản, làm trọn
vòng đời một sản phẩm analytics: dữ liệu → EDA → làm sạch → đặc trưng → mô
hình → triển khai (link chạy thật) → giám sát drift → báo cáo/thuyết trình.

**KPI đặt ra:** sai số điển hình ≤ 10% (MAPE), thiên lệch toàn danh mục ≤ 5%,
và khoảng tin cậy phải *phủ đúng* mức đã công bố (80%).

**Điểm số chấm vào độ chặt chẽ từng bước, không chỉ độ chính xác mô hình** —
nên phần "vì sao chọn thế" (DECISIONS.md) quan trọng ngang phần code.

## 2. Kết quả chính (số liệu để phát biểu)

| Hạng mục | Kết quả |
|---|---|
| CV 5-fold (2006–09) | Ridge tốt nhất về điểm: MAPE 8.99% / R² 0.916 |
| Mô hình triển khai | LightGBM quantile: MAPE 9.78% / R² 0.882 (đánh đổi có chủ ý — D14) |
| Khoảng tin cậy | Thô 59% → sau hiệu chỉnh conformal **80.5%** đo được |
| Độ rộng khoảng | ~$35k (nhà điển hình) → ~$78k (nhóm giá cao) |
| Giám sát 2010 | Tín hiệu retrain bật từ 2010-03; bias −7.9% tới tháng 7; coverage 80% → ~73% |
| Làm sạch | 1.472 → 1.458 dòng; 5 loại lỗi được sửa, có bảng before/after |

Link sống: [ứng dụng Streamlit](https://house-price-analytics-tjpb7ntxsd6kzbapp7bymmv.streamlit.app/)
· API FastAPI chạy local: `uvicorn app.api.main:app` → `/docs`.

## 3. Đọc theo thứ tự nào

1. `PROJECT_BRIEF.md` — đề bài gốc (nguồn chân lý, 8 module).
2. `README.md` — cách cài đặt, lệnh chạy, sơ đồ thư mục.
3. `PROGRESS.md` — trạng thái từng phase + số liệu tổng hợp.
4. `DECISIONS.md` — **17 quyết định thiết kế**, viết bằng ngôn ngữ nghiệp vụ.
   Đây là kho câu trả lời cho hội đồng.
5. `DATA_DICTIONARY.md` — 12 trường dữ liệu tổng hợp: kiểu, đơn vị, miền giá
   trị, logic sinh.
6. `reports/slides-outline.md` — kịch bản thuyết trình + phân công người nói.

Sản phẩm nộp: `reports/hust-house-price-final-report.pdf` và
`reports/hust-house-price-slides.pptx` (mẫu HUST chính thức).

## 4. Chạy lại toàn bộ pipeline

Yêu cầu Python 3.11 + dữ liệu Kaggle đặt trong `data/raw/` (không commit theo
quy định cuộc thi). Mọi bước đều cố định seed → kết quả tái lập được.

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

python -m src.data_generation.generate     # M1 dữ liệu tổng hợp
jupyter nbconvert --execute --inplace notebooks/eda_price_drivers.ipynb  # M2
python -m src.cleaning.clean_listings      # M3 làm sạch (in bảng before/after)
python -m src.features.build_model_table   # M4 đặc trưng + kiểm tra VIF
python -m src.modeling.compare_models      # M5 so sánh mô hình 5-fold
python -m src.modeling.train_final         # M5 mô hình quantile + conformal
python -m src.monitoring.run_monitoring    # M7 replay drift năm 2010
pytest tests/                              # 10 test bất biến + smoke app/API

streamlit run app/streamlit_app.py         # chạy tool định giá tại máy
```

Đường dẫn/seed tập trung ở `src/config.py` (RANDOM_SEED=42, holdout từ
2010-01). Đường dự đoán duy nhất dùng chung cho Streamlit và API:
`src/modeling/valuation_service.py`, artifact `models/valuation_model.pkl`.

## 5. Phân công thuyết trình & vùng Q&A

| Người | Slide phụ trách | Cần thuộc |
|---|---|---|
| Đức | 1, 2, 10 (demo), 12 | bài toán, KPI, demo live, khuyến nghị & giới hạn |
| Việt | 3, 4, 7 | chiến lược dữ liệu, độ tin cậy dữ liệu tổng hợp, làm sạch |
| Minh Huyền | 5, 6 | yếu tố dẫn dắt giá, diễn biến thị trường 2006–10 |
| Huyền Trang | 8 | so sánh mô hình, vì sao ship LightGBM thay vì Ridge |
| Cường | 9, 11 | hiệu chỉnh conformal, 4 trigger retrain |

Câu hỏi hội đồng hay gặp → đọc đúng mục trong `DECISIONS.md`: vì sao dùng USD
(D8) · trục thời gian là thật (D11) · vì sao rebound +9.5% (D12) · vì sao
triển khai LightGBM (D14) · vì sao khoảng tin cậy dùng conformal (D5) · vì sao
loại days-on-market (D15) · sự cố Hugging Face (D3).

## 6. Checklist trước buổi bảo vệ

- [ ] T−10 phút: mở link Streamlit một lần cho container free-tier "thức dậy".
- [ ] Backup: chạy `streamlit run app/streamlit_app.py` trên máy người trình
      bày (cùng artifact, không phụ thuộc mạng).
- [ ] Input demo đã chuẩn bị: NAmes / 1.500 sqft / quality 5 (khoảng hẹp) và
      NridgHt / 3.200 sqft / quality 9 / bếp Ex (khoảng rộng + gợi ý thẩm định).
- [ ] Xác nhận app đang chạy mô hình thật (không còn banner 🚧).
- [ ] Mỗi người đã đọc mục DECISIONS thuộc phần mình.

---

**Câu hỏi chưa chốt:** ai giữ máy trình bày chính, và có cần bản in báo cáo
nộp trực tiếp cho hội đồng không?
