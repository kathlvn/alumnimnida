from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Event, Updates, Forum
from .forms import CustomUserCreationForm

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    model = CustomUser
    list_display = ('student_number', 'full_name', 'degree')
    ordering = ('student_number',)

    fieldsets = (
        (None, {'fields': ('student_number', 'full_name', 'password')}),
        ('Personal Info', {
            'fields': (
                'address', 'current_address', 'degree', 'year_graduated',
                'birthday', 'year_attended', 'contact_number', 'email'
            )
        }),

        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'student_number', 'full_name', 'address', 'current_address',
                'degree', 'year_graduated', 'birthday', 'year_attended',
                'contact_number', 'email', 'is_staff', 'is_active'
            ),
        }),
    )

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Event)
admin.site.register(Updates)
admin.site.register(Forum)
