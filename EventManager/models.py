from django.db import models

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

class Consumer(models.Model):
    name = models.CharField(max_length=255, unique=True)
    last_event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Consumer {self.name} at event {self.last_event_id if self.last_event else 'None'}"
