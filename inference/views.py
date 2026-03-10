import logging

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from inference.forms import ImageUploadForm
from inference.services import InferenceResult, get_pretrained_image_classifier


def _serialize_result(result: InferenceResult) -> dict[str, object]:
    return {
        "model": result.model_name,
        "image": {
            "width": result.width,
            "height": result.height,
        },
        "tags": [
            {
                "label": prediction.label,
                "score": prediction.score,
            }
            for prediction in result.tags
        ],
    }


@require_http_methods(["GET", "POST"])
def home(request: HttpRequest) -> HttpResponse:
    form = ImageUploadForm(request.POST or None, request.FILES or None)
    result_payload = None

    if request.method == "POST" and form.is_valid():
        result = get_pretrained_image_classifier().classify(form.cleaned_data["image"])
        result_payload = _serialize_result(result)
        logging.info(
            "Completed browser inference request model=%s tags=%s",
            result.model_name,
            ",".join(tag["label"] for tag in result_payload["tags"]),
        )

    return render(
        request,
        "inference/home.html",
        {
            "form": form,
            "result": result_payload,
        },
    )


@csrf_exempt
@require_POST
def infer_image(request: HttpRequest) -> JsonResponse:
    form = ImageUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        return JsonResponse({"errors": form.errors.get_json_data()}, status=400)
    
    image = form.cleaned_data["image"]
    
    result = get_pretrained_image_classifier().classify(image)
    result_payload = _serialize_result(result)
    
    logging.info(
        "Completed API inference request model=%s tags=%s",
        result.model_name,
        ",".join(tag["label"] for tag in result_payload["tags"]),
    )
    
    return JsonResponse(result_payload)
