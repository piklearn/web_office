from urllib.parse import quote

# پروفایل‌های پیش‌فرض (SVG داخلی؛ بدون نیاز به فایل تصویر)
AVATARS = [
    {"key": "ava",    "name": "آوا",    "bg": ("#1a7fd6", "#5fb8fa"), "skin": "#f1c9a5", "hair": "#2b1d16"},
    {"key": "kian",   "name": "کیان",   "bg": ("#f9ab08", "#ffe146"), "skin": "#d9a578", "hair": "#111111"},
    {"key": "niloo",  "name": "نیلوفر", "bg": ("#7a3e9d", "#c29be0"), "skin": "#f6d5bd", "hair": "#5a2e12"},
    {"key": "arman",  "name": "آرمان",  "bg": ("#2f6f4f", "#8fd3a6"), "skin": "#b9835a", "hair": "#2a2a2a"},
]
AVATAR_KEYS = [a["key"] for a in AVATARS]


def default_key(user):
    """اگر کاربر چیزی انتخاب نکرده باشد، بر اساس شناسه‌اش یکی از پیش‌فرض‌ها."""
    return AVATARS[(user.pk or 0) % len(AVATARS)]["key"]


def data_uri(key):
    a = next((x for x in AVATARS if x["key"] == key), AVATARS[0])
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{a["bg"][0]}"/><stop offset="1" stop-color="{a["bg"][1]}"/>'
        '</linearGradient></defs><rect width="100" height="100" fill="url(#g)"/>'
        '<path d="M14 100c2-22 18-32 36-32s34 10 36 32z" fill="#fff" fill-opacity=".92"/>'
        f'<circle cx="50" cy="42" r="19" fill="{a["skin"]}"/>'
        f'<path d="M31 41c0-14 8-22 19-22s19 8 19 22c-5-8-12-11-19-11s-14 3-19 11z" fill="{a["hair"]}"/>'
        '</svg>'
    )
    return "data:image/svg+xml;utf8," + quote(svg)
