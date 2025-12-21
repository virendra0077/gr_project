from django.core.management.base import BaseCommand
from apps.service_request.models import SRStatus


class Command(BaseCommand):
    help = "Load SR Status master data"

    def handle(self, *args, **kwargs):

        statuses = [
            {"code": "open", "name": "Open"},
            {"code": "wip", "name": "Work In Progress"},
            {"code": "closed", "name": "Closed"},
        ]

        for status in statuses:
            obj, created = SRStatus.objects.update_or_create(
                code=status["code"],
                defaults={
                    "name": status["name"],
                    "is_active": True
                }
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Created SRStatus: {obj.code}")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"Updated SRStatus: {obj.code}")
                )

        self.stdout.write(
            self.style.SUCCESS("SRStatus master data loaded successfully ✅")
        )
