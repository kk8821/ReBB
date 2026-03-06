"""
analyzer.py
載入並解析 Renmoe 樣式資料庫，建立可搜尋的索引。
"""

import json
import re
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent.parent

# 動態效果關鍵字分類
DYNAMIC_FEATURES = {
    "hover_bg": "_background:hover",
    "hover_border": "_border:hover",
    "css_hover": ":hover",
    "transition": "transition",
    "transform": "transform",
    "animation": "animation",
    "rotate": "rotate",
    "scale": "scale(",
}

# 版面類型關鍵字對應
LAYOUT_KEYWORDS = {
    "hero": ["hero", "landing", "banner", "首頁", "主視覺", "橫幅"],
    "content": ["content", "feature", "功能", "內容", "特色", "服務"],
    "cta": ["cta", "call to action", "call-to-action", "行動召喚", "按鈕區"],
    "faq": ["faq", "常見問題", "accordion", "手風琴"],
    "pricing": ["pricing", "price", "方案", "定價", "價格"],
    "testimonial": ["testimonial", "review", "評價", "見證", "口碑"],
    "blog": ["blog", "post", "article", "文章", "部落格"],
    "contact": ["contact", "form", "聯絡", "表單"],
    "header": ["header", "navigation", "nav", "導覽", "頁首"],
    "footer": ["footer", "頁尾"],
    "gallery": ["gallery", "photo", "圖庫", "相片"],
    "portfolio": ["portfolio", "works", "作品集", "作品"],
    "team": ["team", "member", "staff", "團隊", "成員"],
    "logo": ["logo", "品牌", "標誌"],
    "grid": ["grid", "layout", "網格", "排版"],
}


def load_database() -> dict[str, Any]:
    """載入主要樣式資料庫"""
    db_path = DATA_DIR / "renmoe_styles_database.json"
    with open(db_path, encoding="utf-8") as f:
        return json.load(f)


def load_css_variables() -> list[dict]:
    """載入 CSS 變數定義"""
    path = DATA_DIR / "bricks-css-variables.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("variables", [])


def load_css_classes() -> list[dict]:
    """載入 CSS Class 定義"""
    path = DATA_DIR / "bricks-css-classes.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def detect_dynamic_features(code_str: str) -> list[str]:
    """檢測樣式中的動態效果類型"""
    features = []
    for feat_name, keyword in DYNAMIC_FEATURES.items():
        if keyword in code_str:
            features.append(feat_name)
    return features


def build_style_index(db: dict[str, Any]) -> list[dict[str, Any]]:
    """
    為每個樣式建立可搜尋的索引記錄。
    回傳格式：[{id, name, category, complexity, features, dynamic_features,
                element_types, keywords, code}, ...]
    """
    index = []
    for style in db.get("styles", []):
        code_str = style.get("code", "")
        meta = style.get("metadata", {})

        # 提取動態效果
        dynamic = detect_dynamic_features(code_str)

        # 建立搜尋關鍵字集合
        keywords = set()
        keywords.add(style.get("category", "").lower())
        keywords.add(style.get("name", "").lower())
        keywords.add(style.get("complexity", "").lower())
        for feat in meta.get("features", []):
            keywords.add(feat.replace("has_", "").replace("_", " "))
        for et in meta.get("element_types", {}).keys():
            keywords.add(et)

        index.append({
            "id": style["id"],
            "name": style["name"],
            "category": style.get("category", ""),
            "complexity": style.get("complexity", "medium"),
            "features": meta.get("features", []),
            "dynamic_features": dynamic,
            "element_types": meta.get("element_types", {}),
            "element_count": meta.get("element_count", 0),
            "has_responsive": meta.get("has_responsive_settings", False),
            "keywords": keywords,
            "code": code_str,
        })
    return index


def format_css_variables_for_prompt(variables: list[dict]) -> str:
    """將 CSS 變數格式化成 prompt 用的字串"""
    lines = ["## Renmoe CSS Variables (設計 Token)"]

    # 依類型分組
    groups: dict[str, list] = {
        "顏色": [], "間距": [], "字級": [],
        "網格": [], "寬度": [], "其他": [],
    }
    for v in variables:
        name = v["name"]
        val = v["value"]
        entry = f"  --{name}: {val}"
        if "color" in name or "bg" in name:
            groups["顏色"].append(entry)
        elif "spacing" in name:
            groups["間距"].append(entry)
        elif "text" in name or "font" in name:
            groups["字級"].append(entry)
        elif "grid" in name:
            groups["網格"].append(entry)
        elif "width" in name or "page" in name:
            groups["寬度"].append(entry)
        else:
            groups["其他"].append(entry)

    for group, entries in groups.items():
        if entries:
            lines.append(f"\n### {group}")
            lines.extend(entries)
    return "\n".join(lines)


def format_key_classes_for_prompt(classes: list[dict]) -> str:
    """將最常用的 Global Class 格式化成 prompt 用的字串"""
    lines = ["## 常用 Global Classes"]

    # 挑選最常見、最有代表性的 class
    priority_keywords = [
        "ren-btn", "ren-heading", "ren-container-width",
        "ren-pad-top-bottom", "ren-pad-", "ren-gap-",
        "ren-text-", "ren-grid-", "ren-aspect-",
        "ren-position-", "ren-full-width", "ren-object-fit",
        "ren-margin-", "ren-min-height", "ren-accordion",
        "ren-bg-", "ren-border-", "ren-radius-",
    ]

    shown = set()
    for cls in classes:
        name = cls.get("name", "")
        if name in shown:
            continue
        # 只顯示 ren- 開頭的常用 class
        if not name.startswith("ren-"):
            continue

        settings = cls.get("settings", {})
        # 找到最重要的設定值來描述
        desc_parts = []
        for key, val in settings.items():
            if key == "_cssCustom":
                # 只顯示非 hover 的簡短 CSS
                css = val[:100].replace("\n", " ") if isinstance(val, str) else ""
                if css:
                    desc_parts.append(f"cssCustom: {css}...")
            elif key.startswith("_") and not key.endswith(":hover"):
                desc_parts.append(f"{key[1:]}: {json.dumps(val, ensure_ascii=False)[:60]}")

        if desc_parts:
            lines.append(f"- `{name}`: {'; '.join(desc_parts[:2])}")
            shown.add(name)

        if len(shown) >= 60:
            break

    return "\n".join(lines)


def get_hover_examples(index: list[dict]) -> list[dict]:
    """取得含有 hover/動態效果的樣式範例"""
    examples = []
    seen_categories = set()

    for item in index:
        if not item["dynamic_features"]:
            continue
        cat = item["category"]
        if cat not in seen_categories and len(examples) < 4:
            examples.append(item)
            seen_categories.add(cat)

    return examples


if __name__ == "__main__":
    # 測試載入
    db = load_database()
    index = build_style_index(db)
    print(f"✅ 載入 {len(index)} 個樣式")

    dynamic_count = sum(1 for s in index if s["dynamic_features"])
    print(f"✅ 含動態效果: {dynamic_count} 個")

    cats = {}
    for s in index:
        cats[s["category"]] = cats.get(s["category"], 0) + 1
    print("✅ 類別分布:")
    for cat, cnt in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"   {cat}: {cnt}")
