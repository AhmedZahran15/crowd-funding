from django.shortcuts import render, redirect, get_object_or_404
from django.db import models
from .models import (
    Project,
    Comment,
    Rating,
    Donation,
    Category,
    ProjectReport,
    CommentReport,
    ProjectImage,
    Tag,
)
from django.utils import timezone
from django.db.models import Avg, Sum, Q, Count
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator


def project_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    raised_data = Donation.objects.filter(project=project).aggregate(
        total_raised=Sum("amount")
    )
    raised_money = (
        raised_data["total_raised"] if raised_data["total_raised"] is not None else 0
    )
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "add_comment" and request.user.is_authenticated:
            comment_text = request.POST.get("comment")
            parent_id = request.POST.get("parent_id")

            if comment_text:
                parent_comment = None
                if parent_id:
                    try:
                        parent_comment = Comment.objects.get(
                            id=parent_id, project=project
                        )
                    except Comment.DoesNotExist:
                        pass

                Comment.objects.create(
                    project=project,
                    user=request.user,
                    text=comment_text,
                    parent=parent_comment,
                )
                messages.success(request, "Comment added successfully!")

        elif action == "edit_comment" and request.user.is_authenticated:
            comment_id = request.POST.get("comment_id")
            new_text = request.POST.get("comment")

            try:
                comment = Comment.objects.get(
                    id=comment_id, user=request.user, project=project
                )
                if new_text:
                    comment.text = new_text
                    comment.save()
                    messages.success(request, "Comment updated successfully!")
            except Comment.DoesNotExist:
                messages.error(
                    request,
                    "Comment not found or you don't have permission to edit it.",
                )

        elif action == "delete_comment" and request.user.is_authenticated:
            comment_id = request.POST.get("comment_id")

            try:
                comment = Comment.objects.get(
                    id=comment_id, user=request.user, project=project
                )
                comment.delete()
                messages.success(request, "Comment deleted successfully!")
            except Comment.DoesNotExist:
                messages.error(
                    request,
                    "Comment not found or you don't have permission to delete it.",
                )

        elif action == "report_comment" and request.user.is_authenticated:
            comment_id = request.POST.get("comment_id")
            reason = request.POST.get("reason")

            if not reason or not reason.strip():
                messages.error(
                    request, "Please provide a reason for reporting this comment."
                )
                return redirect("projects", project_id=project.id)

            try:
                comment = Comment.objects.get(id=comment_id, project=project)
                existing_report = CommentReport.objects.filter(
                    user=request.user, comment=comment
                ).first()

                if existing_report:
                    messages.warning(request, "You have already reported this comment.")
                else:
                    CommentReport.objects.create(
                        user=request.user, comment=comment, reason=reason.strip()
                    )
                    messages.success(
                        request,
                        "Comment reported successfully. Our team will review it.",
                    )
            except Comment.DoesNotExist:
                messages.error(request, "Comment not found.")

        elif action == "rate" and request.user.is_authenticated:
            rating_value = request.POST.get("rating")
            if rating_value:
                try:
                    rating_value = int(rating_value)
                    if 1 <= rating_value <= 5:
                        rating, created = Rating.objects.get_or_create(
                            project=project,
                            user=request.user,
                            defaults={"rating": rating_value},
                        )
                        if not created:
                            rating.rating = rating_value
                            rating.save()
                        messages.success(
                            request,
                            f"You rated this project {rating_value} star{'s' if rating_value != 1 else ''}!",
                        )
                except ValueError:
                    messages.error(request, "Invalid rating value.")

        return redirect("projects", project_id=project.id)
    top_level_comments = project.comment_set.filter(parent=None).order_by("-timestamp")
    comments_with_replies = []
    for comment in top_level_comments:
        replies = comment.comment_set.all().order_by("timestamp")
        comments_with_replies.append({"comment": comment, "replies": replies})
    percent = (
        (raised_money / int(project.total_target)) * 100
        if project.total_target > 0
        else 0
    )
    avg_rating = Rating.objects.filter(project=project).aggregate(Avg("rating"))[
        "rating__avg"
    ]
    avg_rating = round(avg_rating, 1) if avg_rating else 0

    total_ratings = Rating.objects.filter(project=project).count()

    user_rating = None
    if request.user.is_authenticated:
        try:
            user_rating_obj = Rating.objects.get(project=project, user=request.user)
            user_rating = user_rating_obj.rating
        except Rating.DoesNotExist:
            pass
    can_be_cancelled = project.can_be_cancelled()
    similar_projects = []
    if project.tags.exists():
        similar_projects = (
            Project.objects.filter(tags__in=project.tags.all(), status="active")
            .exclude(id=project.id)
            .distinct()
            .annotate(
                shared_tags_count=Count("tags", filter=Q(tags__in=project.tags.all())),
                total_raised=Sum("donation__amount", default=0),
            )
            .order_by("-shared_tags_count", "-start_time")[:4]
        )
    if len(similar_projects) < 4:
        category_projects = (
            Project.objects.filter(category=project.category, status="active")
            .exclude(id=project.id)
            .exclude(id__in=[p.id for p in similar_projects])
            .annotate(total_raised=Sum("donation__amount", default=0))
            .order_by("-start_time")[: 4 - len(similar_projects)]
        )

        similar_projects = list(similar_projects) + list(category_projects)

    context = {
        "goal": project.total_target,
        "raised": raised_money,
        "percent": percent,
        "title": project.title,
        "description": project.details,
        "rating": avg_rating,
        "total_ratings": total_ratings,
        "user_rating": user_rating,
        "creator": {
            "name": project.creator.get_full_name(),
            "image": project.creator.profile_picture,
        },
        "created_at": project.start_time,
        "end_time": project.end_time,
        "Category": project.category.name,
        "comments": top_level_comments,
        "comments_with_replies": comments_with_replies,
        "project": project,
        "can_be_cancelled": can_be_cancelled,
        "similar_projects": similar_projects,
    }

    return render(request, "project_details.html", context)


def donation_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    if request.method == "POST":
        amount = request.POST.get("amount")
        if amount and request.user.is_authenticated:
            Donation.objects.create(
                project=project,
                user=request.user,
                amount=amount,
                timestamp=timezone.now(),
            )
            messages.success(request, "Thank you for your donation!")
            return redirect("projects", project_id=project.id)
        elif not request.user.is_authenticated:
            messages.error(request, "You need to be logged in to make a donation.")
            return redirect("account_login")

    return render(request, "donations.html", {"project": project})


def project_list(request):
    search_query = request.GET.get("search", "")
    category_id = request.GET.get("category", "")

    projects = (
        Project.objects.all()
        .annotate(total_raised=Sum("donation__amount", default=0))
        .prefetch_related("tags", "category", "images")
        .order_by("-start_time")
    )
    for project in projects:
        if project.total_target > 0:
            project.progress_percentage = (
                project.total_raised / project.total_target
            ) * 100
        else:
            project.progress_percentage = 0

    if search_query:
        projects = projects.filter(
            Q(title__icontains=search_query)  # Project title
            | Q(details__icontains=search_query)  # Project description
            | Q(tags__name__icontains=search_query)  # Tags (partial match)
            | Q(category__name__icontains=search_query)  # Category name
            | Q(creator__first_name__icontains=search_query)  # Creator first name
            | Q(creator__last_name__icontains=search_query)  # Creator last name
            | Q(creator__username__icontains=search_query)  # Creator username
        ).distinct()
    if category_id:
        projects = projects.filter(category_id=category_id)
    paginator = Paginator(projects, 9)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    categories = Category.objects.all()

    context = {
        "page_obj": page_obj,
        "categories": categories,
        "search_query": search_query,
        "selected_category": int(category_id) if category_id.isdigit() else None,
    }

    return render(request, "project_list.html", context)


def category_projects(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    projects = Project.objects.filter(category=category).order_by("-start_time")
    paginator = Paginator(projects, 9)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "category": category,
        "page_obj": page_obj,
    }

    return render(request, "category_projects.html", context)


@login_required
def create_project(request):
    if request.method == "POST":
        title = request.POST.get("title")
        details = request.POST.get("details")
        category_id = request.POST.get("category")
        total_target = request.POST.get("total_target")
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")
        tags_input = request.POST.get("tags", "")

        if (
            title
            and details
            and category_id
            and total_target
            and start_time
            and end_time
        ):
            try:
                from datetime import datetime

                start_date = datetime.strptime(start_time, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_time, "%Y-%m-%d").date()
                today = timezone.now().date()
                if start_date < today:
                    messages.error(request, "Start date cannot be in the past.")
                    categories = Category.objects.all()
                    return render(
                        request, "create_project.html", {"categories": categories}
                    )

                if end_date < today:
                    messages.error(request, "End date cannot be in the past.")
                    categories = Category.objects.all()
                    return render(
                        request, "create_project.html", {"categories": categories}
                    )

                if end_date <= start_date:
                    messages.error(request, "End date must be after start date.")
                    categories = Category.objects.all()
                    return render(
                        request, "create_project.html", {"categories": categories}
                    )
                project = Project.objects.create(
                    title=title,
                    details=details,
                    category_id=category_id,
                    total_target=total_target,
                    start_time=start_date,
                    end_time=end_date,
                    creator=request.user,
                )
                if tags_input:
                    tag_names = [
                        tag.strip().lower()
                        for tag in tags_input.split(",")
                        if tag.strip()
                    ]
                    for tag_name in tag_names:
                        tag, created = Tag.objects.get_or_create(name=tag_name)
                        project.tags.add(tag)
                images = request.FILES.getlist("images")
                for image in images:
                    ProjectImage.objects.create(project=project, image=image)

                messages.success(request, "Project created successfully!")
                return redirect("projects", project_id=project.id)

            except ValueError as e:
                messages.error(request, "Invalid date format.")
                categories = Category.objects.all()
                return render(
                    request, "create_project.html", {"categories": categories}
                )
        else:
            messages.error(request, "Please fill out all required fields.")
    categories = Category.objects.all()
    context = {
        "categories": categories,
    }

    return render(request, "create_project.html", context)


@login_required
def report_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    if request.method == "POST":
        reason = request.POST.get("reason")
        if reason:
            ProjectReport.objects.create(
                project=project,
                user=request.user,
                reason=reason,
                timestamp=timezone.now(),
            )
            messages.success(
                request,
                "Thank you for reporting this project. Our team will review it.",
            )
            return redirect("projects", project_id=project_id)
        else:
            messages.error(request, "Please provide a reason for reporting.")

    return render(request, "report_project.html", {"project": project})


@login_required
def rate_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    if request.method == "POST":
        rating_value = request.POST.get("rating")
        if rating_value:
            Rating.objects.update_or_create(
                project=project, user=request.user, defaults={"rating": rating_value}
            )
            messages.success(request, "Thank you for rating this project!")
        else:
            messages.error(request, "Please select a rating.")

    return redirect("projects", project_id=project_id)


@login_required
def edit_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.user != project.creator:
        messages.error(request, "You don't have permission to edit this project.")
        return redirect("projects", project_id=project.id)
    if project.status == "cancelled":
        messages.error(request, "Cancelled projects cannot be edited.")
        return redirect("projects", project_id=project.id)

    if request.method == "POST":
        title = request.POST.get("title")
        details = request.POST.get("details")
        category_id = request.POST.get("category")
        total_target = request.POST.get("total_target")
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")
        tags_input = request.POST.get("tags", "")

        if (
            title
            and details
            and category_id
            and total_target
            and start_time
            and end_time
        ):
            try:
                from datetime import datetime

                start_date = datetime.strptime(start_time, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_time, "%Y-%m-%d").date()
                today = timezone.now().date()
                if start_date < today:
                    messages.error(request, "Start date cannot be in the past.")
                    categories = Category.objects.all()
                    context = {
                        "project": project,
                        "categories": categories,
                        "current_tags": ", ".join(
                            [tag.name for tag in project.tags.all()]
                        ),
                    }
                    return render(request, "edit_project.html", context)

                if end_date < today:
                    messages.error(request, "End date cannot be in the past.")
                    categories = Category.objects.all()
                    context = {
                        "project": project,
                        "categories": categories,
                        "current_tags": ", ".join(
                            [tag.name for tag in project.tags.all()]
                        ),
                    }
                    return render(request, "edit_project.html", context)

                if end_date <= start_date:
                    messages.error(request, "End date must be after start date.")
                    categories = Category.objects.all()
                    context = {
                        "project": project,
                        "categories": categories,
                        "current_tags": ", ".join(
                            [tag.name for tag in project.tags.all()]
                        ),
                    }
                    return render(request, "edit_project.html", context)

                project.title = title
                project.details = details
                project.category_id = category_id
                project.total_target = total_target
                project.start_time = start_date
                project.end_time = end_date
                project.save()
                new_images = request.FILES.getlist("images")
                if new_images:
                    for image in new_images:
                        ProjectImage.objects.create(project=project, image=image)
                images_to_delete = request.POST.getlist("delete_images")
                if images_to_delete:
                    ProjectImage.objects.filter(id__in=images_to_delete).delete()
                project.tags.clear()
                if tags_input:
                    tag_names = [
                        tag.strip().lower()
                        for tag in tags_input.split(",")
                        if tag.strip()
                    ]
                    for tag_name in tag_names:
                        tag, created = Tag.objects.get_or_create(name=tag_name)
                        project.tags.add(tag)

                messages.success(request, "Project updated successfully!")
                return redirect("projects", project_id=project.id)

            except ValueError as e:
                messages.error(request, "Invalid date format.")
                categories = Category.objects.all()
                context = {
                    "project": project,
                    "categories": categories,
                    "current_tags": ", ".join([tag.name for tag in project.tags.all()]),
                }
                return render(request, "edit_project.html", context)
        else:
            messages.error(request, "Please fill out all required fields.")
    categories = Category.objects.all()
    context = {
        "project": project,
        "categories": categories,
        "current_tags": ", ".join([tag.name for tag in project.tags.all()]),
    }

    return render(request, "edit_project.html", context)


@login_required
def cancel_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.user != project.creator:
        messages.error(request, "You don't have permission to cancel this project.")
        return redirect("projects", project_id=project.id)
    if not project.can_be_cancelled():
        messages.error(
            request,
            "This project cannot be cancelled because it has received 25% or more of its target funding.",
        )
        return redirect("projects", project_id=project.id)
    donations = project.donation_set.all()
    total_amount = donations.aggregate(total=Sum("amount"))["total"] or 0

    if request.method == "POST":
        project.status = "cancelled"
        project.save()
        Donation.objects.filter(project=project).delete()

        messages.success(
            request,
            "Project has been cancelled successfully and all donations have been removed.",
        )
        return redirect("projects", project_id=project.id)

    context = {
        "project": project,
        "donations": donations,
        "total_amount": total_amount,
        "percentage": (
            (total_amount / project.total_target * 100)
            if project.total_target > 0
            else 0
        ),
    }

    return render(request, "cancel_project.html", context)


@login_required
def report_comment(request, comment_id):
    if request.method == "POST":
        comment = get_object_or_404(Comment, id=comment_id)
        reason = request.POST.get("reason", "").strip()

        if not reason:
            messages.error(
                request, "Please provide a reason for reporting this comment."
            )
        else:
            existing_report = CommentReport.objects.filter(
                user=request.user, comment=comment
            ).first()

            if existing_report:
                messages.warning(request, "You have already reported this comment.")
            else:
                CommentReport.objects.create(
                    user=request.user, comment=comment, reason=reason
                )
                messages.success(
                    request, "Comment reported successfully. Our team will review it."
                )

        return redirect("projects", project_id=comment.project.id)
    comment = get_object_or_404(Comment, id=comment_id)
    return redirect("projects", project_id=comment.project.id)
