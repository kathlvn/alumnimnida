from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import CustomPasswordChangeView
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('redirect-after-login/', views.post_login_redirect, name='post-login-redirect'),

    path('admin-register/', views.admin_register, name='admin_register'),

    path('admin-panel/admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/profile/', views.admin_profile_view, name='admin_profile'),
    path('admin-panel/users/', views.admin_user_list, name='admin_user_list'),
    path('admin-panel/users/add/', views.admin_user_create, name='admin_user_create'),
    path('admin-panel/users/<int:user_id>/edit/', views.admin_user_edit, name='admin_user_edit'),
    path('admin-panel/users/<int:user_id>/delete/', views.admin_user_delete, name='admin_user_delete'),
    path('admin-panel/users/<int:user_id>/reset/', views.admin_user_reset_password, name='admin_user_reset_password'),
    path('admin-panel/users/batch-upload/', views.admin_user_batch_upload, name='admin_user_batch_upload'),


    path('admin-panel/events/', views.admin_event_list, name='admin_event_list'),
    path('admin-panel/events/add/', views.admin_event_create, name='admin_event_create'),
    path('admin-panel/events/<int:event_id>/edit/', views.admin_event_edit, name='admin_event_edit'),
    path('admin-panel/events/<int:event_id>/delete/', views.admin_event_delete, name='admin_event_delete'),
    path('admin-panel/events/done/<int:event_id>/', views.admin_event_mark_done, name='admin_event_mark_done'),
  
    path('admin-panel/updates/', views.admin_updates_list, name='admin_updates_list'),
    path('admin-panel/updates/add/', views.admin_updates_create, name='admin_updates_create'),
    path('admin-panel/updates/edit/<int:update_id>/', views.admin_updates_edit, name='admin_updates_edit'),
    path('admin-panel/updates/delete/<int:update_id>/', views.admin_updates_delete, name='admin_updates_delete'),

    path('admin-panel/forum/', views.admin_forum_list, name='admin_forum_list'),
    path('admin-panel/forum/delete/<int:post_id>/', views.admin_delete_post, name='admin_delete_post'),




    path('', views.home, name='home'),
    path('profile/', views.profile_view, name='profile'),
    # path('profile/job/add/', views.add_job_entry, name='add_job_entry'),
    # path('edit-job/<int:entry_id>/', views.edit_job_entry, name='edit_job_entry'),
    # path('profile/job/delete/<int:job_id>/', views.delete_job_entry, name='delete_job_entry'),


    path('events/', views.events_view, name='events'),
    path('events/attend/<int:event_id>/', views.mark_attended, name='mark_attended'),
    path('updates/', views.updates_view, name='updates'),

    path('forum/', views.forum, name='forum'),
    path('like-post/', views.like_post_ajax, name='like_post_ajax'),
    path('forum/comment/', views.comment_post_ajax, name='comment_post'),
    path('forum/create/', views.forum_create, name='forum_create'),
    path('forum/update/<int:post_id>/', views.forum_update, name='forum_update'),
    path('forum/delete/<int:post_id>/', views.forum_delete, name='forum_delete'),
    path('forum/comment/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),

    path('search/', views.global_search_view, name='global_search'),
    path('change-password/', CustomPasswordChangeView.as_view(), name='change_password'),
    path('logout/', views.logout_view, name='logout'),
]
