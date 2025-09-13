from django.urls import path
from . import views

app_name = 'base'

urlpatterns = [
    path('', views.home, name='home'),
    path('protected/', views.protected_view, name='protected_view'),
    path('set-location/', views.set_location, name='set_location'),
    path('teacher/create/', views.create_teacher, name='create_teacher'),
    path('teacher/edit/', views.edit_teacher, name='edit_teacher'),
    path('academic-profile/create/', views.create_academic_profile, name='create_academic_profile'),
    path('academic-profile/edit/', views.edit_academic_profile, name='edit_academic_profile'),
    path('qualification/create/', views.create_qualification, name='create_qualification'),
    path('qualification/edit/', views.edit_qualification, name='edit_qualification'),
    path('teacher/full-profile/', views.get_teacher_full_profile, name='get_teacher_full_profile'),
    path('availability/create/', views.create_availability_slots, name='create_availability_slots'),
    path('availability/edit/', views.edit_availability_slots, name='edit_availability_slots'),
    path('grade-by-medium/', views.get_grades_by_medium, name='get_grade_by_medium'),
    path('subject-by-grade/', views.get_subjects_by_grade, name='get_subject_by_grade'),
    path('filter-teachers/', views.filter_teachers, name='filter_teachers'),
]