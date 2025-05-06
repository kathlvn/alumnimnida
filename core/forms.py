from django import forms
from .models import CustomUser,JobEntry, Forum, Comment

# class AdminUserCreationForm(forms.ModelForm):
#     class Meta:
#         model = CustomUser
#         fields = '__all__'
#         widgets = {
#             'birthday': forms.DateInput(attrs={'type': 'date'})
#         }

#     def save(self, commit=True):
#         user = super().save(commit=False)
#         student_number = self.cleaned_data.get('student_number')
#         user.username = student_number
#         user.set_password(student_number)
#         if commit:
#             user.save()
#         return user

class CustomUserCreationForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['student_number', 'first_name', 'last_name', 'email', 'degree', 'year_graduated', 'is_active', 'is_staff', 'is_superuser']

    def save(self, commit=True):
        user = super().save(commit=False)
        # Set username = student number
        user.username = user.student_number
        # Set password = student number
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
            'industry',
            'bio',
        ]

class JobEntryForm(forms.ModelForm):
    class Meta:
        model = JobEntry
        fields = ['job_title']

class ForumPostForm(forms.ModelForm):
    class Meta:
        model = Forum
        fields = ['title', 'content']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']

