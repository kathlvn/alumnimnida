from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/job/add/', views.add_job_entry, name='add_job_entry'),
    path('edit-job/<int:entry_id>/', views.edit_job_entry, name='edit_job_entry'),
    path('profile/job/delete/<int:job_id>/', views.delete_job_entry, name='delete_job_entry'),
    path('events/', views.events_view, name='events'),
    path('updates/', views.updates_view, name='updates'),
    path('forum/', views.forum_list, name='forum'),
    path('like-post/', views.like_post_ajax, name='like_post_ajax'),
    path('forum/comment/', views.comment_post_ajax, name='comment_post'),
    path('forum/create/', views.forum_create, name='forum_create'),
    path('forum/update/<int:post_id>/', views.forum_update, name='forum_update'),
    path('forum/delete/<int:post_id>/', views.forum_delete, name='forum_delete'),
    path('forum/comment/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
]
