from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View

from ..forms import ProjectForm
from ..models import Rating, Project, Tag, ProjectImage

def rate_project(request, project_id):
    if not request.user.is_authenticated:
        messages.error(request, 'You must be logged in to rate a project.')
        return redirect('projects:comments')
    
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == 'POST':
        try:
            rating_value = int(request.POST.get('rating'))
            if rating_value < 1 or rating_value > 5:
                messages.error(request, 'Rating must be between 1 and 5.')
                return redirect('projects:project_detail', pk=project_id)
            
            rating, created = Rating.objects.get_or_create(
                project=project,
                user=request.user,
                defaults={'rating': rating_value}
            )
            
            if not created:
                rating.rating = rating_value
                rating.save()
                messages.success(request, 'Rating updated successfully!')
            else:
                messages.success(request, 'Rating added successfully!')
                
        except (ValueError, TypeError):
            messages.error(request, 'Invalid rating value.')
        
        return redirect('projects:project_detail', pk=project_id)
    return redirect('projects:project_detail', pk=project_id)

            
class ProjectCreateView(LoginRequiredMixin, View):
    model = Project
    template_name = "projects/create_project.html"
    context_object_name = 'projects'
    def get(self, request):
        return render(request, self.template_name, {'form': ProjectForm()})
    
    def post(self, request):
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.creator = request.user
            project.save()
            tags = form.cleaned_data['tags'].split(',')
            tag_list = []
            for tag_name in tags:
                tag_name = tag_name.strip()
                if tag_name:
                    tag, created = Tag.objects.get_or_create(name=tag_name)
                    tag_list.append(tag)
            project.tags.add(*tag_list)
            form.save_m2m()
            
            images = request.FILES.getlist('images')
            for image in images:
                ProjectImage.objects.create(project=project, image=image)
            
            messages.success(request, 'Project created successfully')
            return redirect('projects:create-project')

        else:
            print(form.errors)
            messages.error(request, 'There was an error with your submission.')
            return render(request, 'projects/create_project.html', {'form': form})
    