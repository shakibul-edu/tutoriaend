from django.core.management.base import BaseCommand
from base.models import Medium, Grade, Subject


class Command(BaseCommand):
    help = "Seed academic mediums, grades, and subjects"

    def handle(self, *args, **kwargs):

        self.stdout.write(self.style.SUCCESS("Seeding academic data..."))

        # =========================
        # MEDIUMS
        # =========================

        mediums_data = [
            "Bangla Medium",
            "English Version",
            "English Medium (Cambridge)",
            "English Medium (Edexcel)",
        ]

        mediums = {}

        for medium_name in mediums_data:
            medium, _ = Medium.objects.get_or_create(name=medium_name)
            mediums[medium_name] = medium

        # =========================
        # GRADES
        # =========================

        grades_data = [
            ("Play", 1),
            ("Nursery", 2),
            ("KG", 3),
            ("Class 1", 4),
            ("Class 2", 5),
            ("Class 3", 6),
            ("Class 4", 7),
            ("Class 5", 8),
            ("Class 6", 9),
            ("Class 7", 10),
            ("Class 8", 11),
            ("Class 9", 12),
            ("Class 10", 13),
            ("Class 11", 14),
            ("Class 12", 15),
            ("O Level", 16),
            ("A Level", 17),
            ("Admission Test", 18),
            ("University Level", 19),
        ]

        grade_objects = {}

        for grade_name, sequence in grades_data:

            grade, _ = Grade.objects.get_or_create(
                name=grade_name,
                defaults={
                    "sequence": sequence
                }
            )

            # Update sequence if changed
            grade.sequence = sequence
            grade.save()

            grade_objects[grade_name] = grade

        # =========================
        # ATTACH MEDIUMS TO GRADES
        # =========================

        bangla_medium_grades = [
            "Play",
            "Nursery",
            "KG",
            "Class 1",
            "Class 2",
            "Class 3",
            "Class 4",
            "Class 5",
            "Class 6",
            "Class 7",
            "Class 8",
            "Class 9",
            "Class 10",
            "Class 11",
            "Class 12",
            "Admission Test",
            "University Level",
        ]

        english_medium_grades = [
            "Play",
            "Nursery",
            "KG",
            "Class 1",
            "Class 2",
            "Class 3",
            "Class 4",
            "Class 5",
            "Class 6",
            "Class 7",
            "Class 8",
            "O Level",
            "A Level",
        ]

        for grade_name in bangla_medium_grades:

            grade = grade_objects[grade_name]

            grade.medium.add(
                mediums["Bangla Medium"],
                mediums["English Version"]
            )

        for grade_name in english_medium_grades:

            grade = grade_objects[grade_name]

            grade.medium.add(
                mediums["English Medium (Cambridge)"],
                mediums["English Medium (Edexcel)"]
            )

        # =========================
        # SUBJECTS
        # =========================

        subjects_by_grade = {

            # PRIMARY
            "Class 1": [
                "Bangla",
                "English",
                "Mathematics",
                "General Science",
            ],

            "Class 2": [
                "Bangla",
                "English",
                "Mathematics",
                "General Science",
            ],

            "Class 3": [
                "Bangla",
                "English",
                "Mathematics",
                "General Science",
                "Religion",
            ],

            "Class 4": [
                "Bangla",
                "English",
                "Mathematics",
                "General Science",
                "Religion",
                "ICT",
            ],

            "Class 5": [
                "Bangla",
                "English",
                "Mathematics",
                "General Science",
                "Religion",
                "ICT",
            ],

            # CLASS 6-8
            "Class 6": [
                "Bangla",
                "English",
                "Mathematics",
                "General Science",
                "ICT",
                "Religion",
                "Bangladesh & Global Studies",
            ],

            "Class 7": [
                "Bangla",
                "English",
                "Mathematics",
                "General Science",
                "ICT",
                "Religion",
                "Bangladesh & Global Studies",
            ],

            "Class 8": [
                "Bangla",
                "English",
                "Mathematics",
                "General Science",
                "ICT",
                "Religion",
                "Bangladesh & Global Studies",
            ],

            # SSC
            "Class 9": [
                "Bangla",
                "English",
                "Mathematics",
                "Higher Mathematics",
                "Physics",
                "Chemistry",
                "Biology",
                "ICT",
                "Accounting",
                "Finance",
                "Business Entrepreneurship",
                "Economics",
                "History",
            ],

            "Class 10": [
                "Bangla",
                "English",
                "Mathematics",
                "Higher Mathematics",
                "Physics",
                "Chemistry",
                "Biology",
                "ICT",
                "Accounting",
                "Finance",
                "Business Entrepreneurship",
                "Economics",
                "History",
            ],

            # HSC
            "Class 11": [
                "Physics",
                "Chemistry",
                "Biology",
                "Higher Mathematics",
                "ICT",
                "Accounting",
                "Finance",
                "Management",
                "Economics",
            ],

            "Class 12": [
                "Physics",
                "Chemistry",
                "Biology",
                "Higher Mathematics",
                "ICT",
                "Accounting",
                "Finance",
                "Management",
                "Economics",
            ],

            # O LEVEL
            "O Level": [
                "Mathematics",
                "Additional Mathematics",
                "Physics",
                "Chemistry",
                "Biology",
                "Accounting",
                "Economics",
                "Business Studies",
                "ICT",
                "Computer Science",
                "English Language",
                "English Literature",
                "Bangla",
            ],

            # A LEVEL
            "A Level": [
                "Mathematics",
                "Further Mathematics",
                "Physics",
                "Chemistry",
                "Biology",
                "Accounting",
                "Economics",
                "Business",
                "Computer Science",
                "Psychology",
                "Law",
            ],
        }

        # =========================
        # CREATE SUBJECTS
        # =========================

        for grade_name, subjects in subjects_by_grade.items():

            grade = grade_objects.get(grade_name)

            for index, subject_name in enumerate(subjects, start=1):

                # subject_code = (
                #     subject_name.upper()
                #     .replace(" ", "_")
                #     .replace("&", "AND")
                # )

                # subject_code = f"{subject_code}_{grade.sequence}"

                Subject.objects.get_or_create(
                    name=f"{subject_name} - {grade_name}",
                    grade=grade,
                    defaults={
                        "description": f"{subject_name} subject for {grade_name}",
                        # "subject_code": subject_code,
                    }
                )

        self.stdout.write(
            self.style.SUCCESS("Academic data seeded successfully!")
        )