from django import forms
from django.forms import inlineformset_factory
from .models import CustomUser, JobEntry, ClubOrg, Event, Updates, Forum, Comment, Batch, Degree

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

class UserProfileEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            'full_name',
            'student_number',
            'degree',
            'year_graduated',
            'address',
            'employment_status',
            'bio',
            'profile_picture',
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make these fields readonly (disabled)
        readonly_fields = ['full_name', 'student_number', 'degree', 'year_graduated']
        for field_name in readonly_fields:
            if field_name in self.fields:
                self.fields[field_name].disabled = True  # disables field (read-only in form)


class ClubOrgForm(forms.ModelForm):
    class Meta:
        model = ClubOrg
        fields = ['org_name']

class JobEntryForm(forms.ModelForm):
    class Meta:
        model = JobEntry
        fields = ['job_title']
        exclude = ['is_current']
        
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
    
DEGREE_CHOICES = CustomUser._meta.get_field('degree').choices
BATCH_CHOICES = CustomUser._meta.get_field('year_graduated').choices

visibility_choices = [
    ('public', 'Public'),
    ('batch', 'By Batch'),
    ('degree', 'By Degree'),
    ('both', 'By Batch and Degree'),
]

class EventForm(forms.ModelForm):

    visibility_type = forms.ChoiceField(choices=visibility_choices)

    visibility_batches = forms.ModelMultipleChoiceField(
        queryset=Batch.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    visibility_degrees = forms.ModelMultipleChoiceField(
        queryset=Degree.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )    

    class Meta:
        model = Event
        fields = ['title', 'description', 'date', 'time', 'location', 'visibility_type', 'visibility_degrees', 'visibility_batches']
        labels = {
            'date': 'Event Date',
            'time': 'Event Time',
        }
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def clean(self):
        cleaned = super().clean()
        vis = cleaned.get('visibility_type')
        if vis == 'public':
            cleaned['visibility_batches'] = []
            cleaned['visibility_degrees'] = []
        return cleaned

    

        
class UpdatesForm(forms.ModelForm):

    visibility_type = forms.ChoiceField(choices=visibility_choices)

    visibility_batches = forms.ModelMultipleChoiceField(
        queryset=Batch.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    visibility_degrees = forms.ModelMultipleChoiceField(
        queryset=Degree.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )    

    class Meta:
        model = Updates
        fields = ['title', 'content', 'related_event', 'visibility_type', 'visibility_degrees', 'visibility_batches']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4}),
        }

    def clean(self):
        cleaned = super().clean()
        related_event = cleaned.get('related_event')

        if related_event:
            # Inherit visibility from event
            cleaned['visibility_type'] = related_event.visibility_type
            cleaned['visibility_batches'] = related_event.visibility_batches.all()
            cleaned['visibility_degrees'] = related_event.visibility_degrees.all()
        else:
            vis = cleaned.get('visibility_type')
            if vis == 'public':
                cleaned['visibility_batches'] = []
                cleaned['visibility_degrees'] = []

        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)

        if self.cleaned_data.get('related_event'):
            event = self.cleaned_data['related_event']
            instance.visibility_type = event.visibility_type
            if commit:
                instance.save()
                instance.visibility_batches.set(event.visibility_batches.all())
                instance.visibility_degrees.set(event.visibility_degrees.all())
        else:
            if commit:
                instance.save()
                instance.visibility_batches.set(self.cleaned_data['visibility_batches'])
                instance.visibility_degrees.set(self.cleaned_data['visibility_degrees'])

        return instance


class ForumPostForm(forms.ModelForm):
    class Meta:
        model = Forum
        fields = ['title', 'content', 'visibility_type']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control'}),
            'visibility_type': forms.Select(attrs={'class': 'form-control'}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }