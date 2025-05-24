
from django.urls import path
from .views.comments_views import (
     CommentListView, CommentCreateView, 
    CommentUpdateView, CommentDeleteView, 
    comment_report, 
)
from .views.rating_views import (rate_project, ProjectCreateView)
from .views.projects_views import project_view

app_name = 'projects'

urlpatterns = [
    path('<int:project_id>/', project_view, name='projects'),

    path('comments/', CommentListView.as_view(), name='comments'),
    path('comments/add/', CommentCreateView.as_view(), name='comment-add'),
    path('comments/<int:pk>/edit/', CommentUpdateView.as_view(), name='comment_edit'),
    path('comments/<int:pk>/delete/', CommentDeleteView.as_view(), name='comment_delete'),
    path('comment/<int:comment_id>/report/', comment_report, name='comment_report'),
    
    path('rate-project/', rate_project, name='rate-project'),
    path('', ProjectCreateView.as_view(), name='create-project'),
]