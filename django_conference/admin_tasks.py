from django import forms
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.admin.views.decorators import staff_member_required

from django_conference.models import Meeting, Registration


class AdminTask(object):
    """
    Represents an administrative task that can be performed.
    """
    def __init__(self, description, view_func):
        self.description = description
        if isinstance(view_func, (list, tuple)):
            views = __import__(view_func[0], {}, {}, [view_func[1]])
            view_func = getattr(views, view_func[1])
        self.view_func = view_func


def generic_task_view(request, meeting, template, formats=["html"],
        show_user_limit=True):
    """
    View for a generic admin task. Suitable for simple tasks (e.g. generating
    spreadsheets)
    """
    form = None
    if len(formats) > 1 or show_user_limit:
        form = AdminTaskOptionsForm(formats, show_user_limit,
                request.POST or None)

    if request.POST and form.is_valid():
        try:
            limit = int(form.clean().get('user_limit', None))
        except (ValueError, TypeError):
            limit = None
        format = form.clean().get('format', formats[0])
    else:
        limit = None
        format = formats[0]

    if not form or (request.POST and form.is_valid()):
        registrations = (meeting.registrations
                            .select_related()
                            .order_by('auth_user.last_name')[:limit])
        rendered = render_to_string(template, {
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
    }, context_instance=RequestContext(request))


def get_task_list():
    from django_conference import settings
    return [
        # this would be cleaner if python supported currying but oh well
        AdminTask("Meeting Statistics", lambda r,m: generic_task_view(r, m,
            "django_conference/stats.html", show_user_limit=False)),
        AdminTask("Meeting Spreadsheet", lambda r,m: generic_task_view(r, m, 
            "django_conference/spreadsheet.html", ["xls"])),
    ] + [
        AdminTask(*args) for args in settings.DJANGO_CONFERENCE_ADMIN_TASKS
    ]


class AdminTaskChoiceForm(forms.Form):
    """
    Allow staff to choose a administrative task to perform.
    """
    TASKS = [(task_index, task.description)
             for task_index, task in
             enumerate(get_task_list())]
    task = forms.ChoiceField(choices = TASKS, required = True)


class AdminTaskOptionsForm(forms.Form):
    """
    Allows picking a couple common options for the task.
    """
    LIMIT_HELP = "Limits number of registrants included. Leave the field "+\
                 "blank for no limit."
    format = forms.ChoiceField(required = True)
    user_limit = forms.IntegerField(required = False, min_value = 0,
        help_text = LIMIT_HELP)

    def __init__(self, formats, show_user_limit, *args, **kwargs):
        super(AdminTaskOptionsForm, self).__init__(*args, **kwargs)
        if not show_user_limit:
            del self.fields['user_limit']
        formats = [(f, f.upper()) for f in formats]
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
    }, context_instance=RequestContext(request))


@staff_member_required
def do_task(request, meeting_id, task_id):
    """
    Visited after choose_task. If the chosen admin task has options
    associated it (e.g. different output format), then show an appropiate
    form. If the task has no options, or said form validates, execute it.
    """
    try:
        tasks = get_task_list()
        task = tasks[int(task_id)]
        meeting = Meeting.objects.get(pk=int(meeting_id))
    except Exception, err:
        kwargs = {'meeting_id': meeting_id}
        url = reverse('django_conference_choose_admin_task', kwargs=kwargs)
        return HttpResponseRedirect(url)
    return task.view_func(request, meeting)
