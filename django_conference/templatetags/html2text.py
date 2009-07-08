from subprocess import Popen, PIPE

from django import template

register = template.Library()

@register.filter
def html2text(value):
    """
    Pipes given HTML string into the text browser W3M, which renders it.
    Rendered text is grabbed from STDOUT and returned.
    """
    try:
        cmd = "/usr/local/bin/w3m -dump -T text/html -cols 80 -O ascii"
        proc = Popen(cmd, shell = True, stdin = PIPE, stdout = PIPE)
        return proc.communicate(str(value))[0]
    except OSError:
        # something bad happened, so just return the input
        return value


if __name__ == "__main__":
    from urllib import urlopen
    print html2text(urlopen("http://www.w3.org/TR/REC-html40/").read())
