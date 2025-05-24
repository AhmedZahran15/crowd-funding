from django.shortcuts import render
from projects.models import Project, Category
from django.db.models import Count, Avg


def home(request):
    featured_projects = Project.objects.filter(is_featured=True)[:5]
    latest_projects = Project.objects.order_by("-start_time")[:5]
    highest_rated_projects = (
        Project.objects.annotate(avg_rating=Avg("rating__rating"))
        .filter(avg_rating__isnull=False)
        .order_by("-avg_rating")[:5]
    )
    if highest_rated_projects.count() < 5:
        highest_rated_projects = Project.objects.annotate(
            donation_count=Count("donation")
        ).order_by("-donation_count")[:5]
    categories = Category.objects.all()[:5]
    context = {
        "featured_projects": featured_projects,
        "latest_projects": latest_projects,
        "highest_rated_projects": highest_rated_projects,
        "categories": categories,
    }
    return render(request, "home.html", context)
