# -*- coding: utf-8 -*-

import shutil
import tempfile
from pathlib import Path
import pytest
from freezegun import freeze_time
from src import folder_sort_unified as sorter


@pytest.fixture
def temp_dirs():
    """一時ディレクトリを作成してクリーンアップする共通フィクスチャ"""
    src = Path(tempfile.mkdtemp())
    dst = Path(tempfile.mkdtemp())
    yield src, dst
    shutil.rmtree(src, ignore_errors=True)
    shutil.rmtree(dst, ignore_errors=True)


def create_file(path: Path, name: str, content="x"):
    """指定した場所にテスト用ファイルを作成"""
    f = path / name
    f.write_text(content, encoding="utf-8")
    return f


# ============================================================
# 基本機能テスト
# ============================================================

@freeze_time("2025-10-14")
def test_sort_by_date_dry_run(temp_dirs, capsys):
    """日付モード(dry-run)でファイルが移動されずに予定出力されるか"""
    src, dst = temp_dirs
    f1 = create_file(src, "a.txt")
    f2 = create_file(src, "b.txt")

    moved, failed = sorter.sort_by_date(src, dst, "2025-10-14", dry_run=True)
    captured = capsys.readouterr().out

    assert "[DRY-RUN]" in captured
    assert "a.txt" in captured
    assert moved == 2
    assert failed == 0
    assert f1.exists() and f2.exists()  # dry-runなので残る


@freeze_time("2025-10-14")
def test_sort_by_date_force(temp_dirs):
    """日付モード(force)で実際に移動されるか"""
    src, dst = temp_dirs
    f = create_file(src, "sample.txt")

    moved, failed = sorter.sort_by_date(src, dst, "2025-10-14", dry_run=False)

    assert moved == 1
    assert failed == 0
    assert not f.exists()
    assert (dst / "2025-10-14" / "sample.txt").exists()


def test_sort_by_ext_modes(temp_dirs):
    """拡張子モード(all/last)で適切にフォルダ分けされるか"""
    src, dst = temp_dirs
    create_file(src, "archive.tar.gz")
    create_file(src, "image.jpg")
    create_file(src, "note")

    sorter.sort_by_ext(src, dst, dry_run=False, ext_mode="all")
    assert (dst / "TAR.GZ" / "archive.tar.gz").exists()
    assert (dst / "JPG" / "image.jpg").exists()
    assert (dst / "NOEXT" / "note").exists()

    # lastモードでも動作確認
    src2, dst2 = temp_dirs
    create_file(src2, "archive.tar.gz")
    sorter.sort_by_ext(src2, dst2, dry_run=False, ext_mode="last")
    assert (dst2 / "GZ" / "archive.tar.gz").exists()


# ============================================================
# 安全設計・除外・例外処理テスト
# ============================================================

def test_safe_move_collision(temp_dirs):
    """同名ファイルの重複回避リネームが行われるか"""
    src, dst = temp_dirs
    f1 = create_file(src, "dup.txt")
    sorter.safe_move(f1, dst / "dup.txt")

    # 同名ファイルを再作成して再度移動
    f2 = create_file(src, "dup.txt")
    ok, candidate = sorter.safe_move(f2, dst / "dup.txt")
    assert ok
    assert candidate.name == "dup (1).txt"
    assert candidate.exists()


def test_is_hidden_or_temp(tmp_path, mocker):
    """隠しファイル・Windows属性ファイルを検知できるか"""
    hidden_file = tmp_path / ".hidden"
    hidden_file.write_text("x")

    assert sorter.is_hidden_or_temp(hidden_file)

    # Windows属性ファイルのモック
    mocker.patch("sys.platform", "win32")
    stat_mock = mocker.patch("os.stat")
    stat_mock.return_value.st_file_attributes = 2  # FILE_ATTRIBUTE_HIDDEN
    assert sorter.is_hidden_or_temp(hidden_file)


def test_main_invalid_src(tmp_path):
    """存在しないsrc指定でエラーコード1を返すか"""
    bad = tmp_path / "missing"
    rc = sorter.main(["--src", str(bad)])
    assert rc == 1


def test_main_same_src_dst(temp_dirs):
    """srcとdstが同一フォルダの場合、警告で中止されるか"""
    src, _ = temp_dirs
    f = create_file(src, "a.txt")
    rc = sorter.main(["--src", str(src), "--dst", str(src)])
    assert rc == 1
    assert f.exists()  # 移動していない


def test_error_handling(monkeypatch, temp_dirs):
    """移動時にPermissionErrorが発生しても安全に処理されるか"""
    src, dst = temp_dirs
    f = create_file(src, "x.txt")

    def raise_error(*args, **kwargs):
        raise PermissionError("Access denied")

    monkeypatch.setattr("shutil.move", raise_error)
    ok, _ = sorter.safe_move(f, dst / "x.txt", dry_run=False)
    assert not ok
