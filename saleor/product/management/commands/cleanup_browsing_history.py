from django.core.management.base import BaseCommand
from django.utils import timezone
from ...models import ProductBrowsingHistory

class Command(BaseCommand):
    help = 'Clean up expired product browsing history records'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Keep records from the last N days, default is 90 days'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Only show the number of records that would be deleted, without actually deleting them'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        
        if dry_run:
            count = ProductBrowsingHistory.objects.filter(
                created_at__lt=cutoff_date
            ).count()
            self.stdout.write(
                self.style.SUCCESS(f'Would delete {count} records older than {days} days')
            )
        else:
            deleted_count = ProductBrowsingHistory.cleanup_old_records(days)
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {deleted_count} expired records')
            )
