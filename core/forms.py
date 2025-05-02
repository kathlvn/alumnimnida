from django import forms
from .models import CustomUser, Forum

class AdminUserCreationForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = '__all__'
        widgets = {
            'birthday': forms.DateInput(attrs={'type': 'date'})
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        student_number = self.cleaned_data.get('student_number')
        user.username = student_number
        user.set_password(student_number)
        if commit:
            user.save()
        return user
    

class ForumPostForm(forms.ModelForm):
    class Meta:
        model = Forum
        fields = ['title', 'content']

