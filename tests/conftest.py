import io
from unittest.mock import MagicMock

import pytest
from PIL import Image

from inference.services import InferenceResult, TagPrediction


MOCK_RESULT = InferenceResult(
    model_name="squeezenet1_1.onnx",
    tags=[
        TagPrediction(label="tabby cat", score=0.8231),
        TagPrediction(label="tiger cat", score=0.1102),
        TagPrediction(label="Egyptian cat", score=0.0421),
    ],
    width=640,
    height=480,
    preprocessing_ms=2.1,
    model_ms=18.4,
    cache_hit=False,
)


@pytest.fixture
def mock_classifier(monkeypatch):
    """Replaces the real classifier with a mock that returns MOCK_RESULT."""
    mock = MagicMock()
    mock.classify.return_value = MOCK_RESULT
    monkeypatch.setattr("inference.views.get_pretrained_image_classifier", lambda: mock)
    return mock


@pytest.fixture
def png_image():
    """Minimal valid PNG as an in-memory file."""
    buf = io.BytesIO()
    Image.new("RGB", (32, 32), color=(100, 149, 237)).save(buf, format="PNG")
    buf.seek(0)
    return buf
