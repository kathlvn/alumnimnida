import json
import csv
from django.contrib import messages
from collections import Counter
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.views import PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.db.models import Count, F, ExpressionWrapper, IntegerField
from django.forms import inlineformset_factory
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_POST
from django.views.generic import DetailView
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
    UserProfileEditForm,
    AdminProfileForm,
)
from .models import Comment, CustomUser, Event, Forum, JobEntry, ClubOrg, Like, Updates, Batch, Degree
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.timezone import now
from datetime import date



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
            full_name=request.POST.get('full_name'),
            
            is_staff=True,
            is_superuser=False 
        )
        messages.success(request, "Admin account created successfully.")
        return redirect('login')

    return render(request, 'admin_register.html')


def is_admin(user):
    return user.is_staff or user.is_superuser

# @login_required
# @user_passes_test(is_admin)
# def post_login_redirect(request):
#     user = request.user
#     if user.is_staff:
#         return redirect('admin_dashboard')  
#     else:
#         return redirect('home')

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    degrees = CustomUser.objects.values_list('degree', flat=True)
    count = Counter(degrees)

    course_data = {
        "IT": count.get("IT", 0),
        "CS": count.get("CS", 0),
        "ACT": count.get("ACT", 0),
        "EMC": count.get("EMC", 0)
    }

    return render(request, 'admin_panel/admin_dashboard.html', {
        'course_data': course_data,
        'user': request.user
    })

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
            Q(full_name__icontains=query) |
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
            full_name = row.get('full_name')
            address =  row.get('address')
            degree = row.get('degree')
            year_graduated = row.get('year_graduated')

            if not student_number:
                continue

            if CustomUser.objects.filter(student_number=student_number).exists():
                continue  # skip dupes

            user = CustomUser.objects.create_user(
                student_number=student_number,
                password=student_number,
                full_name=full_name,
                address=address,
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
    user_name = user.full_name or user.username
    user.delete()
    messages.success(request, f"{user_name} has been deactivated.")
    return redirect('admin_user_list')

@login_required
@user_passes_test(is_admin)
def admin_user_reset_password(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    new_password = user.student_number or user.username
    user.set_password(new_password)
    user.save()
    messages.success(request, f"Password for {user.full_name or user.username} has been reset to: {new_password}")
    return redirect('admin_user_list')


## ADMIN EVENT

@login_required
@user_passes_test(is_admin)
def admin_event_list(request):
    query = request.GET.get('q', '')
    sort_by = request.GET.get('sort', '-created_at')
    today = date.today()

    if query:
        events = events.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(date__icontains=query) |
            Q(location__icontains=query)
        )  

    events = Event.objects.all().order_by(sort_by)
    events= list(events)
    events.sort(key=lambda e:e.done)

    return render(request, 'admin_panel/event_list.html', {'events': events, query: query, 'today': date.today(),})

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
    if not event.done:
        event.done = True
        event.save()
        messages.success(request, f'Event "{event.title}" marked as done.')
    else:
        messages.info(request, f'Event "{event.title}" is already done.')
    return redirect('admin_event_list')


## ADMIN UPDATES

@login_required
@user_passes_test(is_admin)
def admin_updates_list(request):
    query = request.GET.get('q', '')
    sort_by = request.GET.get('sort', '-date_posted')
    updates = Updates.objects.all().order_by(sort_by)


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
            Q(author__full_name__icontains=query) |
            Q(date_posted__icontains=query) 
        )

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
    current_datetime = timezone.now()
    upcoming_events = Event.objects.filter(date__gte=timezone.now()).order_by('date')[:5]
    recent_updates = Updates.objects.all().order_by('-date_posted')
    forum_posts_count = Forum.objects.filter(author=request.user).count()
    comments_count = Comment.objects.filter(user=user).count()
    

    return render(request, 'core/home.html', {
        'user': user,
        'upcoming_events': upcoming_events,
        'recent_updates': recent_updates,
        'forum_posts_count': forum_posts_count,
        'comments_count': comments_count,
    })



@login_required
def profile_view(request):
    user = request.user

    job_entries = user.job_entries.all().order_by('-date_added')
    club_orgs = user.club_orgs.all()

    context = {
        'user_profile': user,
        'job_entries': job_entries,
        'club_orgs': club_orgs,
        'can_edit': False,  # no editing in this view
    }

    return render(request, 'core/profile.html', context)


@login_required
def profile_edit_view(request):
    user = request.user

    JobEntryFormSet = inlineformset_factory(CustomUser, JobEntry, form=JobEntryForm, extra=1, can_delete=True)
    ClubOrgFormSet = inlineformset_factory(CustomUser, ClubOrg, form=ClubOrgForm, extra=1, can_delete=True)

    if request.method == 'POST':
        form = UserProfileEditForm(request.POST, request.FILES, instance=user)
        job_formset = JobEntryFormSet(request.POST, instance=user)
        club_formset = ClubOrgFormSet(request.POST, instance=user)

        if form.is_valid() and job_formset.is_valid() and club_formset.is_valid():
            form.save()
            job_entries = job_formset.save(commit=False)

            JobEntry.objects.filter(user=user).update(is_current=False)
            for job in job_entries:
                job.user = user
                if not job.is_current:
                    job.is_current = True
                job.save()
            job_formset.save_m2m()
            club_formset.save()

            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')  # Redirect to read-only profile page
    else:
        form = UserProfileEditForm(instance=user)
        job_formset = JobEntryFormSet(instance=user)
        club_formset = ClubOrgFormSet(instance=user)

    context = {
        'form': form,
        'formset': job_formset,
        'club_formset': club_formset,
        'can_edit': True,
    }
    return render(request, 'core/profile.html', context)


class UserProfileDetailView(DetailView):
    model = CustomUser
    template_name = 'core/search_detail.html'
    context_object_name = 'user_profile'


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_staff:
                return redirect('admin_dashboard')
            else:
                return redirect('home')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')



@login_required
def events_view(request):
    user = request.user
    now = timezone.now()
    visibility_filter = request.GET.get('visibility', '')

    # Initial queryset (not done and still upcoming/ongoing)
    events = Event.objects.filter(done=False).exclude(
        Q(date__lt=now.date()) |
        Q(date=now.date(), time__lte=now.time())
    )

    # Apply visibility filter
    if visibility_filter == 'public':
        events = events.filter(visibility_type='public')
    elif visibility_filter == 'batch':
        events = events.filter(visibility_type='batch', visibility_batches__year=user.year_graduated)
    elif visibility_filter == 'degree':
        events = events.filter(visibility_type='degree', visibility_degrees__code=user.degree)
    else:
        events = events.filter(
            Q(visibility_type='public') |
            Q(visibility_type='batch', visibility_batches__year=user.year_graduated) |
            Q(visibility_type='degree', visibility_degrees__code=user.degree)
        ).distinct()

    events = events.order_by('-created_at')

    # Recently concluded = manually marked as done OR past events
    recently_concluded = Event.objects.filter(
        Q(done=True) |
        Q(date__lt=now.date()) |
        Q(date=now.date(), time__lte=now.time())
    ).filter(
        Q(visibility_type='public') |
        Q(visibility_type='batch', visibility_batches__year=user.year_graduated) |
        Q(visibility_type='degree', visibility_degrees__code=user.degree)
    ).distinct().order_by('-date', '-time')[:5]  # limit for panel

    context = {
        'events': events,
        'recently_concluded': recently_concluded,
        'now': now,
        'visibility_filter': visibility_filter
    }

    return render(request, 'core/events.html', context)



@login_required
def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    return render(request, 'core/event_detail.html', {'event': event, 'now': timezone.now()})

class EventDetailView(DetailView):
    model = Event
    template_name = 'core/search_detail.html'
    context_object_name = 'event'

@login_required
def updates_view(request):
    user = request.user
    visibility_filter = request.GET.get('visibility', '')

    updates = Updates.objects.all()

    if visibility_filter == 'public':
        updates = updates.filter(visibility_type='public')
    elif visibility_filter == 'batch':
        updates = updates.filter(visibility_type='batch', visibility_batches__year=user.year_graduated)
    elif visibility_filter == 'degree':
        updates = updates.filter(visibility_type='degree', visibility_degrees__code=user.degree)
    else:
        updates = updates.filter(
            Q(visibility_type='public') |
            Q(visibility_type='batch', visibility_batches__year=user.year_graduated) |
            Q(visibility_type='degree', visibility_degrees__code=user.degree)
        ).distinct()

    updates = updates.order_by('-date_posted')  

    recent_updates = updates[:5]

    return render(request, 'core/updates.html', {
        'updates': updates,
        'recent_updates': recent_updates,
        'visibility_filter': visibility_filter
    })

class UpdateDetailView(DetailView):
    model = Updates
    template_name = 'core/search_detail.html'
    context_object_name = 'updates'

@login_required
def forum(request):
    user = request.user
    posts = Forum.visible.user_visible(request.user).order_by('-date_posted')

    visibility_filter = request.GET.get('visibility', '')
    if visibility_filter == 'public':
        posts = posts.filter(visibility_type='public')
    elif visibility_filter == 'batch':
        posts = posts.filter(visibility_type='batch', visibility_batches__year=user.year_graduated)
    elif visibility_filter == 'degree':
        posts = posts.filter(visibility_type='degree', visibility_degrees__code=user.degree)


    if request.method == 'POST':
        visibility_filter = request.GET.get('visibility', '') or request.POST.get('visibility', '')
        query_param = f'?visibility={visibility_filter}' if visibility_filter else ''
        if 'create_post' in request.POST:
            form = ForumPostForm(request.POST)
            if form.is_valid():
                post = form.save(commit=False)
                post.author = request.user
                post.save()

                post.visibility_batches.clear()
                post.visibility_degrees.clear()

                if post.visibility_type == 'batch':
                    batch = Batch.objects.filter(year=user.year_graduated).first()
                    if batch:
                        post.visibility_batches.add(batch)
                elif post.visibility_type == 'degree':
                    degree = Degree.objects.filter(code=user.degree).first()
                    if degree:
                        post.visibility_degrees.add(degree)

                        

                return redirect(f"{reverse('forum')}{query_param}")


        elif 'like_post' in request.POST:
            post_id = request.POST.get('like_post')
            post = get_object_or_404(Forum, id=post_id)
            existing = Like.objects.filter(user=request.user, post=post)
            if existing.exists():
                existing.delete()
            else:
                Like.objects.create(user=request.user, post=post)
            return redirect(f"{reverse('forum')}{query_param}")


        elif 'comment_post' in request.POST:
            post_id = request.POST.get('comment_post')
            comment_content = request.POST.get('comment_content')
            post = get_object_or_404(Forum, id=post_id)
            if comment_content.strip():
                Comment.objects.create(user=request.user, post=post, content=comment_content)
            return redirect(f"{reverse('forum')}{query_param}")


        elif 'delete_comment' in request.POST:
            comment_id = request.POST.get('delete_comment')
            comment = get_object_or_404(Comment, id=comment_id)
            if comment.user == request.user or request.user.is_staff:
                comment.delete()
            return redirect(f"{reverse('forum')}{query_param}")

        
        elif 'delete_post' in request.POST:
            post_id = request.POST.get('delete_post')
            post = get_object_or_404(Forum, id=post_id)
            if post.author == request.user or request.user.is_staff:
                post.delete()
            return redirect(f"{reverse('forum')}{query_param}")



    # Trending based on likes + comments
    trending_posts = Forum.objects.annotate(
        num_likes=Count('likes'),
        num_comments=Count('comments'),
        popularity=ExpressionWrapper(
            Count('likes') + Count('comments'),
            output_field=IntegerField()
        )
    ).order_by('-popularity')[:5]

    context = {
        'posts': posts,
        'create_form': ForumPostForm(),
        'visibility_filter': visibility_filter,
        'comment_form': CommentForm(),
        'liked_post_ids': Like.objects.filter(user=request.user).values_list('post_id', flat=True),
        'trending_posts': trending_posts
    }

    return render(request, 'core/forum.html', context)


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
            'user_name': request.user.full_name,
            'comment_content': comment.content
        })

    return JsonResponse({'success': False})

@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.user != request.user and not request.user.is_staff:
        return redirect('forum')

    comment.delete()
    return redirect('forum')


class ForumPostDetailView(DetailView):
    model = Forum
    template_name = 'core/search_detail.html'
    context_object_name = 'forum'


def global_search_view(request):
    query = request.GET.get('q')
    users = admins = events = updates = forums = []

    if query:
        users = CustomUser.objects.filter(
            Q(is_staff=False) &
            (Q(student_number__icontains=query) |
             Q(full_name__icontains=query) |
             Q(address__icontains=query) |
             Q(degree__icontains=query) |
             Q(year_graduated__icontains=query))
            #  Q(org_name__icontains=query) |
            #  Q(job_title__icontains=query))
        )

        admins = CustomUser.objects.filter(
            Q(is_staff=True) &
            (Q(full_name__icontains=query) |
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

        forums = Forum.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(author__full_name__icontains=query)
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