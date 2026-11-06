from django.contrib import admin

from .models import AttributeDef, Category, Inquiry, Listing, ListingValue


class AttributeInline(admin.TabularInline):
    model = AttributeDef
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "icon")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [AttributeInline]


class ValueInline(admin.TabularInline):
    model = ListingValue
    extra = 0


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "deal", "price", "city", "owner", "is_active", "created")
    list_filter = ("category", "deal", "is_active")
    search_fields = ("title", "city", "owner__username")
    inlines = [ValueInline]


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ("listing", "author", "date_from", "date_to", "created")
