from django.shortcuts import render, redirect
from .forms import RegistrationForm, LoginForm, ProfileEditForm, DeleteAccountForm
from .models import User
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from datetime import date
from django.core.exceptions import ValidationError


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            user = authenticate(request, email=email, password=password)

            if user is not None:
                if user.is_active:
                    login(request, user)
                    next_url = request.GET.get("next", "home")
                    return redirect(next_url)
                else:
                    messages.error(
                        request, "Account is inactive. Please activate your account."
                    )
            else:
                messages.error(request, "Invalid email or password.")
    else:
        form = LoginForm()

    return render(request, "login/login.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect("login")


@login_required
def profile_view(request):
    from projects.models import Project, Donation

    user_projects = Project.objects.filter(creator=request.user)
    user_donations = Donation.objects.filter(user=request.user)

    context = {
        "user": request.user,
        "projects": user_projects,
        "donations": user_donations,
    }
    return render(request, "profile/profile.html", context)


@login_required
def edit_profile(request):
    if request.method == "POST":
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = request.user.email
            user.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect("profile")
    else:
        form = ProfileEditForm(instance=request.user)

    return render(request, "profile/edit_profile.html", {"form": form})


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.set_password(form.cleaned_data["password"])
            if "profile_picture" in request.FILES:
                user.profile_picture = request.FILES["profile_picture"]

            user.save()
            current_site = get_current_site(request)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            activation_link = (
                f"http://{current_site.domain}/auth/activate/{uid}/{token}/"
            )

            mail_subject = "Activate your crowdfunding account"
            message = render_to_string(
                "register/activation_email.html",
                {
                    "user": user,
                    "activation_link": activation_link,
                },
            )
            to_email = form.cleaned_data.get("email")
            email = EmailMessage(mail_subject, message, to=[to_email])
            email.content_subtype = "html"

            email.send()

            return render(request, "register/activation_sent.html")
    else:
        form = RegistrationForm()
    return render(request, "register/register.html", {"form": form})


def activate(request, uidb64, token):
    User = get_user_model()
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return render(request, "register/activation_success.html")
    else:
        return render(request, "register/activation_invalid.html")


@login_required
def delete_account(request):
    if request.method == "POST":
        form = DeleteAccountForm(request.POST, user=request.user)
        if form.is_valid():
            username = request.user.username
            user = request.user
            logout(request)
            user.delete()

            messages.success(
                request, f"Account '{username}' has been permanently deleted."
            )
            return redirect("login")
    else:
        form = DeleteAccountForm(user=request.user)

    return render(request, "profile/delete_account.html", {"form": form})
