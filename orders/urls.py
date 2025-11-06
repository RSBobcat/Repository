from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('create/', views.CreateOrderView.as_view(), name='create'),
    path('success/<int:order_id>/', views.OrderSuccessView.as_view(), name='success'),
    path('history/', views.OrderHistoryView.as_view(), name='history'),
    path('detail/<int:order_id>/', views.OrderDetailView.as_view(), name='detail'),
]