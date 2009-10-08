from django import forms
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.admin.views.decorators import staff_member_required

from django_conference.models import Meeting, Registration
from django_conference import settings


class AdminTask(object):
    """
    Represents an administrative task that can be performed.
    """
    def __init__(self, template, desc, formats=["html"], show_user_limit=True):
        self.template = template
        self.description = desc
        self.formats = formats
        self.show_user_limit = show_user_limit


admin_tasks = [
    AdminTask("django_conference/stats.html", "Meeting Statistics",
        show_user_limit=False),
    AdminTask("django_conference/spreadsheet.html", "Meeting Spreadsheet",
        ["xls"]),
] + [
    AdminTask(*args) for args in settings.DJANGO_CONFERENCE_ADMIN_TASKS
]


class AdminTaskChoiceForm(forms.Form):
    """
    Allow staff to choose a administrative task to perform.
    """
    TASKS = [(admin_tasks.index(at), at.description) for at in admin_tasks]
    task = forms.ChoiceField(choices = TASKS, required = True)


class AdminTaskOptionsForm(forms.Form):
    """
    Allows picking pertinent options for the selected administrative task.
    """
    LIMIT_HELP = "Limits number of registrants included. Leave the field "+\
                 "blank for no limit."
    format = forms.ChoiceField(required = True)
    user_limit = forms.IntegerField(required = False, min_value = 0,
        help_text = LIMIT_HELP)

    def __init__(self, task, *args, **kwargs):
        super(AdminTaskOptionsForm, self).__init__(*args, **kwargs)
        if not task.show_user_limit:
            del self.fields['user_limit']
        formats = [(f, f.upper()) for f in task.formats]
        self.fields['format'].choices = formats


@staff_member_required
def choose_task(request, meeting_id):
    """
    Allows choosing between various administrative tasks (e.g. generating name
    badges) associated with meetings.
    """
    form = AdminTaskChoiceForm(request.POST or None)
    if form.is_valid():
        task_id = form.clean()['task']
        kwargs = {'meeting_id': meeting_id, 'task_id': task_id}
        url = reverse('django_conference_do_admin_task', kwargs=kwargs)
        return HttpResponseRedirect(url)
    return render_to_response("django_conference/admin_tasks.html", {
        'form': form,
    })


@staff_member_required
def do_task(request, meeting_id, task_id):
    """
    Visited after choose_task. If the chosen admin task has options
    associated it (e.g. different output format), then show an appropiate
    form. If the task has no options, or said form validates, execute it.
    """
    try:
        task = admin_tasks[int(task_id)]
        meeting = Meeting.objects.get(pk=int(meeting_id))
    except Exception, err:
        kwargs = {'meeting_id': meeting_id}
        url = reverse('django_conference_choose_admin_task', kwargs=kwargs)
        return HttpResponseRedirect(url)
    form = None
    if len(task.formats) > 1 or task.show_user_limit:
        form = AdminTaskOptionsForm(task, request.POST or None)

    if request.POST and form.is_valid():
        try:
            limit = int(form.clean().get('user_limit', None))
        except (ValueError, TypeError):
            limit = None
        format = form.clean().get('format', task.formats[0])
    else:
        limit = None
        format = task.formats[0]

    if not form or (request.POST and form.is_valid()):
        registrations = (meeting.registrations
                            .select_related()
                            .order_by('auth_user.last_name')[:limit])
        rendered = render_to_string(task.template, {
           'meeting': meeting,
           'registrations': registrations,
        })

        response = HttpResponse("Unknown error")
        if format == "html":
            response = HttpResponse(rendered)
        elif format == "xls":
            response = HttpResponse(rendered)
            filename = "meeting%s.xls" % (meeting.pk)
            response['Content-Disposition'] = 'attachment; filename='+filename
            response['Content-Type'] = 'application/vnd.ms-excel;charset=utf-8'
        elif format == "xml":
            response = HttpResponse(rendered)
            response['Content-Type'] = 'application/xml;charset=utf-8'
        return response
    return render_to_response("django_conference/admin_tasks.html", {
        'form': form,
    })
