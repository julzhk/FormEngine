from django.core.management.base import BaseCommand
from FormComposer.models import get_processor_klasses

class Command(BaseCommand):
    help = 'Iterates through all processor classes and calls their consume method'

    def handle(self, *args, **options):
        processor_klasses = get_processor_klasses()
        self.stdout.write(f"Found {len(processor_klasses)} processor(s).")
        
        for klass in processor_klasses:
            self.stdout.write(f"Running consumer for {klass.__name__}...")
            try:
                klass.consume()
                self.stdout.write(self.style.SUCCESS(f"Successfully ran consumer for {klass.__name__}"))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error running consumer for {klass.__name__}: {e}"))
