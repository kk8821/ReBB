"""
image_handler.py
處理 Bricks JSON 中的圖片佔位符網址。
提供：列出佔位符、替換特定 URL、批次替換。
"""

import json
import re
from typing import Any


# Renmoe 官方圖片佔位符網域
PLACEHOLDER_DOMAINS = [
    "renmoe.com",
    "placeholder.com",
    "via.placeholder",
    "placehold.it",
    "picsum.photos",
    "dummyimage.com",
]

# Renmoe 預設佔位符圖片對應（原始 URL -> 建議用途）
RENMOE_PLACEHOLDERS = {
    "Renmoe-Library-Placeholder-Image-Half-Width.jpg": "半版寬度圖片 (適合並排卡片)",
    "Renmoe-Library-Placeholder-Image-Half-Width-Longer.jpg": "半版較高圖片 (適合背景卡片)",
    "Renmoe-Library-Placeholder-Image-Full-Width.jpg": "全版寬度圖片 (適合 Hero 背景)",
    "Renmoe-Library-Placeholder-Image-Square.jpg": "正方形圖片 (適合頭像/Logo)",
    "Renmoe-Library-Placeholder-Image-Portrait.jpg": "直式圖片 (適合人物照片)",
}


def is_placeholder_url(url: str) -> bool:
    """判斷是否為佔位符圖片網址"""
    url_lower = url.lower()
    return any(domain in url_lower for domain in PLACEHOLDER_DOMAINS)


def find_image_urls(json_str: str) -> list[dict[str, str]]:
    """
    從 Bricks JSON 字串中找出所有圖片 URL。

    Returns:
        [{"url": "...", "type": "placeholder|real", "hint": "用途說明"}, ...]
    """
    # 找出所有 URL 模式
    url_pattern = r'https?://[^\s"\'\\]+\.(?:jpg|jpeg|png|gif|webp|svg)'
    found_urls = re.findall(url_pattern, json_str, re.IGNORECASE)

    seen = set()
    results = []
    for url in found_urls:
        if url in seen:
            continue
        seen.add(url)

        is_ph = is_placeholder_url(url)
        hint = ""

        # 辨識 Renmoe 佔位符類型
        for ph_name, ph_hint in RENMOE_PLACEHOLDERS.items():
            if ph_name.lower() in url.lower():
                hint = ph_hint
                break

        results.append({
            "url": url,
            "type": "placeholder" if is_ph else "real",
            "hint": hint,
        })

    return results


def list_placeholders(bricks_json: str) -> list[dict[str, str]]:
    """只回傳佔位符圖片清單"""
    all_urls = find_image_urls(bricks_json)
    return [u for u in all_urls if u["type"] == "placeholder"]


def replace_url(bricks_json: str, old_url: str, new_url: str) -> str:
    """替換 JSON 字串中的特定圖片 URL"""
    return bricks_json.replace(old_url, new_url)


def replace_by_index(bricks_json: str, replacements: dict[int, str]) -> str:
    """
    依序號替換圖片（從 0 開始）。
    使用者只需指定第幾張圖換成什麼。

    Args:
        bricks_json: Bricks JSON 字串
        replacements: {0: "https://...", 2: "https://..."} 格式
    """
    placeholders = list_placeholders(bricks_json)
    result = bricks_json

    for idx, new_url in replacements.items():
        if idx < len(placeholders):
            old_url = placeholders[idx]["url"]
            result = result.replace(old_url, new_url)

    return result


def replace_all_placeholders(bricks_json: str, new_urls: list[str]) -> str:
    """
    將所有佔位符依序替換為提供的 URL 清單。
    URL 數量不足時，剩餘佔位符保持不變。
    """
    placeholders = list_placeholders(bricks_json)
    result = bricks_json

    for i, ph in enumerate(placeholders):
        if i < len(new_urls):
            result = result.replace(ph["url"], new_urls[i])

    return result


def print_placeholder_report(bricks_json: str) -> None:
    """印出佔位符圖片報告（供使用者參考替換）"""
    placeholders = list_placeholders(bricks_json)

    if not placeholders:
        print("✅ 此樣式不含佔位符圖片，無需替換。")
        return

    print(f"\n📸 發現 {len(placeholders)} 個圖片佔位符需要替換：\n")
    for i, ph in enumerate(placeholders):
        hint = f"  [{ph['hint']}]" if ph["hint"] else ""
        print(f"  [{i}] {ph['url']}{hint}")

    print("\n替換方式：")
    print("  程式碼: replace_by_index(json_str, {0: '您的圖片URL', 1: '...'})")
    print("  或: replace_all_placeholders(json_str, ['URL1', 'URL2', ...])")


def extract_image_info_from_code(code_obj: Any) -> list[dict]:
    """
    從解析後的 Bricks JSON 物件中提取圖片資訊（含元素位置）。

    Returns:
        [{"element_id": "...", "element_name": "...", "url": "...", "hint": "..."}, ...]
    """
    results = []

    def walk(obj, element_id="", element_name=""):
        if isinstance(obj, dict):
            # 如果是元素節點
            el_id = obj.get("id", element_id)
            el_name = obj.get("name", element_name)

            # 找 image settings
            settings = obj.get("settings", {})
            image_data = settings.get("image", {})
            if image_data and "url" in image_data:
                url = image_data["url"]
                hint = ""
                for ph_name, ph_hint in RENMOE_PLACEHOLDERS.items():
                    if ph_name.lower() in url.lower():
                        hint = ph_hint
                        break
                results.append({
                    "element_id": el_id,
                    "element_name": el_name,
                    "url": url,
                    "is_placeholder": is_placeholder_url(url),
                    "hint": hint,
                })

            # 背景圖片
            bg = settings.get("_background", {})
            bg_image = bg.get("image", {}) if isinstance(bg, dict) else {}
            if bg_image and "url" in bg_image:
                url = bg_image["url"]
                hint = "背景圖片"
                results.append({
                    "element_id": el_id,
                    "element_name": el_name,
                    "url": url,
                    "is_placeholder": is_placeholder_url(url),
                    "hint": hint,
                })

            for v in obj.values():
                walk(v, el_id, el_name)
        elif isinstance(obj, list):
            for item in obj:
                walk(item, element_id, element_name)

    walk(code_obj)
    return results


if __name__ == "__main__":
    # 測試
    test_json = '{"url":"https://renmoe.com/wp-content/uploads/Renmoe-Library-Placeholder-Image-Half-Width.jpg"}'
    phs = list_placeholders(test_json)
    print(f"找到 {len(phs)} 個佔位符")
    for ph in phs:
        print(f"  {ph}")
