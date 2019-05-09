from __future__ import absolute_import

from django.db import models
from django.utils.translation import ugettext_lazy as _

CHOICES = ((1, "this"), (2, _("that")))


class Pet(models.Model):
    name = models.CharField(max_length=30)
    age = models.PositiveIntegerField()


class FilmDetails(models.Model):
    location = models.CharField(max_length=30)
    film = models.OneToOneField(
        "Film", on_delete=models.CASCADE, related_name="details"
    )


class Film(models.Model):
    genre = models.CharField(
        max_length=2,
        help_text="Genre",
        choices=[("do", "Documentary"), ("ot", "Other")],
        default="ot",
    )
    reporters = models.ManyToManyField("Reporter", related_name="films")


class DoeReporterManager(models.Manager):
    def get_queryset(self):
        return super(DoeReporterManager, self).get_queryset().filter(last_name="Doe")


class Reporter(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField()
    pets = models.ManyToManyField("self")
    a_choice = models.CharField(max_length=30, choices=CHOICES)
    objects = models.Manager()
    doe_objects = DoeReporterManager()

    reporter_type = models.IntegerField(
        "Reporter Type",
        null=True,
        blank=True,
        choices=[(1, u"Regular"), (2, u"CNN Reporter")],
    )

    def __str__(self):  # __unicode__ on Python 2
        return "%s %s" % (self.first_name, self.last_name)

    def __init__(self, *args, **kwargs):
        """
        Override the init method so that during runtime, Django
        can know that this object can be a CNNReporter by casting
        it to the proxy model. Otherwise, as far as Django knows,
        when a CNNReporter is pulled from the database, it is still
        of type Reporter. This was added to test proxy model support.
        """
        super(Reporter, self).__init__(*args, **kwargs)
        if self.reporter_type == 2:  # quick and dirty way without enums
            self.__class__ = CNNReporter


class CNNReporter(Reporter):
    """
    This class is a proxy model for Reporter, used for testing
    proxy model support
    """

    class Meta:
        proxy = True


class Article(models.Model):
    headline = models.CharField(max_length=100)
    pub_date = models.DateField()
    pub_date_time = models.DateTimeField()
    reporter = models.ForeignKey(
        Reporter, on_delete=models.CASCADE, related_name="articles"
    )
    editor = models.ForeignKey(
        Reporter, on_delete=models.CASCADE, related_name="edited_articles_+"
    )
    lang = models.CharField(
        max_length=2,
        help_text="Language",
        choices=[("es", "Spanish"), ("en", "English")],
        default="es",
    )
    importance = models.IntegerField(
        "Importance",
        null=True,
        blank=True,
        choices=[(1, u"Very important"), (2, u"Not as important")],
    )

    def __str__(self):  # __unicode__ on Python 2
        return self.headline

    class Meta:
        ordering = ("headline",)
