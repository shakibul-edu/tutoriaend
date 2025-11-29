from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (CustomUser, AcademicProfile, TeacherProfile, 
                     Subject, Medium, Availability,
                     Qualification,Grade, JobPost, BidJob, JobPostAvailability
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

class JobPostAvailabilityInline(admin.StackedInline):
    model = JobPostAvailability
    extra = 0

    
class BidJobInline(admin.StackedInline):
    model = BidJob
    extra = 0

class JobPostAdmin(admin.ModelAdmin):
    inlines = [JobPostAvailabilityInline, BidJobInline]

admin.site.register(JobPost, JobPostAdmin)
admin.site.register(BidJob)





