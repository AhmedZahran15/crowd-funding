from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View

from ..models import Project, Comment, CommentReport
from ..forms import CommentForm

class CommentListView(ListView):
    model = Comment
    template_name = "projects/comments.html"
    context_object_name = 'comments'
    ordering = ['-timestamp']

    def get_queryset(self):
        project_id = self.request.GET.get('project')
        queryset = Comment.objects.all().order_by('-timestamp')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['projects'] = Project.objects.all()
        return context

class CommentCreateView(LoginRequiredMixin, View):
    def post(self, request):
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.save()
            messages.success(request, 'Comment added successfully!')
        else:
            messages.error(request, 'There was an error with your comment.')

        return redirect('projects:comments')


class CommentUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk, user=request.user)
        new_text = request.POST.get('text', '').strip()

        if new_text:
            comment.text = new_text
            comment.save()
            messages.success(request, 'Comment updated successfully!')
        else:
            messages.error(request, 'Comment text cannot be empty.')
        return redirect('projects:comments')


class CommentDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk, user=request.user)
        comment.delete()
        messages.success(request, 'Comment deleted successfully!')
        return redirect('projects:comments')


def comment_report(request, comment_id):
    if request.method == 'POST' and request.user.is_authenticated:
        comment = get_object_or_404(Comment, id=comment_id)
        reason = request.POST.get('reason', '')
        if not reason:
            messages.warning(request, 'Please provide a reason for reporting.')
            return redirect('projects:comments')

        existing_report = CommentReport.objects.filter(
            user=request.user,
            comment=comment
        ).first()

        if existing_report:
            messages.warning(request, 'You have already reported this comment.')
        else:
            CommentReport.objects.create(
                user=request.user,
                comment=comment,
                reason=reason
            )
            messages.success(request, 'Comment reported successfully.')
    return redirect('projects:comments')
# def project_comments(request, project_id):
#     """Get all comments for a specific project"""
#     project = get_object_or_404(Project, id=project_id)
#     comments = Comment.objects.filter(project=project).order_by('-created_at')
    
#     paginator = Paginator(comments, 5)
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)
    
#     context = {
#         'project': project,
#         'comments': page_obj,
#         'comment_count': comments.count()
#     }
    
#     return render(request, 'projects/project_comments.html', context)

