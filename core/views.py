from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    return render(request, 'core/home.html', {'user': request.user})

@login_required
def profile_view(request):
    return render(request, 'core/profile.html')

@login_required
def events_view(request):
    return render(request, 'core/events.html')

@login_required
def updates_view(request):
    return render(request, 'core/updates.html')

@login_required
def forum_view(request):
    return render(request, 'core/forum.html')

@login_required
def change_password_view(request):
    return render(request, 'core/change_password.html')
