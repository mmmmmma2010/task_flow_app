"""
Serializers for Task API.

Serializers handle:
1. Converting model instances to JSON (serialization)
2. Converting JSON to model instances (deserialization)
3. Validation of input data
4. Nested relationships
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone

from tasks.models import Task, CompletedTask

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model (for nested representation)."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class TaskSerializer(serializers.ModelSerializer):
    """
    Main serializer for Task model.
    
    Provides full CRUD operations with validation.
    """
    
    # Nested user representations (read-only)
    created_by = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    
    # Write-only fields for user assignment
    assigned_to_id = serializers.IntegerField(
        write_only=True,
        required=False,
        allow_null=True,
        help_text="ID of user to assign task to"
    )
    
    # Computed fields
    is_overdue = serializers.BooleanField(read_only=True)
    days_until_due = serializers.IntegerField(read_only=True, allow_null=True)
    
    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'status',
            'priority',
            'due_date',
            'completed_at',
            'created_by',
            'assigned_to',
            'assigned_to_id',
            'is_deleted',
            'deleted_at',
            'created_at',
            'updated_at',
            'is_overdue',
            'days_until_due',
        ]
        read_only_fields = [
            'id',
            'created_by',
            'completed_at',
            'is_deleted',
            'deleted_at',
            'created_at',
            'updated_at',
            'is_overdue',
            'days_until_due',
        ]
    
    def validate_due_date(self, value):
        """Validate that due_date is in the future for new tasks."""
        if value and value < timezone.now():
            # Allow past due dates for updates, but warn
            if not self.instance:
                raise serializers.ValidationError(
                    "Due date cannot be in the past for new tasks."
                )
        return value
    
    def validate_assigned_to_id(self, value):
        """Validate that assigned user exists."""
        if value is not None:
            try:
                User.objects.get(id=value)
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    f"User with id {value} does not exist."
                )
        return value
    
    def validate(self, attrs):
        """Object-level validation."""
        # If status is completed, ensure completed_at will be set
        if attrs.get('status') == Task.STATUS_COMPLETED:
            if not self.instance or self.instance.status != Task.STATUS_COMPLETED:
                # Status is changing to completed
                attrs['completed_at'] = timezone.now()
        
        return attrs
    
    def create(self, validated_data):
        """Create a new task using the service layer."""
        from tasks.services import TaskService
        
        # Extract assigned_to_id and get user
        assigned_to_id = validated_data.pop('assigned_to_id', None)
        assigned_to = None
        if assigned_to_id:
            assigned_to = User.objects.get(id=assigned_to_id)
        
        # Get current user from context
        created_by = self.context['request'].user
        
        # Use service layer to create task
        task = TaskService.create_task(
            title=validated_data['title'],
            created_by=created_by,
            description=validated_data.get('description', ''),
            priority=validated_data.get('priority', Task.PRIORITY_MEDIUM),
            status=validated_data.get('status', Task.STATUS_PENDING),
            due_date=validated_data.get('due_date'),
            assigned_to=assigned_to,
        )
        
        return task
    
    def update(self, instance, validated_data):
        """Update a task using the service layer."""
        from tasks.services import TaskService
        
        # Extract assigned_to_id and convert to user
        assigned_to_id = validated_data.pop('assigned_to_id', None)
        if assigned_to_id is not None:
            validated_data['assigned_to'] = User.objects.get(id=assigned_to_id)
        
        # Get current user from context
        user = self.context['request'].user
        
        # Use service layer to update task
        task = TaskService.update_task(
            task_id=instance.id,
            user=user,
            **validated_data
        )
        
        return task


class TaskCreateSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for task creation.
    
    This provides a cleaner interface for creating tasks
    without exposing all fields.
    """
    
    assigned_to_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="ID of user to assign task to"
    )
    
    class Meta:
        model = Task
        fields = [
            'title',
            'description',
            'priority',
            'due_date',
            'assigned_to_id',
        ]
    
    def validate_assigned_to_id(self, value):
        """Validate that assigned user exists."""
        if value is not None:
            try:
                User.objects.get(id=value)
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    f"User with id {value} does not exist."
                )
        return value
    
    def create(self, validated_data):
        """Create task using service layer."""
        from tasks.services import TaskService
        
        assigned_to_id = validated_data.pop('assigned_to_id', None)
        assigned_to = None
        if assigned_to_id:
            assigned_to = User.objects.get(id=assigned_to_id)
        
        created_by = self.context['request'].user
        
        task = TaskService.create_task(
            title=validated_data['title'],
            created_by=created_by,
            description=validated_data.get('description', ''),
            priority=validated_data.get('priority', Task.PRIORITY_MEDIUM),
            due_date=validated_data.get('due_date'),
            assigned_to=assigned_to,
        )
        
        return task


class TaskListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for task lists.
    
    Reduces payload size by excluding heavy fields.
    """
    
    created_by_username = serializers.CharField(
        source='created_by.username',
        read_only=True
    )
    assigned_to_username = serializers.CharField(
        source='assigned_to.username',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'status',
            'priority',
            'due_date',
            'created_by_username',
            'assigned_to_username',
            'created_at',
            'is_overdue',
        ]


class CompletedTaskSerializer(serializers.ModelSerializer):
    """
    Serializer for CompletedTask proxy model.
    
    This is read-only and provides completion-specific fields.
    """
    
    created_by = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    days_since_completion = serializers.SerializerMethodField()
    completion_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = CompletedTask
        fields = [
            'id',
            'title',
            'description',
            'priority',
            'due_date',
            'completed_at',
            'created_by',
            'assigned_to',
            'created_at',
            'days_since_completion',
            'completion_summary',
        ]
        read_only_fields = '__all__'
    
    def get_days_since_completion(self, obj):
        """Get days since task was completed."""
        return obj.days_since_completion()
    
    def get_completion_summary(self, obj):
        """Get completion summary."""
        return obj.get_completion_summary()


class TaskStatisticsSerializer(serializers.Serializer):
    """Serializer for task statistics."""
    
    total = serializers.IntegerField()
    pending = serializers.IntegerField()
    in_progress = serializers.IntegerField()
    completed = serializers.IntegerField()
    overdue = serializers.IntegerField()
    high_priority = serializers.IntegerField()
