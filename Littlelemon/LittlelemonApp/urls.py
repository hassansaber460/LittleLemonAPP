from django.urls import path
from . import views

urlpatterns = [
    path(
        'categories/<slug:slug>/',
        views.CategoryDetailView.as_view(),
        name='category-detail'
    ),
    path('menu-item/<str:title>', views.MenuItemDetailView.as_view(), name='menu-item-detail'),
    path('categories', views.CategoryViews.as_view()),
    path('menu-item', views.MenuItemViews.as_view(), name='menu-item'),

]
