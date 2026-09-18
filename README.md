# Rail Ops Briefing DSS｜鐵道營運簡報決策輔助

> 作者：顧晉瑋（靜宜大學 資訊管理學系）  
> 授權：MIT｜資料：**合成 KPI**（可重現種子）  
> **誠實聲明：學習向作品；與臺鐵數據力企劃相關研究脈絡有關，未宣稱得獎／晉級／正式部署。**

---

## 這是什麼？

一個可互動的 **Streamlit 營運簡報面板**，用合成的路線 × 尖離峰 KPI 展示：

- **延誤風險**、**擁擠代理指標**、準點率（OTP）、平均延誤分鐘  
- **What-if 槓桿**：加掛／運能、調度緩衝、尖峰需求轉移  
- **規則式建議**：依門檻產出當日簡報行動要點（透明、非黑箱）

適合作為備審「決策支援／資料視覺化／營運分析」作品，以及延續鐵道數據主題的**學習練習**。

---

## 與臺鐵數據力企劃的關係

- 本人另有「臺鐵數據力｜數據資料創意發想」海選企劃（見作品集 `competition-lab/tra_data2026/`）。  
- 本 repo 是獨立的 **精簡 DSS 原型**：用合成資料把「簡報面板＋槓桿＋建議」跑通。  
- **請勿解讀為得獎作品或官方合作**；僅記錄學習方向與系統化思考能力。

---

## 快速開始

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

無 UI 的快速煙霧測試：

```bash
python -c "from src.synthetic_kpis import generate_ops_panel, apply_whatif; from src.recommend import briefing_recommendations; df=generate_ops_panel(); print(df.shape); print(briefing_recommendations(df)[0])"
```

---

## 專案結構

```
rail-ops-briefing-dss/
├── app.py                 # Streamlit 儀表板
├── src/
│   ├── synthetic_kpis.py  # 合成 KPI + what-if
│   └── recommend.py       # 規則式建議
├── requirements.txt
├── LICENSE
└── README.md
```

---

## 學習重點

- 營運 KPI 面板設計（風險 × 負荷 × 準點）  
- What-if 敏感度：槓桿如何改變指標  
- 可解釋規則 vs 純預測模型的角色分工  

## 授權

MIT © 2026 顧晉瑋
