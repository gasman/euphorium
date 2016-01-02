from django.db import models


class Site(models.Model):
    name = models.CharField(max_length=255)
    engine = models.CharField(max_length=255)
    origin_url = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name
