"""Tests for batch_classifier — find photos, move files, update DB."""
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

from homeiq.classifier.batch_classifier import find_unknown_photos, move_photo


def test_find_unknown_photos_finds_images(tmp_path):
    unknown_dir = tmp_path / "security" / "vivint.com" / "unknown"
    unknown_dir.mkdir(parents=True)
    (unknown_dir / "abc123.jpg").write_bytes(b"fake")
    (unknown_dir / "def456.png").write_bytes(b"fake")
    (unknown_dir / "skip.txt").write_bytes(b"text")

    results = find_unknown_photos(tmp_path, niche="security")
    names = {p.name for p in results}
    assert "abc123.jpg" in names
    assert "def456.png" in names
    assert "skip.txt" not in names


def test_find_unknown_photos_all_niches(tmp_path):
    for niche in ["security", "bathroom"]:
        d = tmp_path / niche / "site.com" / "unknown"
        d.mkdir(parents=True)
        (d / "photo.jpg").write_bytes(b"x")

    results = find_unknown_photos(tmp_path, niche="")
    assert len(results) == 2


def test_move_photo_creates_target_dir(tmp_path):
    src_dir = tmp_path / "security" / "vivint.com" / "unknown"
    src_dir.mkdir(parents=True)
    src = src_dir / "abc123.jpg"
    src.write_bytes(b"img")

    new_path = move_photo(src, "product")

    assert not src.exists()
    assert new_path.exists()
    assert new_path.parent.name == "product"
    assert new_path.name == "abc123.jpg"


def test_move_photo_target_dir_already_exists(tmp_path):
    src_dir = tmp_path / "security" / "site.com" / "unknown"
    src_dir.mkdir(parents=True)
    target_dir = tmp_path / "security" / "site.com" / "hero"
    target_dir.mkdir(parents=True)

    src = src_dir / "img.jpg"
    src.write_bytes(b"img")

    new_path = move_photo(src, "hero")
    assert new_path.exists()


@pytest.mark.asyncio
async def test_classify_batch_dry_run_no_move(tmp_path):
    unknown_dir = tmp_path / "security" / "site.com" / "unknown"
    unknown_dir.mkdir(parents=True)
    photo = unknown_dir / "test.jpg"
    photo.write_bytes(b"fake-jpeg-data")

    from homeiq.classifier.vision_client import ClassifyResult
    mock_client = MagicMock()
    mock_client.classify = AsyncMock(
        return_value=ClassifyResult("product", 0.92, "interior", "clean product")
    )

    from homeiq.classifier.batch_classifier import classify_batch
    # Patch prefilter so test image passes through to the mock client
    with patch("homeiq.classifier.batch_classifier.prefilter", return_value=None):
        with patch("homeiq.classifier.batch_classifier.postfilter", side_effect=lambda r, p: r):
            counts = await classify_batch([photo], mock_client, max_concurrent=1, dry_run=True)

    assert counts.get("product", 0) == 1
    assert photo.exists()  # NOT moved in dry run


@pytest.mark.asyncio
async def test_classify_batch_moves_file(tmp_path):
    unknown_dir = tmp_path / "security" / "site.com" / "unknown"
    unknown_dir.mkdir(parents=True)
    photo = unknown_dir / "abc123.jpg"
    photo.write_bytes(b"fake-jpeg-data")

    from homeiq.classifier.vision_client import ClassifyResult
    mock_client = MagicMock()
    mock_client.classify = AsyncMock(
        return_value=ClassifyResult("hero", 0.90, "lifestyle", "wide banner")
    )

    with patch("homeiq.classifier.batch_classifier.prefilter", return_value=None):
        with patch("homeiq.classifier.batch_classifier.postfilter", side_effect=lambda r, p: r):
            with patch("homeiq.classifier.batch_classifier.update_db") as mock_db:
                from homeiq.classifier.batch_classifier import classify_batch
                counts = await classify_batch(
                    [photo], mock_client, max_concurrent=1,
                    dry_run=False, base_dir=tmp_path
                )

    assert counts.get("hero", 0) == 1
    assert not photo.exists()
    assert (unknown_dir.parent / "hero" / "abc123.jpg").exists()
    mock_db.assert_called_once()
