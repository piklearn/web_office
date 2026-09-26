from .models import SiteSettings


def site_settings(request):
    """در تمام قالب‌ها متغیر site_settings را در دسترس می‌گذارد."""
    return {"site_settings": SiteSettings.load()}
