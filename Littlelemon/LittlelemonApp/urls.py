from django.urls import path

from . import views


urlpatterns = [
    path("categories/", views.CategoryViews.as_view(), name="category-list"),
    path("categories/<slug:slug>/", views.CategoryDetailView.as_view(), name="category-detail"),
    path("menu-items/", views.MenuItemViews.as_view(), name="menu-item-list"),
    path("menu-items/<str:title>/", views.MenuItemDetailView.as_view(), name="menu-item-detail"),
    path("create-new-user/", views.UserViews.as_view(), name="create-new-user"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("cart/menu-items/", views.CartView.as_view(), name="cart"),
    path("orders/", views.OrderView.as_view(), name="orders"),
    path("orders/<int:pk>/", views.SingleOrderView.as_view(), name="order-detail"),
    path(
        "groups/manager/users",
        views.ManagerGroupViewSet.as_view({"get": "list", "post": "create", "delete": "destroy"}),
        name="manager-users",
    ),
    path(
        "groups/delivery-crew/users",
        views.DeliveryCrewViewSet.as_view({"get": "list", "post": "create", "delete": "destroy"}),
        name="delivery-crew-users",
    ),
]
