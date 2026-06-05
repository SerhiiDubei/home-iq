"""Tests for vision_client — AI image classifier."""
from homeiq.config import cfg


def test_classifier_config_loads():
    assert cfg.classifier.model == "google/gemini-2.5-flash"
    assert cfg.classifier.max_concurrent == 5
    assert cfg.classifier.cost_per_image_usd == 0.0001


def test_classifier_fallback_model_set():
    assert cfg.classifier.fallback_model == "google/gemini-2.5-flash"


def test_classifier_api_key_from_env(monkeypatch):
    """OPENROUTER_API_KEY env var takes precedence over config.yaml value."""
    import importlib
    import homeiq.config as config_module

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-env-key")
    importlib.reload(config_module)
    assert config_module.cfg.classifier.openrouter_api_key == "test-env-key"
    importlib.reload(config_module)


import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
from homeiq.classifier.vision_client import VisionClient, VALID_CATEGORIES, ClassifyResult


def test_valid_categories_complete():
    expected = {"hero", "before_after", "installation", "product",
                "lifestyle", "exterior", "interior", "text_overlay",
                "portrait", "reject"}
    assert VALID_CATEGORIES == expected


def _make_jpeg(tmp_path, name="test.jpg", size=(500, 400)):
    from PIL import Image as PILImage
    import io
    img = PILImage.new("RGB", size, color=(120, 80, 60))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    f = tmp_path / name
    f.write_bytes(buf.getvalue())
    return f


@pytest.mark.asyncio
async def test_classify_returns_valid_category(tmp_path):
    img_file = _make_jpeg(tmp_path)
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"category":"product","confidence":0.92,"runner_up":"interior","reason":"clean product shot"}'

    with patch("homeiq.classifier.vision_client.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat.completions.create = AsyncMock(return_value=mock_response)
        client = VisionClient(api_key="test-key", model="test-model")
        result = await client.classify(img_file)

    assert isinstance(result, ClassifyResult)
    assert result.category == "product"
    assert result.confidence == 0.92
    assert result.runner_up == "interior"


@pytest.mark.asyncio
async def test_classify_unknown_response_returns_unknown(tmp_path):
    img_file = _make_jpeg(tmp_path)
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"category":"something_invalid","confidence":0.3,"runner_up":"reject","reason":"unclear"}'

    with patch("homeiq.classifier.vision_client.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat.completions.create = AsyncMock(return_value=mock_response)
        client = VisionClient(api_key="test-key", model="test-model")
        result = await client.classify(img_file)

    assert result.category == "unknown"


@pytest.mark.asyncio
async def test_classify_uses_fallback_on_error(tmp_path):
    img_file = _make_jpeg(tmp_path)
    mock_ok = MagicMock()
    mock_ok.choices[0].message.content = '{"category":"hero","confidence":0.88,"runner_up":"lifestyle","reason":"wide banner"}'
    call_count = 0

    async def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("rate limited")
        return mock_ok

    with patch("homeiq.classifier.vision_client.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat.completions.create = side_effect
        client = VisionClient(api_key="key", model="free-model", fallback_model="paid-model")
        result = await client.classify(img_file)

    assert result.category == "hero"
    assert call_count == 2


@pytest.mark.asyncio
async def test_classify_confidence_below_review_threshold(tmp_path):
    """Low confidence result should still return ClassifyResult with low confidence."""
    img_file = _make_jpeg(tmp_path)
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"category":"lifestyle","confidence":0.40,"runner_up":"reject","reason":"ambiguous scene"}'

    with patch("homeiq.classifier.vision_client.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat.completions.create = AsyncMock(return_value=mock_response)
        client = VisionClient(api_key="test-key", model="test-model")
        result = await client.classify(img_file)

    assert result.category == "lifestyle"
    assert result.confidence == 0.40


@pytest.mark.asyncio
async def test_classify_json_with_markdown_fences(tmp_path):
    """Model sometimes wraps JSON in ```json ... ``` fences."""
    img_file = _make_jpeg(tmp_path)
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '```json\n{"category":"exterior","confidence":0.91,"runner_up":"hero","reason":"building facade"}\n```'

    with patch("homeiq.classifier.vision_client.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat.completions.create = AsyncMock(return_value=mock_response)
        client = VisionClient(api_key="test-key", model="test-model")
        result = await client.classify(img_file)

    assert result.category == "exterior"
    assert result.confidence == 0.91
