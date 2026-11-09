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
    path('create-new-user', views.UserViews.as_view()),
    path("login/", views.LoginView.as_view(), name="login"),
    path('cart/menu-items', views.CartView.as_view()),
    path('orders', views.OrderView.as_view()),
    path('orders/<int:pk>', views.SingleOrderView.as_view()),
    path('groups/manager/users', views.GroupViewSet.as_view(
        {'get': 'list', 'post': 'create', 'delete': 'destroy'})),

    path('groups/delivery-crew/users', views.DeliveryCrewViewSet.as_view(
        {'get': 'list', 'post': 'create', 'delete': 'destroy'}))

]
