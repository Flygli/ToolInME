from django.urls import path

from . import views

urlpatterns = [
    path("", views.listing_list, name="list"),
    path("listing/<int:pk>/", views.listing_detail, name="detail"),
    path("listing/<int:pk>/edit/", views.listing_edit, name="edit"),
    path("listing/<int:pk>/delete/", views.listing_delete, name="delete"),
    path("new/", views.listing_new, name="new"),
    path("new/<slug:slug>/", views.listing_create, name="create"),
    path("my/", views.my, name="my"),
    path("accounts/register/", views.register, name="register"),
]
