from django.conf import settings
from django.db import models
from django.urls import reverse


class Category(models.Model):
    name = models.CharField("Название", max_length=80)
    slug = models.SlugField("Slug", unique=True)
    icon = models.CharField("Иконка (emoji)", max_length=8, blank=True, default="🛠")

    class Meta:
        ordering = ["name"]
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name


class AttributeDef(models.Model):
    """Описание характеристики категории. Новые атрибуты добавляются в админке."""
    CHOICE, NUMBER, TEXT = "choice", "number", "text"
    KINDS = [(CHOICE, "Выбор из списка"), (NUMBER, "Число"), (TEXT, "Текст")]

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="attributes")
    key = models.SlugField("Ключ", help_text="Латиницей, например: watt")
    name = models.CharField("Название", max_length=80)
    kind = models.CharField("Тип", max_length=10, choices=KINDS, default=TEXT)
    unit = models.CharField("Единица", max_length=16, blank=True)
    choices = models.TextField("Варианты", blank=True, help_text="Для списка: по одному варианту в строке")
    order = models.PositiveSmallIntegerField("Порядок", default=0)
    show_in_card = models.BooleanField("Показывать в карточке", default=True)

    class Meta:
        ordering = ["order", "id"]
        unique_together = [("category", "key")]
        verbose_name = "Характеристика"
        verbose_name_plural = "Характеристики"

    def __str__(self):
        return f"{self.category.name}: {self.name}"

    def choice_list(self):
        return [c.strip() for c in self.choices.splitlines() if c.strip()]

    @property
    def label(self):
        return f"{self.name}, {self.unit}" if self.unit else self.name


class Listing(models.Model):
    RENT, SALE = "rent", "sale"
    DEALS = [(RENT, "Аренда"), (SALE, "Продажа")]

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="listings")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="listings")
    deal = models.CharField("Сделка", max_length=4, choices=DEALS, default=RENT)
    title = models.CharField("Название", max_length=140)
    price = models.PositiveIntegerField("Цена, ₽", help_text="Для аренды — цена за сутки")
    city = models.CharField("Город", max_length=80)
    contact = models.CharField("Контакт", max_length=120, help_text="Телефон или Telegram")
    description = models.TextField("Описание", blank=True)
    photo = models.ImageField("Фото", upload_to="photos/", blank=True)
    is_active = models.BooleanField("Показывать в каталоге", default=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]
        verbose_name = "Объявление"
        verbose_name_plural = "Объявления"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("detail", args=[self.pk])

    @property
    def price_label(self):
        s = f"{self.price:,}".replace(",", " ") + " ₽"
        return s + " / сутки" if self.deal == self.RENT else s

    def sorted_values(self):
        vals = list(self.values.all())
        vals.sort(key=lambda v: (v.attribute.order, v.attribute_id))
        return vals

    def card_values(self):
        return [v for v in self.sorted_values() if v.attribute.show_in_card][:4]


class ListingValue(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="values")
    attribute = models.ForeignKey(AttributeDef, on_delete=models.CASCADE)
    text = models.CharField(max_length=200, blank=True)
    number = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = [("listing", "attribute")]

    def __str__(self):
        return f"{self.attribute.name}: {self.display()}"

    def display(self):
        if self.attribute.kind == AttributeDef.NUMBER and self.number is not None:
            s = f"{self.number.normalize():f}"
        else:
            s = self.text
        return f"{s} {self.attribute.unit}".strip()


class Inquiry(models.Model):
    """Заявка на аренду или покупку."""
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="inquiries")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="inquiries")
    date_from = models.DateField("С", null=True, blank=True)
    date_to = models.DateField("По", null=True, blank=True)
    message = models.TextField("Сообщение", blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"

    def __str__(self):
        return f"{self.author} → {self.listing}"
