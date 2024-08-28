from django.urls import path
from .views import register_view, login_view, edit_operator_profile, logout, change_password

urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('edit-profile/', edit_operator_profile, name='edit-profile'),
    path('logout/', logout, name='logout'),
    path('change-password/', change_password, name='change-password'),
]
