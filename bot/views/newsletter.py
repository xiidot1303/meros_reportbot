import base64
import json
from django.http import HttpResponse, JsonResponse, HttpRequest
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from bot.control.updater import application
from telegram import Update, InlineKeyboardMarkup, ReplyKeyboardMarkup
from bot import NewsletterUpdate


@method_decorator(csrf_exempt, name='dispatch')
class NewsletterView(View):
    async def post(self, request: HttpRequest, *args, **kwargs):
        data = json.loads(request.body)
        user_id = data.get('user_id')
        text = data.get('text')
        inline_buttons = data.get('inline_buttons', [])
        keyboard_buttons = data.get('keyboard_buttons', [])
        location = data.get('location', None)
        document = data.get('document')
        document_name = data.get('document_name')
        document_bytes = None
        if document:
            document_bytes = base64.b64decode(document)
        reply_markup = None
        if inline_buttons:
            reply_markup = InlineKeyboardMarkup(inline_buttons)
        elif keyboard_buttons:
            reply_markup = ReplyKeyboardMarkup(keyboard_buttons, resize_keyboard=True)

        await application.update_queue.put(NewsletterUpdate(
                    user_id=int(user_id),
                    text=text,
                    reply_markup=reply_markup,
                    location=location,
                    document=document_bytes,
                    document_name=document_name,
                ))
        
        return JsonResponse({"status": "success", "message": "Newsletter sent successfully."})