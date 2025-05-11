from django import forms
from django.forms import inlineformset_factory
from .models import CustomUser, JobEntry, Event, Updates, Forum, Comment

class CustomUserCreationForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['student_number', 'first_name', 'last_name', 'email', 'contact', 'birthday', 'address', 'curr_location', 'degree', 'year_attended', 'year_graduated', 'is_active', 'is_staff', 'is_superuser']
        # fields = '__all__'
        labels = {
            'curr_location': 'Current Location',
        }
        widgets = {'birthday': forms.DateInput(attrs={'type':'date'})}

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.student_number
        user.set_password(user.student_number)
        if commit:
            user.save()
        return user

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            'address',
            'curr_location',
            'contact',
            'employment_status',
            'bio',
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        }

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'datetime', 'location']
        labels = {
            'datetime': 'Date and Time',
        }
        widgets = {
            'datetime': forms.DateTimeInput(attrs={
                'type': 'datetime-local'
            }),}
        
class UpdatesForm(forms.ModelForm):
    class Meta:
        model = Updates
        fields = ['title', 'content', 'related_event']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4}),
        }

class JobEntryForm(forms.ModelForm):
    class Meta:
        model = JobEntry
        fields = ['job_title', 'is_current']
        
JobEntryFormSet = inlineformset_factory(
    CustomUser,
    JobEntry,
    form=JobEntryForm,
    extra=1,
    can_delete=True
)

class ForumPostForm(forms.ModelForm):
    class Meta:
        model = Forum
        fields = ['title', 'content']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']