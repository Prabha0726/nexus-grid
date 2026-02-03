from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def health_check(request):
    return HttpResponse("OK")

urlpatterns = [
    path('health/', health_check),
    path('admin/', admin.site.urls),
    path('', include('chat.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
]
