from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('xiidot1303/', admin.site.urls),
    path('', include('app.urls')),
    path('', include('bot.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
