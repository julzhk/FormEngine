from django.db import models

from FormComposer.models import get_processor_choices

class Event(models.Model):
    data = models.BinaryField()
    metadata = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def save(self, *args, **kwargs):
        if self.pk:
            # Simple way to discourage updates, though not perfectly immutable at the DB level via Django models
            raise TypeError("Event objects are immutable and cannot be updated.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Event {self.id} created at {self.created_at}"

class ConsumerOffset(models.Model):
    processor_class = models.CharField(
        max_length=255,
        choices=get_processor_choices,
        unique=True
    )
    offset = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ConsumerOffset for {self.processor_class} at event {self.offset_id if self.offset else 'None'}"
