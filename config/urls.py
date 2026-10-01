from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = "پنل مدیریت دفتر"
admin.site.site_title = "مدیریت سایت"
admin.site.index_title = "خوش آمدید"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
    path('support/', include('support.urls')),
    path('shop/', include('sales.urls')),
    path('crm/', include('crm.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
