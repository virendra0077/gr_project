from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, login
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
from django.views.decorators.csrf import csrf_protect
from grievance_management.forms import UserCreateForm
from apps.service_request.models import ServiceRequest, SRComment, SRStatus
from django.contrib.auth import authenticate
from apps.users.models import UserProfile


@csrf_protect
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid username or password")
            return redirect("login")

    return render(request, "users/login.html")


@login_required(login_url="login")
def dashboard_view(request):

    # ---- BASIC COUNTS ----
    total_sr = ServiceRequest.objects.count()

    open_sr = ServiceRequest.objects.filter(status__id="1").count()
    wip_sr = ServiceRequest.objects.filter(status__id="2").count()
    closed_sr = ServiceRequest.objects.filter(status__id="3").count()

    # ---- PIE CHART PERCENTAGES ----
    def pct(part, total):
        return round((part / total) * 100, 1) if total else 0

    open_pct = pct(open_sr, total_sr)
    wip_pct = pct(wip_sr, total_sr)
    closed_pct = pct(closed_sr, total_sr)

    # ---- LAST 7 DAYS SR CREATION ----
    today = timezone.now().date()
    start_date = today - timedelta(days=6)

    sr_by_day = (
        ServiceRequest.objects
        .filter(created_at__date__gte=start_date)
        .extra(select={"day": "DATE(created_at)"})
        .values("day")
        .annotate(count=Count("id"))
    )

    sr_day_map = {str(x["day"]): x["count"] for x in sr_by_day}

    bar_data = []
    max_count = 0
    
    # First pass: collect data and find max
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = sr_day_map.get(str(day), 0)
        max_count = max(max_count, count)
        bar_data.append({
            "label": day.strftime("%a"),
            "count": count
        })
    
    # Second pass: calculate heights as percentage of max
    if max_count > 0:
        for item in bar_data:
            item["height"] = int((item["count"] / max_count) * 100)
    else:
        for item in bar_data:
            item["height"] = 0

    context = {
        "total_sr": total_sr,
        "open_sr": open_sr,
        "wip_sr": wip_sr,
        "closed_sr": closed_sr,
        "open_pct": open_pct,
        "wip_pct": wip_pct,
        "closed_pct": closed_pct,
        "bar_data": bar_data,
        "max_count": max_count,
    }

    return render(request, "home.html", context)


@login_required
def logout_view(request):
    """
    Handle user logout
    """
    username = request.user.username
    logout(request)

    messages.success(request, "You have been logged out successfully.")
    return redirect('login')

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("login")



@login_required
def profile_view(request):
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)

    if request.method == "POST":
        user.first_name = request.POST.get("first_name", "").strip()
        user.last_name = request.POST.get("last_name", "").strip()
        user.email = request.POST.get("email", "").strip()
        profile.phone = request.POST.get("phone", "").strip()

        try:
            user.save()
            profile.save()
            messages.success(request, "Profile updated successfully!")
        except Exception as e:
            messages.error(request, f"Error updating profile: {e}")

        return redirect("profile")

    return render(
        request,
        "accounts/profile.html",
        {"user": user, "profile": profile}
    )


@login_required
def change_password_view(request):
    if request.method == "POST":
        old_password = request.POST.get("old_password")
        new_password1 = request.POST.get("new_password1")
        new_password2 = request.POST.get("new_password2")

        user = request.user

        if not user.check_password(old_password):
            messages.error(request, "Old password is incorrect.")
            return redirect("change_password")

        if new_password1 != new_password2:
            messages.error(request, "Passwords do not match.")
            return redirect("change_password")

        if len(new_password1) < 8:
            messages.error(request, "Password must be at least 8 characters.")
            return redirect("change_password")

        user.set_password(new_password1)
        user.save()

        login(request, user)  # re-login
        messages.success(request, "Password changed successfully.")
        return redirect("dashboard")

    return render(request, "accounts/change_password.html")


@login_required
def user_create_view(request):
    #  Admin-only protection
    if not request.user.profile.is_admin:
        messages.error(request, "You are not allowed to access this page.")
        return redirect("dashboard")

    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "User created successfully!")
            return redirect("dashboard")
    else:
        form = UserCreateForm()

    return render(request, "users/user_create.html", {
        "form": form
    })