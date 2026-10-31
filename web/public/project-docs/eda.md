# EDA, Feature Engineering และการพัฒนา HMM สำหรับราคาทองคำไทย

เอกสารนี้อธิบายผลจากโน้ตบุ๊ก [Dataset A_gold price cleaned.ipynb](../dataset/datset%20a%20gold%20price/Dataset%20A_gold%20price%20cleaned.ipynb) โดยอ้างอิงผลที่บันทึกใน notebook, ไฟล์ [thai_gold_features_v1.csv](../dataset/datset%20a%20gold%20price/data/processed/thai_gold_features_v1.csv) และ [data audit](../dataset/thai-gold-portfolio-simulator/reports/data_audit.md) ไม่ใช่การทดสอบย้อนหลังที่สร้างขึ้นใหม่ ตัวเลขจึงผูกกับ snapshot ข้อมูลซึ่งสิ้นสุดวันที่ 13 ตุลาคม 2026

ภาพรวมขั้นตอนอยู่ใน [แผนภาพ EDA → HMM](eda_pipeline.html); ตารางสำหรับสร้างกราฟซ้ำได้อยู่ในโฟลเดอร์ [eda-chart-data/](eda-chart-data/).

## 1. ขอบเขตข้อมูลและความหมายของแถว

ข้อมูลมาจากประวัติประกาศราคาของสมาคมค้าทองคำ (GTA) ครอบคลุมวันที่ 1 พฤษภาคม 2006 ถึง 13 ตุลาคม 2026 มีข้อมูลก่อนสรุปรายวัน **24,519 ประกาศ** และข้อมูลที่ส่งออกเป็น feature dataset มี **6,261 แถวรายวัน × 31 คอลัมน์** ตัวแปรราคาหลักคือทองคำแท่งรับซื้อ/ขายออก, ทองรูปพรรณ, Gold Spot และ USD/THB

ต้องแยกสองระดับนี้ออกจากกัน:

- **ประกาศระหว่างวัน (intraday):** เก็บแต่ละประกาศไว้ตามเวลาและลำดับ `session` เพื่อวัดการเปลี่ยนแปลงระหว่างประกาศ
- **ชุดข้อมูลรายวัน:** หนึ่งแถวต่อวันที่มีราคา โดยใช้ประกาศสุดท้ายของวันเป็นราคาปิดรายวัน และคำนวณ high/low จากประกาศของวันนั้นสำหรับการทดลอง HMM

การตรวจ timestamp ใน notebook พบ timestamp ซ้ำ **8 กลุ่ม** ในข้อมูลประกาศ; จึงไม่ควรลบแถวจาก timestamp ซ้ำอย่างเดียว เพราะประกาศที่เวลาเดียวกันอาจมีราคา/ลำดับ session ต่างกัน การเรียงตาม `timestamp_parsed` และ `session` ทำให้การเลือกประกาศท้ายวันมีลำดับแน่นอน ส่วนข้อมูล feature ที่ export แล้วมีหนึ่งแถวต่อวันและไม่พบ date ซ้ำใน audit ของไฟล์นั้น ตัวเลข duplicate ของ raw notebook จึงไม่ขัดกับผลตรวจไฟล์ daily

ช่วงข้อมูลครอบคลุมปฏิทิน 7,471 วัน แต่มีวันประกาศราคาที่ใช้ได้ 6,261 วัน; วันที่ไม่มีราคาโดยมากเป็นวันหยุดหรือวันที่ไม่มีการประกาศ ไม่ได้ถูกเติมเป็นแถวสังเคราะห์ ข้อมูลจบกลางปี 2026 จึงเป็นปีบางส่วน ไม่ควรเทียบจำนวนวันของปี 2026 กับปีเต็ม

## 2. ผล EDA และการตรวจคุณภาพ

### 2.1 การเคลื่อนไหวของระดับราคา

กราฟราคาทองคำแท่งรายวันแสดงการเปลี่ยนแปลงของ **ระดับราคาเป็น THB ต่อหนึ่งบาทน้ำหนัก (15.244 กรัม; ความบริสุทธิ์ 96.5%) ตามราคา GTA** ในช่วงยาวกว่า 20 ปี โดยราคาทองแท่งรับซื้อในไฟล์อยู่ระหว่าง **10,050–81,400 บาท** การดูกราฟระดับราคาอย่างเดียวไม่เหมาะกับการเทียบความผันผวนระหว่างช่วงที่ฐานราคาต่างกันมาก จึงสร้างผลตอบแทนแบบ log return เพิ่มสำหรับการวิเคราะห์ข้ามเวลาและข้ามตลาด

ในข้อมูลรายวัน 6,261 แถว ค่า `gold_spot_clean` หาย **540 แถว** และ `thb_usd_clean` หาย **691 แถว** ขณะที่ราคา quote หลักของทองคำไทยมีครบใน snapshot นี้ การเก็บ missing ไว้สำคัญกว่าการทำให้ตารางดูเต็ม: forward-fill อาจสร้างการเปลี่ยนแปลงเป็นศูนย์เทียมและกด volatility/correlation ให้ต่ำลง

### 2.2 Intraday change และ daily change

โน้ตบุ๊กคำนวณ change ของทองคำแท่ง, ทองรูปพรรณ, Spot และ FX สองระดับ:

- **Intraday change:** ราคาประกาศปัจจุบันลบราคาประกาศก่อนหน้าในวันเดียวกัน; เปอร์เซ็นต์ change หารด้วยราคาก่อนหน้าแล้วคูณ 100
- **Daily change:** ราคาประกาศสุดท้ายของวันลบราคาประกาศสุดท้ายของวันประกาศก่อนหน้า; ใช้หลักเดียวกันสำหรับเปอร์เซ็นต์ change

ค่าที่หายของ `bar_buy_change_intraday` จำนวน **6,261 ค่า** เป็นแถวแรกของแต่ละวันทั้งหมด (มี 6,261 วัน) ไม่ใช่ missing ที่ผิดพลาด; แถวแรกไม่มีประกาศก่อนหน้าในวันเดียวกันให้เปรียบเทียบ ส่วน `bar_buy_change_daily` หายหนึ่งค่าเพราะวันแรกไม่มีวันก่อนหน้าในชุดข้อมูล

### 2.3 ผลตอบแทนรายวันและการกระจายตัว

ผลตอบแทนใช้ log return ระหว่างราคาวันที่มีข้อมูลติดกัน (ไม่ใช่ทุกวันปฏิทิน):

| ผลตอบแทน | จำนวนค่าที่ใช้ได้ | ค่าเฉลี่ย | ส่วนเบี่ยงเบนมาตรฐาน | มัธยฐาน | ต่ำสุด | สูงสุด |
|---|---:|---:|---:|---:|---:|---:|
| ทองคำไทย (`thai_gold_return`) | 6,260 | 0.000281 | 0.008270 | 0.000000 | -0.119844 | 0.074901 |
| Gold Spot (`global_gold_return`) | 5,189 | 0.000216 | 0.011028 | 0.000360 | -0.115849 | 0.105241 |
| USD/THB (`usd_thb_return`) | 4,936 | -0.000005 | 0.003820 | 0.000000 | -0.029687 | 0.030629 |

ค่าผลตอบแทนเป็นสัดส่วน ไม่ใช่เปอร์เซ็นต์ เช่น 0.01 เท่ากับประมาณ 1% สำหรับ log return เมื่อค่าเปลี่ยนไม่มาก การกระจายมีทั้งค่าศูนย์และค่าปลายหาง จึงรายงานทั้งมัธยฐาน/ควอไทล์และ extreme values แทนการอธิบายตลาดด้วยค่าเฉลี่ยอย่างเดียว ผลลัพธ์นี้เป็นคำอธิบายข้อมูล ไม่ใช่การทดสอบว่าผลตอบแทนคงที่หรือแจกแจงปกติ

### 2.4 ความสัมพันธ์ระหว่างทองไทย ทองโลก และค่าเงิน

คำนวณ Pearson (ความสัมพันธ์เชิงเส้น) และ Spearman (ความสัมพันธ์เชิงอันดับ) แบบ pairwise โดยตัดเฉพาะแถวที่คู่ตัวแปรนั้นขาดข้อมูล:

| คู่ตัวแปร | จำนวนคู่ข้อมูล | Pearson r | Spearman ρ |
|---|---:|---:|---:|
| ทองไทย – Gold Spot | 5,189 | 0.9249 | 0.8948 |
| ทองไทย – USD/THB | 4,936 | -0.1582 | -0.1791 |
| Gold Spot – USD/THB | 4,935 | -0.4519 | -0.5121 |

ผลใน snapshot นี้ชี้ว่าผลตอบแทนทองไทยเคลื่อนไหวไปในทิศเดียวกับ Gold Spot ค่อนข้างสูง ขณะที่ความสัมพันธ์กับ USD/THB มีขนาดเล็กกว่าและเป็นลบ; Gold Spot กับ USD/THB มีความสัมพันธ์ลบระดับปานกลาง ข้อสังเกตนี้ **ไม่ใช่หลักฐานเหตุและผล** และจำนวนตัวอย่างของแต่ละคู่ไม่เท่ากันเพราะข้อมูล Spot/FX ขาดหาย

มีการคำนวณ rolling correlation แบบหน้าต่าง 60 observations โดยกำหนดข้อมูลคู่ที่ใช้ได้อย่างน้อย 30 จุด ผลสรุป rolling median Pearson คือทองไทย–Gold Spot **0.9388**, ทองไทย–USD/THB **-0.1707**, และ Gold Spot–USD/THB **-0.5163** จึงเห็นได้ว่าความสัมพันธ์เปลี่ยนตามเวลาได้; ค่ารวมทั้งช่วงไม่ควรถูกนำไปใช้แทนความสัมพันธ์เฉพาะ regime

### 2.5 Missingness และข้อควรระวังในการตีความ

missing ของ Spot/FX ส่งต่อไปยัง returns, volatility, correlation และ residual โดยไม่ impute ตัวอย่างเช่นไฟล์ `thai_gold_features_v1.csv` มี missing 540 จุดใน Spot และ 691 จุดใน FX; feature ที่อนุพันธ์จาก FX-adjusted residual จึงหาย **1,326 จุด** และ rolling volatility 60 วันของ FX/residual หาย **3,974 จุด** การหายเพิ่มขึ้นเป็นผลจากทั้ง source gaps และข้อกำหนดว่าหน้าต่าง rolling ต้องมีข้อมูลครบ ไม่ได้หมายความว่าราคาทองไทยหายตามไปด้วย

ใน EDA ยังมีการวาด time series, histogram, boxplot และ correlation heatmap เพื่อตรวจ trend, การกระจาย, outliers และการเปลี่ยนความสัมพันธ์ แต่ notebook ไม่ได้ทำ formal stationarity test, hypothesis test ที่ปรับ multiple comparisons หรือกำหนด causal model ดังนั้นไม่ควรใช้กราฟ/ค่า correlation เหล่านี้กล่าวอ้าง causal effect หรือความสามารถพยากรณ์

## 3. Feature engineering ที่ทำ

ไฟล์ `thai_gold_features_v1.csv` มี 31 คอลัมน์ แบ่งได้เป็นราคาต้นทาง/metadata และ engineered features ด้านล่าง การคำนวณเรียงตามวันที่และเก็บ missing ตามต้นทาง; ค่า `valid_price_pair` เป็น flag ว่าคำนวณ price change เทียบจุดอ้างอิงได้หรือไม่ ไม่ใช่เกณฑ์ตัดแถวราคาออก

### 3.1 ผลตอบแทนและการแยกองค์ประกอบตลาด

กำหนด \(P_t\) เป็นราคาปิดท้ายวันของชุดราคาที่เกี่ยวข้อง:

- `thai_gold_return` = \(\ln(bar\_buy_t / bar\_buy_{t-1})\)
- `global_gold_return` = \(\ln(spot_t / spot_{t-1})\)
- `usd_thb_return` = \(\ln(fx_t / fx_{t-1})\)
- `global_plus_fx_return` = `global_gold_return + usd_thb_return` เป็น baseline เชิงบวกขององค์ประกอบทองโลกกับ FX ในหน่วย log return
- `thai_minus_global_return` = `thai_gold_return - global_gold_return` แสดงส่วนต่างทองไทยกับทองโลก
- `fx_adjusted_residual` = `thai_gold_return - global_gold_return - usd_thb_return` เป็น residual เชิงวินิจฉัยหลังหักองค์ประกอบสองตัว

`global_plus_fx_return` และ residual เป็นการบวก/ลบ return เพื่อสำรวจ decomposition ไม่ใช่สมการตีราคาเต็มรูปแบบ: ยังไม่ได้ calibrate ด้วยหน่วย/สัญญา/เวลา quote, premium, spread, ภาษี หรือค่าคงที่ และไม่ควรตีความ residual เป็น mispricing หรือกำไรที่ทำได้จริง

### 3.2 Rolling volatility

ใช้ sample standard deviation (`pandas rolling.std`, `ddof=1`) ของผลตอบแทนในหน้าต่างย้อนหลัง:

- หน้าต่าง **20 และ 60 observations** สำหรับทองไทย, Gold Spot, FX และ `fx_adjusted_residual` ในไฟล์ feature หลัก
- หน้าต่าง **5 และ 20 observations** ในการวิเคราะห์ Phase D เพิ่มเติมเพื่อดูความผันผวนระยะสั้นเทียบระยะกลาง
- `min_periods` เท่ากับขนาดหน้าต่างใน volatility หลัก จึงไม่แสดงค่าจนกว่าจะมีข้อมูลครบ; Phase D ก็ใช้ `min_periods=window`

คำว่า “วัน” ในชื่อ feature สื่อถึงแถวรายวัน/observations ไม่ได้เติมวันปฏิทินที่ไม่มีราคาเข้าไป หน้าต่างจึงนับวันสังเกตการณ์ที่มีแถวข้อมูล

### 3.3 Rolling correlation และ robust residual score

- `corr_thai_global_60d`: rolling Pearson correlation 60 แถวระหว่างผลตอบแทนทองไทยกับ Gold Spot; ขั้นต่ำ 30 คู่ข้อมูล
- `corr_thai_global_fx_60d`: rolling Pearson correlation ระหว่างผลตอบแทนทองไทยกับ `global_plus_fx_return` ด้วยหน้าต่าง 60 และขั้นต่ำ 30 observations
- `residual_robust_z_60d`: ใช้ rolling median และ median absolute deviation (MAD) ในหน้าต่าง 60 จุด (ขั้นต่ำ 30) แล้วคำนวณ \(0.67448975 \times (residual - median) / MAD\); หาก MAD เป็นศูนย์จะคงค่าเป็น missing

robust z-score ใช้ชี้ residual ที่ผิดจากพฤติกรรมใกล้เคียงในอดีตเพื่อการตรวจสอบ ไม่ได้เป็นการทดสอบ outlier แบบยืนยัน และไม่ได้เป็น trigger ซื้อขาย

### 3.4 ตรวจสอบผลลัพธ์ก่อน export

feature pipeline บันทึกทั้งข้อมูลต้นทาง flags (`price_changed`, `valid_price_pair`, `is_first_session`, `data_quality_flag`) และคอลัมน์คำนวณไว้ใน CSV/Parquet เพื่อย้อนรอยได้ การ audit ที่ทำกับ snapshot ปัจจุบันยืนยัน 6,261 rows, 31 columns, ไม่มี date ซ้ำ, quote ทองไทยหลักไม่ missing และยังคง null ของ Spot/FX/derived columns ไว้ การ export ไม่เติมข้อมูลตลาดที่ขาด

## 4. การพัฒนาและคัดเลือก Gaussian HMM

### 4.1 เป้าหมายและตัวแปรเข้า

HMM ใช้จัดกลุ่มพฤติกรรมตลาดที่ซ่อนอยู่จากลำดับข้อมูล ไม่ได้เรียนรู้ป้ายกำกับวิกฤต/ขาขึ้น/ขาลง เพราะไม่มี supervised labels ที่ผ่านการยืนยัน:

1. `bar_buy_log_return` = log(ราคาทองแท่งรับซื้อท้ายวัน / ราคาท้ายวันของวันประกาศก่อนหน้า)
2. `intraday_range_pct` = (ราคาสูงสุดประกาศในวันนั้น − ราคาต่ำสุด) / ราคาแรกของวัน

`intraday_range_pct` ใช้ข้อมูลประกาศทั้งหมดของวันนั้น จึงเป็นข้อมูลที่รู้เมื่อวันนั้นสิ้นสุดแล้ว เหมาะกับการจัด regime ณ สิ้นวัน ไม่ใช่สัญญาณที่รับประกันว่าจะคำนวณได้ก่อนปิดวัน โมเดลใช้ 6,260 observations หลังตัดแถวแรกที่ยังไม่มี return; matrix ที่ใช้ fit ไม่มี missing

### 4.2 ลำดับการฝึกและการเลือกจำนวน states

1. เรียงตามเวลาและแบ่งแบบ chronological: train 70% (**4,382**, 2006-05-02–2020-10-28), validation 15% (**939**, 2020-10-29–2023-10-28), test 15% (**939**, 2023-10-30–2026-10-13)
2. Fit `StandardScaler` เฉพาะ train แล้วใช้ scaler เดิมแปลง validation/test เพื่อไม่ให้ค่าเฉลี่ย/ส่วนเบี่ยงเบนจากอนาคตรั่วเข้า train
3. ฝึก `hmmlearn.GaussianHMM` แบบ diagonal covariance, candidates \(K=2,3,4\), seeds 11/21/42, iteration limit 200, tolerance \(10^{-3}\), `min_covar=10^{-3}` และ log implementation
4. สำหรับแต่ละ K เก็บ fit ที่มี train likelihood สูงสุดจาก seeds ที่รันสำเร็จ แล้วเลือก K ด้วย **validation predictive log-likelihood ต่อแถว** ซึ่งคำนวณแบบ forward filtering พร้อมส่ง posterior ท้าย train ไปเริ่ม validation
5. ประเมิน test ตามลำดับเวลาโดยส่ง filtered state distribution จาก train → validation → test; วิธีนี้ใช้ข้อมูลอดีตและ observation ปัจจุบัน ไม่ใช้ future observations ในการคำนวณ posterior ของแถวนั้น

ผลการเลือก baseline:

| จำนวน states K | Seed ที่ชนะใน K | Validation predictive log-likelihood/row | ผล |
|---:|---:|---:|---|
| 2 | 11 | -1.710718 | ไม่เลือก |
| 3 | 42 | **-0.883659** | เลือก |
| 4 | 21 | -1.643224 | ไม่เลือก |

ค่า log-likelihood ที่มากกว่า/ติดลบน้อยกว่าเป็นผลดีกว่าภายใต้ชุด feature และวิธีประเมินเดียวกัน ผล test ของ baseline K=3 เท่ากับ **-1.892303 ต่อแถว** บน 939 observations ส่วน train score ต่อแถวเท่ากับ -0.314882 ความแตกต่างระหว่าง train กับ validation/test เป็นเหตุให้ต้องระวัง overfit และ regime shift; ไม่ใช่ “accuracy” หรือสัดส่วนการทายถูก

### 4.3 ความหมายของสาม state

state ID ของ HMM ไม่มีความหมายเรียงลำดับในตัว โมเดลจึงเรียง state จากค่าเฉลี่ย `intraday_range_pct` แบบ posterior-weighted บน train และตั้งชื่อเพื่ออธิบายเท่านั้น:

| ป้ายอธิบาย | Weighted mean log return (train) | Weighted mean intraday range | Posterior mass บน train |
|---|---:|---:|---:|
| low-range | 0.000464 | 0.000000 (0.000%) | 41.1% |
| mid-range | 0.000372 | 0.003298 (0.330%) | 45.6% |
| high-range | -0.001180 | 0.008826 (0.883%) | 13.3% |

high-range ใน train มี range เฉลี่ยสูงกว่าและผลตอบแทนเฉลี่ยติดลบในตัวอย่างนี้ จึงเป็น candidate สำหรับตรวจสอบเหตุการณ์ ไม่ใช่ข้อพิสูจน์ว่าเป็น crisis state, คำทำนายทิศทาง หรือ signal ซื้อ/ขาย ป้าย low/mid/high ถูกกำหนดจาก range ใน train; state IDs อาจสลับได้เมื่อฝึกโมเดลใหม่

### 4.4 ทางเลือกที่ทดลองและเหตุผลที่ยังไม่เลือก

| แบบทดลอง | รายละเอียดผลที่บันทึก | ข้อสรุป |
|---|---|---|
| Baseline Gaussian HMM | 2 features, K=3; validation -0.883659 และ test -1.892303 ต่อแถว | เลือกเป็น baseline ที่บันทึกไว้; fit selection ใช้เวลาประมาณ 6.93 วินาทีใน run ของ notebook |
| EGARCH + HMM | เพิ่ม `egarch_sigma_pct` เป็น feature ที่สาม; เลือก K=4; validation -1.651751, test -2.734749 | ไม่ชนะ baseline ในผลชุดนี้ แต่ **ห้ามเทียบ density score ตรง ๆ อย่างเด็ดขาด** เพราะจำนวน dimensions ต่างกัน; เป็นสัญญาณให้ทดลองอย่างควบคุมเพิ่ม ไม่ใช่หลักฐานตัดสินจากคะแนนเพียงตัวเดียว |
| AH-HMM-inspired prototype | 2 meta-regimes × 3 market regimes; EM ถึง iteration cap 30; validation -1.637820, test -2.502737 | prototype มี transition structure ซับซ้อนกว่าแต่คะแนนที่บันทึกต่ำกว่า baseline; matrices ของ market regimes สอง meta-regimes ในผลนี้เหมือนกัน จึงยังไม่มีหลักฐานว่าชั้น meta-regime เพิ่มประโยชน์ |
| PyTorch Gaussian HMM บน GPU | K=3, EM 20 iterations; output ใน cell เปรียบเทียบรายงาน GPU fit 48.753s, CPU `hmmlearn` reference 0.189s; validation -1.636500 เทียบ -1.704222 และ test -2.496296 เทียบ -2.601768 | GPU implementation ช้ากว่าใน workload นี้และ score ต่างกันเพียงเล็กน้อย; initialization/implementation ไม่เหมือนกัน จึงไม่ใช่ controlled speedup หรือหลักฐานว่า GPU ทำให้โมเดลแม่นกว่า |

**ความไม่สอดคล้องใน notebook:** Markdown สรุปผลที่ cell 89 ระบุเวลา GPU 84.11s และ CPU 0.245s แต่ output ที่บันทึกใน cell เปรียบเทียบภายหลังระบุ 48.753s และ 0.189s จึงไม่ควรนำตัวเลขเวลา GPU/CPU ไปอ้างโดยไม่ระบุว่าอ้าง cell ใด เอกสารนี้ยึดตาราง output ที่บันทึกใน cell เปรียบเทียบ และชี้ความคลาดเคลื่อนนี้ไว้เพื่อไม่กลบปัญหา provenance

### 4.5 ข้อจำกัดของการประเมินและการนำไปใช้

- ไม่มี ground-truth regime labels จึงไม่มี accuracy, precision/recall ของ “ทำนายวิกฤต” ให้รายงาน คะแนนที่ใช้เป็น density/predictive log-likelihood เท่านั้น
- มีการทดลองหลาย model variants และรายงานคะแนน test ใน notebook เดียวกัน; test split นี้จึงควรมองเป็น **ผลเปรียบเทียบเชิงพัฒนา** ไม่ใช่ final untouched benchmark สำหรับประกาศประสิทธิภาพทั่วไป
- การเลือกสาม states อาศัยข้อมูลราคาสอง feature; ไม่ได้พิสูจน์ความสามารถพยากรณ์ราคาในอนาคตหรือช่วยทำกำไรหลังค่าธรรมเนียม/spread
- `model/gold_hmm_v1/metadata.json` ระบุ 3 states, feature 2 ตัว, `hmmlearn`, CPU และข้อจำกัดว่า states เป็น statistical regimes ไม่ใช่ crisis labels/standalone trading signal
- ฟังก์ชันทดลอง `inspect_market_regime` ใน notebook เรียก `predict_proba` กับ observation เดี่ยว และมี warning ว่าไม่เทียบเท่าการกรองตามลำดับเวลาเต็มชุด การใช้งานแบบ sequential ต้องใช้ข้อมูลตามลำดับและ filtered posterior ไม่ควรตีความ probability จาก one-row helper เป็น state history ที่สมบูรณ์

## 5. สรุป

EDA ยืนยันว่ามีประวัติราคาทองคำไทยรายวันยาวกว่า 20 ปี พร้อมข้อมูล Gold Spot และ FX ที่มีช่องว่างจริง การสร้าง returns, rolling volatility/correlation และ FX-adjusted residual ทำให้ตรวจแยกการเคลื่อนไหวและความเสี่ยงได้มากกว่าดูระดับราคา แต่ missingness ทำให้ sample ของแต่ละ feature ต่างกัน และความสัมพันธ์ที่พบยังเป็น descriptive association

Gaussian HMM แบบ 3 states เป็น baseline ที่ดีที่สุดตาม validation predictive log-likelihood ในชุดทดลอง 2-feature นี้ โดยใช้เฉพาะ return และ intraday range อย่างไรก็ตามผลนี้ยังเป็นการแบ่งกลุ่มเชิงสถิติ ต้องทดสอบความเสถียรข้ามช่วงเวลาและเทียบกับเหตุการณ์ที่มนุษย์ตรวจแล้วก่อนนำไปเรียก regime วิกฤตหรือใช้ตัดสินใจลงทุน

## 6. ชุดข้อมูลพร้อมสร้างกราฟ

ไฟล์ใน [eda-chart-data/](eda-chart-data/) เป็น CSV แบบ tidy แยกตามวัตถุประสงค์ เพื่อให้นำไปใช้กับ Python, R, Excel หรือเครื่องมือ dashboard ได้โดยไม่ต้องดึงค่าจากย่อหน้าเอกสาร:

| ไฟล์ | กราฟที่เหมาะ | คอลัมน์หลัก | ข้อควรระวัง |
|---|---|---|---|
| [annual_gold_price.csv](eda-chart-data/annual_gold_price.csv) | เส้นราคา year-end; ช่วง min–max ต่อปี; trend ของราคาเฉลี่ย | `year`, `year_end_thb`, `observed_low_thb`, `observed_high_thb`, `mean_thb`, `quote_days` | `year_open_thb`/`year_end_thb` คือ quote แรก/สุดท้ายที่สังเกต ไม่ใช่ทุกวัน; ปี 2006 และ 2026 เป็นปีบางส่วน |
| [return_summary.csv](eda-chart-data/return_summary.csv) | Dot/bar เปรียบเทียบ volatility (`stddev`) และช่วง Q25–Q75; ตาราง descriptive stats | `feature`, `valid_n`, `mean`, `stddev`, `q25`, `median`, `q75`, `min`, `max` | ค่าผลตอบแทนเป็น log-return fraction; คูณ 100 หากต้องการแสดงเป็นเปอร์เซ็นต์ |
| [cross_market_correlations.csv](eda-chart-data/cross_market_correlations.csv) | Diverging bar ของ Pearson/Spearman รอบศูนย์ | `pair`, `n_pairs`, `pearson_r`, `spearman_rho` | แกน coefficient ต้องอยู่ระหว่าง -1 ถึง +1; แสดงจำนวนคู่ข้อมูล เพราะแต่ละคู่มี missing ไม่เท่ากัน |
| [missingness_summary.csv](eda-chart-data/missingness_summary.csv) | Horizontal bar เรียงตาม missing percentage | `feature`, `missing_n`, `rows`, `missing_pct` | เปรียบเทียบได้ในฐาน 6,261 rows; missing ของ rolling feature รวม source gaps และช่วง warm-up ที่ยังมีข้อมูลไม่ครบ |
| [hmm_validation_scores.csv](eda-chart-data/hmm_validation_scores.csv) | Bar เปรียบเทียบ validation predictive log-likelihood ต่อแถวตาม K | `states_k`, `val_predictive_loglik_per_row`, `best_seed`, `iterations` | ใช้คะแนนบน validation เท่านั้นเพื่อเลือก K; คะแนนที่สูงกว่า/ติดลบน้อยกว่าดีกว่า ห้ามเรียก accuracy |
| [hmm_state_profiles.csv](eda-chart-data/hmm_state_profiles.csv) | Dot/bar แยก state สำหรับ weighted mean range, return และ train posterior mass | `range_label`, `weighted_mean_log_return`, `weighted_mean_intraday_range_pct`, `train_posterior_mass_pct` | แต่ละ metric มีหน่วยต่างกัน ควรทำคนละ panel; ป้าย state เรียงจาก range ใน train ไม่ใช่ป้ายวิกฤต |

ตัวอย่างการโหลดด้วย pandas:

```python
import pandas as pd

annual = pd.read_csv("md/eda-chart-data/annual_gold_price.csv")
correlations = pd.read_csv("md/eda-chart-data/cross_market_correlations.csv")
hmm_selection = pd.read_csv("md/eda-chart-data/hmm_validation_scores.csv")
```

ค่าภายในไฟล์เหล่านี้มาจาก feature CSV หรือ output ที่บันทึกไว้ของ notebook ตามคำอธิบายแต่ละชุด ไม่ได้สร้าง observation ใหม่; หากอัปเดต source data หรือฝึกโมเดลใหม่ ต้องสร้างชุดสรุปเหล่านี้ใหม่ก่อนนำไปเผยแพร่