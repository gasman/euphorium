from forums.models import ForumGroup

from .home_page import HomePage


def scrape(site):
    home_page = HomePage(site.origin_url)

    for category_group in home_page.category_groups:
        forum_group, created = ForumGroup.objects.get_or_create(
            site=site, source_reference=category_group.identifier,
            defaults={'name': category_group.name}
        )
        if forum_group.name != category_group.name:
            forum_group.name = category_group.name
            forum_group.save()
