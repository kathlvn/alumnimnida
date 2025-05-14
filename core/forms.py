from django import forms
from django.forms import inlineformset_factory
from .models import CustomUser, JobEntry, ClubOrg, Event, Updates, Forum, Comment

class CustomUserCreationForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['student_number', 'full_name','address', 'degree', 'year_graduated', 'is_active', 'is_staff', 'is_superuser']
        # fields = '__all__'
        # labels = {
        #     'curr_location': 'Current Location',
        # }
        # widgets = {'birthday': forms.DateInput(attrs={'type':'date'})}

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
            'employment_status',
            'bio',
            'profile_picture',
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        }

class ClubOrgForm(forms.ModelForm):
    class Meta:
        model = ClubOrg
        fields = ['org_name']

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

class AdminProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'full_name', 'profile_picture']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.student_number = user.username
        
        if commit:
            user.save()
        
        return user

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

class ForumPostForm(forms.ModelForm):
    class Meta:
        model = Forum
        fields = ['title', 'content']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']