from django.shortcuts import render, redirect , get_object_or_404
from datetime import datetime
from .models import Project, Comment
from django.utils import timezone

comments = [
    {
        'name': 'Alice Johnson',
        'comment': 'So happy to see this goal reached. Truly inspiring!',
        'time': datetime(2024, 3, 25, 14, 30).strftime('%B %d, %Y %H:%M')
    },
    {
        'name': 'Mohamed Salah',
        'comment': 'May God reward everyone who contributed ❤️',
        'time': datetime(2024, 3, 25, 16, 45).strftime('%B %d, %Y %H:%M')
    },
    {
        'name': 'Fatima Elbaz',
        'comment': 'This is the power of community. Well done everyone!',
        'time': datetime(2024, 3, 26, 9, 15).strftime('%B %d, %Y %H:%M')
    },
        {
        'name': 'Alice Johnson',
        'comment': 'So happy to see this goal reached. Truly inspiring!',
        'time': datetime(2024, 3, 25, 14, 30).strftime('%B %d, %Y %H:%M')
    },
    {
        'name': 'Mohamed Salah',
        'comment': 'May God reward everyone who contributed ❤️',
        'time': datetime(2024, 3, 25, 16, 45).strftime('%B %d, %Y %H:%M')
    }
]

def fundraiser_view(request, project_id):


    project = get_object_or_404(Project, pk=project_id)
    # Handle comment submission

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
        return redirect('fundraiser', project_id=project.id)

    # Fetch comments from the database by time
    comments = project.comments.order_by('-time')
    percent = int(min((project.raised / project.goal) * 100, 100))



    context = {
        'goal': project.goal,
        'raised': project.raised,
        'percent': percent,
        'description': project.description,
        'rating': project.rating,
        'creator': {
            'name': project.creator_name,
            'image': project.creator_image,
        },
        'created_at': project.created_at,
        'comments': comments,
    }

    return render(request, 'fundraiser.html', context)
