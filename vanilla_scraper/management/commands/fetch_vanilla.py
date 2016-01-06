import datetime

from django.core.management.base import BaseCommand

from forums.models import Site
from vanilla_scraper.scraper import scrape


class Command(BaseCommand):
    help = "Fetches discussion data from all Vanilla sites"

    def add_arguments(self, parser):
        parser.add_argument('--days',
            type=int,
            help='Fetch posts made within the last N days',
            default=7)

    def handle(self, *args, **options):
        now = datetime.datetime.now(datetime.timezone.utc)
        min_date = now - datetime.timedelta(days=options['days'])
        for site in Site.objects.filter(engine='vanilla'):
            scrape(site, min_date=min_date)
