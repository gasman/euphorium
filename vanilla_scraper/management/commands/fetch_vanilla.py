from django.core.management.base import BaseCommand

from forums.models import Site
from vanilla_scraper.scraper import scrape


class Command(BaseCommand):
    def handle(self, *args, **options):
        for site in Site.objects.filter(engine='vanilla'):
            scrape(site)
