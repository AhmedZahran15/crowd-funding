from django.urls import path
from . import views

urlpatterns = [
    path("", views.project_list, name="project_list"),
    path("<int:project_id>/", views.project_view, name="projects"),
    path("<int:project_id>/donate/", views.donation_view, name="donation"),
    path(
        "category/<int:category_id>/", views.category_projects, name="category_projects"
    ),
    path("create/", views.create_project, name="create_project"),
    path("<int:project_id>/edit/", views.edit_project, name="edit_project"),
    path("<int:project_id>/report/", views.report_project, name="report_project"),
    path("<int:project_id>/rate/", views.rate_project, name="rate_project"),
    path("<int:project_id>/cancel/", views.cancel_project, name="cancel_project"),
]
