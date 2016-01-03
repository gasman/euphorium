from forums.models import ForumGroup, Forum, Topic

from .home_page import HomePage
from .recent_discussions import RecentDiscussionsPage


def scrape(site):
    home_page = HomePage(site.origin_url)
    forums_by_identifier = {}

    for category_group in home_page.category_groups:
        forum_group, created = ForumGroup.objects.get_or_create(
            site=site, source_reference=category_group.identifier,
            defaults={'name': category_group.name}
        )
        if not created:
            changed_fields = []
            if forum_group.name != category_group.name:
                changed_fields.append('name')
                forum_group.name = category_group.name

            if changed_fields:
                forum_group.save(update_fields=changed_fields)

        for category in category_group.categories:
            forum, created = Forum.objects.get_or_create(
                site=site, source_reference=category.identifier,
                defaults={
                    'forum_group': forum_group,
                    'name': category.name,
                    'description': category.description
                }
            )
            if not created:
                changed_fields = []
                if forum.forum_group != forum_group:
                    changed_fields.append('forum_group')
                    forum.forum_group = forum_group
                if forum.name != category.name:
                    changed_fields.append('name')
                    forum.name = category.name
                if forum.description != category.description:
                    changed_fields.append('description')
                    forum.description = category.description

                if changed_fields:
                    forum.save(update_fields=changed_fields)

            forums_by_identifier[category.identifier] = forum

    recent_discussions = RecentDiscussionsPage(site.origin_url)

    for discussion in recent_discussions.discussions:
        topic, created = Topic.objects.get_or_create(
            forum=forums_by_identifier[discussion.category_identifier],
            source_reference=discussion.id,
            defaults={'title': discussion.title}
        )
