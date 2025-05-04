from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Event, Updates, Forum
from .forms import AdminUserCreationForm

class CustomUserAdmin(UserAdmin):
    add_form = AdminUserCreationForm
    model = CustomUser
    list_display = ('student_number', 'first_name', 'last_name', 'email', 'degree')
    ordering = ('student_number',)

    fieldsets = (
        (None, {'fields': ('student_number', 'email', 'first_name', 'last_name', 'password')}),
        ('Personal Info', {'fields': (
            'birthday', 'address', 'curr_location', 'degree', 'year_attended', 'year_graduated',
            'contact'
        )}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'student_number', 'first_name', 'last_name', 'email', 'birthday', 'address',
                'curr_location', 'degree', 'year_attended', 'year_graduated', 'contact', 'is_staff', 'is_active'
            ),
        }),
    )

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Event)
admin.site.register(Updates)
admin.site.register(Forum)
