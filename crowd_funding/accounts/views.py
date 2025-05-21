from django.shortcuts import render, redirect
from .forms import RegistrationForm
from .models import User
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate, login
from django.contrib import messages

# For Login
def login_view(request):
    from .forms import LoginForm

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)

            if user is not None:
                if user.is_active:
                    login(request, user)
                    return redirect('home')  # or any page you want
                else:
                    messages.error(request, 'Account is inactive. Please activate your account.')
            else:
                messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()
    
    return render(request, 'login/login.html', {'form': form})

# For Registeration
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.set_password(form.cleaned_data['password'])
            user.save()

            # Email activation
            current_site = get_current_site(request)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            activation_link = f"http://{current_site.domain}/auth/activate/{uid}/{token}/"

            mail_subject = 'Activate your crowdfunding account'
            message = render_to_string('register/activation_email.html', {
                'user': user,
                'activation_link': activation_link,
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(mail_subject, message, to=[to_email])
            email.content_subtype = "html"  

            email.send()

            return render(request, 'register/activation_sent.html')
    else:
        form = RegistrationForm()
    return render(request, 'register/register.html', {'form': form})

# Activation Email
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
        return render(request, 'register/activation_success.html')
    else:
        return render(request, 'register/activation_invalid.html')


