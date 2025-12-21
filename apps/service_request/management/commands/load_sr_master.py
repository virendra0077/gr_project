from django.core.management.base import BaseCommand
from apps.service_request.models import SRNature, SRType


class Command(BaseCommand):
    help = "Load SR Nature and SR Type master data"

    def handle(self, *args, **options):

        sr_natures = [
            {"code": "complaint", "name": "Complaint"},
            {"code": "request", "name": "Request"},
            {"code": "query", "name": "Query"},
        ]

        sr_types = [
            {"code": "card_issue", "name": "Card Issue"},
            {"code": "netbanking_issue", "name": "NetBanking Issue"},
            {"code": "branch_service", "name": "Branch Service"},
            {"code": "loan_related", "name": "Loan Related"},
            {"code": "account_opening", "name": "Account Opening"},
            {"code": "transaction_dispute", "name": "Transaction Dispute"},
            {"code": "others", "name": "Others"},
        ]

        self.stdout.write(self.style.NOTICE("Loading SR Nature master data..."))

        for nature in sr_natures:
            obj, created = SRNature.objects.get_or_create(
                code=nature["code"],
                defaults={"name": nature["name"], "is_active": True},
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created SR Nature: {obj.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"SR Nature already exists: {obj.name}"))

        self.stdout.write(self.style.NOTICE("Loading SR Type master data..."))

        for sr_type in sr_types:
            obj, created = SRType.objects.get_or_create(
                code=sr_type["code"],
                defaults={"name": sr_type["name"], "is_active": True},
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created SR Type: {obj.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"SR Type already exists: {obj.name}"))

        self.stdout.write(self.style.SUCCESS("SR master data loading completed "))
