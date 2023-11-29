from django.urls import path
from . import views

app_name = 'user'

urlpatterns = [
    path('getcsrf/', views.get_csrf, name='getcsrf'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.user_register, name='register'),
    path('update/', views.user_update, name='update'),

    path('addItem/', views.item_add, name='addItem'),
    path('getItems/', views.item_get, name='getItems'),
    path('getAllItems/', views.item_get_all, name='getAllItems'), # All items regardless of user
    path('sellItem/', views.item_sell, name='sellItem'),
    path('getSalesItems/', views.item_get_sales, name='getSalesItems'),
    path('getExpiryItems/', views.item_get_expiry, name='getExpiryItems'),
    path('getNotifications/', views.get_notifications, name='getNotifications'),

    path('createPost/', views.post_create, name='createPost'),
    path('getPostEmergency/', views.post_get_emergency, name='getPostEmergency'),
    path('getPostRegular/', views.post_get_regular, name='getPostRegular'),
    path('getAlerts/', views.get_alerts, name='getAlerts'),

    path('getuser/', views.getuser, name='getuser'),
    path('getaddress/', views.getaddress, name='getaddress'),
    path('putaddress/', views.putaddress, name='putaddress'),
    path('getbloodgroup/', views.getbloodgroup, name='getbloodgroup'),
    path('putbloodgroup/', views.putbloodgroup, name='putbloodgroup')
]