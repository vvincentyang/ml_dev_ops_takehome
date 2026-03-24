from dataclasses import dataclass
from functools import lru_cache
import time
from typing import BinaryIO

import numpy
import onnxruntime
from PIL import Image, ImageOps

from inference.assets import LABELS_PATH, MODEL_PATH, ensure_model_assets


IMAGE_INPUT_SIZE = (224, 224)
IMAGE_MEAN = numpy.array([0.485, 0.456, 0.406], dtype=numpy.float32)
IMAGE_STD = numpy.array([0.229, 0.224, 0.225], dtype=numpy.float32)


@dataclass(frozen=True)
class TagPrediction:
    label: str
    score: float


@dataclass(frozen=True)
class InferenceResult:
    model_name: str
    tags: list[TagPrediction]
    width: int
    height: int
    preprocessing_ms: float
    model_ms: float


class PretrainedImageClassifier:
    def __init__(self) -> None:
        ensure_model_assets()
        self.model_name = MODEL_PATH.name
        self.labels = tuple(
            label.strip()
            for label in LABELS_PATH.read_text().splitlines()
            if label.strip()
        )
        self.session = onnxruntime.InferenceSession(
            MODEL_PATH.as_posix(),
            providers=["CPUExecutionProvider"],
        )
        self.input_name = self.session.get_inputs()[0].name

    def classify(self, uploaded_image: BinaryIO) -> InferenceResult:
        uploaded_image.seek(0)
        with Image.open(uploaded_image) as image:
            normalized_image = ImageOps.exif_transpose(image).convert("RGB")
            width, height = normalized_image.size

            t0 = time.perf_counter()
            input_tensor = self._build_input_tensor(normalized_image)
            preprocessing_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        raw_output = self.session.run(None, {self.input_name: input_tensor})[0]
        model_ms = (time.perf_counter() - t0) * 1000

        scores = self._normalize_scores(numpy.asarray(raw_output).squeeze())
        top_indices = numpy.argsort(scores)[-3:][::-1]
        predictions = [
            TagPrediction(
                label=self.labels[class_index],
                score=round(float(scores[class_index]), 4),
            )
            for class_index in top_indices
        ]

        return InferenceResult(
            model_name=self.model_name,
            tags=predictions,
            width=width,
            height=height,
            preprocessing_ms=preprocessing_ms,
            model_ms=model_ms,
        )

    def _build_input_tensor(self, image: Image.Image) -> numpy.ndarray:
        fitted_image = ImageOps.fit(
            image, 
            size=IMAGE_INPUT_SIZE, 
            method=Image.Resampling.BILINEAR
        )
        image_array = numpy.asarray(fitted_image, dtype=numpy.float32) / 255.0
        normalized_array = (image_array - IMAGE_MEAN) / IMAGE_STD
        chw_array = numpy.transpose(normalized_array, (2, 0, 1))
        return numpy.expand_dims(chw_array, axis=0).astype(numpy.float32)

    def _normalize_scores(self, model_output: numpy.ndarray) -> numpy.ndarray:
        if numpy.all(model_output >= 0) and numpy.isclose(float(model_output.sum()), 1.0, atol=1e-3):
            return model_output

        shifted_output = model_output - numpy.max(model_output)
        exponentiated_output = numpy.exp(shifted_output)
        return exponentiated_output / exponentiated_output.sum()


@lru_cache(maxsize=1)
def get_pretrained_image_classifier() -> PretrainedImageClassifier:
    return PretrainedImageClassifier()
