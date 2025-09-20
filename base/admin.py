from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (CustomUser, AcademicProfile, TeacherProfile, 
                     Subject, Medium, Availability,
                     Qualification,Grade,
                     )

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('is_teacher','location', 'banned')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('is_teacher','location', 'banned')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)

admin.site.register(Grade)
class AcademicProfileInline(admin.StackedInline):
    model = AcademicProfile
    extra = 0

class AvailabilityInline(admin.StackedInline):
    model = Availability
    extra = 0

class QualificationInline(admin.StackedInline):
    model = Qualification
    extra = 0

class TeacherProfileAdmin(admin.ModelAdmin):
    inlines = [AcademicProfileInline, AvailabilityInline, QualificationInline]

admin.site.register(TeacherProfile, TeacherProfileAdmin)
admin.site.register(Subject)
admin.site.register(Medium)





