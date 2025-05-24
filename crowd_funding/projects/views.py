from django.shortcuts import render, redirect , get_object_or_404
from datetime import datetime
from .models import Project, Comment, Rating , Donation
from django.utils import timezone
from django.db.models import Avg
from django.db.models import Sum


def project_view(request, project_id):


    project = get_object_or_404(Project, id=project_id)
    # Handle comment submission


    raised_data = Donation.objects.filter(project=project).aggregate(total_raised=Sum('amount'))
    raised_money = raised_data['total_raised'] if raised_data['total_raised'] is not None else 0


    if request.method == 'POST':
        name = request.POST.get('name')
        comment = request.POST.get('comment')
        if name and comment:
            Comment.objects.create(
                project=project,
                name=name,
                comment=comment,
                time=timezone.now()
            )
        return redirect('projects', project_id=project.id)

    # Fetch comments from the database by time
    comments = project.comment_set.order_by('-timestamp')
    percent = (raised_money / int(project.total_target)) * 100
    print(f"{project.total_target}")

    print(f"{percent}%")


    # Average rating
    avg_rating = Rating.objects.filter(project=project).aggregate(Avg('rating'))['rating__avg']
    avg_rating = round(avg_rating, 1) if avg_rating else 0

    context = {
        'goal': project.total_target,
        'raised': raised_money,
        'percent': percent,
        'title': project.title,
        'description': project.details,
        'rating': avg_rating,
        'creator': {
            'name': project.creator.username,
            'image': project.creator.profile_picture,
        },
        'created_at': project.start_time,
        'end_time': project.end_time,
        'Category': project.category.name,
        'comments': project.comment_set.all(),
        'project': project,
    }

    return render(request, 'project_details.html', context)


def donation_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    if request.method == 'POST':
        amount = request.POST.get('amount')
        if amount:
            Donation.objects.create(
                project=project,
                user=request.user,
                amount=amount,
                timestamp=timezone.now()
            )
            return redirect('projects', project_id=project.id)

    return render(request, 'donations.html', {'project': project})