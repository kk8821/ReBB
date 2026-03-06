# Renmoe 樣式資料庫使用指南

## 📦 檔案說明

### 1. `renmoe_styles_database.json` (2.12 MB)
**完整資料庫**,包含:
- 264 個樣式的完整 Bricks JSON 程式碼
- 每個樣式的詳細 metadata
- 用於 AI 生成和直接導入 Bricks

**結構**:
```json
{
  "metadata": {
    "total_styles": 281,
    "valid_styles": 264,
    "categories": { "Content": 80, "Hero": 48, ... }
  },
  "styles": [
    {
      "id": "blog_101",
      "name": "Blog 101",
      "category": "Blog",
      "complexity": "medium",
      "metadata": {
        "element_count": 11,
        "features": ["has_image", "has_loop"],
        ...
      },
      "code": "完整的 Bricks JSON..."
    }
  ]
}
```

### 2. `renmoe_styles_index.json` (162 KB)
**輕量級索引**,不含完整程式碼:
- 用於快速搜尋和瀏覽
- 查看樣式的 metadata 不需載入完整資料庫

### 3. `renmoe_styles_catalog.md` (2114 行)
**人類可讀的完整目錄**:
- 按類別組織的所有樣式
- 每個樣式的詳細資訊
- 適合用瀏覽器或 Markdown 閱讀器查看

### 4. `renmoe_styles_quick_ref.md`
**快速查詢表**:
- 表格格式,一眼掃描所有樣式
- 適合快速找到目標樣式

---

## 🔍 查詢範例

### Python 查詢範例
```python
import json

# 載入資料庫
with open('renmoe_styles_database.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

# 範例 1: 找出所有 Hero 樣式
hero_styles = [s for s in db['styles'] if s['category'] == 'Hero']
print(f"找到 {len(hero_styles)} 個 Hero 樣式")

# 範例 2: 找出包含表單的樣式
form_styles = [s for s in db['styles'] 
               if 'has_form' in s['metadata']['features']]
print(f"找到 {len(form_styles)} 個包含表單的樣式")

# 範例 3: 找出複雜度為 simple 的 Contact 樣式
simple_contact = [s for s in db['styles'] 
                  if s['category'] == 'Contact' and s['complexity'] == 'simple']

# 範例 4: 按元素數排序,找出最複雜的 5 個樣式
top_complex = sorted(db['styles'], 
                     key=lambda x: x['metadata']['element_count'], 
                     reverse=True)[:5]
for s in top_complex:
    print(f"{s['name']}: {s['metadata']['element_count']} 個元素")

# 範例 5: 獲取特定樣式的完整 JSON
blog_101 = next(s for s in db['styles'] if s['id'] == 'blog_101')
bricks_code = blog_101['code']
# 現在可以直接複製到 Bricks Builder
```

---

## 🤖 AI 生成工作流程

### 階段 1: 需求分析
使用者輸入: "我需要一個 SaaS 產品的落地頁,包含 Hero、功能介紹、價格表和 FAQ"

### 階段 2: 樣式推薦
AI 分析資料庫,推薦:
- Hero: hero_110 (有背景圖和按鈕)
- Content: content_083 (3 欄式功能介紹)
- Pricing: pricing_789 (帶 CTA 按鈕)
- FAQ: faq_972 (手風琴式)

### 階段 3: 組合生成
將推薦的樣式 JSON 合併,調整:
- 統一配色 (使用 global classes)
- 調整間距
- 替換佔位文字

### 階段 4: 輸出
生成完整的 Bricks JSON,使用者可直接導入

---

## 📋 常見使用情境

### 情境 1: 找特定類型的樣式
**目標**: 找所有 CTA (Call-to-Action) 區塊

**方法**:
1. 打開 `renmoe_styles_catalog.md`
2. 搜尋 "### CTA"
3. 瀏覽該類別下的所有樣式

或用程式:
```python
cta_styles = [s for s in db['styles'] if s['category'] == 'CTA']
```

### 情境 2: 找包含特定功能的樣式
**目標**: 找所有有背景圖的 Hero 區塊

**方法**:
```python
hero_with_bg = [s for s in db['styles'] 
                if s['category'] == 'Hero' 
                and 'has_background_image' in s['metadata']['features']]
```

### 情境 3: 按複雜度篩選
**目標**: 找簡單的 Contact 表單(元素少,容易客製化)

**方法**:
```python
simple_contact = [s for s in db['styles'] 
                  if s['category'] == 'Contact' 
                  and s['complexity'] == 'simple']
```

---

## 🎨 設計系統整合

所有樣式都使用 Renmoe 的 global classes 和 CSS variables:

### Global Classes (來自 `bricks-css-classes.json`)
- `ren-btn`: 按鈕樣式
- `ren-heading-1/2/3`: 標題樣式
- `ren-container-width-lg/sm`: 容器寬度
- `ren-pad-top-bottom-lg`: 間距

### CSS Variables (來自 `bricks-css-variables.json`)
- 顏色: `--color-primary`, `--color-secondary`
- 間距: `--spacing-xs` ~ `--spacing-3xl`
- 字級: `--text-sm` ~ `--text-3xl`

**這意味著**: 
- 改變一個 CSS variable,所有樣式的配色/間距會一致更新
- AI 生成新樣式時,只要使用這些 global classes,就能保持設計一致性

---

## 🚀 下一步

1. **測試查詢**: 用 Python 腳本測試上述範例
2. **建立 AI 提示詞**: 訓練 AI 理解這個資料庫結構
3. **開發生成器**: 輸入需求 → 自動推薦和組合樣式
4. **視覺化**: 建立網頁介面瀏覽所有樣式(配合截圖)

---

## 📞 資料庫維護

### 新增樣式
當 Renmoe 更新時:
1. 從網站複製新樣式的 JSON
2. 加入 Excel 的 Column J
3. 重新執行資料庫建立腳本

### 修正問題樣式
目前有 17 個問題樣式(見 `catalog.md` 底部),可以:
1. 檢查原始 Excel 是否資料不完整
2. 從 Renmoe 網站重新抓取
3. 手動修正 JSON 格式錯誤

---

**建立時間**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**總樣式數**: 264
**資料完整率**: 93.9% (264/281)
