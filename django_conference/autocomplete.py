from django.apps import apps
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models.functions import Concat
from django.db.models import Value as V
from django.utils.decorators import method_decorator

from dal import autocomplete

from django_conference import settings
from django_conference.models import Paper, PaperPresenter


class PaperAutocomplete(autocomplete.Select2QuerySetView):
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(PaperAutocomplete, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        qs = Paper.objects.all()

        if self.q:
            qs = Paper.objects.filter(title__icontains=self.q)

        return qs


class PaperPresenterAutocomplete(autocomplete.Select2QuerySetView):
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(PaperPresenterAutocomplete, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        qs = PaperPresenter.objects.annotate(
            full_name=Concat('first_name', V(' '), 'last_name'),
        )

        if self.q:
            qs = qs.filter(full_name__icontains=self.q)

        return qs


class UserAutocomplete(autocomplete.Select2QuerySetView):
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(UserAutocomplete, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        user_model = apps.get_model(settings.DJANGO_CONFERENCE_USER_MODEL)
        qs = user_model.objects.all()

        if self.q:
            qs = settings.DJANGO_CONFERENCE_USER_AUTOCOMPLETE_FILTER(qs,
                self.q)

        return qs
