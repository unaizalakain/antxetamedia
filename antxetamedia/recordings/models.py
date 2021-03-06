from __future__ import unicode_literals

from django.db import models
from django.contrib.contenttypes import generic
from django.utils.translation import ugettext as _
from django.core.validators import ValidationError
from django.utils.six import text_type

from markitup.fields import MarkupField
from autoslug.fields import AutoSlugField
from datetime import date

from antxetamedia.multimedia.models import Media, EmbededMedia
from antxetamedia.structure.models import Node

INTERVIEW = 0
FULL_PROGRAM = 1


class NewsCategory(models.Model):
    class Meta:
        verbose_name = _('news category')
        verbose_name_plural = _('news categories')

    name = models.CharField(_('name'), max_length=100)
    slug = AutoSlugField(editable=False, always_update=True, unique=True,
            populate_from='name')

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return 'news:category', (), {'slug': self.slug}


class Recording(models.Model):
    class Meta:
        abstract = True

    principal = models.BooleanField(_('principal'), default=False)
    pub_date = models.DateField(_('publication date'), default=date.today())

    text = MarkupField(_('text'), default='')

    medias = generic.GenericRelation(Media)
    embeded_medias = generic.GenericRelation(EmbededMedia)

    link = models.URLField(_('link'), blank=True)
    image = models.ImageField(_('image'), blank=True, upload_to='img')


class News(Recording):
    class Meta:
        verbose_name = _('news ')
        verbose_name_plural = _('news')
        ordering = '-principal', '-pub_date', '-id'

    title = models.CharField(_('title'), max_length=250)
    slug = AutoSlugField(editable=False, always_update=True, unique=True,
            populate_from='title')

    categories = models.ManyToManyField('NewsCategory', blank=True, null=True,
            verbose_name=_('categories'))

    def __unicode__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        return 'news:detail', (), {'slug': self.slug}

    def save(self, *args, **kwargs):
        if self.principal:
            try:
                old = News.objects.get(principal=True)
            except News.DoesNotExist:
                pass
            else:
                if old.pk is not self.pk:
                    old.principal = False
                    old.save()
        super(News, self).save(*args, **kwargs)

    def metadata(self):
        return {
                'x-archive-meta-title': text_type(self),
                'x-archive-meta-creator': 'Berriak',
                'x-archive-meta-description': text_type(self.text.raw),
                'x-archive-meta-subject': text_type(self),
                'x-archive-meta-date': self.pub_date.strftime('%Y-%m-%d'),
                }


class Program(Recording):
    INTERVIEW = INTERVIEW
    FULL_PROGRAM = FULL_PROGRAM
    class Meta:
        verbose_name = _('program')
        verbose_name_plural = _('programs')
        ordering = '-principal', '-pub_date', '-id'

    title = models.CharField(_('title'), max_length=250, blank=True,
        help_text=_('Left empty if full program'))

    type = models.PositiveSmallIntegerField(_('type'), default=0, choices=(
        (INTERVIEW, _('interview')),
        (FULL_PROGRAM, _('full program')),
        ))

    program = models.ForeignKey(Node, verbose_name=_('program'))

    slug = AutoSlugField(editable=False, always_update=True, unique=True,
            populate_from=lambda self: self.__unicode__())

    def __unicode__(self):
        if self.type is INTERVIEW:
            return self.title
        return '%s - %s' % (self.pub_date, self.program)

    @models.permalink
    def get_absolute_url(self):
        if self.type is INTERVIEW:
            return 'interviews:detail', (), {'slug': self.slug}
        return 'programs:detail', (), {'slug': self.slug}

    def clean(self):
        if self.type is INTERVIEW and not self.title:
            raise ValidationError(_('You must set a title for an interview'))

    def save(self, *args, **kwargs):
        if self.principal:
            try:
                old = Program.objects.get(principal=True,
                        program=self.program)
            except Program.DoesNotExist:
                pass
            else:
                if old.pk is not self.pk:
                    old.principal = False
                    old.save()
        super(Program, self).save(*args, **kwargs)

    def metadata(self):
        return {
                'x-archive-meta-title': text_type(self),
                'x-archive-meta-creator': text_type(self.program),
                'x-archive-meta-description': text_type(self.text.raw),
                'x-archive-meta-subject': text_type(self),
                'x-archive-meta-date': self.pub_date.strftime('%Y-%m-%d'),
                }
