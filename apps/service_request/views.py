from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
from .models import ServiceRequest, SRComment, SRStatus
from django.conf import settings
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction

from .models import ServiceRequest, SRNature, SRType, SRStatus



@login_required
@require_POST
def create_sr_submit(request):

    if request.method != "POST":
        return redirect("service_request:create_sr_form")

    context = {
        "form_data": request.POST,
        "sr_natures": SRNature.objects.filter(is_active=True),
        "sr_types": SRType.objects.filter(is_active=True),
    }

    category = request.POST.get("category", "").strip()
    account_number = request.POST.get("account_number", "").strip()
    sr_nature_id = request.POST.get("sr_nature", "").strip()
    sr_type_id = request.POST.get("sr_type", "").strip()
    subject = request.POST.get("subject", "").strip()
    description = request.POST.get("description", "").strip()
    email = request.POST.get("email", "").strip()
    phone = request.POST.get("phone", "").strip()
    address = request.POST.get("address", "").strip()

    errors = {}

    # --- validation logic ---
    if not category or category not in ("parented", "unparented"):
        errors["category"] = "Please select a valid SR category"

    if category == "parented" and not account_number:
        errors["account_number"] = "Account number is required for Parented SR"

    if not sr_nature_id:
        errors["sr_nature"] = "Please select SR nature"

    if not sr_type_id:
        errors["sr_type"] = "Please select SR type"

    if not subject or len(subject) < 5:
        errors["subject"] = "Subject must be at least 5 characters"

    if not description or len(description) < 20:
        errors["description"] = "Description must be at least 20 characters"

    if not email:
        errors["email"] = "Email is required"

    if not phone:
        errors["phone"] = "Phone number is required"

    if errors:
        context["errors"] = errors
        return render(request, "service_request/create_sr.html", context)

    try:
        with transaction.atomic():

            sr_nature = get_object_or_404(SRNature, id=sr_nature_id, is_active=True)
            sr_type = get_object_or_404(SRType, id=sr_type_id, is_active=True)
            open_status = get_object_or_404(SRStatus, id="1", is_active=True)

            sr = ServiceRequest.objects.create(
                category=category,
                account_number=account_number if category == "parented" else None,
                sr_nature=sr_nature,
                sr_type=sr_type,
                subject=subject,
                description=description,
                email=email,
                phone=phone,
                address=address,
                created_by=request.user,
                assigned_to=request.user if request.user.is_staff else None,
                status= open_status,
            )

        messages.success(
            request,
            f"Service Request {sr.sr_number} created successfully!"
        )
        return redirect("view_sr", sr_id=sr.id)

    except Exception as e:
        print("CREATE SR ERROR:", e)
        messages.error(
            request,
            "Something went wrong while creating the service request. Please try again."
        )
        return render(request, "service_request/create_sr.html", context)

@login_required
def create_sr_form(request):
    """
    Display Create Service Request form (GET)
    """
    return render(request, "service_request/create_sr.html", {
        "sr_natures": SRNature.objects.filter(is_active=True),
        "sr_types": SRType.objects.filter(is_active=True),
    })



@login_required
def list_sr(request):
    srs = ServiceRequest.objects.all()
    search_query = request.GET.get('search', '').strip()
    if search_query:
        srs = srs.filter(
            Q(sr_number__icontains=search_query) |
            Q(subject__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    category = request.GET.get('category', '').strip()
    if category:
        srs = srs.filter(category=category)

    # FIX: Use status__code instead of status
    status = request.GET.get('status', '').strip()
    if status:
        srs = srs.filter(status__code=status.upper())

    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()

    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            srs = srs.filter(created_at__date__gte=date_from_obj.date())
        except ValueError:
            messages.warning(request, 'Invalid start date format')

    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            srs = srs.filter(created_at__date__lte=date_to_obj.date())
        except ValueError:
            messages.warning(request, 'Invalid end date format')

    sort_by = request.GET.get('sort', '-created_at')
    valid_sorts = [
        'sr_number', '-sr_number',
        'created_at', '-created_at',
        'status', '-status',
    ]
    if sort_by in valid_sorts:
        srs = srs.order_by(sort_by)

    # FIX: Use status__code for filtering
    stats = {
        'total': srs.count(),
        'open': srs.filter(status__code='OPEN').count(),
        'wip': srs.filter(status__code='WIP').count(),
        'closed': srs.filter(status__code='CLOSED').count(),
    }

    items_per_page = getattr(settings, 'ITEMS_PER_PAGE', 15)
    paginator = Paginator(srs, items_per_page)
    page_number = request.GET.get('page', 1)
    
    try:
        page_obj = paginator.get_page(page_number)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.get_page(1)

    context = {
        'service_requests': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'stats': stats,
        'search_query': search_query,
        'filters': {
            'category': category,
            'status': status,
            'date_from': date_from,
            'date_to': date_to,
            'sort': sort_by,
        }
    }

    return render(request, 'service_request/list_sr.html', context)

@login_required
def view_sr(request, sr_id):
    """
    View detailed information of a specific Service Request
    """
    sr = get_object_or_404(ServiceRequest, id=sr_id)

    comments = sr.comments.all().order_by("created_at")

    context = {
        "sr": sr,
        "comments": comments,
    }

    return render(request, "service_request/view_sr.html", context)



@login_required
def update_sr_status(request, sr_id):
    """
    Update the status of a Service Request (agents only)
    """
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to update service requests.")
        return redirect('service_request:list_sr')
    
    sr = get_object_or_404(ServiceRequest, id=sr_id)
    
    if request.method == 'POST':
        old_status = sr.status
        new_status = request.POST.get('status', '').strip()
        notes = request.POST.get('notes', '').strip()
        
        if new_status and new_status != old_status:
            sr.status = new_status
            
            # Handle closing
            if new_status == 'closed':
                sr.closed_by = request.user
                sr.closed_at = timezone.now()
            
            sr.save()
            
            messages.success(request, f'Status updated to {sr.get_status_display()}')
    
    return redirect('service_request:view_sr', sr_id=sr.id)


@login_required
def assign_sr(request, sr_id):
    """
    Assign a Service Request to an agent
    """
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to assign SRs.")
        return redirect("list_sr")

    
    sr = get_object_or_404(ServiceRequest, id=sr_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'assign_to_me':
            sr.assigned_to = request.user
            sr.save()
            messages.success(request, f'SR {sr.sr_number} assigned to you.')
            
        
        return redirect('service_request:view_sr', sr_id=sr.id)
    
    return redirect('service_request:list_sr')

@login_required
@require_POST
def add_sr_comment(request, sr_id):
    sr = get_object_or_404(ServiceRequest, id=sr_id)

    comment_text = request.POST.get("comment", "").strip()

    if comment_text:
        SRComment.objects.create(
            service_request=sr,
            user=request.user,
            comment=comment_text,
        )
        messages.success(request, "Comment added successfully.")
    else:
        messages.error(request, "Comment cannot be empty.")

    return redirect("view_sr", sr_id=sr.id)
