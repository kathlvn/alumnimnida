from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.http import JsonResponse, HttpRequest, HttpResponse
import json
from django.forms import inlineformset_factory
from django.urls import reverse
from django.contrib import messages
from .models import CustomUser, JobEntry, Event, Updates, Forum, Like, Comment
from .forms import CustomUserCreationForm, ForumPostForm, UserProfileForm, JobEntryForm, CommentForm
from django.utils.crypto import get_random_string
from django.db.models import Q




CustomUser = get_user_model()

def is_admin(user):
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(is_admin)
def admin_user_list(request):
    query = request.GET.get('q', '')
    users = CustomUser.objects.all()

    if query:
        users = users.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(student_number__icontains=query) |
            Q(year_graduated__icontains=query) |
            Q(degree__icontains=query)
        )

    return render(request, 'admin_panel/user_list.html', {'users': users, 'query': query})

@login_required
@user_passes_test(is_admin)
def admin_user_create(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_user_list')
    else:
        form = CustomUserCreationForm()
    return render(request, 'admin_panel/user_form.html', {'form': form, 'is_edit': False})

@login_required
@user_passes_test(is_admin)
def admin_user_edit(request, user_id):
    print("edit")
    user = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, instance=user)
        if form.is_valid():
            print("valid")
            form.save()
            return redirect('admin_user_list')
    else:
        form = CustomUserCreationForm(instance=user)
    return render(request, 'admin_panel/user_form.html', {'form': form, 'is_edit': True})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_user_delete(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_active = False
    user.save()
    messages.success(request, f"{user.get_full_name or user.username} has been deactivated.")
    return redirect('admin_user_list')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_user_reset_password(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    new_password = user.username  # Or use `get_random_string(8)` if you want random
    user.set_password(new_password)
    user.save()
    messages.success(request, f"Password for {user.get_full_name() or user.username} has been reset to: {new_password}")
    return redirect('admin_user_list')


@login_required
def home(request): #kanan stats po in
    stats = {
        'total_alumni': CustomUser.objects.filter(is_active=True).count(),
        'total_events': Event.objects.count(),
        'total_posts': Forum.objects.count(),
        'total_updates': Updates.objects.count(),
        'total_comments': Comment.objects.count(),
    }
    return render(request, 'core/home.html', stats)



JobEntryFormSet = inlineformset_factory(CustomUser, JobEntry, form=JobEntryForm, extra=1, can_delete=True)
@login_required
def profile_view(request):
    user = request.user
    can_edit = request.GET.get('edit') == '1'

    if request.method == 'POST' and can_edit:
        form = UserProfileForm(request.POST, instance=user)
        formset = JobEntryFormSet(request.POST, instance=user)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user)
        formset = JobEntryFormSet(instance=user)

    return render(request, 'core/profile.html', {
        'form': form,
        'formset': formset,
        'can_edit': can_edit
    })

@login_required
def add_job_entry(request):
    if request.method == 'POST':
        form = JobEntryForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.user = request.user
            job.save()
            return redirect('profile?edit=1')  # return to edit mode
    return redirect('profile?edit=1')

@login_required
def edit_job_entry(request, entry_id):
    job = get_object_or_404(JobEntry, id=entry_id, user=request.user)
    if request.method == 'POST':
        form = JobEntryForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            return redirect('profile?edit=1')
    else:
        form = JobEntryForm(instance=job)
    return render(request, 'core/edit_job_entry.html', {'form': form, 'job': job})

@login_required
def delete_job_entry(request, entry_id):
    job = get_object_or_404(JobEntry, id=entry_id, user=request.user)
    if request.method == 'POST':
        job.delete()
        return redirect('profile?edit=1')
    return render(request, 'core/jobentry_confirm_delete.html', {'job': job})


@login_required
def events_view(request):
    events = Event.objects.order_by('-date')
    return render(request, 'core/events.html', {'events': events})



def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')



@login_required
def updates_view(request):
    updates = Updates.objects.order_by('-date_posted')
    return render(request, 'core/updates.html', {'updates': updates})

@login_required
def change_password_view(request):
    return render(request, 'core/change_password.html')


@login_required
def forum_list(request):
    posts = Forum.objects.all().order_by('-date_posted')


    if request.method == 'POST':
        if 'like_post' in request.POST:
            post_id = request.POST.get('like_post')
            post = get_object_or_404(Forum, id=post_id)
            like, created = Like.objects.get_or_create(user=request.user, post=post)
            if not created:
                like.delete()
            return redirect('forum')

        elif 'comment_post' in request.POST:
            post_id = request.POST.get('comment_post')
            comment_content = request.POST.get('comment_content')
            post = get_object_or_404(Forum, id=post_id)
            if comment_content:
                Comment.objects.create(user=request.user, post=post, content=comment_content)
            return redirect('forum')

        elif 'create_post' in request.POST:
            form = ForumPostForm(request.POST)
            if form.is_valid():
                forum = form.save(commit=False)
                forum.author = request.user
                forum.save()
            return redirect('forum')
        
    for post in posts:
        post.edit_form = ForumPostForm(instance=post)


    create_form = ForumPostForm()
    comment_form = CommentForm()

  
    liked_post_ids = Like.objects.filter(user=request.user).values_list('post_id', flat=True)

    return render(request, 'core/forum_list.html', {
        'posts': posts,
        'create_form': create_form,
        'comment_form': comment_form,
        'liked_post_ids': liked_post_ids,
    })

@require_POST
@login_required
def like_post_ajax(request):
    post_id = request.POST.get('post_id')
    post = get_object_or_404(Forum, id=post_id)

    like, created = Like.objects.get_or_create(user=request.user, post=post)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True

    return JsonResponse({
        'liked': liked,
        'like_count': post.likes.count()
    })

@require_POST
def comment_post_ajax(request):
    data = json.loads(request.body)
    post_id = data.get('post_id')
    comment_content = data.get('comment_content')

    post = get_object_or_404(Forum, id=post_id)

    if comment_content.strip():
        comment = Comment.objects.create(
            user=request.user,
            post=post,
            content=comment_content
        )
        return JsonResponse({
            'success': True,
            'user_name': request.user.first_name,
            'comment_content': comment.content
        })

    return JsonResponse({'success': False})

@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.user != request.user and not request.user.is_staff:
        return redirect('forum')

    if request.method == 'POST':
        comment.delete()
        return redirect('forum')

    return render(request, 'core/comment_delete_confirm.html', {'comment': comment})



@login_required
def forum_create(request):
    # if request.user.is_staff:
    #     return redirect('forum_list')  # Staff can't create
    if request.method == 'POST':
        print("submitted")
        form = ForumPostForm(request.POST)
        if form.is_valid():
            print("valid")
            forum = form.save(commit=False)
            forum.author = request.user
            forum.save()
            return redirect('forum')
    else:
        form = ForumPostForm()
    return render(request, 'core/forum_create.html', {'form': form})

@login_required
def forum_update(request, post_id):
    post = get_object_or_404(Forum, id=post_id)

    # Only author can update
    if post.author != request.user:
        return redirect('forum')

    if request.method == 'POST':
        form = ForumPostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect('forum')
    else:
        form = ForumPostForm(instance=post)
    
    return render(request, 'core/forum_update.html', {'form': form})

@login_required
def forum_delete(request, post_id):
    post = get_object_or_404(Forum, id=post_id)

    # Author or staff can delete
    if post.author != request.user and not request.user.is_staff:
        return redirect('forum')

    if request.method == 'POST':
        post.delete()
        return redirect('forum')
    
    return render(request, 'core/forum_delete.html', {'post': post})

def logout_view(request):
    logout(request)
    return redirect('login')    


