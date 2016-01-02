from django.db import models


class Site(models.Model):
    name = models.CharField(max_length=255)
    engine = models.CharField(max_length=255)
    origin_url = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name


class ForumGroup(models.Model):
    site = models.ForeignKey(Site, related_name='forum_groups')
    name = models.CharField(max_length=255)
    source_reference = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = [
            ('site', 'source_reference'),
        ]


class Forum(models.Model):
    site = models.ForeignKey(Site, related_name='forums')
    forum_group = models.ForeignKey(
        ForumGroup, related_name='forums', blank=True, null=True
    )
    name = models.CharField(max_length=255)
    source_reference = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = [
            ('site', 'source_reference'),
        ]
