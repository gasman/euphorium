import time

from forums.models import ForumGroup, Forum, Topic, User, Post

from .home_page import HomePage
from .recent_discussions import RecentDiscussionsPage
from .discussion import DiscussionPage


def scrape(site, verbose=True):
    home_page = HomePage(site.origin_url)
    forums_by_identifier = {}

    for category_group in home_page.category_groups:
        # find / create ForumGroup
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
            # find / create Forum
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

    discussions_to_fetch = []

    recent_discussions = RecentDiscussionsPage(site.origin_url)

    for discussion in recent_discussions.discussions:
        # find / create Topic
        topic, created = Topic.objects.get_or_create(
            forum=forums_by_identifier[discussion.category_identifier],
            source_reference=discussion.id,
            defaults={'title': discussion.title}
        )
        discussions_to_fetch.append(
            (topic, discussion.slug, discussion.page_count)
        )

    time.sleep(5)

    for topic, slug, page_count in discussions_to_fetch:
        if verbose:
            print("Fetching topic: %s" % topic.title)

        discussion_page = DiscussionPage(
            site.origin_url, topic.source_reference, slug
        )

        for source_post in discussion_page.posts:
            # find / create User
            user, created = User.objects.get_or_create(
                site=site, source_reference=source_post.author_id,
                defaults={'username': source_post.author_username}
            )
            if not created and source_post.author_username != user.username:
                user.username = source_post.author_username
                user.save(update_fields=['username'])

            # find / create Post
            post, created = Post.objects.get_or_create(
                topic=topic, source_reference=source_post.id,
                defaults={
                    'author': user, 'created_at': source_post.datetime,
                    'body': source_post.body
                }
            )

        time.sleep(5)
