import json
import csv
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.views import PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.forms import inlineformset_factory
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_POST
from .forms import (
    CommentForm,
    CustomUserCreationForm,
    EventForm,
    ForumPostForm,
    JobEntryForm,
    JobEntryFormSet,
    ClubOrgForm,
    UpdatesForm,
    UserProfileForm,
    AdminProfileForm,
)
from .models import Comment, CustomUser, Event, Forum, JobEntry, Like, Updates


def admin_register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        verifier_username = request.POST.get('verifier_username')
        verifier_password = request.POST.get('verifier_password')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('admin_register')

        verifier = authenticate(username=verifier_username, password=verifier_password)
        if verifier is None or not verifier.is_staff:
            messages.error(request, "Verification failed. Invalid admin credentials.")
            return redirect('admin_register')

        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect('admin_register')

        CustomUser.objects.create_admin(
            username=username,
            password=password,
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'), 
            
            is_staff=True,
            is_superuser=False 
        )
        messages.success(request, "Admin account created successfully.")
        return redirect('login')

    return render(request, 'admin_register.html')

CustomUser = get_user_model()

def is_admin(user):
    return user.is_staff or user.is_superuser

@login_required
# @user_passes_test(is_admin)
def post_login_redirect(request):
    user = request.user
    if user.is_staff:
        return redirect('admin_dashboard')  
    else:
        return redirect('home')

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    return render(request, 'admin_panel/admin_dashboard.html')

## ADMIN USER

@login_required
@user_passes_test(is_admin)
def admin_profile_view(request):
    form = AdminProfileForm(instance=request.user)

    if request.method == 'POST':
        form = AdminProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('admin_profile')

    edit_mode = request.method == 'POST' or request.GET.get('edit') == '1'
    return render(request, 'admin_panel/admin_profile.html', {
        'form': form,
        'edit_mode': edit_mode,
        'admin_user': request.user,
    })

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
def admin_user_batch_upload(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'This is not a CSV file.')
            return redirect('admin_user_batch_upload')

        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)

        created_count = 0
        for row in reader:
            student_number = row.get('student_number')
            first_name = row.get('first_name')
            last_name = row.get('last_name')
            email = row.get('email')
            contact = row.get('contact')
            birthday = row.get('birthday')
            address =  row.get('address')
            curr_location = row.get('curr_location')
            degree = row.get('degree')
            year_attended = row.get('year_attended')
            year_graduated = row.get('year_graduated')

            if not student_number:
                continue

            if CustomUser.objects.filter(student_number=student_number).exists():
                continue  # Skip duplicates

            user = CustomUser.objects.create_user(
                student_number=student_number,
                password=student_number,
                first_name=first_name,
                last_name=last_name,
                email=email,
                degree=degree,
                year_graduated=year_graduated
            )
            created_count += 1

        messages.success(request, f'{created_count} users created successfully.')
        return redirect('admin_user_list')

    return render(request, 'admin_panel/csv_upload.html')

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
@user_passes_test(is_admin)
def admin_user_delete(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_active = False
    user.save()
    messages.success(request, f"{user.get_full_name or user.username} has been deactivated.")
    return redirect('admin_user_list')

@login_required
@user_passes_test(is_admin)
def admin_user_reset_password(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    new_password = user.student_number or user.username
    user.set_password(new_password)
    user.save()
    messages.success(request, f"Password for {user.get_full_name or user.username} has been reset to: {new_password}")
    return redirect('admin_user_list')


## ADMIN EVENT

@login_required
@user_passes_test(is_admin)
def admin_event_list(request):
    query = request.GET.get('q', '')
    sort_by = request.GET.get('sort', '-created_at')
    events = Event.objects.all().order_by('done', sort_by)

    if query:
        events = events.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(datetime__icontains=query) |
            Q(location__icontains=query)
        )  

    return render(request, 'admin_panel/event_list.html', {'events': events, query: query})

@login_required
@user_passes_test(is_admin)
def admin_event_create(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event created successfully.')
            return redirect('admin_event_list')
    else:
        form = EventForm()
    return render(request, 'admin_panel/event_form.html', {'form': form, 'is_edit': False})

@login_required
@user_passes_test(is_admin)
def admin_event_edit(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event updated successfully.')
            return redirect('admin_event_list')
    else:
        form = EventForm(instance=event)
    return render(request, 'admin_panel/event_form.html', {'form': form, 'is_edit': True})

@login_required
@user_passes_test(is_admin)
def admin_event_delete(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.delete()
    messages.success(request, f'Event "{event.title}" has been deleted.')
    return redirect('admin_event_list')

@login_required
@user_passes_test(is_admin)
def admin_event_mark_done(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.done = True
    event.save()
    return redirect('admin_event_list')


## ADMIN UPDATES

@login_required
@user_passes_test(is_admin)
def admin_updates_list(request):
    query = request.GET.get('q', '')
    sort_by = request.GET.get('sort', '-date_posted')
    updates = Updates.objects.order_by(sort_by)

    if query:
        updates = updates.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(date_posted__icontains=query) |
            Q(related_event__title__icontains=query)
        )  

    return render(request, 'admin_panel/updates_list.html', {'updates': updates})


@login_required
@user_passes_test(is_admin)
def admin_updates_create(request):
    if request.method == 'POST':
        form = UpdatesForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_updates_list')
    else:
        form = UpdatesForm()
    return render(request, 'admin_panel/updates_form.html', {'form': form, 'is_edit': False})

@login_required
@user_passes_test(is_admin)
def admin_updates_edit(request, update_id):
    update = get_object_or_404(Updates, pk=update_id)
    if request.method == 'POST':
        form = UpdatesForm(request.POST, instance=update)
        if form.is_valid():
            form.save()
            return redirect('admin_updates_list')
    else:
        form = UpdatesForm(instance=update)
    return render(request, 'admin_panel/updates_form.html', {'form': form, 'is_edit': True})

@login_required
@user_passes_test(is_admin)
def admin_updates_delete(request, update_id):
    update = get_object_or_404(Updates, pk=update_id)
    update.delete()
    return redirect('admin_updates_list')


## ADMIN FORUM

@login_required
@user_passes_test(is_admin)
def admin_forum_list(request):
    query = request.GET.get('q', '')
    posts = Forum.objects.select_related('author').prefetch_related('comments__user').order_by('-date_posted')

    if query:
        posts = posts.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(author__student_number__icontains=query) |
            Q(author__first_name__icontains=query) |
            Q(author__last_name__icontains=query) |
            Q(date_posted__icontains=query) 
        )

    posts = posts.order_by('-date_posted')
    return render(request, 'admin_panel/forum_list.html', {'posts': posts, 'query': query})

@login_required
@user_passes_test(is_admin)
def admin_delete_post(request, post_id):
    post = get_object_or_404(Forum, id=post_id)
    post.delete()
    return redirect('admin_forum_list')


## USER SIDE

@login_required
def home(request):
    user = request.user
    profile = user  # Assuming CustomUser is your user model

    events = Event.objects.filter(datetime__gte=timezone.now()).order_by('datetime')[:2]
    updates = Updates.objects.order_by('-date_posted')[:2]

    stats = {
        'posts': Forum.objects.filter(author=user).count(),
        'comments': Comment.objects.filter(user=user).count(),
    }

    return render(request, 'home.html', {
        'user': user,
        'profile': profile,
        'events': events,
        'updates': updates,
        'stats': stats,
    })


@login_required
def profile_view(request):
    user = request.user
    can_edit = request.GET.get('edit') == '1'

    JobEntryFormSet = inlineformset_factory(CustomUser, JobEntry, form=JobEntryForm, extra=1, can_delete=True)
    ClubOrgFormSet = inlineformset_factory(CustomUser, ClubOrg, form=ClubOrgForm, extra=1, can_delete=True)

    if request.method == 'POST' and can_edit:
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        job_formset = JobEntryFormSet(request.POST, instance=user)
        club_formset = ClubOrgFormSet(request.POST, instance=user)

        if form.is_valid() and job_formset.is_valid() and club_formset.is_valid():
            form.save()
            job_entries = job_formset.save(commit=False)

            # Reset all job entries' is_current flags
            JobEntry.objects.filter(user=user).update(is_current=False)

            for job in job_entries:
                job.user = user
                if not job.is_current:
                    job.is_current = True
                job.save()
            job_formset.save_m2m()
            club_formset.save()

            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user)
        job_formset = JobEntryFormSet(instance=user)
        club_formset = ClubOrgFormSet(instance=user)

    job_entries = user.job_entries.all().order_by('-date_added')
    club_orgs = user.club_orgs.all()

    return render(request, 'core/profile.html', {
        'form': form,
        'formset': job_formset,
        'club_formset': club_formset,
        'can_edit': can_edit,
        'user_profile': user,
        'job_entries': job_entries,
        'club_orgs': club_orgs,
    })

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('post-login-redirect')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

@login_required
def events_view(request):
    events = Event.objects.all()

    # Get Attendance entries for the logged-in user
    attended_events = Attendance.objects.filter(user=request.user).select_related('event')
    attended_event_ids = attended_events.values_list('event_id', flat=True)

    context = {
        'events': events,
        'attended_event_ids': attended_event_ids,
        'attended_events': [entry.event for entry in attended_events],  # for sidebar
    }
    return render(request, 'core/events.html', context)

@login_required
def mark_attended(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    Attendance.objects.get_or_create(user=request.user, event=event)
    return redirect('events')

@login_required
def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    attended = Attendance.objects.filter(user=request.user, event=event).exists()
    return render(request, 'core/event_detail.html', {'event': event, 'attended': attended, 'now': timezone.now()})

@login_required
def updates_view(request):
    updates = Updates.objects.order_by('-date_posted')
    recent_updates = Updates.objects.order_by('-date_posted')[:5]
    return render(request, 'core/updates.html', {
        'updates': updates,
        'recent_updates': recent_updates
    })

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

    if post.author != request.user and not request.user.is_staff:
        return redirect('forum')

    if request.method == 'POST':
        post.delete()
        return redirect('forum')
    
    return render(request, 'core/forum_delete.html', {'post': post})



def global_search_view(request):
    query = request.GET.get('q')
    users = admins = events = updates = forums = []

    if query:
        users = CustomUser.objects.filter(
            Q(is_staff=False) &
            (Q(student_number__icontains=query) |
             Q(first_name__icontains=query) |
             Q(last_name__icontains=query) |
             Q(address__icontains=query) |
             Q(degree__icontains=query) |
             Q(year_graduated__icontains=query))
            #  Q(org_name__icontains=query) |
            #  Q(job_title__icontains=query))
        )

        admins = CustomUser.objects.filter(
            Q(is_staff=True) &
            (Q(first_name__icontains=query) |
             Q(last_name__icontains=query) |
             Q(username__icontains=query))
        )

        events = Event.objects.filter(
            Q(title__icontains=query) |
            Q(location__icontains=query) |
            Q(description__icontains=query)
        )

        updates = Updates.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(related_event__title__icontains=query)
        )

        forum = Forum.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(author__first_name__icontains=query) |
            Q(author__last_name__icontains=query)
        )

    context = {
        'query': query,
        'users': users,
        'admins': admins,
        'events': events,
        'updates': updates,
        'forums': forums,  
    }
    return render(request, 'search_results.html', context)


class CustomPasswordChangeView(SuccessMessageMixin, PasswordChangeView):
    template_name = 'change_password.html'
    success_url = reverse_lazy('change_password')
    success_message = "Your password was successfully updated."

def logout_view(request):
    logout(request)
    return redirect('login')    