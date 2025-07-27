from django.urls import path
from . import views

urlpatterns = [
    path('predict/', views.predict_melanoma, name='predict_melanoma'),
    path('health/', views.health_check, name='health_check'),
    path('chatbot/', views.chatbot, name='chatbot'),
] 