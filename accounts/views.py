from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import CustomUserCreationForm, CustomAuthenticationForm, EditProfileForm, ChangePasswordForm
from .models import CustomUser
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponse

User = get_user_model()

def send_verification_email(user, request):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    verification_link = request.build_absolute_uri(f"/accounts/verify/{uid}/{token}/")

    subject = "Verify Your Email"
    
    # Render the email template
    context = {"user": user, "verification_link": verification_link}
    html_message = render_to_string("emails/verification_email.html", context)

    # Send email with HTML content
    send_mail(
        subject,
        "",  # Leave plain text message empty
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
        html_message=html_message,  # This makes the email HTML formatted
    )


def verify_email_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.email_confirmation = True
        user.save()
        messages.success(request, "Your email has been verified. You can now log in.")
        return redirect("login")
    else:
        messages.error(request, "Invalid verification link.")
        return redirect("register")
       

def register_view(request):
    # Redirect authenticated users
    if request.user.is_authenticated:
        return redirect("dashboard")  
    
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()

            send_verification_email(user, request)
            messages.success(request, "Registration successful! Check your email to verify your account.")
            return redirect("login")  # Redirect to login instead of logging in automatically

    else:
        form = CustomUserCreationForm()

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    # Check if the user is already logged in
    if request.user.is_authenticated:
        return redirect("dashboard")  # Redirect to dashboard if already logged in
    
    if request.method == "POST":
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.email_confirmation:
                messages.error(request, "Please verify your email before logging in.")
                return redirect("login")
            login(request, user)
            next_url = request.GET.get("next", "dashboard")  # Redirect to 'next' if available
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")  # Add error message

    else:
        form = CustomAuthenticationForm()

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def dashboard_view(request):
    return render(request, "dashboard.html")


# Check if user is an admin
def is_admin(user):
    return user.is_authenticated and user.is_staff


@login_required
@user_passes_test(is_admin)
def users_view(request):
    users = CustomUser.objects.exclude(id=request.user.id)  # Exclude logged-in admin

    # Pagination
    paginator = Paginator(users, 1)  # Show 10 users per page
    page_number = request.GET.get("page")
    page_users = paginator.get_page(page_number)

    return render(request, "accounts/users.html", {"users": page_users})


@login_required
def edit_profile_view(request):
    user = request.user  # Get the logged-in user

    profile_form = EditProfileForm(instance=user)
    password_form = ChangePasswordForm(user)

    if request.method == "POST":
        if "save_profile" in request.POST:  # Profile update form submission
            profile_form = EditProfileForm(request.POST, instance=user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Your profile has been updated successfully!")
                return redirect("edit_profile")

        elif "change_password" in request.POST:  # Password change form submission
            password_form = ChangePasswordForm(user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Keep the user logged in
                messages.success(request, "Your password has been changed successfully!")
                return redirect("edit_profile")

    return render(request, "accounts/edit_profile.html", {
        "profile_form": profile_form,
        "password_form": password_form,
    })


def send_test_email(request):
    subject = "Django Email Test"
    message = "This is a test email sent from Django."
    recipient_list = ["gkmamun26@gmail.com"]  # Replace with your email

    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
        return HttpResponse("Test email sent successfully!")
    except Exception as e:
        return HttpResponse(f"Failed to send email: {e}")