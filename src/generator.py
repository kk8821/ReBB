"""
generator.py
使用 Claude API (claude-opus-4-6) 生成 Bricks Builder JSON。
支援：文字描述生成、圖片設計圖分析生成、樣式組合。
"""

import base64
import json
import re
import sys
from pathlib import Path
from typing import Any

import anthropic

from src.analyzer import (
    build_style_index,
    format_css_variables_for_prompt,
    format_key_classes_for_prompt,
    load_css_classes,
    load_css_variables,
    load_database,
)
from src.image_handler import list_placeholders, print_placeholder_report
from src.rag import format_retrieved_styles, retrieve, retrieve_by_categories

# ─── 系統 Prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT_TEMPLATE = """你是一位專精 WordPress Bricks Builder 的網頁設計 AI。
你的任務是根據使用者的需求，生成完整、可直接匯入 Bricks Builder 的 JSON 程式碼。

## Bricks Builder JSON 格式規範

### 頂層結構
```json
{{
  "content": [ ...元素陣列... ],
  "source": "bricksCopiedElements",
  "sourceUrl": "https://your-site.com",
  "version": "1.12.3",
  "globalClasses": [ ...此段用到的 class 定義... ],
  "globalElements": []
}}
```

### 元素節點格式
```json
{{
  "id": "六位英數字ID",
  "name": "元素類型",
  "parent": "父元素ID或0",
  "children": ["子元素ID陣列"],
  "settings": {{
    "_cssGlobalClasses": ["class_id_1", "class_id_2"],
    "_cssCustom": "/* 自訂 CSS */"
  }},
  "label": "可選顯示標籤"
}}
```

### 元素類型（name 欄位）
- `section` - 最外層區段（parent=0）
- `container` - 容器/列（彈性盒子或網格）
- `block` - 區塊（常搭配 loop）
- `heading` - 標題（搭配 tag: h1/h2/h3/h4/h5/h6）
- `text` - 段落文字（content 為 HTML）
- `text-basic` - 簡單文字
- `image` - 圖片
- `button` - 按鈕
- `icon` - 圖示
- `divider` - 分隔線
- `form` - 表單
- `accordion` - 手風琴（FAQ 用）
- `tabs` - 標籤頁
- `slider` - 輪播

### ID 命名規則
- 使用 6 位隨機英數字（小寫），例如：`quoavr`, `vvpmfx`, `dnkrih`
- 每個元素 ID 必須唯一

### Hover 與動態效果寫法

**方法 1：Bricks 內建 hover 設定**（在 settings 中直接設定）
```json
{{
  "_background": {{"color": {{"hex": "#7f4afc"}}}},
  "_background:hover": {{"color": {{"hex": "#ff704c"}}}},
  "_border:hover": {{"color": {{"hex": "#ff704c"}}}},
  "_typography:hover": {{"color": {{"raw": "var(--color-light)"}}}}
}}
```

**方法 2：CSS Transition + Transform**（在 _cssCustom 中）
```css
#brxe-ELEMENT_ID {{
  transition: all 0.3s ease;
}}
#brxe-ELEMENT_ID:hover {{
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
}}
```

**方法 3：Global Class 中的 hover CSS**
```json
{{
  "id": "class_id",
  "name": "ren-card-hover",
  "settings": {{
    "_cssCustom": ".ren-card-hover {{ transition: all 0.3s ease; }}\\n.ren-card-hover:hover {{ transform: translateY(-4px); }}"
  }}
}}
```

**方法 4：手風琴/Accordion 動態（icon 旋轉）**
```css
.ren-accordion .brxe-icon {{
  transition: transform 0.3s ease;
}}
.ren-accordion .brx-open .brxe-icon {{
  transform: rotate(90deg);
}}
```

### 常見樣式模式

**按鈕（含 hover）**：
```json
{{
  "id": "btn001",
  "name": "button",
  "settings": {{
    "text": "立即開始",
    "_background": {{"color": {{"raw": "var(--color-primary)"}}}},
    "_background:hover": {{"color": {{"raw": "var(--color-accent)"}}}},
    "_typography": {{"color": {{"raw": "var(--color-light)"}}, "font-weight": "600"}},
    "_padding": {{"top": "var(--spacing-sm)", "right": "var(--spacing-lg)", "bottom": "var(--spacing-sm)", "left": "var(--spacing-lg)"}},
    "_border": {{"radius": {{"top": "4", "right": "4", "bottom": "4", "left": "4"}}}},
    "_cssCustom": "#brxe-btn001 {{ transition: all 0.2s ease; }}\\n#brxe-btn001:hover {{ transform: translateY(-2px); }}"
  }}
}}
```

**卡片（含 hover shadow）**：
在 container/block 的 settings 中：
```json
{{
  "_cssCustom": "#brxe-CARD_ID {{ transition: box-shadow 0.3s ease, transform 0.3s ease; border-radius: var(--radius-sm); }}\\n#brxe-CARD_ID:hover {{ box-shadow: 0 12px 32px rgba(0,0,0,0.12); transform: translateY(-4px); }}"
}}
```

**圖片縮放 hover**：
```json
{{
  "_cssCustom": "#brxe-IMG_ID {{ overflow: hidden; }}\\n#brxe-IMG_ID img {{ transition: transform 0.4s ease; }}\\n#brxe-IMG_ID:hover img {{ transform: scale(1.05); }}"
}}
```

### 響應式設定
在 settings 中加上斷點後綴：
```json
{{
  "_gridTemplateColumns": "var(--grid-3)",
  "_gridTemplateColumns:tablet_portrait": "var(--grid-2)",
  "_gridTemplateColumns:mobile_landscape": "var(--grid-1)"
}}
```

### 圖片佔位符
使用 Renmoe 標準佔位符（之後使用者會替換）：
```json
{{
  "image": {{
    "id": 1,
    "filename": "placeholder.jpg",
    "url": "https://renmoe.com/bricksnativeglobal/wp-content/uploads/2025/01/Renmoe-Library-Placeholder-Image-Half-Width.jpg"
  }}
}}
```

{css_variables}

{key_classes}

## 重要規則
1. 必須輸出完整可用的 JSON，不可截斷
2. globalClasses 必須包含所有用到的 class 完整定義
3. 所有 ID 必須唯一（6位英數字）
4. 優先使用 CSS Variables 確保設計一致性
5. 每個 section 的 parent 必須是 0
6. 子元素的 parent 必須對應正確的父元素 ID
7. Hover 效果是加分項，主動加入使版面更生動
8. 必須包含響應式斷點設定
9. 圖片使用 Renmoe 標準佔位符
10. 輸出格式：只輸出純 JSON，不要有 markdown code block 包裹
"""


def build_system_prompt() -> str:
    """建立含 CSS Variables 和 Classes 的完整系統 prompt"""
    css_vars = load_css_variables()
    css_classes = load_css_classes()

    vars_text = format_css_variables_for_prompt(css_vars)
    classes_text = format_key_classes_for_prompt(css_classes)

    return SYSTEM_PROMPT_TEMPLATE.format(
        css_variables=vars_text,
        key_classes=classes_text,
    )


def generate_bricks_json(
    description: str,
    page_sections: list[str] | None = None,
    style_index: list[dict] | None = None,
    image_path: str | None = None,
    streaming: bool = True,
) -> str:
    """
    根據描述生成 Bricks Builder JSON。

    Args:
        description: 版面需求描述（中文或英文）
        page_sections: 頁面區塊清單，如 ["hero", "content", "cta", "faq"]
                      若為 None，AI 會自行決定
        style_index: 預載的樣式索引（若為 None 則自動載入）
        image_path: 設計圖片路徑（可選，用於視覺參考）
        streaming: 是否使用串流輸出

    Returns:
        Bricks Builder JSON 字串
    """
    client = anthropic.Anthropic()

    # 載入樣式索引
    if style_index is None:
        db = load_database()
        style_index = build_style_index(db)

    # RAG：檢索相關範例
    if page_sections:
        retrieved = retrieve_by_categories(style_index, page_sections, top_k_per_cat=1)
    else:
        retrieved = retrieve(style_index, description, top_k=3)

    examples_text = format_retrieved_styles(retrieved)

    # 建立使用者 prompt
    sections_hint = ""
    if page_sections:
        sections_hint = f"\n\n**頁面結構要求**：\n請依序生成以下區塊：{' → '.join(page_sections)}"

    user_message_text = f"""請為以下需求生成完整的 Bricks Builder JSON：

## 需求描述
{description}
{sections_hint}

## 設計規格要求
- 包含 hover 互動效果（按鈕、卡片、圖片等）
- 使用 CSS Variables 確保設計一致性
- 必須有響應式斷點設定（桌機/平板/手機）
- 圖片使用 Renmoe 標準佔位符
- 版面要美觀、專業、符合現代網頁設計標準

## 參考範例（來自 Renmoe 樣式庫）
以下是最相關的既有樣式，請參考其結構和 global classes 的使用方式，
但要根據需求生成全新的 JSON，不要直接複製：

{examples_text}

## 輸出要求
請輸出完整的 Bricks Builder JSON（可直接匯入使用）。
只輸出純 JSON，開頭為 `{{`，結尾為 `}}`。"""

    # 建立訊息內容（支援圖片輸入）
    message_content: list[dict] = []

    if image_path:
        # 加入設計圖片作為視覺參考
        img_path = Path(image_path)
        if img_path.exists():
            suffix = img_path.suffix.lower()
            media_type_map = {
                ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                ".png": "image/png", ".gif": "image/gif",
                ".webp": "image/webp",
            }
            media_type = media_type_map.get(suffix, "image/jpeg")

            with open(img_path, "rb") as f:
                img_data = base64.standard_b64encode(f.read()).decode("utf-8")

            message_content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": img_data,
                },
            })
            message_content.append({
                "type": "text",
                "text": f"以上是設計參考圖，請根據此視覺風格和以下文字需求生成 JSON：\n\n{user_message_text}",
            })
        else:
            print(f"⚠️  圖片路徑不存在：{image_path}，略過圖片輸入")
            message_content.append({"type": "text", "text": user_message_text})
    else:
        message_content.append({"type": "text", "text": user_message_text})

    system_prompt = build_system_prompt()

    print(f"✅ 找到 {len(retrieved)} 個參考範例：{[r['name'] for r in retrieved]}")
    print("🤖 正在生成 Bricks JSON...")

    if streaming:
        # 串流輸出（適合長輸出，避免 timeout）
        full_text = ""
        print("\n" + "─" * 60)
        with client.messages.stream(
            model="claude-opus-4-6",
            max_tokens=32000,
            thinking={"type": "adaptive"},
            system=system_prompt,
            messages=[{"role": "user", "content": message_content}],
        ) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
                full_text += text
        print("\n" + "─" * 60)
        return full_text
    else:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=32000,
            thinking={"type": "adaptive"},
            system=system_prompt,
            messages=[{"role": "user", "content": message_content}],
        )
        return next(
            (b.text for b in response.content if b.type == "text"),
            ""
        )


def generate_section(
    section_type: str,
    description: str,
    style_index: list[dict] | None = None,
) -> str:
    """
    生成單一頁面區塊的 JSON。

    Args:
        section_type: 區塊類型（hero, content, cta, faq 等）
        description: 此區塊的具體需求

    Returns:
        Bricks JSON 字串
    """
    full_desc = f"[{section_type.upper()} 區塊] {description}"
    return generate_bricks_json(
        description=full_desc,
        page_sections=[section_type],
        style_index=style_index,
    )


def validate_json(json_str: str) -> tuple[bool, str]:
    """
    驗證生成的 JSON 是否有效。

    Returns:
        (is_valid, error_message)
    """
    # 清理可能的 markdown code block
    cleaned = json_str.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
        cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)

        # 檢查必要欄位
        errors = []
        if "content" not in data:
            errors.append("缺少 'content' 欄位")
        if "source" not in data:
            errors.append("缺少 'source' 欄位（應為 'bricksCopiedElements'）")
        if "globalClasses" not in data:
            errors.append("缺少 'globalClasses' 欄位")

        if errors:
            return False, "JSON 結構問題：" + "；".join(errors)

        return True, "✅ JSON 有效"

    except json.JSONDecodeError as e:
        return False, f"JSON 解析錯誤：{e}"


def clean_json_output(raw_output: str) -> str:
    """清理 AI 輸出，提取純 JSON"""
    # 移除 markdown code block
    cleaned = raw_output.strip()
    if "```" in cleaned:
        match = re.search(r"```(?:json)?\n?([\s\S]*?)\n?```", cleaned)
        if match:
            cleaned = match.group(1).strip()

    # 找到 JSON 開頭
    start = cleaned.find("{")
    if start > 0:
        cleaned = cleaned[start:]

    return cleaned


if __name__ == "__main__":
    # 快速測試
    print("🔧 載入樣式資料庫...")
    db = load_database()
    index = build_style_index(db)
    print(f"✅ 載入 {len(index)} 個樣式")

    # 測試生成
    result = generate_bricks_json(
        description="SaaS 產品落地頁的 Hero 區塊，標題、副標題、CTA 按鈕，有背景漸層",
        page_sections=["hero"],
        style_index=index,
        streaming=True,
    )

    is_valid, msg = validate_json(result)
    print(f"\n驗證結果：{msg}")

    if is_valid:
        clean = clean_json_output(result)
        placeholders = list_placeholders(clean)
        print(f"圖片佔位符數量：{len(placeholders)}")
