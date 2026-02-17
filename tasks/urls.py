from django.urls import path
from . import views
urlpatterns = [
	path('', views.index, name="list"),
     path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
	path('update_task/<str:pk>/', views.updateTask, name="update_task"),
	path('delete_task/<str:pk>/', views.deleteTask, name="delete"),
	path('add/<str:provider>/', views.add_series_to_watchlist, name='add_series'),
    
	# France Connect
    path('fc/login/', views.fc_login_redirect, name='france_connect_login'),
    path('callback/', views.fc_callback, name='france_connect_callback')
]