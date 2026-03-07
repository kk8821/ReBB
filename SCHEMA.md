# Bricks Builder 樣式資料庫 Schema

> 版本 1.0 | 2026-03-07 | 264 個樣式

---

## 資料庫檔案清單

| 檔案 | 大小 | 用途 |
|------|------|------|
| `styles_index.json` | ~360 KB | **主要索引**（搜尋/過濾用，不含 code） |
| `styles_index.jsonl` | ~240 KB | 同上，JSONL 格式（每行一筆，適合 grep）|
| `renmoe_styles_database.json` | ~2.3 MB | 完整資料庫（含 Bricks JSON code）|
| `design_tokens.json` | ~5 KB | CSS Variables 設計 Token（顏色/間距/字級）|
| `bricks-css-classes.json` | ~100 KB | Global CSS Classes 原始定義 |
| `bricks-css-variables.json` | ~5 KB | CSS 變數原始定義 |

---

## 樣式索引 Schema（styles_index.json）

```jsonc
{
  // ── 識別 ──────────────────────────────────
  "id": "hero_311",              // 唯一識別碼
  "name": "Hero 693",           // 顯示名稱
  "source": "renmoe_lifetime",  // 來源
  "bricks_version": "1.12.3",

  // ── 分類系統 ──────────────────────────────
  "area": "hero",               // 頁面區域（見區域清單）
  "complexity": "medium",       // simple | medium | complex

  // ── 部件（功能元件）───────────────────────
  "components": ["button", "image"],

  // ── 元素統計 ──────────────────────────────
  "element_count": 11,
  "element_types": {
    "section": 1, "container": 2,
    "heading": 1, "button": 2, "image": 3
  },

  // ── 動態效果 ──────────────────────────────
  "has_dynamics": true,         // 快速篩選用
  "dynamic_effects": [
    "css_hover",
    "hover_background",
    "hover_border",
    "transition",
    "translate"
  ],

  // ── 版面配置 ──────────────────────────────
  "layout": {
    "pattern": "2_col_flex",    // 版面模式
    "columns": 2,               // 欄數 1-4
    "has_loop": false,          // 是否有 WordPress Loop
    "is_responsive": true       // 是否有響應式設定
  },

  // ── 設計特徵 ──────────────────────────────
  "design_features": ["has_button", "has_image"],

  // ── Global Classes ─────────────────────────
  "global_classes": {
    "count": 12,
    "prefix_style": "rl",       // ren | rl | mixed
    "names": ["rl-section-padding-lg", "rl-button-primary"]
  },

  // ── 多維標籤（快速 filter）────────────────
  "tags": ["hero", "button", "image", "css_hover", "transition"]
}
```

---

## 分類系統

### 頁面區域（area）

| area | 中文 | 樣式數 |
|------|------|--------|
| `hero` | 主視覺 | 48 |
| `content` | 內容區 | 80 |
| `cta` | 行動召喚 | 15 |
| `header` | 頁首/導覽 | 20 |
| `footer` | 頁尾 | 10 |
| `faq` | 常見問題 | 10 |
| `testimonial` | 客戶見證 | 11 |
| `gallery` | 圖庫 | 9 |
| `portfolio` | 作品集 | 9 |
| `blog` | 部落格列表 | 8 |
| `pricing` | 定價方案 | 8 |
| `team` | 團隊成員 | 6 |
| `product` | WooCommerce 商品 | 6 |
| `grid` | 純網格版面 | 6 |
| `contact` | 聯絡表單 | 5 |
| `single` | 單篇文章 | 5 |
| `logo` | Logo 展示 | 4 |
| `navbar` | 導覽列 | 4 |

### 部件（components）

| 值 | 說明 |
|----|------|
| `button` | 按鈕 |
| `image` | 圖片 |
| `form` | 表單 |
| `accordion` | 手風琴/FAQ |
| `slider` | 輪播 |
| `tabs` | 標籤頁 |
| `icon` | 圖示 |
| `icon_box` | 圖示+文字組合 |
| `video` | 影片 |
| `testimonial` | 見證引言 |
| `rating` | 星級評分 |
| `counter` | 數字計數器 |
| `social_icons` | 社群圖示 |
| `navigation` | 導覽選單 |
| `logo` | 品牌 Logo |
| `divider` | 分隔線 |
| `list` | 清單 |

---

## 動態效果類型（dynamic_effects）

| 效果值 | 說明 | 實現方式 |
|--------|------|---------|
| `hover_background` | 懸停背景色 | `_background:hover` |
| `hover_border` | 懸停邊框 | `_border:hover` |
| `hover_text_color` | 懸停文字色 | `_typography:hover` |
| `css_hover` | 自訂 CSS hover | `_cssCustom` `:hover` |
| `transition` | 過渡動畫 | `transition: all 0.3s` |
| `rotate` | 旋轉（accordion 圖示）| `rotate(90deg)` |
| `scale` | 縮放（圖片放大）| `scale(1.05)` |
| `translate` | 位移（卡片浮起）| `translateY(-4px)` |
| `hover_shadow` | 懸停陰影 | `:hover { box-shadow }` |
| `hover_opacity` | 懸停透明度 | `:hover { opacity }` |
| `keyframe_animation` | 關鍵影格動畫 | `@keyframes` |

### 常用 Hover 程式碼範例

**Bricks 內建 hover：**
```json
{
  "_background": {"color": {"raw": "var(--color-primary)"}},
  "_background:hover": {"color": {"raw": "var(--color-accent)"}},
  "_border:hover": {"color": {"raw": "var(--color-accent)"}}
}
```

**卡片浮起 + 陰影：**
```css
#brxe-ID { transition: all 0.3s ease; }
#brxe-ID:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0,0,0,0.12);
}
```

**圖片縮放：**
```css
#brxe-WRAP { overflow: hidden; }
#brxe-WRAP img { transition: transform 0.4s ease; }
#brxe-WRAP:hover img { transform: scale(1.05); }
```

**Accordion 旋轉：**
```css
.ren-accordion .brxe-icon { transition: transform 0.3s ease; }
.ren-accordion .brx-open .brxe-icon { transform: rotate(90deg); }
```

---

## 版面模式（layout.pattern）

| 值 | 說明 |
|----|------|
| `1_col` | 單欄垂直 |
| `2_col_flex` | 兩欄 Flexbox |
| `2_col_grid` | 兩欄 Grid |
| `3_col_grid` | 三欄 Grid |
| `4_col_grid` | 四欄 Grid |
| `multi_container` | 多容器組合 |
| `dynamic_loop` | WordPress Loop |
| `slider` | 輪播 |
| `tabs` | 標籤頁 |
| `accordion` | 手風琴 |

---

## 設計 Token（design_tokens.json）

```css
/* 顏色 */
--color-primary:   #7f4afc   /* 主色（紫）*/
--color-secondary: #0f121b   /* 次要（深黑）*/
--color-tertiary:  #535862   /* 輔助（灰）*/
--color-accent:    #ff7652   /* 強調（橘）*/
--color-light:     #ffffff
--color-dark:      #000000
--bg-surface:      #ebeef7

/* 間距（XS 到 3XL） */
--spacing-2xs / --spacing-xs / --spacing-sm
--spacing-md / --spacing-lg / --spacing-xl
--spacing-2xl / --spacing-3xl

/* 字級 */
--text-sm / --text-md / --text-lg
--text-xl / --text-2xl / --text-3xl

/* 網格 */
--grid-1: 1fr
--grid-2: repeat(2, 1fr)
--grid-3: repeat(3, 1fr)
--grid-4: repeat(4, 1fr)
/* ...到 --grid-12 */
```

---

## 查詢範例

### Python
```python
import json

with open('styles_index.json') as f:
    db = json.load(f)
styles = db['styles']

# 找含 hover 效果的 Hero 樣式
hero_hover = [s for s in styles
              if s['area'] == 'hero' and s['has_dynamics']]

# 找 SaaS 落地頁各區塊最佳選擇
for area in ['hero', 'content', 'pricing', 'faq', 'cta']:
    best = [s for s in styles
            if s['area'] == area and s['layout']['is_responsive']]
    print(f"{area}: {best[0]['name'] if best else 'N/A'}")

# 找含表單的樣式
with_form = [s for s in styles if 'form' in s['components']]

# 統計各動態效果使用次數
from collections import Counter
effects = Counter(e for s in styles for e in s['dynamic_effects'])
print(effects.most_common())
```

### Shell grep（JSONL）
```bash
# 找所有 Hero 樣式
grep '"area": "hero"' styles_index.jsonl

# 找含 hover_shadow 效果
grep 'hover_shadow' styles_index.jsonl

# 找有表單的 Contact 樣式
grep '"area": "contact"' styles_index.jsonl | grep '"form"'

# 統計各 area 樣式數
grep -o '"area":"[^"]*"' styles_index.jsonl | sort | uniq -c | sort -rn
```

### AI 生成指令
```bash
python main.py generate "SaaS 落地頁" --sections hero content pricing cta faq
python main.py generate "餐廳網站" --image mockup.png
python main.py search "三欄卡片 hover 效果"
python main.py section hero "雙欄 + 背景漸層 + 兩個 CTA 按鈕"
```

---

## 未來 GitHub 資料庫建議結構

```
bricks-styles-db/
├── README.md
├── SCHEMA.md              ← 本文件
├── styles_index.json      ← 輕量索引（搜尋用）
├── styles_index.jsonl     ← JSONL 索引（grep 用）
├── design_tokens.json     ← CSS Variables
├── global_classes.json    ← Global Class 定義
│
├── styles/                ← 完整樣式（按 area 分資料夾）
│   ├── hero/
│   │   ├── hero_101.json  ← 含完整 Bricks JSON code
│   │   ├── hero_693.json
│   │   └── ...
│   ├── content/
│   ├── cta/
│   └── ...
│
├── previews/              ← 樣式預覽截圖
│   ├── hero_101.png
│   └── ...
│
└── tools/
    ├── main.py            ← AI 生成器 CLI
    ├── src/analyzer.py
    ├── src/rag.py
    ├── src/generator.py
    └── src/image_handler.py
```

### 新增樣式標準格式

```json
{
  "id": "hero_NEW001",
  "name": "Hero XXX",
  "source": "custom",
  "bricks_version": "1.12.3",
  "area": "hero",
  "complexity": "medium",
  "components": ["button", "image"],
  "element_count": 10,
  "element_types": {"section":1,"container":2,"heading":2,"button":1,"image":1},
  "has_dynamics": true,
  "dynamic_effects": ["css_hover", "transition", "translate"],
  "layout": {
    "pattern": "2_col_flex",
    "columns": 2,
    "has_loop": false,
    "is_responsive": true
  },
  "design_features": ["has_button", "has_image"],
  "global_classes": {
    "count": 8,
    "prefix_style": "ren",
    "names": ["ren-pad-top-bottom-lg", "ren-container-width-lg"]
  },
  "tags": ["hero", "button", "image", "css_hover", "transition"]
}
```

---

## 版本紀錄

| 版本 | 日期 | 說明 |
|------|------|------|
| 1.0 | 2026-03-07 | 初始版本，264 個 Renmoe 樣式 |
