from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import InquiryForm, ListingForm
from .models import AttributeDef, Category, Inquiry, Listing

SORTS = {"new": "-created", "p1": "price", "p2": "-price"}


def _num(value):
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError):
        return None


def listing_list(request):
    g = request.GET
    qs = Listing.objects.filter(is_active=True).select_related("category").prefetch_related("values__attribute")
    cat = Category.objects.filter(slug=g.get("cat")).first() if g.get("cat") else None

    if cat:
        qs = qs.filter(category=cat)
    if g.get("deal") in (Listing.RENT, Listing.SALE):
        qs = qs.filter(deal=g["deal"])
    if (lo := _num(g.get("pmin"))) is not None:
        qs = qs.filter(price__gte=lo)
    if (hi := _num(g.get("pmax"))) is not None:
        qs = qs.filter(price__lte=hi)
    if g.get("city"):
        qs = qs.filter(city__icontains=g["city"])
    if g.get("q"):
        qs = qs.filter(Q(title__icontains=g["q"]) | Q(description__icontains=g["q"]))

    # Фильтры по характеристикам выбранной категории (как «параметры» на auto.ru)
    filters = []
    if cat:
        for a in cat.attributes.all():
            f = {"attr": a, "value": g.get(f"a_{a.key}", ""),
                 "min": g.get(f"a_{a.key}_min", ""), "max": g.get(f"a_{a.key}_max", "")}
            filters.append(f)
            if a.kind == AttributeDef.CHOICE and f["value"]:
                qs = qs.filter(values__attribute=a, values__text=f["value"])
            elif a.kind == AttributeDef.TEXT and f["value"]:
                qs = qs.filter(values__attribute=a, values__text__icontains=f["value"])
            elif a.kind == AttributeDef.NUMBER:
                if (lo := _num(f["min"])) is not None:
                    qs = qs.filter(values__attribute=a, values__number__gte=lo)
                if (hi := _num(f["max"])) is not None:
                    qs = qs.filter(values__attribute=a, values__number__lte=hi)

    qs = qs.order_by(SORTS.get(g.get("sort"), "-created")).distinct()
    page = Paginator(qs, 12).get_page(g.get("page"))
    params = g.copy()
    params.pop("page", None)
    return render(request, "list.html", {
        "categories": Category.objects.all(), "cat": cat, "filters": filters,
        "page_obj": page, "g": g, "qs": params.urlencode(),
    })


def listing_detail(request, pk):
    listing = get_object_or_404(
        Listing.objects.select_related("category", "owner").prefetch_related("values__attribute"), pk=pk)
    is_owner = request.user.is_authenticated and request.user == listing.owner
    if not listing.is_active and not is_owner:
        raise Http404
    form = None
    if request.user.is_authenticated and not is_owner:
        form = InquiryForm(request.POST or None)
        if request.method == "POST" and form.is_valid():
            inq = form.save(commit=False)
            inq.listing, inq.author = listing, request.user
            inq.save()
            messages.success(request, "Заявка отправлена владельцу")
            return redirect(listing)
    return render(request, "detail.html", {
        "l": listing, "values": listing.sorted_values(), "form": form, "is_owner": is_owner,
        "inquiries": listing.inquiries.select_related("author") if is_owner else [],
    })


@login_required
def listing_new(request):
    return render(request, "choose_category.html", {"categories": Category.objects.all()})


@login_required
def listing_create(request, slug):
    cat = get_object_or_404(Category, slug=slug)
    form = ListingForm(request.POST or None, request.FILES or None, category=cat)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.owner, obj.category = request.user, cat
        obj.save()
        form.save_values(obj)
        messages.success(request, "Объявление опубликовано")
        return redirect(obj)
    return render(request, "listing_form.html", {"form": form, "category": cat, "title": "Новое объявление"})


@login_required
def listing_edit(request, pk):
    obj = get_object_or_404(Listing, pk=pk, owner=request.user)
    form = ListingForm(request.POST or None, request.FILES or None, instance=obj, category=obj.category)
    if request.method == "POST" and form.is_valid():
        form.save()
        form.save_values(obj)
        messages.success(request, "Сохранено")
        return redirect(obj)
    return render(request, "listing_form.html", {"form": form, "category": obj.category, "title": "Редактирование"})


@login_required
@require_POST
def listing_delete(request, pk):
    get_object_or_404(Listing, pk=pk, owner=request.user).delete()
    messages.success(request, "Объявление удалено")
    return redirect("my")


@login_required
def my(request):
    return render(request, "my.html", {
        "listings": request.user.listings.select_related("category"),
        "received": Inquiry.objects.filter(listing__owner=request.user).select_related("listing", "author"),
        "sent": request.user.inquiries.select_related("listing"),
    })


def register(request):
    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.save())
        return redirect("list")
    return render(request, "registration/register.html", {"form": form})
