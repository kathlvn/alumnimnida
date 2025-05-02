from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Event, Updates, Forum
from .forms import ForumPostForm

@login_required
def home(request):
    return render(request, 'core/home.html', {'user': request.user})

@login_required
def profile_view(request):
    return render(request, 'core/profile.html')




@login_required
def events_view(request):
    events = Event.objects.order_by('-date')
    return render(request, 'core/events.html', {'events': events})



@login_required
# def updates_view(request):
#     event_id = request.GET.get('event')
#     events = Event.objects.all()

#     if event_id:
#         updates = Updates.objects.filter(related_event_id=event_id).order_by('-date_posted')
#     else:
#         updates = Updates.objects.all().order_by('-date_posted')

#     return render(request, 'core/updates.html', {'updates': updates, 'events': events, 'selected_event': event_id})
def updates_view(request):
    updates = Updates.objects.order_by('-date_posted')
    return render(request, 'core/updates.html', {'updates': updates})

@login_required
def change_password_view(request):
    return render(request, 'core/change_password.html')




@login_required
def forum_list(request):
    posts = Forum.objects.all().order_by('-date_posted')
    # if request.method == 'POST':
    #     form = ForumPostForm(request.POST)
        # if form.is_valid():
        #     visibility = Visibility.objects.create(
        #         visibility_type=form.cleaned_data['visibility_type'],
        #         program=request.user.program,
        #         batch=request.user.batch
        #     )
        #     post = form.save(commit=False)
        #     post.author = request.user
        #     post.visibility = visibility
        #     post.save()
        #     return redirect('forum-list')
    return render(request, 'core/forum_list.html', {'posts': posts})


@login_required
def forum_create(request):
    # if request.user.is_staff:
    #     return redirect('forum_list')  # Staff can't create
    if request.method == 'POST':
        print("Form successfully submitted")
        form = ForumPostForm(request.POST)
        if form.is_valid():
            print("Form is valid")
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


