from django.db import models
from django.utils.translation import gettext_lazy as _


class Links(models.Model):
    name = models.CharField(_('Name'), max_length=100)

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    class Meta:
        db_table = 'links'
        verbose_name = _('Service')
        verbose_name_plural = _('Services')

    def __str__(self):
        return '%s' % self.name

