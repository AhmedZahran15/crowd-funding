from django.contrib import admin
from .models import Project, ProjectImage, Donation, Comment, Rating, ProjectReport, CommentReport, Category, Tag

# Register your models here.

admin.site.register(Project)
admin.site.register(ProjectImage)
admin.site.register(Donation)
admin.site.register(Comment)
admin.site.register(Rating)
admin.site.register(ProjectReport)
admin.site.register(CommentReport)
admin.site.register(Category)
admin.site.register(Tag)
