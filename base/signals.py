from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ContactRequest
from .utils import send_email
from django.template.loader import render_to_string


@receiver(post_save, sender=ContactRequest)
def notify_teacher_on_request(sender, instance, created, **kwargs):
    if not created:
        return

    teacher = instance.teacher
    user = teacher.user  # assuming TeacherProfile has user FK

    subject = "New Tuition Request 🎓"
    html = render_to_string(
    "emails/student_contact_request.html",
    {
        "username": user.username,
        "student_name": instance.student_name,
        "student_phone": instance.student_phone,
        "fee_budget": instance.fee_budget,
        "message": instance.message,
        "dashboard_url": f"https://etuition.app/dashboard"
    }
)

    send_email(
        to_email=user.email,
        to_name=user.username,
        subject=subject,
        html_content=html
    )


@receiver(post_save, sender=ContactRequest)
def notify_student_on_accept(sender, instance, created, **kwargs):
    if created:
        return

    if instance.status == "accepted" and not instance.is_accept_notified:
        student = instance.student
        user = instance.student 
        subject = "Your Tuition Request Has Been Accepted! 🎉"
        html = render_to_string(
    "emails/teacher_contacat_request_accepted.html",
    {
        
        "username": student.username,
        "teacher_name": instance.teacher.user.username,
        "teacher_phone": getattr(instance.teacher, "phone", None),
        "dashboard_url": f"https://etuition.app/dashboard"
    }
)

        send_email(
        to_email=user.email,
        to_name=user.username,
        subject=subject,
        html_content=html
    )

        instance.is_accept_notified = True
        instance.save(update_fields=["is_accept_notified"])