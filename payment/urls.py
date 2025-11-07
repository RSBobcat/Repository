from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    # Stripe URLs
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('stripe/success/', views.stripe_success, name='stripe_success'),
    path('stripe/cancel/', views.stripe_cancel, name='stripe_cancel'),
    
    # Heleket URLs
    path('heleket/webhook/', views.heleket_webhook, name='heleket_webhook'),
    path('heleket/success/', views.heleket_success, name='heleket_success'),
    path('heleket/cancel/', views.heleket_cancel, name='heleket_cancel'),
    path('heleket/processing/', views.heleket_processing, name='heleket_processing'),
]