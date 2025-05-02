from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('profile/', views.profile_view, name='profile'),
    path('events/', views.events_view, name='events'),
    path('updates/', views.updates_view, name='updates'),
    path('forum/', views.forum_list, name='forum'),
    path('forum/create/', views.forum_create, name='forum_create'),
    path('forum/update/<int:post_id>/', views.forum_update, name='forum_update'),
    path('forum/delete/<int:post_id>/', views.forum_delete, name='forum_delete'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
]
