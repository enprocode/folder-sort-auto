# Folder Sort Unified

[![Run Tests](https://github.com/enprocode/folder-sort-auto/actions/workflows/test.yml/badge.svg)](https://github.com/enprocode/folder-sort-auto/actions/workflows/test.yml)

クロスプラットフォーム対応（macOS / Windows）のフォルダ整理ツールです。  
指定したフォルダ内のファイルを、**日付単位**または**拡張子単位**で自動整理します。

---

## ✨ 特徴

- ✅ **日付モード（--mode date）**  
  → `YYYY-MM-DD` フォルダを作成し、ファイルを日付単位で整理
- ✅ **拡張子モード（--mode ext）**  
  → ファイルの拡張子ごとに整理（`.tar.gz` のような複合拡張子にも対応）
- ✅ **dry-run（デフォルト）**  
  → 実際にファイルを移動せず、予定動作のみを一覧表示
- ✅ **--no-dry-run で実行**  
  → dry-run を無効化してファイルを実際に移動
- ✅ **--force で安全確認スキップ**  
  → `--no-dry-run` と併用することで警告を無視して強制実行
- ✅ **重複ファイル対応**  
  → `(1)`, `(2)` のように自動でリネームして安全に移動
- ✅ **Windows隠し属性にも対応**  
  → `FILE_ATTRIBUTE_HIDDEN` を判定して自動除外

---

## 🧩 インストール方法

特別な外部ライブラリは不要です（Python 標準ライブラリのみ）。  
Python 3.9 以上を推奨します。

```bash
git clone https://github.com/enprocode/folder-sort-auto.git
cd folder-sort-auto
```

---

## 🚀 実行方法

### 🔹 日付モード（デフォルト）

```bash
python src/folder_sort_unified.py --mode date
```

出力例（dry-run）：

```
[DRY-RUN] /Users/user/Desktop/report.txt → /Users/user/Documents/Sorted/2025-10-14/report.txt
[DRY-RUN] /Users/user/Desktop/photo.png → /Users/user/Documents/Sorted/2025-10-14/photo.png

整理予定: 2件 成功, 0件 失敗
対象: /Users/user/Desktop
出力: /Users/user/Documents/Sorted/2025-10-14
```

実際に移動する場合：

```bash
python src/folder_sort_unified.py --mode date --no-dry-run
# 警告を無視して強制実行する場合は --force も指定
# python src/folder_sort_unified.py --mode date --no-dry-run --force
```

---

### 🔹 拡張子モード

```bash
python src/folder_sort_unified.py --mode ext
```

出力例：

```
[DRY-RUN] /Users/user/Desktop/archive.tar.gz → /Users/user/Documents/Sorted/TAR.GZ/archive.tar.gz
[DRY-RUN] /Users/user/Desktop/image.jpg → /Users/user/Documents/Sorted/JPG/image.jpg
```

---

## ⚙️ オプション一覧

| オプション | 説明 | デフォルト |
|-------------|------|-------------|
| `--mode {date, ext}` | 整理モードを選択 | `date` |
| `--src <path>` | 整理元フォルダ | `~/Desktop` |
| `--dst <path>` | 整理先フォルダ | `~/Documents/Sorted` |
| `--ext-mode {last, all}` | 拡張子モード: `last`（最終拡張子のみ）, `all`（複合拡張子） | `all` |
| `--dry-run` | 実際に移動せず予定のみ表示 | 有効（デフォルト） |
| `--no-dry-run` | dry-runを無効化して実際に移動 | 無効 |
| `--force` | 警告（同一フォルダ/配下チェックなど）を無視して実行 | 無効 |

---

## 🧱 除外ルール

以下のファイルは整理対象外です：

- 隠しファイル（`.` で始まるもの）
- 一時ファイル（`~$` で始まるもの）
- Windows の隠し属性 (`FILE_ATTRIBUTE_HIDDEN`) が設定されているもの

---

## 💡 実装仕様

| 機能 | 内容 |
|------|------|
| 安全性 | dry-runデフォルト + --no-dry-run明示で実行 |
| 日付モード | main() で決定した日付文字列を一貫使用 |
| 拡張子モード | `.tar.gz → TAR.GZ`（--ext-mode=all） |
| ファイル重複 | 自動リネーム `(1)`, `(2)` |
| ログ出力 | dry-run時: `[DRY-RUN] src → dst` / 実行時: `[MOVED] src → dst` |
| エラーハンドリング | 各ファイル移動を try/except で安全化 |
| Windows対応 | `FILE_ATTRIBUTE_HIDDEN` を使用して隠し属性を検出 |

---

## 🧪 テスト

`pytest` による自動テストに対応しています。

```bash
pytest -v
```

カバレッジ確認も可能です：

```bash
pytest --cov=src
```

---

## 📦 CI/CD（GitHub Actions）

このプロジェクトには以下の2段階CI構成を推奨します：

1. ✅ **テスト（pytest）** — 全OS/バージョンで実行  
2. 🤖 **AIレビューBot** — テスト成功後に自動レビュー  

`.github/workflows/test.yml` にて構成済みです。

---

## 📄 ライセンス

MIT License  
Copyright (c) 2025

[LICENSE](LICENSE)

---

## 🧑‍💻 作者

Created by **ENPRO**  
https://github.com/enprocode
