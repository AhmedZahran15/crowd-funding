from django import forms
from .models import Comment, Project
from django.core.exceptions import ValidationError
from django.forms.widgets import ClearableFileInput
from django.utils import timezone
from datetime import datetime


class ProjectForm(forms.ModelForm):
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter each tag and press Enter",
                "data-bs-toggle": "tooltip",
                "data-bs-placement": "top",
                "title": "Add relevant tags to help people find your project",
            }
        ),
    )

    class Meta:
        model = Project
        fields = [
            "title",
            "details",
            "category",
            "total_target",
            "start_time",
            "end_time",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "details": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "total_target": forms.NumberInput(
                attrs={"class": "form-control", "min": "500", "step": "0.01"}
            ),
            "start_time": forms.DateInput(
                attrs={"class": "form-control", "type": "date", "id": "start_date"}
            ),
            "end_time": forms.DateInput(
                attrs={"class": "form-control", "type": "date", "id": "end_date"}
            ),
        }

    def clean_total_target(self):
        total_target = self.cleaned_data.get("total_target")
        if not total_target or total_target < 500:
            raise ValidationError("Funding goal must be at least $500")
        return total_target

    def clean_start_time(self):
        start_time = self.cleaned_data.get("start_time")
        if start_time and start_time < timezone.now().date():
            raise ValidationError("Start date cannot be in the past")
        return start_time

    def clean_end_time(self):
        end_time = self.cleaned_data.get("end_time")
        start_time = self.cleaned_data.get("start_time")

        if end_time:
            if end_time < timezone.now().date():
                raise ValidationError("End date cannot be in the past")

            if start_time and end_time <= start_time:
                raise ValidationError("End date must be after start date")

        return end_time


class ProjectImageForm(forms.Form):
    files = forms.FileField(
        widget=ClearableFileInput(attrs={"multiple": False}), required=False
    )
