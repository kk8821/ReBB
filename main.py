#!/usr/bin/env python3
"""
main.py
Renmoe Bricks Builder JSON 生成器 - 主程式 CLI 介面

使用方式：
  python main.py generate "SaaS 落地頁，包含 Hero、功能介紹、CTA"
  python main.py generate "餐廳網站" --sections hero content gallery contact
  python main.py generate "科技公司" --image design.png
  python main.py section hero "有背景圖和兩個 CTA 按鈕"
  python main.py search "含 hover 效果的 CTA 區塊"
  python main.py list --category hero
  python main.py replace output.json --image-0 "https://..." --image-1 "https://..."
"""

import argparse
import json
import sys
from pathlib import Path

from src.analyzer import build_style_index, load_database
from src.generator import (
    clean_json_output,
    generate_bricks_json,
    generate_section,
    validate_json,
)
from src.image_handler import (
    list_placeholders,
    print_placeholder_report,
    replace_all_placeholders,
    replace_by_index,
)
from src.rag import retrieve


def cmd_generate(args):
    """生成完整頁面或指定區塊的 Bricks JSON"""
    db = load_database()
    index = build_style_index(db)

    sections = args.sections if hasattr(args, "sections") and args.sections else None
    image = args.image if hasattr(args, "image") and args.image else None

    raw_output = generate_bricks_json(
        description=args.description,
        page_sections=sections,
        style_index=index,
        image_path=image,
        streaming=True,
    )

    # 清理並驗證
    clean = clean_json_output(raw_output)
    is_valid, msg = validate_json(clean)
    print(f"\n🔍 驗證結果：{msg}")

    # 儲存輸出
    output_file = args.output if hasattr(args, "output") and args.output else "output.json"
    Path(output_file).write_text(clean, encoding="utf-8")
    print(f"💾 已儲存至：{output_file}")

    # 圖片佔位符報告
    print_placeholder_report(clean)

    return clean


def cmd_section(args):
    """生成單一區塊"""
    db = load_database()
    index = build_style_index(db)

    raw_output = generate_section(
        section_type=args.section_type,
        description=args.description,
        style_index=index,
    )

    clean = clean_json_output(raw_output)
    is_valid, msg = validate_json(clean)
    print(f"\n🔍 驗證結果：{msg}")

    output_file = args.output if hasattr(args, "output") and args.output else f"{args.section_type}.json"
    Path(output_file).write_text(clean, encoding="utf-8")
    print(f"💾 已儲存至：{output_file}")

    print_placeholder_report(clean)


def cmd_search(args):
    """搜尋樣式資料庫"""
    db = load_database()
    index = build_style_index(db)

    results = retrieve(index, args.query, top_k=args.top_k)

    print(f"\n🔍 搜尋：「{args.query}」\n")
    print(f"找到 {len(results)} 個相關樣式：\n")

    for i, r in enumerate(results, 1):
        dynamic = ", ".join(r["dynamic_features"]) if r["dynamic_features"] else "無"
        features = ", ".join(r["features"][:3]) if r["features"] else "基本"
        print(f"{'─'*50}")
        print(f"[{i}] {r['name']}  ({r['category']})")
        print(f"    複雜度：{r['complexity']}  元素數：{r['element_count']}")
        print(f"    功能：{features}")
        print(f"    動態效果：{dynamic}")
        print(f"    響應式：{'✓' if r['has_responsive'] else '✗'}")

        if args.show_code:
            print(f"\n    Bricks JSON (前 300 字):")
            print(f"    {r['code'][:300]}...")

    print(f"{'─'*50}")


def cmd_list(args):
    """列出所有樣式"""
    db = load_database()
    index = build_style_index(db)

    category_filter = args.category.lower() if args.category else None

    if category_filter:
        filtered = [s for s in index if s["category"].lower() == category_filter]
        print(f"\n📂 類別「{args.category}」共 {len(filtered)} 個樣式：\n")
    else:
        filtered = index
        # 顯示類別統計
        cats = {}
        for s in index:
            cats[s["category"]] = cats.get(s["category"], 0) + 1
        print(f"\n📊 樣式資料庫統計（共 {len(index)} 個）：\n")
        for cat, cnt in sorted(cats.items(), key=lambda x: -x[1]):
            bar = "█" * (cnt // 3)
            print(f"  {cat:15} {cnt:3d}  {bar}")
        print()

    for s in filtered:
        dynamic = "⚡" if s["dynamic_features"] else "  "
        responsive = "📱" if s["has_responsive"] else "  "
        print(f"  {dynamic}{responsive} {s['name']:20} | {s['complexity']:8} | {s['element_count']:3d} 元素")


def cmd_replace(args):
    """替換 JSON 檔案中的圖片佔位符"""
    json_file = Path(args.json_file)
    if not json_file.exists():
        print(f"❌ 找不到檔案：{args.json_file}")
        sys.exit(1)

    content = json_file.read_text(encoding="utf-8")

    # 顯示現有佔位符
    placeholders = list_placeholders(content)
    print(f"\n📸 檔案中有 {len(placeholders)} 個圖片佔位符：\n")
    for i, ph in enumerate(placeholders):
        hint = f"  ({ph['hint']})" if ph["hint"] else ""
        print(f"  [{i}] {ph['url']}{hint}")

    # 建立替換映射
    replacements = {}
    for key, val in vars(args).items():
        if key.startswith("image_") and val:
            try:
                idx = int(key.replace("image_", ""))
                replacements[idx] = val
            except ValueError:
                pass

    if not replacements:
        print("\n💡 使用方式：")
        print(f"  python main.py replace {args.json_file} --image-0 '您的圖片URL' --image-1 '...'")
        return

    # 執行替換
    new_content = replace_by_index(content, replacements)
    output_file = args.output if args.output else str(json_file).replace(".json", "_replaced.json")
    Path(output_file).write_text(new_content, encoding="utf-8")

    print(f"\n✅ 替換了 {len(replacements)} 個圖片")
    print(f"💾 已儲存至：{output_file}")


def cmd_info(args):
    """顯示系統資訊"""
    db = load_database()
    index = build_style_index(db)

    meta = db.get("metadata", {})
    print("\n" + "═"*60)
    print("  Renmoe Bricks Builder JSON 生成器")
    print("═"*60)
    print(f"\n  📦 樣式資料庫：{meta.get('total_styles', 0)} 個樣式（有效：{meta.get('valid_styles', 0)}）")
    print(f"  🔧 Bricks 版本：{meta.get('bricks_version', 'N/A')}")
    print(f"  📅 資料建立：{meta.get('created_at', 'N/A')[:10]}")

    dynamic_count = sum(1 for s in index if s["dynamic_features"])
    responsive_count = sum(1 for s in index if s["has_responsive"])
    print(f"\n  ⚡ 含動態效果：{dynamic_count} 個")
    print(f"  📱 含響應式：{responsive_count} 個")

    print("\n  📂 類別分布：")
    cats = {}
    for s in index:
        cats[s["category"]] = cats.get(s["category"], 0) + 1
    for cat, cnt in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"    {cat:15} {cnt:3d} 個")

    print("\n  🛠️  可用指令：")
    print("    generate  - 生成完整頁面 JSON")
    print("    section   - 生成單一區塊 JSON")
    print("    search    - 搜尋樣式資料庫")
    print("    list      - 列出所有樣式")
    print("    replace   - 替換圖片佔位符")
    print("\n  💡 快速開始：")
    print('    python main.py generate "SaaS 落地頁" --sections hero content pricing cta faq')
    print('    python main.py generate "餐廳網站" --image design.png')
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Renmoe Bricks Builder JSON 生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command")

    # generate 指令
    gen_parser = subparsers.add_parser("generate", help="生成 Bricks JSON")
    gen_parser.add_argument("description", help="版面需求描述")
    gen_parser.add_argument(
        "--sections", nargs="+",
        help="頁面區塊清單，如: hero content cta faq",
        metavar="SECTION",
    )
    gen_parser.add_argument("--image", help="設計參考圖片路徑", metavar="PATH")
    gen_parser.add_argument("--output", "-o", help="輸出檔案名稱", default="output.json")

    # section 指令
    sec_parser = subparsers.add_parser("section", help="生成單一區塊")
    sec_parser.add_argument("section_type", help="區塊類型（hero/content/cta/faq/...）")
    sec_parser.add_argument("description", help="此區塊的具體需求")
    sec_parser.add_argument("--output", "-o", help="輸出檔案名稱")

    # search 指令
    search_parser = subparsers.add_parser("search", help="搜尋樣式資料庫")
    search_parser.add_argument("query", help="搜尋關鍵字")
    search_parser.add_argument("--top-k", type=int, default=5, help="顯示結果數量")
    search_parser.add_argument("--show-code", action="store_true", help="顯示 JSON 程式碼")

    # list 指令
    list_parser = subparsers.add_parser("list", help="列出樣式")
    list_parser.add_argument("--category", "-c", help="篩選類別")

    # replace 指令
    replace_parser = subparsers.add_parser("replace", help="替換圖片佔位符")
    replace_parser.add_argument("json_file", help="JSON 檔案路徑")
    replace_parser.add_argument("--output", "-o", help="輸出檔案名稱")
    for i in range(20):
        replace_parser.add_argument(f"--image-{i}", dest=f"image_{i}", help=f"第 {i} 張圖片的 URL")

    # info 指令
    subparsers.add_parser("info", help="顯示系統資訊")

    args = parser.parse_args()

    if args.command == "generate":
        cmd_generate(args)
    elif args.command == "section":
        cmd_section(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "replace":
        cmd_replace(args)
    elif args.command == "info":
        cmd_info(args)
    else:
        cmd_info(args)


if __name__ == "__main__":
    main()
