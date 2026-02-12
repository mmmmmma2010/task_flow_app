"""
Django admin configuration for tasks app.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from tasks.models import Task, CompletedTask


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """
    Admin interface for Task model.
    
    Provides comprehensive management interface with:
    - List display with key fields
    - Filtering and searching
    - Bulk actions
    - Readonly fields for timestamps
    """
    
    list_display = [
        'id',
        'title',
        'status_badge',
        'priority_badge',
        'created_by',
        'assigned_to',
        'due_date',
        'is_overdue_display',
        'created_at',
    ]
    
    list_filter = [
        'status',
        'priority',
        'is_deleted',
        'created_at',
        'due_date',
    ]
    
    search_fields = [
        'title',
        'description',
        'created_by__username',
        'assigned_to__username',
    ]
    
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'completed_at',
        'deleted_at',
        'is_overdue_display',
        'days_until_due_display',
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'title', 'description')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority')
        }),
        ('Dates', {
            'fields': ('due_date', 'completed_at', 'is_overdue_display', 'days_until_due_display')
        }),
        ('Assignment', {
            'fields': ('created_by', 'assigned_to')
        }),
        ('Deletion', {
            'fields': ('is_deleted', 'deleted_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_completed', 'mark_as_pending', 'soft_delete_tasks']
    
    def status_badge(self, obj):
        """Display status as colored badge."""
        colors = {
            'pending': '#ffc107',
            'in_progress': '#17a2b8',
            'completed': '#28a745',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def priority_badge(self, obj):
        """Display priority as colored badge."""
        colors = {
            'low': '#28a745',
            'medium': '#ffc107',
            'high': '#dc3545',
        }
        color = colors.get(obj.priority, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'
    
    def is_overdue_display(self, obj):
        """Display overdue status."""
        if obj.is_overdue:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠ OVERDUE</span>'
            )
        return format_html('<span style="color: green;">✓ On Track</span>')
    is_overdue_display.short_description = 'Overdue Status'
    
    def days_until_due_display(self, obj):
        """Display days until due."""
        days = obj.days_until_due
        if days is None:
            return 'No due date'
        if days < 0:
            return format_html(
                '<span style="color: red;">{} days overdue</span>',
                abs(days)
            )
        return f'{days} days remaining'
    days_until_due_display.short_description = 'Days Until Due'
    
    @admin.action(description='Mark selected tasks as completed')
    def mark_as_completed(self, request, queryset):
        """Bulk action to mark tasks as completed."""
        count = 0
        for task in queryset:
            if task.status != Task.STATUS_COMPLETED:
                task.mark_complete()
                count += 1
        self.message_user(request, f'{count} tasks marked as completed.')
    
    @admin.action(description='Mark selected tasks as pending')
    def mark_as_pending(self, request, queryset):
        """Bulk action to mark tasks as pending."""
        count = queryset.update(status=Task.STATUS_PENDING)
        self.message_user(request, f'{count} tasks marked as pending.')
    
    @admin.action(description='Soft delete selected tasks')
    def soft_delete_tasks(self, request, queryset):
        """Bulk action to soft delete tasks."""
        count = 0
        for task in queryset:
            if not task.is_deleted:
                task.soft_delete()
                count += 1
        self.message_user(request, f'{count} tasks soft deleted.')


@admin.register(CompletedTask)
class CompletedTaskAdmin(admin.ModelAdmin):
    """
    Admin interface for CompletedTask proxy model.
    
    This demonstrates how proxy models can have different admin interfaces
    while sharing the same database table.
    
    This admin is read-only and focused on completion metrics.
    """
    
    list_display = [
        'id',
        'title',
        'priority_badge',
        'completed_at',
        'days_since_completion_display',
        'created_by',
        'is_archivable_display',
    ]
    
    list_filter = [
        'priority',
        'completed_at',
        'created_at',
    ]
    
    search_fields = [
        'title',
        'description',
        'created_by__username',
    ]
    
    readonly_fields = [
        'id',
        'title',
        'description',
        'status',
        'priority',
        'due_date',
        'completed_at',
        'created_by',
        'assigned_to',
        'created_at',
        'updated_at',
        'days_since_completion_display',
        'completion_summary_display',
    ]
    
    fieldsets = (
        ('Task Information', {
            'fields': ('id', 'title', 'description', 'priority')
        }),
        ('Completion Details', {
            'fields': ('completed_at', 'days_since_completion_display', 'completion_summary_display')
        }),
        ('Assignment', {
            'fields': ('created_by', 'assigned_to')
        }),
        ('Dates', {
            'fields': ('due_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['archive_tasks']
    
    def has_add_permission(self, request):
        """Disable add permission (read-only admin)."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable delete permission (read-only admin)."""
        return False
    
    def priority_badge(self, obj):
        """Display priority as colored badge."""
        colors = {
            'low': '#28a745',
            'medium': '#ffc107',
            'high': '#dc3545',
        }
        color = colors.get(obj.priority, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'
    
    def days_since_completion_display(self, obj):
        """Display days since completion."""
        days = obj.days_since_completion()
        if days is None:
            return 'N/A'
        return f'{days} days ago'
    days_since_completion_display.short_description = 'Days Since Completion'
    
    def is_archivable_display(self, obj):
        """Display if task is archivable."""
        if obj.is_archivable():
            return format_html('<span style="color: orange;">📦 Archivable</span>')
        return format_html('<span style="color: gray;">Recent</span>')
    is_archivable_display.short_description = 'Archive Status'
    
    def completion_summary_display(self, obj):
        """Display completion summary."""
        summary = obj.get_completion_summary()
        return format_html(
            '<pre>{}</pre>',
            '\n'.join([f'{k}: {v}' for k, v in summary.items()])
        )
    completion_summary_display.short_description = 'Completion Summary'
    
    @admin.action(description='Archive selected completed tasks')
    def archive_tasks(self, request, queryset):
        """Bulk action to archive old completed tasks."""
        count = 0
        errors = 0
        for task in queryset:
            try:
                task.archive()
                count += 1
            except ValueError:
                errors += 1
        
        self.message_user(
            request,
            f'{count} tasks archived. {errors} tasks could not be archived (not old enough).'
        )
