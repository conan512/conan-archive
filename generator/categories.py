# -*- coding: utf-8 -*-
"""Category rules for DetectiveConanIR site. Order matters: first match wins."""

CATEGORIES = [
    {"slug": "movies", "title": "فیلم‌ها و تئاتر", "icon": "🎬",
     "desc": "پرونده‌های سینمایی کارآگاه کونان؛ تیزرها، تحلیل‌ها و اخبار فیلم‌های سالانه.",
     "tags": ["Movie28", "Movie27", "Movie26", "Movie25", "Movie24", "Movie23", "Movie22", "Movie21",
              "Movie20", "Movie", "Movies", "Preview", "ConanAnniversary", "ConanMovie", "Theater",
              "MovieNews", "BoxOffice", "OVA", "Special"]},

    {"slug": "news", "title": "اخبار و اطلاعیه", "icon": "📡",
     "desc": "آخرین خبرهای رسمی دنیای کونان، مصاحبه‌ها و اطلاعیه‌های کانال.",
     "tags": ["ConanNews", "News", "اخبار", "اطلاعیه", "ادمین", "Admin", "ConanInterview",
              "Interview", "مصاحبه", "اختصاصی", "Announcement", "Aoyama", "GoshoAoyama"]},

    {"slug": "manga", "title": "مانگا، اپیزود و زیرنویس", "icon": "📖",
     "desc": "ترجمهٔ فارسی مانگا، زیرنویس اپیزودها، فصل‌های جدید و راهنمای فیلرها.",
     "tags": ["مانگا_فارسی", "Manga", "MangaScreen", "MangaColor", "Chapter", "فصل",
              "زیرنویس_فارسی", "Subtitle", "Sub", "Episode", "اپیزود", "قسمت", "فیلر", "Filler",
              "SDB", "SuperDigest", "Volume", "جلد", "Raw", "Spoiler", "اسپویل"]},

    {"slug": "characters", "title": "شخصیت‌ها", "icon": "🕵️",
     "desc": "پرونده‌های شخصی؛ از کودو شینیچی و هایبارا تا اعضای سازمان سیاه.",
     "tags": ["EdogawaConan", "KudoShinichi", "MouriRan", "MouriKogoro", "HaibaraAi", "MiyanoShiho",
              "AkaiShuichi", "FuruyaRei", "OkiyaSubaru", "KaitoKid", "KurobaKaito", "Gin", "Rum",
              "Vermouth", "Vodka", "Korn", "Chianti", "Bourbon", "Amuro", "Rye",
              "YamatoKansuke", "MorofushiTakaaki", "MorofushiHiromitsu", "UeharaYui", "HasebeRikuo",
              "KazamiYuya", "HayashiAtsunobu", "SametaniKoji", "Seta", "MatsudaJinpei", "HagiwaraKenji",
              "HattoriHeiji", "ToyamaKazuha", "SuzukiSonoko", "ShinRan", "HeiKazu", "Sera", "SeraMasumi",
              "Jodie", "Camel", "James", "Megure", "Takagi", "Sato", "Chiba", "Shiratori",
              "Agasa", "Ayumi", "Genta", "Mitsuhiko", "Yukiko", "YusakuKudo", "Eri", "Kisaki",
              "Hakuba", "Akako", "Nakamori", "Aoko", "Kir", "Akemi", "Elena", "Atsushi"]},

    {"slug": "art", "title": "آرت و گالری", "icon": "🎨",
     "desc": "آرت‌ورک‌ها، والپیپرها، ادیت‌ها، کاسپلی و ساخته‌های هوش مصنوعی.",
     "tags": ["ConanArt", "ConanGallery", "Gallery", "ConanEdit", "Edit", "ConanAI", "AI",
              "ConanCosplay", "Cosplay", "Wallpaper", "والپیپر", "Fanart", "FanArt", "Doujin",
              "ConanPhoto", "Sketch", "Colored", "ConanIcon", "Icon", "Profile", "Merch"]},

    {"slug": "video", "title": "ویدیو و نماهنگ", "icon": "🎞️",
     "desc": "کلیپ‌ها، AMVها، تیک‌تاک‌ها، تیزرها و نماهنگ‌های کانال.",
     "tags": ["ConanTikTok", "TikTok", "ConanAMV", "AMV", "ConanClip", "Clip", "کلیپ",
              "ConanVideo", "Trailer", "تیزر", "Opening", "Ending", "OP", "ED", "Music", "OST",
              "MeitanteiPrecure", "CrossOver", "Short", "Reels"]},

    {"slug": "cases", "title": "معما و تئوری", "icon": "🔍",
     "desc": "پرونده‌ها، ترفندهای جنایی، مقایسه‌ها، تئوری‌ها و معماهای طرفداران.",
     "tags": ["Case", "پرونده", "ConanTrick", "Trick", "ConanComparison", "Comparison",
              "Theory", "تئوری", "معما", "Riddle", "Quiz", "کوییز", "ConanRegret",
              "ConanQuestion", "سوال", "Detective", "Mystery", "Analysis", "تحلیل"]},

    {"slug": "community", "title": "جامعه و توییت‌ها", "icon": "💬",
     "desc": "توییت‌ها، کامنت‌های اعضا، ارسالی‌های مخاطبان و لحظات سرگرم‌کننده.",
     "tags": ["ConanTweet", "Tweet", "توییت", "ConanComment", "Comment", "کامنت",
              "ارسالی", "ConanFun", "Fun", "Meme", "میم", "Food", "All", "all",
              "KugaYu", "UchihaShu", "Haru", "Mobin", "Birthday", "تولد", "Poll", "نظرسنجی",
              "Challenge", "Fandom", "فندوم"]},
]

FALLBACK = {"slug": "misc", "title": "متفرقه", "icon": "🗂️",
            "desc": "پست‌هایی که در دسته‌بندی‌های اصلی جای نگرفتند.", "tags": []}

_MAP = {}
for c in CATEGORIES:
    for t in c["tags"]:
        _MAP.setdefault(t.lower(), c["slug"])


_ORDER = {c["slug"]: i for i, c in enumerate(CATEGORIES)}


def categorize(post):
    """Pick the highest-priority category among all hashtags on the post,
    so #Movie28 wins over a generic #ConanNews regardless of hashtag order."""
    best = None
    for h in post.get("hashtags", []):
        s = _MAP.get(h.lower())
        if s and (best is None or _ORDER[s] < _ORDER[best]):
            best = s
    if best:
        return best
    if post.get("docs"):
        return "manga"
    if post.get("videos"):
        return "video"
    if post.get("photos"):
        return "art"
    return "misc"


ALL_CATEGORIES = CATEGORIES + [FALLBACK]
