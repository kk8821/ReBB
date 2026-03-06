"""
rag.py
基於關鍵字 + TF-IDF 的樣式檢索系統（RAG）。
不需要外部 embedding 服務，純 Python 實現。
"""

import re
from typing import Any

from src.analyzer import LAYOUT_KEYWORDS


def tokenize(text: str) -> set[str]:
    """簡易中英文 tokenizer"""
    text = text.lower()
    # 英文詞
    en_tokens = set(re.findall(r"[a-z]+", text))
    # 中文字（單字）
    zh_tokens = set(re.findall(r"[\u4e00-\u9fff]", text))
    return en_tokens | zh_tokens


def score_style(style: dict, query_tokens: set[str],
                required_categories: list[str],
                required_features: list[str]) -> float:
    """
    計算樣式與查詢的相關性分數。
    分數越高越相關。
    """
    score = 0.0

    # 1. 類別完全匹配 (最重要)
    style_cat = style["category"].lower()
    if required_categories:
        if style_cat in required_categories:
            score += 10.0
        elif any(kw in style_cat for kw in required_categories):
            score += 5.0
    else:
        # 從 query_tokens 推斷類別
        for cat, keywords in LAYOUT_KEYWORDS.items():
            if any(kw in query_tokens for kw in keywords):
                if cat == style_cat:
                    score += 8.0
                    break

    # 2. 特徵匹配
    for feat in required_features:
        if feat in style.get("features", []):
            score += 3.0
        if feat in style.get("dynamic_features", []):
            score += 2.0

    # 3. 關鍵字重疊
    style_keywords = style.get("keywords", set())
    overlap = query_tokens & style_keywords
    score += len(overlap) * 1.5

    # 4. 動態效果加分（使用者通常希望有動態）
    if style.get("dynamic_features"):
        score += 1.0

    # 5. 響應式設計加分
    if style.get("has_responsive"):
        score += 0.5

    # 6. 複雜度調整（中等複雜度最好）
    complexity = style.get("complexity", "medium")
    if complexity == "medium":
        score += 0.3
    elif complexity == "complex":
        score += 0.1  # 太複雜可能不好客製化

    return score


def parse_query(query: str) -> tuple[set[str], list[str], list[str]]:
    """
    解析使用者查詢，提取：
    - tokens: 關鍵字集合
    - categories: 需要的版面類型
    - features: 需要的功能特徵
    """
    tokens = tokenize(query)

    # 識別類別
    categories = []
    for cat, keywords in LAYOUT_KEYWORDS.items():
        for kw in keywords:
            if kw in query.lower() or kw in tokens:
                if cat not in categories:
                    categories.append(cat)

    # 識別特徵需求
    features = []
    feature_map = {
        "圖片": "has_image",
        "image": "has_image",
        "圖": "has_image",
        "迴圈": "has_loop",
        "loop": "has_loop",
        "表單": "has_form",
        "form": "has_form",
        "按鈕": "has_button",
        "button": "has_button",
        "背景": "has_background_image",
        "background": "has_background_image",
        "動畫": "animation",
        "animation": "animation",
        "hover": "css_hover",
        "滑鼠懸停": "css_hover",
        "過渡": "transition",
        "transition": "transition",
    }
    for keyword, feature in feature_map.items():
        if keyword in query.lower():
            if feature not in features:
                features.append(feature)

    return tokens, categories, features


def retrieve(
    index: list[dict[str, Any]],
    query: str,
    top_k: int = 3,
    category_filter: str | None = None,
) -> list[dict[str, Any]]:
    """
    從索引中檢索最相關的樣式。

    Args:
        index: 樣式索引（來自 analyzer.build_style_index）
        query: 使用者查詢字串
        top_k: 回傳前 N 個最相關結果
        category_filter: 強制指定類別（可選）

    Returns:
        按相關性排序的樣式清單
    """
    query_tokens, categories, features = parse_query(query)

    if category_filter:
        categories = [category_filter.lower()]

    # 計算每個樣式的分數
    scored = []
    for style in index:
        score = score_style(style, query_tokens, categories, features)
        if score > 0:
            scored.append((score, style))

    # 排序並取 top_k
    scored.sort(key=lambda x: -x[0])

    # 去重：每個類別最多取 2 個，確保多樣性
    results = []
    cat_counts: dict[str, int] = {}
    for score, style in scored:
        cat = style["category"]
        if len(results) >= top_k:
            break
        count = cat_counts.get(cat, 0)
        if count < 2:
            results.append(style)
            cat_counts[cat] = count + 1

    return results


def retrieve_by_categories(
    index: list[dict[str, Any]],
    categories: list[str],
    top_k_per_cat: int = 1,
) -> list[dict[str, Any]]:
    """
    依指定類別清單各取最佳樣式（用於頁面組合）。

    Args:
        index: 樣式索引
        categories: 類別清單，如 ["hero", "content", "cta", "faq"]
        top_k_per_cat: 每個類別取幾個樣式

    Returns:
        按類別順序排列的樣式清單
    """
    results = []
    for cat in categories:
        cat_styles = [s for s in index if s["category"].lower() == cat.lower()]
        # 優先選有動態效果且響應式的
        cat_styles.sort(key=lambda s: (
            -len(s.get("dynamic_features", [])),
            -int(s.get("has_responsive", False)),
            -s.get("element_count", 0),
        ))
        results.extend(cat_styles[:top_k_per_cat])
    return results


def format_retrieved_styles(styles: list[dict[str, Any]]) -> str:
    """
    將檢索結果格式化成可注入 prompt 的字串。
    只包含 code（完整 Bricks JSON）和基本 metadata。
    """
    if not styles:
        return "（無相關範例）"

    parts = []
    for i, style in enumerate(styles, 1):
        dynamic = style.get("dynamic_features", [])
        feat_str = ", ".join(style.get("features", []))
        dyn_str = ", ".join(dynamic) if dynamic else "無"

        parts.append(f"""### 範例 {i}: {style['name']} ({style['category']})
- 複雜度: {style['complexity']}
- 功能特徵: {feat_str or '基本'}
- 動態效果: {dyn_str}
- 元素數: {style['element_count']}

**完整 Bricks JSON Code:**
```json
{style['code']}
```""")

    return "\n\n".join(parts)


if __name__ == "__main__":
    from src.analyzer import load_database, build_style_index

    db = load_database()
    index = build_style_index(db)

    # 測試查詢
    test_queries = [
        "SaaS 產品落地頁，需要 Hero 和 CTA",
        "餐廳網站，有圖片展示和聯絡表單",
        "部落格文章列表，有 hover 效果",
    ]

    for q in test_queries:
        print(f"\n查詢: {q}")
        results = retrieve(index, q, top_k=3)
        for r in results:
            print(f"  → {r['name']} ({r['category']}) | 動態: {r['dynamic_features']}")
