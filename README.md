# Rail Ops Briefing DSS

營運異常發生時，真正麻煩的不是「多一張圖」，而是值班人員要在短時間內知道：**哪一條線先看、影響多大、哪些動作值得先做**。

這個 repo 把原本單純的 KPI 儀表板往前推一層，加入可驗證的 incident feed、事件去重、影響情境、優先級排序與可直接輸出的 briefing。

> 所有 KPI、事件與事件影響係數都是合成／情境資料。這是決策支援原型，不是臺鐵或任何鐵路公司的正式系統，也不把情境係數包裝成真實營運估計。

## Flow

```text
synthetic KPI panel
        +
incident JSONL
        ↓
validation + dedup
        ↓
active incident window
        ↓
explicit impact assumptions
        ↓
line / peak priority score
        ↓
briefing + Streamlit dashboard
```

## 目前做得到

- 固定 seed 的 route × peak KPI panel
- 事件 schema 驗證：類型、severity、timezone、開始／預估解除時間
- 以 `incident_id` 去重，重複 feed delivery 不會重複加影響
- 只套用在 `as_of` 時刻仍 active 的事件
- 事件對 capacity / delay / risk 的假設係數集中管理，方便 code review
- 將 delay risk、crowding、OTP、active incident 合成透明 priority score
- 產出 Markdown briefing，可放進排程、CI artifact 或營運交班流程
- Streamlit 保留 what-if 操作介面
- `unittest` + GitHub Actions 驗證 deterministic behavior

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python -m unittest discover -s tests -v
python cli.py --out briefing.md
streamlit run app.py
```

CLI 預設會讀 `sample/incidents.jsonl`，在固定 `as_of` 時刻產生可重現的 briefing。

## Incident contract

每一筆事件至少需要：

```json
{
  "incident_id": "inc-001",
  "line": "西部幹線北段",
  "kind": "signal",
  "severity": "major",
  "reported_at": "2026-09-14T07:50:00+08:00",
  "expected_clear_at": "2026-09-14T09:20:00+08:00"
}
```

`kind` 目前接受：

`signal` · `rolling_stock` · `weather` · `track` · `passenger` · `power`

`severity` 使用 `minor / moderate / major`。係數不是從真實營運資料估出來，而是刻意寫死的 scenario assumptions，避免把 demo 說成實證模型。

## 一個刻意修掉的 reproducibility 問題

舊版用 Python `hash(line)` 產生路線偏移。Python 預設會對字串 hash 做 process-level randomization，所以「同一個 seed」在不同 process / CI runner 上不保證得到一樣的資料。

現在改成明確的 `LINE_BIAS` mapping。這個改動很小，但比多加一張圖更重要：**可重現的 demo 才能真的被測試。**

## Project structure

```text
app.py
cli.py
src/
  synthetic_kpis.py   deterministic KPI generator + what-if
  incidents.py        incident contract / dedup / active window
  briefing.py         impact model / ranking / markdown
  recommend.py        dashboard compatibility layer
sample/
  incidents.jsonl
tests/
.github/workflows/test.yml
```

## What this project does not claim

- 不預測真實列車延誤
- 不使用官方即時事件 feed
- 不估計真實 capacity loss
- 不代表任何鐵路營運單位採用
- priority score 是 decision heuristic，不是最佳化器或 ML 模型

這個作品的重點是：資料進來後怎麼保持可重現、怎麼避免重複事件、怎麼把假設寫成能被 review 的規則，以及怎麼把結果壓成值班人員可以快速讀的 briefing。

## License

MIT
