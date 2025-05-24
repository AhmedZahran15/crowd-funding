from django import forms
from .models import Comment, Project
from django.core.exceptions import ValidationError
from django.forms.widgets import ClearableFileInput
class ProjectForm(forms.ModelForm):
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter tags separated by commas'
        }),
    )
    class Meta:
        model = Project
        fields = ['title','details','category', 'total_target', 'start_time', 'end_time']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'details': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'total_target': forms.TextInput(attrs={'class': 'form-control'}),
            'start_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'end_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
        }

    def clean_total_target(self):
        total_target = self.cleaned_data.get('total_target')
        if not total_target or total_target < 500:
            raise ValidationError('Funding goal must be greater than 500')
        return total_target

    def clean_dates(self):
        start_time = self.cleaned_data.get('start_time')
        end_time = self.cleaned_data.get('end_time')
        if start_time > end_time:
            raise ValidationError('Start date must be before end date.')
        return
class ProjectImageForm(forms.Form):
    files = forms.FileField(
        widget=ClearableFileInput(attrs={'multiple': True}),
        required=False
    )
   
        
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['project', 'text']

        widgets = {
            'project': forms.Select(attrs={'class': 'form-control'}),
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

        labels = {
            'project': 'Project',
            'text': 'Your Comment',
       }
