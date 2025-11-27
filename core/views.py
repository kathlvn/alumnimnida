import json
import csv
from django.contrib import messages
from collections import Counter, defaultdict
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.views import PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.db.models import Count, F, ExpressionWrapper, IntegerField
from django.db.models.functions import ExtractYear
from django.forms import inlineformset_factory
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_POST
from django.views.generic import DetailView
from django.core.paginator import Paginator
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
from datetime import datetime



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

    # Chart 1: Total alumni by degree
    course_data = {
        "BSIT": count.get("BSIT", 0),
        "BSCS": count.get("BSCS", 0),
        "ACT": count.get("ACT", 0),
        "BSEMC": count.get("BSEMC", 0)
    }

    # Chart 2: Alumni count per year per degree
    alumni_years = (
        CustomUser.objects
        .values('year_graduated', 'degree')
    )

    yearly_distribution = defaultdict(lambda: {"BSIT": 0, "BSCS": 0, "ACT": 0, "BSEMC": 0})
    for record in alumni_years:
        year = record["year_graduated"]
        degree = record["degree"]
        if year:
            yearly_distribution[year][degree] += 1


    # Convert to sorted list for JSON
    yearly_data = [{"year": y, **d} for y, d in sorted(yearly_distribution.items())]

    # provide admin profile form so the dashboard can open the edit modal in-place
    admin_profile_form = AdminProfileForm(instance=request.user)

    return render(request, 'admin_panel/admin_dashboard.html', {
        'course_data': course_data,
        'yearly_data': yearly_data,
        'user': request.user,
        'admin_profile_form': admin_profile_form,
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
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'redirect': reverse('admin_dashboard')})
            return redirect('admin_dashboard')
        # AJAX invalid -> return partial with errors
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render(request, 'admin_panel/partials/admin_profile_partial.html', {
                'admin_profile_form': form,
                'edit_url': reverse('admin_profile')
            })
            return HttpResponse(html.content, status=400)
        return redirect('admin_dashboard')

    # For AJAX GET, return the modal partial so the frontend can inject a pre-populated form
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'admin_panel/partials/admin_profile_partial.html', {
            'admin_profile_form': form,
            'edit_url': reverse('admin_profile')
        })

    # Non-AJAX GET: redirect to dashboard (profile editing available via modal)
    return redirect('admin_dashboard')


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
            Q(address__icontains=query) |
            Q(degree__icontains=query)
        )

    paginator = Paginator(users, 10)  # 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # provide a blank user form for the modal (create)
    user_form = CustomUserCreationForm()
    admin_profile_form = AdminProfileForm(instance=request.user)

    return render(request, 'admin_panel/admin_list.html', {
        'panel': 'users',
        'users': page_obj.object_list,
        'query': query,
        'page_obj': page_obj,
        'user_form': user_form,
        'admin_profile_form': admin_profile_form,
    })

@login_required
@user_passes_test(is_admin)
def admin_user_create(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'redirect': reverse('admin_user_list')})
            return redirect('admin_user_list')
        # AJAX invalid -> return partial HTML with errors
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            user_form = form
            html = render(request, 'admin_panel/partials/user_form_partial.html', {
                'user_form': user_form,
                'edit_url': reverse('admin_user_create')
            })
            return HttpResponse(html.content, status=400)
        return redirect('admin_user_list')
    # GET: redirect to users list since modal will be used
    return redirect('admin_user_list')

@login_required
@user_passes_test(is_admin)
def admin_user_batch_upload(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'This is not a CSV file.')
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'This is not a CSV file.'}, status=400)
            return redirect('admin_user_batch_upload')

        try:
            decoded_file = csv_file.read().decode('utf-8').splitlines()
        except UnicodeDecodeError:
            csv_file.seek(0)
            decoded_file = csv_file.read().decode('windows-1252').splitlines()

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
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'redirect': reverse('admin_user_list')})
        return redirect('admin_user_list')

    # GET: redirect to users list (csv upload available via modal)
    return redirect('admin_user_list')

@login_required
@user_passes_test(is_admin)
def admin_user_edit(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'redirect': reverse('admin_user_list')})
            return redirect('admin_user_list')
        # AJAX invalid -> return partial with errors
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            user_form = form
            html = render(request, 'admin_panel/partials/user_form_partial.html', {
                'user_form': user_form,
                'edit_url': reverse('admin_user_edit', args=[user.id])
            })
            return HttpResponse(html.content, status=400)
        return redirect('admin_user_list')
    # For AJAX GET: return partial HTML for modal injection (pre-populated form)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        user_form = CustomUserCreationForm(instance=user)
        return render(request, 'admin_panel/partials/user_form_partial.html', {
            'user_form': user_form,
            'edit_url': reverse('admin_user_edit', args=[user.id])
        })
    # Non-AJAX GET: redirect to users list (modal UI used instead)
    return redirect('admin_user_list')

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
    today = datetime.now()
    events = Event.objects.all().order_by(sort_by, 'done')

    if query:
        events = events.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(date__icontains=query) |
            Q(location__icontains=query)
        )  

    events= list(events)
    events.sort(key=lambda e:e.done)

    paginator = Paginator(events, 10)  # 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # blank event form for modal
    event_form = EventForm()
    admin_profile_form = AdminProfileForm(instance=request.user)

    return render(request, 'admin_panel/admin_list.html', {
        'panel': 'events',
        'events': page_obj.object_list,
        'query': query,
        'page_obj': page_obj,
        'today': today,
        'event_form': event_form,
        'admin_profile_form': admin_profile_form,
    })

@login_required
@user_passes_test(is_admin)
def admin_event_create(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event created successfully.')
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'redirect': reverse('admin_event_list')})
            return redirect('admin_event_list')
        # If AJAX POST and invalid, return rendered partial HTML with errors
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            event_form = form
            html = render(request, 'admin_panel/partials/event_form_partial.html', {
                'event_form': event_form,
                'edit_url': reverse('admin_event_create')
            })
            return HttpResponse(html.content, status=400)
        # Non-AJAX fallthrough
        return redirect('admin_event_list')
    # For GET requests, redirect to events list (modal is used instead)
    return redirect('admin_event_list')

@login_required
@user_passes_test(is_admin)
def admin_event_edit(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event updated successfully.')
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'redirect': reverse('admin_event_list')})
            return redirect('admin_event_list')
        # AJAX invalid -> return partial with errors
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            event_form = form
            html = render(request, 'admin_panel/partials/event_form_partial.html', {
                'event_form': event_form,
                'edit_url': reverse('admin_event_edit', args=[event.id])
            })
            return HttpResponse(html.content, status=400)
        return redirect('admin_event_list')
    # For GET: if AJAX, return the form partial HTML so the modal can load it via AJAX.
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        event_form = EventForm(instance=event)
        return render(request, 'admin_panel/partials/event_form_partial.html', {
            'event_form': event_form,
            'edit_url': reverse('admin_event_edit', args=[event.id])
        })
    # Non-AJAX GETs redirect to the list (modal UI is used instead)
    return redirect('admin_event_list')

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

    paginator = Paginator(updates, 10)  # 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    updates_form = UpdatesForm()
    admin_profile_form = AdminProfileForm(instance=request.user)

    return render(request, 'admin_panel/admin_list.html', {
        'panel': 'updates',
        'updates': page_obj.object_list,
        'page_obj': page_obj,
        'query': query,
        'updates_form': updates_form,
        'admin_profile_form': admin_profile_form,
    })


@login_required
@user_passes_test(is_admin)
def admin_updates_create(request):
    if request.method == 'POST':
        form = UpdatesForm(request.POST)
        if form.is_valid():
            form.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'redirect': reverse('admin_updates_list')})
            return redirect('admin_updates_list')
        # If AJAX POST and invalid, return rendered partial HTML with errors
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            updates_form = form
            html = render(request, 'admin_panel/partials/updates_form_partial.html', {
                'updates_form': updates_form,
                'edit_url': reverse('admin_updates_create')
            })
            return HttpResponse(html.content, status=400)
        return redirect('admin_updates_list')
    # GET: redirect to updates list (modal used instead)
    return redirect('admin_updates_list')

@login_required
@user_passes_test(is_admin)
def admin_updates_edit(request, update_id):
    update = get_object_or_404(Updates, pk=update_id)
    if request.method == 'POST':
        form = UpdatesForm(request.POST, instance=update)
        if form.is_valid():
            form.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'redirect': reverse('admin_updates_list')})
            return redirect('admin_updates_list')
        # AJAX invalid -> return partial with errors
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            updates_form = form
            html = render(request, 'admin_panel/partials/updates_form_partial.html', {
                'updates_form': updates_form,
                'edit_url': reverse('admin_updates_edit', args=[update.id])
            })
            return HttpResponse(html.content, status=400)
        return redirect('admin_updates_list')
    # For GET: if AJAX, return the form partial HTML so the modal can load it via AJAX.
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        updates_form = UpdatesForm(instance=update)
        return render(request, 'admin_panel/partials/updates_form_partial.html', {
            'updates_form': updates_form,
            'edit_url': reverse('admin_updates_edit', args=[update.id])
        })
    # Non-AJAX GETs redirect to the list (modal UI is used instead)
    return redirect('admin_updates_list')

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

    paginator = Paginator(posts, 5)  # 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    admin_profile_form = AdminProfileForm(instance=request.user)

    return render(request, 'admin_panel/admin_list.html', {
        'panel': 'forum',
        'posts': page_obj.object_list,
        'page_obj': page_obj,
        'query': query,
        'admin_profile_form': admin_profile_form,
    })

@login_required
@user_passes_test(is_admin)
def admin_delete_post(request, post_id):
    post = get_object_or_404(Forum, id=post_id)
    post.delete()
    return redirect('admin_forum_list')


@login_required
@user_passes_test(is_admin)
def admin_panel_router(request):
    """Compatibility router: accepts ?panel=users|events|updates|forum and redirects to the proper admin list view.

    This helps when external links or bookmarks point to a generic admin panel with a `panel` query param.
    """
    panel = request.GET.get('panel', '').lower()
    q = request.GET.get('q', '')
    page = request.GET.get('page', '')

    params = []
    if q:
        params.append(f"q={q}")
    if page:
        params.append(f"page={page}")
    qs = ('?' + '&'.join(params)) if params else ''

    if panel == 'users':
        return redirect(f"{reverse('admin_user_list')}{qs}")
    if panel == 'events':
        return redirect(f"{reverse('admin_event_list')}{qs}")
    if panel == 'updates':
        return redirect(f"{reverse('admin_updates_list')}{qs}")
    if panel == 'forum':
        return redirect(f"{reverse('admin_forum_list')}{qs}")

    # default to dashboard
    return redirect('admin_dashboard')


## USER SIDE

@login_required
def home(request):
    user = request.user
    current_datetime = timezone.now()
    upcoming_events = Event.objects.filter(date__gte=timezone.now()).order_by('date')[:5]
    recent_updates = Updates.objects.all().order_by('-date_posted')
    forum_posts_count = Forum.objects.filter(author=request.user).count()
    comments_count = Comment.objects.filter(user=user).count()
    events_attended_count = Event.objects.filter(done=True, interested=request.user).count()

    return render(request, 'core/contents.html', {
        'page_name': 'home',
        'user': user,
        'upcoming_events': upcoming_events,
        'recent_updates': recent_updates,
        'forum_posts_count': forum_posts_count,
        'comments_count': comments_count,
        'events_attended_count': events_attended_count,
    })



@login_required
def profile_view(request):
    user = request.user

    job_entries = user.job_entries.all().order_by('-date_added')
    club_orgs = user.club_orgs.all()
    # Determine active/inactive state for display:
    # Consider these employment statuses as "active-capable" (include freelancing and others as requested)
    ACTIVE_STATUSES = {'employed', 'freelancing', 'studying', 'other'}
    active_capable = (user.employment_status in ACTIVE_STATUSES)

    if active_capable and job_entries.exists():
        # Prefer jobs explicitly marked current; if multiple, pick the most recent one by date_added
        current_jobs = [j for j in job_entries if j.is_current]
        if current_jobs:
            # pick most recent current job
            active_job = max(current_jobs, key=lambda j: j.date_added or datetime.min)
        else:
            # if only one job, it's active; otherwise choose the most recent job
            if job_entries.count() == 1:
                active_job = job_entries[0]
            else:
                active_job = max(job_entries, key=lambda j: j.date_added or datetime.min)

        for job in job_entries:
            job.is_active = (job.pk == active_job.pk)
    else:
        for job in job_entries:
            job.is_active = False

    context = {
        'user': user,
        'job_entries': job_entries,
        'club_orgs': club_orgs,
        'can_edit': False,  # no editing in this view
        
    }

    context['page_name'] = 'profile'
    return render(request, 'core/contents.html', context)

@login_required
def profile_edit_view(request):
    user = request.user

    JobEntryFormSet = inlineformset_factory(CustomUser, JobEntry, form=JobEntryForm, extra=1, can_delete=True)
    ClubOrgFormSet = inlineformset_factory(CustomUser, ClubOrg, form=ClubOrgForm, extra=1, can_delete=True)

    if request.method == 'POST':
        form = UserProfileEditForm(request.POST, request.FILES, instance=user)
        job_formset = JobEntryFormSet(request.POST, instance=user, prefix='jobentry_set')
        club_formset = ClubOrgFormSet(request.POST, instance=user, prefix='cluborg_set')

        if form.is_valid() and job_formset.is_valid() and club_formset.is_valid():
            form.save()

            # Delete removed job entries
            for deleted_form in job_formset.deleted_forms:
                if deleted_form.instance.pk:
                    deleted_form.instance.delete()

            # Save job entries (new and updated)
            job_entries = job_formset.save(commit=False)
            for job in job_entries:
                job.user = user
                job.save()
            job_formset.save_m2m()

            # Delete removed clubs
            for deleted_form in club_formset.deleted_forms:
                if deleted_form.instance.pk:
                    deleted_form.instance.delete()


            # Save club entries (new and updated)
            club_entries = club_formset.save(commit=False)
            for club in club_entries:
                club.user = user
                club.save()
            club_formset.save_m2m()

            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
        else:
            messages.error(request, 'There were errors in your form. Please check and try again.')
    else:
        
        form = UserProfileEditForm(instance=user)
        job_formset = JobEntryFormSet(instance=user, prefix='jobentry_set')
        club_formset = ClubOrgFormSet(instance=user, prefix='cluborg_set')

    # Annotate each form in the job formset with an `is_active` flag for template rendering.
    ACTIVE_STATUSES = {'employed', 'freelancing', 'studying', 'other'}
    active_capable = (user.employment_status in ACTIVE_STATUSES)

    # Collect existing job instances (those with pk) ordered by date_added desc
    existing_jobs = list(JobEntry.objects.filter(user=user).order_by('-date_added'))
    existing_count = len(existing_jobs)

    # Determine which job should be active in the edit UI
    active_job_pk = None
    if active_capable and (existing_count > 0 or any(not getattr(jf.instance, 'pk', None) for jf in job_formset.forms)):
        # Prefer explicit current flags among existing jobs
        current_existing = [j for j in existing_jobs if j.is_current]
        if current_existing:
            active_job_pk = max(current_existing, key=lambda j: j.date_added or datetime.min).pk
        else:
            # If there's any new (unsaved) form, make the newest new form active (assume it's appended last)
            new_forms = [jf for jf in job_formset.forms if not getattr(jf.instance, 'pk', None)]
            if new_forms:
                # mark the last new form as active by setting a marker on the form (no pk available)
                # we'll set is_active=True on that form below
                pass
            else:
                # fallback: if only one existing job, active that; else pick most recent existing
                if existing_count == 1:
                    active_job_pk = existing_jobs[0].pk
                elif existing_count > 1:
                    active_job_pk = existing_jobs[0].pk

    # Apply is_active flags to formset forms
    if active_capable:
        # find last new form if any
        new_forms = [jf for jf in job_formset.forms if not getattr(jf.instance, 'pk', None)]
        last_new_form = new_forms[-1] if new_forms else None

        for jf in job_formset.forms:
            inst = getattr(jf, 'instance', None)
            if inst and getattr(inst, 'pk', None):
                jf.is_active = (active_job_pk is not None and inst.pk == active_job_pk)
            else:
                # unsaved/new form: active if it's the last new form and no existing job was explicitly selected
                jf.is_active = (last_new_form is not None and jf is last_new_form and active_job_pk is None)
    else:
        for jf in job_formset.forms:
            jf.is_active = False

    context = {
        'form': form,
        'formset': job_formset,
        'club_formset': club_formset,
        'can_edit': True,
    }
    context['page_name'] = 'profile'
    return render(request, 'core/contents.html', context)




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

    events = events.order_by('-created_at').prefetch_related('interested')

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
    # prefetch interested users so membership checks in template don't hit the DB repeatedly
    recently_concluded = recently_concluded.prefetch_related('interested')

    context = {
        'page_name': 'events',
        'events': events,
        'recently_concluded': recently_concluded,
        'now': now,
        'visibility_filter': visibility_filter
    }

    # For client-side rendering of user's current interest state
    try:
        user_interested_ids = set(request.user.interested_events.values_list('id', flat=True))
    except Exception:
        user_interested_ids = set()
    context['user_interested_ids'] = user_interested_ids

    return render(request, 'core/contents.html', context)


@require_POST
@login_required
def toggle_event_interest(request, pk):
    """Toggle the current user's interest for an event. Returns JSON with state and counts.
    Interest is recorded regardless of event.done; callers may choose to show counts only when event.done is True.
    """
    event = get_object_or_404(Event, pk=pk)
    user = request.user

    if event.interested.filter(pk=user.pk).exists():
        event.interested.remove(user)
        interested = False
    else:
        event.interested.add(user)
        interested = True

    # interest count (total users who marked interest)
    interest_count = event.interested.count()

    return JsonResponse({
        'interested': interested,
        'interest_count': interest_count,
        'done': bool(event.done),
    })



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

    return render(request, 'core/contents.html', {
        'page_name': 'updates',
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
        'trending_posts': trending_posts,
        'page_name': 'forum'
    }

    return render(request, 'core/contents.html', context)


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
    success_url = reverse_lazy('profile')
    success_message = "Your password was successfully updated."

def logout_view(request):
    logout(request)
    return redirect('login')    