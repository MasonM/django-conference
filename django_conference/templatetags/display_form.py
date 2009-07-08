from django import template

register = template.Library()


@register.tag()
def display_form(parser, token):
    """
    Wrapper that shows the given form wrapped in a <div> of class form-row
    and each field inside a <p>.
    """
    tag_name, form_name = token.split_contents()
    return FormFieldNode(form_name)


class FormFieldNode(template.Node):
    """
    Does all HTML outputting for the form.
    """
    def __init__(self, form_name):
        self.form_name = form_name

    def render(self, context):
        form = template.resolve_variable(self.form_name, context)
        output = u'<div class="form-row">'
        if form.errors:
            #convert keys to human-readable form,
            #e.g. "first_name" => "First Name"
            errors = map(lambda x: (x[0].replace("_", " ").title(), x[1]),
                         form.errors.items())
            output += template.loader.render_to_string('errors.html',
                {'error_dict': errors})
        for field in form:
            output += "<p class='container' id='%s_container'>" % field.auto_id
            if field.field.required:
                output += u"<b>%s</b>" % field.label_tag(field.label)
            else:
                output += field.label_tag(field.label)
            output += u"%s%s</p>\n" % (field, field.help_text)
        output += u"</div>"
        return output
