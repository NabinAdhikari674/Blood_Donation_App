from django.urls import path
from . import views

app_name = 'user'

urlpatterns = [
    path('getcsrf/', views.get_csrf, name='getcsrf'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.user_register, name='register'),
    path('getuser/', views.getuser, name='getuser'),
    path('getaddress/', views.getaddress, name='getaddress'),
    path('putaddress/', views.putaddress, name='putaddress'),
    path('getbloodgroup/', views.getbloodgroup, name='getbloodgroup'),
    path('putbloodgroup/', views.putbloodgroup, name='putbloodgroup')
]