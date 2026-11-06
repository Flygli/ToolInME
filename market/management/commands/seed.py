from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from market.models import AttributeDef, Category, Listing, ListingValue

BRANDS = "Bosch\nMakita\nDeWalt\nMetabo\nHilti\nИнтерскол"
POWER = "Сеть 220 В\nАккумулятор"

# slug: (название, иконка, [(ключ, название, тип, единица, варианты)])
CATS = {
    "drill": ("Дрели и шуруповёрты", "🔩", [
        ("type", "Тип", "choice", "", "Дрель\nУдарная дрель\nШуруповёрт\nДрель-миксер"),
        ("brand", "Бренд", "choice", "", BRANDS), ("power", "Питание", "choice", "", POWER),
        ("watt", "Мощность", "number", "Вт", ""), ("chuck", "Патрон", "number", "мм", ""),
        ("weight", "Вес", "number", "кг", "")]),
    "perf": ("Перфораторы", "⛏", [
        ("type", "Патрон", "choice", "", "SDS-plus\nSDS-max"),
        ("brand", "Бренд", "choice", "", BRANDS), ("power", "Питание", "choice", "", POWER),
        ("watt", "Мощность", "number", "Вт", ""), ("joule", "Энергия удара", "number", "Дж", ""),
        ("weight", "Вес", "number", "кг", "")]),
    "grinder": ("Болгарки (УШМ)", "⚙", [
        ("brand", "Бренд", "choice", "", BRANDS),
        ("disc", "Диаметр диска", "choice", "", "115 мм\n125 мм\n150 мм\n180 мм\n230 мм"),
        ("power", "Питание", "choice", "", POWER), ("watt", "Мощность", "number", "Вт", ""),
        ("rpm", "Обороты", "number", "об/мин", "")]),
    "saw": ("Пилы", "🪚", [
        ("type", "Тип", "choice", "", "Циркулярная\nЛобзик\nСабельная\nЦепная\nТорцовочная"),
        ("brand", "Бренд", "choice", "", BRANDS + "\nStihl"),
        ("power", "Питание", "choice", "", POWER + "\nБензин"),
        ("watt", "Мощность", "number", "Вт", ""), ("depth", "Глубина реза", "number", "мм", "")]),
    "gen": ("Генераторы", "⚡", [
        ("fuel", "Топливо", "choice", "", "Бензин\nДизель\nИнвертор"),
        ("brand", "Бренд", "choice", "", "Honda\nChampion\nHuter\nFubag\nHyundai"),
        ("phase", "Фазы", "choice", "", "1 фаза\n3 фазы"),
        ("kw", "Мощность", "number", "кВт", ""), ("tank", "Бак", "number", "л", "")]),
}

SAMPLES = [
    ("drill", "rent", "Bosch GSB 18V-55 ударный", 600, "Москва", "+7 900 111-22-33",
     {"type": "Ударная дрель", "brand": "Bosch", "power": "Аккумулятор", "watt": 550, "chuck": 13, "weight": 1.8},
     "Два аккумулятора, зарядка, кейс. Залог 5000 ₽."),
    ("drill", "sale", "Makita DF333D шуруповёрт", 7900, "Казань", "@kazan_tools",
     {"type": "Шуруповёрт", "brand": "Makita", "power": "Аккумулятор", "watt": 300, "chuck": 10, "weight": 1.2},
     "Новый, в упаковке, гарантия 1 год."),
    ("perf", "rent", "Hilti TE 7-C SDS-plus", 1200, "Москва", "+7 900 111-22-33",
     {"type": "SDS-plus", "brand": "Hilti", "power": "Сеть 220 В", "watt": 800, "joule": 3.2, "weight": 3.7},
     "Бур 12 мм в комплекте."),
    ("perf", "sale", "Makita HR5212C SDS-max", 42000, "Санкт-Петербург", "+7 911 555-44-33",
     {"type": "SDS-max", "brand": "Makita", "power": "Сеть 220 В", "watt": 1510, "joule": 20, "weight": 8.1},
     "Б/у, один сезон."),
    ("grinder", "rent", "DeWalt DWE4257 125 мм", 500, "Москва", "@msk_rent",
     {"brand": "DeWalt", "disc": "125 мм", "power": "Сеть 220 В", "watt": 1200, "rpm": 11800},
     "Защитный кожух, два диска."),
    ("saw", "rent", "Makita HS7601 циркулярная", 700, "Москва", "+7 900 111-22-33",
     {"type": "Циркулярная", "brand": "Makita", "power": "Сеть 220 В", "watt": 1200, "depth": 66},
     "Диск на 24 зуба."),
    ("gen", "rent", "Champion GG6500 бензиновый", 2500, "Тверь", "+7 920 000-11-22",
     {"fuel": "Бензин", "brand": "Champion", "phase": "1 фаза", "kw": 5.5, "tank": 25},
     "Заправлен, для стройплощадки."),
]


class Command(BaseCommand):
    help = "Заполняет базу демо-категориями, характеристиками и объявлениями"

    def handle(self, *args, **opts):
        if Category.objects.exists():
            self.stdout.write("Категории уже есть, пропускаю")
            return
        cats = {}
        for slug, (name, icon, attrs) in CATS.items():
            c = Category.objects.create(slug=slug, name=name, icon=icon)
            cats[slug] = {}
            for i, (key, label, kind, unit, choices) in enumerate(attrs):
                cats[slug][key] = AttributeDef.objects.create(
                    category=c, key=key, name=label, kind=kind, unit=unit, choices=choices, order=i)
        user, _ = get_user_model().objects.get_or_create(username="demo")
        user.set_password("demo12345")
        user.save()
        for slug, deal, title, price, city, contact, vals, desc in SAMPLES:
            l = Listing.objects.create(owner=user, category=Category.objects.get(slug=slug), deal=deal,
                                       title=title, price=price, city=city, contact=contact, description=desc)
            for key, v in vals.items():
                a = cats[slug][key]
                is_num = a.kind == AttributeDef.NUMBER
                ListingValue.objects.create(listing=l, attribute=a, text="" if is_num else v,
                                            number=v if is_num else None)
        self.stdout.write(self.style.SUCCESS("Готово. Демо-пользователь: demo / demo12345"))
