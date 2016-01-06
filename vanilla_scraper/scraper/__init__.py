import time

from forums.models import ForumGroup, Forum, Topic, User, Post

from .home_page import HomePage
from .recent_discussions import RecentDiscussionsPage
from .discussion import DiscussionPage


def has_seen_post(site, topic, user_id, post_datetime):
    # return whether we've already seen a post from the given user
    # at the given time in the given topic
    try:
        user = site.users.get(source_reference=user_id)
    except User.DoesNotExist:
        # user is unknown, so we can't have seen this post before
        return False

    return bool(topic.posts.filter(
        author=user, created_at=post_datetime
    ))


def scrape(site, min_date=None, get_updates=False, verbose=True):
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

    page_num = 1
    has_reached_min_date = False

    while not has_reached_min_date:
        if verbose:
            print("Scanning recent discussions, page %d" % page_num)

        recent_discussions = RecentDiscussionsPage(
            site.origin_url, page_number=page_num
        )

        for discussion in recent_discussions.discussions:

            last_poster = discussion.last_poster
            if (min_date is not None and last_poster.datetime < min_date):
                # discussion is older than min_date
                if discussion.is_sticky:
                    # move to next discussion
                    continue
                else:
                    # all subsequent discussions are older than min_date
                    has_reached_min_date = True
                    break

            # find / create Topic
            topic, created = Topic.objects.get_or_create(
                forum=forums_by_identifier[discussion.category_identifier],
                source_reference=discussion.id,
                defaults={'title': discussion.title}
            )

            if (
                get_updates and not created
                and has_seen_post(site, topic, last_poster.user_id, last_poster.datetime)
            ):
                if discussion.is_sticky:
                    continue
                else:
                    has_reached_min_date = True
                    break

            # last post of discussion is within range and not already seen -
            # fetch the discussion
            discussions_to_fetch.append(
                (topic, discussion.slug, discussion.page_count)
            )

        if page_num >= recent_discussions.max_page_number:
            # we have reached the end of the listing
            has_reached_min_date = True

        time.sleep(5)
        page_num += 1

    # fetch discussions in reverse order, so that if an error occurs we will
    # have scanned all the discussions older than that one, and can resume by
    # re-running the task
    for topic, slug, page_count in reversed(discussions_to_fetch):
        has_reached_min_date = False

        posts_to_add = []

        for page_num in range(page_count, 0, -1):
            if verbose:
                print(
                    "Fetching topic: %s, page %d of %d" % (
                        topic.title, page_num, page_count
                    )
                )

            discussion_page = DiscussionPage(
                site.origin_url, topic.source_reference, slug, page_number=page_num
            )

            for post in reversed(discussion_page.posts):
                if min_date is not None and post.datetime < min_date:
                    has_reached_min_date = True
                    break
                elif get_updates and has_seen_post(site, topic, post.author_id, post.datetime):
                    has_reached_min_date = True
                    break
                else:
                    posts_to_add.append(post)

            time.sleep(5)

            if has_reached_min_date:
                break

        for source_post in reversed(posts_to_add):
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
