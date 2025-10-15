# -*- coding: utf-8 -*-

"""
Cross-platform (macOS & Windows) folder sorter

Features:
- Mode "date": Move files into a date folder (YYYY-MM-DD) under the destination.
- Mode "ext" : Group files by extension under the destination.
- Dry-run (default): Shows planned moves without changing files.
- Safe rename: Avoids collisions with "name (1).ext", "name (2).ext", ...
- Skips hidden files (dotfiles, ~$temp files, Windows hidden attributes).
- Ext mode supports "--ext-mode all" for compound extensions (.tar.gz -> TAR.GZ).
- Adds --force option to actually move files (dry-run by default).
- Provides readable logging for each file (planned or moved).

Usage examples:
  # Date mode (default): preview planned moves
  python src/folder_sort_unified.py --mode date

  # Actually move files
  python src/folder_sort_unified.py --mode date --force

  # Extension mode: group by extensions
  python src/folder_sort_unified.py --mode ext --ext-mode all

  # Custom directories
  python src/folder_sort_unified.py --mode ext --src "/path/to/src" --dst "/path/to/dst"

Notes:
- Default behavior is dry-run for safety.
- On Windows, hidden attributes are checked in addition to dotfiles.
- License: MIT
"""

import os
import sys
import shutil
import argparse
from datetime import datetime
from pathlib import Path
from typing import Tuple


# ============================================================
#  Utility functions
# ============================================================

def is_hidden_or_temp(path: Path) -> bool:
    """Return True if file is hidden or temporary (cross-platform)."""
    name = path.name
    if name.startswith(".") or name.startswith("~$"):
        return True

    if sys.platform == "win32":
        try:
            import stat
            attrs = os.stat(path).st_file_attributes
            if attrs & stat.FILE_ATTRIBUTE_HIDDEN:
                return True
        except Exception:
            pass

    return False


def safe_move(src_path: Path, dst_path: Path, dry_run: bool = False) -> Tuple[bool, Path]:
    """
    Move file safely, avoiding name collisions.
    Returns (success, target_path).
    In dry-run mode, only prints the planned move.
    """
    dst_parent = dst_path.parent
    dst_parent.mkdir(parents=True, exist_ok=True)

    base, suf = dst_path.stem, dst_path.suffix
    candidate = dst_path
    i = 1
    while candidate.exists():
        candidate = dst_path.with_name(f"{base} ({i}){suf}")
        i += 1

    if dry_run:
        print(f"[DRY-RUN] {src_path} → {candidate}")
        return True, candidate

    try:
        shutil.move(str(src_path), str(candidate))
        print(f"[MOVED] {src_path} → {candidate}")
        return True, candidate
    except Exception as e:
        print(f"[ERROR] {src_path} の移動に失敗: {e}")
        return False, candidate


# ============================================================
#  Core sorting logic
# ============================================================

def sort_by_date(src_dir: Path, dst_dir: Path, date_str: str, dry_run: bool = False) -> Tuple[int, int]:
    """Move files into date-based folder (YYYY-MM-DD)."""
    target_root = dst_dir / date_str
    moved = failed = 0

    for src in src_dir.iterdir():
        if not src.is_file() or is_hidden_or_temp(src):
            continue
        dst = target_root / src.name
        ok, _ = safe_move(src, dst, dry_run)
        if ok:
            moved += 1
        else:
            failed += 1

    return moved, failed


def sort_by_ext(src_dir: Path, dst_dir: Path, dry_run: bool = False, ext_mode: str = "all") -> Tuple[int, int]:
    """Group files by extension (supports compound extensions)."""
    moved = failed = 0

    for src in src_dir.iterdir():
        if not src.is_file() or is_hidden_or_temp(src):
            continue
        try:
            if ext_mode == "last":
                ext = src.suffix[1:].upper() if src.suffix else "NOEXT"
            else:
                ext = ".".join([e[1:].upper() for e in src.suffixes]) or "NOEXT"
            dst = (dst_dir / ext) / src.name
            ok, _ = safe_move(src, dst, dry_run)
            if ok:
                moved += 1
            else:
                failed += 1
        except Exception as e:
            print(f"[ERROR] {src}: {e}")
            failed += 1

    return moved, failed


# ============================================================
#  CLI entry point
# ============================================================

def main(argv=None) -> int:
    home = Path.home()
    default_src = home / "Desktop"
    default_dst = home / "Documents" / "Sorted"

    parser = argparse.ArgumentParser(description="フォルダを日付または拡張子で整理します。")
    parser.add_argument("--mode", choices=["date", "ext"], default="date", help="整理モードを選択 (dateまたはext)")
    parser.add_argument("--src", type=Path, default=default_src, help=f"整理元フォルダ（デフォルト: {default_src}）")
    parser.add_argument("--dst", type=Path, default=default_dst, help=f"整理先フォルダ（デフォルト: {default_dst}）")
    parser.add_argument("--ext-mode", choices=["last", "all"], default="all", help="拡張子モード: last=最終のみ, all=複合拡張子全体")
    parser.add_argument("--dry-run", action="store_true", default=True, help="実際に移動せず予定のみ表示（デフォルト有効）")
    parser.add_argument("--force", action="store_true", help="dry-runを無効化して実際に移動する")

    args = parser.parse_args(argv)

    # 環境確認と安全装置
    if not args.src.exists():
        print(f"[ERROR] フォルダが見つかりません: {args.src}")
        return 1
    if not args.src.is_dir():
        print(f"[ERROR] ディレクトリではありません: {args.src}")
        return 1
    if args.src.resolve() == args.dst.resolve():
        print("[WARN] srcとdstが同一です。--force指定がない場合は中止します。")
        if not args.force:
            return 1
    if args.dst.is_relative_to(args.src):
        print("[WARN] dstがsrc配下です。--force指定がない場合は中止します。")
        if not args.force:
            return 1

    dry_run = not args.force
    date_str = datetime.now().strftime("%Y-%m-%d")

    if args.mode == "date":
        moved, failed = sort_by_date(args.src, args.dst, date_str, dry_run)
        detail = args.dst / date_str
    else:
        moved, failed = sort_by_ext(args.src, args.dst, dry_run, args.ext_mode)
        detail = args.dst

    action = "予定" if dry_run else "完了"
    print(f"\n整理{action}: {moved}件 成功, {failed}件 失敗")
    print(f"対象: {args.src}")
    print(f"出力: {detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
