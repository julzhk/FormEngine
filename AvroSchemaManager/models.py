from django.db import models

class SchemaRegistry(models.Model):
    name = models.CharField(max_length=255)
    namespace = models.CharField(max_length=255)
    version = models.IntegerField()
    avro_schema = models.JSONField(blank=True, null=True)

    class Meta:
        unique_together = ('name', 'version')
        verbose_name_plural = "Schema Registries"

    def __str__(self):
        return f"{self.name} (v{self.version})"
