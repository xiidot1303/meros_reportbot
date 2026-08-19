import json

from asgiref.sync import sync_to_async
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from bot.services.feedback_service import create_feedback
from bot.utils.webapp_auth import verify_init_data


FORM_TEXTS = {
    "title": ["Murojaat yuborish", "Оставить обращение"],
    "subtitle": [
        "Savolingiz yoki shikoyatingizni yozib qoldiring",
        "Оставьте ваш вопрос или жалобу",
    ],
    "ttn_label": ["Yuk xati raqami (TTN)", "Номер товарно-транспортной накладной (ТТН)"],
    "ttn_placeholder": ["Masalan: 123456", "Например: 123456"],
    "ttn_error": ["TTN raqamini kiriting", "Введите номер ТТН"],
    "text_label": ["Murojaat matni", "Текст обращения"],
    "text_placeholder": ["Murojaatingizni yozing...", "Опишите ваше обращение..."],
    "text_error": ["Murojaat matnini kiriting", "Введите текст обращения"],
    "submit": ["Yuborish", "Отправить"],
}


def _texts(lang):
    return {key: value[lang] for key, value in FORM_TEXTS.items()}


def _payload(request):
    try:
        return json.loads(request.body or b"{}")
    except (ValueError, UnicodeDecodeError):
        return None


@method_decorator(csrf_exempt, name="dispatch")
class FeedbackFormView(View):
    """Telegram WebApp: the client's feedback form (ТТН number + message)."""

    async def get(self, request, *args, **kwargs):
        lang = 1 if request.GET.get("lang") == "ru" else 0
        return await sync_to_async(render)(
            request,
            "webapp/feedback_form.html",
            {"t": _texts(lang), "error_text": FORM_TEXTS["text_error"][lang]},
        )

    async def post(self, request, *args, **kwargs):
        data = _payload(request)
        if data is None:
            return JsonResponse({"status": "error", "message": "Invalid JSON."}, status=400)

        user = verify_init_data(data.get("_auth"))
        if not user or not user.get("id"):
            return JsonResponse({"status": "error", "message": "Unauthorized."}, status=401)

        ttn_number = (data.get("ttn_number") or "").strip()
        text = (data.get("text") or "").strip()
        if not ttn_number or not text:
            return JsonResponse(
                {"status": "error", "message": "ttn_number and text are required."}, status=400
            )

        feedback = await sync_to_async(create_feedback)(
            user_id=user["id"], ttn_number=ttn_number, text=text
        )
        if not feedback:
            return JsonResponse({"status": "error", "message": "Unknown user."}, status=404)

        from bot.services.feedback_notifier import notify_new_feedback
        await notify_new_feedback(feedback)

        return JsonResponse({"status": "success", "feedback_id": feedback.id})
