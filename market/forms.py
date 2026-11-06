from django import forms

from .models import AttributeDef, Inquiry, Listing, ListingValue


class ListingForm(forms.ModelForm):
    """Базовые поля + поля характеристик, которые зависят от категории."""

    class Meta:
        model = Listing
        fields = ["deal", "title", "price", "city", "contact", "description", "photo", "is_active"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, category, **kwargs):
        super().__init__(*args, **kwargs)
        self.category = category
        self.attr_names = []
        existing = {}
        if self.instance.pk:
            existing = {v.attribute_id: v for v in self.instance.values.all()}
        if not self.instance.pk:
            self.fields.pop("is_active")
        for a in category.attributes.all():
            if a.kind == AttributeDef.CHOICE:
                field = forms.ChoiceField(choices=[("", "—")] + [(c, c) for c in a.choice_list()], required=False)
            elif a.kind == AttributeDef.NUMBER:
                field = forms.DecimalField(required=False, max_digits=12, decimal_places=2, min_value=0)
            else:
                field = forms.CharField(required=False, max_length=200)
            field.label = a.label
            name = f"attr_{a.key}"
            self.fields[name] = field
            self.attr_names.append(name)
            v = existing.get(a.id)
            if v:
                self.initial[name] = v.number if a.kind == AttributeDef.NUMBER else v.text

    def main(self):
        return [self[n] for n in self.fields if n not in self.attr_names]

    def attrs(self):
        return [self[n] for n in self.attr_names]

    def save_values(self, listing):
        for a in self.category.attributes.all():
            raw = self.cleaned_data.get(f"attr_{a.key}")
            if raw in (None, ""):
                listing.values.filter(attribute=a).delete()
                continue
            is_num = a.kind == AttributeDef.NUMBER
            ListingValue.objects.update_or_create(
                listing=listing, attribute=a,
                defaults={"text": "" if is_num else raw, "number": raw if is_num else None},
            )


class InquiryForm(forms.ModelForm):
    class Meta:
        model = Inquiry
        fields = ["date_from", "date_to", "message"]
        widgets = {
            "date_from": forms.DateInput(attrs={"type": "date"}),
            "date_to": forms.DateInput(attrs={"type": "date"}),
            "message": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        data = super().clean()
        a, b = data.get("date_from"), data.get("date_to")
        if a and b and b < a:
            self.add_error("date_to", "Дата окончания раньше начала")
        return data
