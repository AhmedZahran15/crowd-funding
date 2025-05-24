from django.shortcuts import redirect
from django.urls import resolve
from django.contrib import messages


class AuthRoutesMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            current_url_name = resolve(request.path_info).url_name
            auth_routes = [
                "login",
                "register",
                "password_reset",
                "password_reset_done",
                "password_reset_confirm",
                "password_reset_complete",
            ]
            if current_url_name in auth_routes:
                messages.info(request, "You are already logged in.")
                return redirect("home")
        response = self.get_response(request)
        return response
