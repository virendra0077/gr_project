import random
from django.core.management.base import BaseCommand
from apps.service_request.models import SRNature, SRType, SRTATDays


class Command(BaseCommand):
    help = "Automatically allot random TAT (5, 10, 15 days) for each SR Nature + SR Type"

    def handle(self, *args, **options):

        tat_pool = [5, 10, 15]

        sr_natures = SRNature.objects.filter(is_active=True)
        sr_types = SRType.objects.filter(is_active=True)

        if not sr_natures.exists() or not sr_types.exists():
            self.stdout.write(
                self.style.ERROR("SRNature or SRType master data missing")
            )
            return

        created_count = 0

        for nature in sr_natures:
            for sr_type in sr_types:

                tat_value = random.choice(tat_pool)

                obj, created = SRTATDays.objects.get_or_create(
                    sr_nature=nature,
                    sr_type=sr_type,
                    defaults={
                        'tat_days': tat_value,
                        'is_active': True
                    }
                )

                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"TAT {tat_value} days created for {nature.name} - {sr_type.name}"
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"Auto TAT allotment completed. Total new records: {created_count}"
            )
        )

