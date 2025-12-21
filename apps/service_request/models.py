
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import RegexValidator


# --- Choices ---
SR_CATEGORY_CHOICES = [
    ('parented', 'Parented SR'),
    ('unparented', 'Unparented SR'),
]

SR_NATURE_CHOICES = [
    ('complaint', 'Complaint'),
    ('request', 'Request'),
    ('query', 'Query'),
]

SR_TYPE_CHOICES = [
    ('card_issue', 'Card Issue'),
    ('netbanking_issue', 'NetBanking Issue'),
    ('branch_service', 'Branch Service'),
    ('loan_related', 'Loan Related'),
    ('account_opening', 'Account Opening'),
    ('transaction_dispute', 'Transaction Dispute'),
    ('others', 'Others'),
]

# SR_STATUS_CHOICES = [
#     ('open', 'Open'),
#     ('WIP', 'Work In Progress'),
#     ('closed', 'Closed'),
# ]






class ServiceRequest(models.Model):
    """
    Main Service Request model for handling customer grievances and requests.
    """

    # --- Identifiers and Categorization ---
    sr_number = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        db_index=True,
        db_column="sr_number"
    )

    category = models.CharField(
        max_length=20,
        choices=SR_CATEGORY_CHOICES,
        help_text="Whether the request is Parented (linked to account) or Unparented.",
        db_column="category"
    )

    sr_nature = models.ForeignKey(
        "SRNature",
        on_delete=models.PROTECT,
        related_name="service_requests",
        db_column="sr_nature"
    )

    sr_type = models.ForeignKey(
        "SRType",
        on_delete=models.PROTECT,
        related_name="service_requests",
        db_column="sr_type"
    )

    # --- Content ---
    subject = models.CharField(
        max_length=200,
        help_text="Brief subject of the service request",
        db_column="subject"
    )

    description = models.TextField(
        help_text="Detailed description of the issue or request",
        db_column="description"
    )

    tat = models.ForeignKey(
        "SRTATDays",
        on_delete=models.PROTECT,
        related_name="service_requests",
        null=True,
        blank=True,
        db_column="tat"
    )

    # --- User / Account Details ---
    account_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        db_index=True,
        help_text="Associated account number (for Parented SRs).",
        db_column="account_number"
    )

    email = models.EmailField(
        db_column="email"
    )

    phone = models.CharField(
        max_length=17,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone must be in format: '+999999999'. Up to 15 digits."
        )],
        db_column="phone"
    )

    address = models.TextField(
        blank=True,
        null=True,
        db_column="address"
    )

    # --- Relationships ---
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="service_requests_created",
        db_column="created_by"
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="service_requests_assigned",
        db_column="assigned_to"
    )

    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="service_requests_closed",
        db_column="closed_by"
    )

    status = models.ForeignKey(
        "SRStatus",
        on_delete=models.PROTECT,
        related_name="service_requests",
        db_column="status"
    )

    # --- Timestamps ---
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        db_column="created_at"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        db_column="updated_at"
    )

    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        db_column="closed_at"
    )

    # --- Custom Methods ---
    def _generate_unique_sr_number(self):
        now = timezone.now()
        date_part = now.strftime("%Y%m%d")
        time_part = now.strftime("%H%M%S")
        counter = int(now.microsecond / 100)

        for _ in range(100):
            sr_number = f"SR-{date_part}-{time_part}-{counter:04d}"
            if not ServiceRequest.objects.filter(sr_number=sr_number).exists():
                return sr_number
            counter = (counter + 1) % 10000

        import random
        return f"SR-{date_part}-{time_part}-{random.randint(1000, 9999)}"

    def save(self, *args, **kwargs):
        if not self.sr_number:
            self.sr_number = self._generate_unique_sr_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.sr_number} - {self.subject[:50]}"

    class Meta:
        ordering = ["-created_at"]


class SRComment(models.Model):
    """
    Comments/Notes added to Service Requests for tracking communication.
    """
    service_request = models.ForeignKey(
        ServiceRequest,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sr_comments'
    )
    
    comment = models.TextField()
    
    is_internal = models.BooleanField(
        default=False,
        help_text="Internal notes not visible to customers"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "SR Comment"
        verbose_name_plural = "SR Comments"
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment on {self.service_request.sr_number} by {self.user}"

class SRStatus(models.Model):
    STATUS_OPEN = "open"
    STATUS_WIP = "wip"
    STATUS_CLOSED = "closed"

    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_WIP, "Work In Progress"),
        (STATUS_CLOSED, "Closed"),
    ]

    code = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        unique=True
    )

    name = models.CharField(max_length=30)

    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "SR Status"
        verbose_name_plural = "SR Statuses"

    def __str__(self):
        return self.name


class SRTATDays(models.Model):
    """
    Defines TAT (in days) for each SR Nature + SR Type combination
    """

    sr_nature = models.CharField(
        max_length=20,
        choices=SR_NATURE_CHOICES
    )

    sr_type = models.CharField(
        max_length=30,
        choices=SR_TYPE_CHOICES
    )

    tat_days = models.PositiveIntegerField(
        help_text="TAT in days"
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('sr_nature', 'sr_type')
        verbose_name = "SR TAT (Days)"
        verbose_name_plural = "SR TATs (Days)"

    def __str__(self):
        return f"{self.sr_nature} | {self.sr_type} → {self.tat_days} days"


class SRNature(models.Model):
    """
    Master table for SR Nature
    """

    code = models.CharField(
        max_length=20,
        unique=True
    )

    name = models.CharField(
        max_length=50
    )

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "sr_nature"
        ordering = ["name"]


class SRType(models.Model):
    """
    Master table for SR Type
    """

    code = models.CharField(
        max_length=30,
        unique=True
    )

    name = models.CharField(
        max_length=100)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "sr_type"
        ordering = ["name"]
