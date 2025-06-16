from django.urls import path
from .views import (home, protected_view,
set_location, create_teacher,
edit_teacher, create_academic_profile,
edit_academic_profile, create_qualification, edit_qualification,
get_teacher_full_profile
)

app_name = 'base'

urlpatterns = [
    path('', home, name='home'),
    path('protected/', protected_view, name='protected_view'),
    path('set-location/', set_location, name='set_location'),
    path('teacher/create/', create_teacher, name='create_teacher'),
    path('teacher/edit/', edit_teacher, name='edit_teacher'),
    path('academic-profile/create/', create_academic_profile, name='create_academic_profile'),
    path('academic-profile/edit/', edit_academic_profile, name='edit_academic_profile'),
    path('qualification/create/', create_qualification, name='create_qualification'),
    path('qualification/edit/', edit_qualification, name='edit_qualification'),
    path('teacher/full-profile/', get_teacher_full_profile, name='get_teacher_full_profile'),
]