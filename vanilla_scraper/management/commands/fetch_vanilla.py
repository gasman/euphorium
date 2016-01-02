from django.core.management.base import NoArgsCommand

from forums.models import Site
from vanilla_scraper.scraper import scrape


class Command(NoArgsCommand):
	def handle_noargs(self, **options):
		for site in Site.objects.filter(engine='vanilla'):
			scrape(site)
