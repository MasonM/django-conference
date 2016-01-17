# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

import django_conference.models
from django_conference import settings


class Migration(migrations.Migration):

    dependencies = settings.DJANGO_CONFERENCE_MIGRATION_DEPENDENCIES

    operations = [
        migrations.CreateModel(
            name='DonationType',
            fields=[
                ('name', models.CharField(help_text=b'A short, unique name for this field.', max_length=10, serialize=False, primary_key=True)),
                ('label', models.CharField(help_text=b'Label for this field on the registration page. Enter as HTML.', max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ExtraType',
            fields=[
                ('name', models.CharField(help_text=b'A short, unique name for this field.', max_length=10, serialize=False, primary_key=True)),
                ('label', models.CharField(help_text=b'Label for this field on the registration page. Enter as HTML.', max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Meeting',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_active', models.BooleanField(default=False, help_text=b'Check this to allow meeting registration and paper submission.')),
                ('location', models.CharField(help_text=b'General location for where this meeting is taking place, e.g. "Gainesville, FL"', max_length=45)),
                ('start_date', models.DateField(verbose_name=b'Start of meeting')),
                ('end_date', models.DateField(verbose_name=b'End of meeting')),
                ('reg_start', models.DateField(verbose_name=b'Start of early registration')),
                ('early_reg_deadline', models.DateField(help_text=b'This also marks the beginning of regular registration', verbose_name=b'End of Early registration')),
                ('reg_deadline', models.DateField(verbose_name=b'End of regular registration')),
                ('paper_submission_start', models.DateTimeField(verbose_name=b'Start of paper submission')),
                ('paper_submission_end', models.DateTimeField(verbose_name=b'End of Paper submission end')),
                ('session_submission_start', models.DateTimeField(verbose_name=b'Start of session submission')),
                ('session_submission_end', models.DateTimeField(verbose_name=b'End of session submission')),
                ('preliminary_program', models.URLField(help_text=b'If specified, a link to the form will be shown above the session selection section of the registration page.', verbose_name=b'Preliminary program URL', blank=True)),
                ('register_form', models.URLField(help_text=b'If specified, a link to the form will be shown at the top of the registration page.', verbose_name=b'Registration form URL', blank=True)),
            ],
            options={
                'ordering': ['start_date'],
                'get_latest_by': 'end_date',
            },
        ),
        migrations.CreateModel(
            name='MeetingDonation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('help_text', models.CharField(help_text=b'Text to be shown next to the donation input box.', max_length=255, blank=True)),
                ('donate_type', models.ForeignKey(to='django_conference.DonationType')),
                ('meeting', models.ForeignKey(related_name='donations', to='django_conference.Meeting')),
            ],
        ),
        migrations.CreateModel(
            name='MeetingExtra',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('price', models.DecimalField(default=0, help_text=b'The price for one quantity of this extra.', max_digits=6, decimal_places=2)),
                ('help_text', models.CharField(help_text=b'Text to be shown next to the extra.', max_length=255, blank=True)),
                ('max_quantity', models.PositiveIntegerField(default=1, help_text=b'The maximum of this extra that a registrant can order. If set to 1, it will be shown as a checkbox.')),
                ('position', models.PositiveSmallIntegerField(default=1, help_text=b'Used for determining position of the extra on the registration page')),
                ('extra_type', models.ForeignKey(to='django_conference.ExtraType')),
                ('meeting', models.ForeignKey(related_name='extras', to='django_conference.Meeting')),
            ],
            options={
                'ordering': ['meeting', 'position'],
            },
        ),
        migrations.CreateModel(
            name='MeetingInstitution',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('acronym', models.CharField(max_length=4)),
                ('name', models.CharField(max_length=45)),
                ('meeting', models.ForeignKey(related_name='institutions', to='django_conference.Meeting')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Paper',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=300)),
                ('abstract', models.TextField()),
                ('coauthor', models.CharField(max_length=255, blank=True)),
                ('is_poster', models.BooleanField(default=False, verbose_name=b'Is this a poster?')),
                ('av_info', models.CharField(default=b'N', max_length=1, verbose_name=b'Audiovisual Requirement', blank=True, choices=[(b'N', b'None'), (b'L', b'LCD(PowerPoint)'), (b'O', b'Overhead Projector')])),
                ('notes', models.TextField(blank=True)),
                ('accepted', models.BooleanField(default=False)),
                ('prior_sundays', models.CharField(default=b'0', max_length=1, verbose_name=b'How many times over the past 5 years have you been assigned to a Sunday morning slot on the program?', choices=[(b'0', 0), (b'1', 1), (b'2', 2), (b'M', b'More')])),
                ('creation_time', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='PaperPresenter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=100)),
                ('gender', models.CharField(blank=True, max_length=1, choices=[(b'M', b'Male'), (b'F', b'Female'), (b'O', b'Other')])),
                ('birth_year', models.CharField(blank=True, max_length=6, choices=[(b'<46', b'Born before 1946'), (b'46-64', b'1946 - 1964'), (b'65-81', b'1965 - 1981'), (b'82-95', b'1982 - 1995'), (b'>95', b'After 1995')])),
                ('status', models.CharField(blank=True, max_length=2, choices=[(b'O', b'Other'), (b'F', b'Faculty Member'), (b'I', b'Independent Scholar'), (b'G', b'Graduate Student'), (b'A', b'Administrator'), (b'P', b'Post-Doctoral Fellow'), (b'H', b'Public Historian')])),
            ],
        ),
        migrations.CreateModel(
            name='PaperPresenterRegion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('region', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='PaperPresenterSubject',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('subject', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='PaperPresenterTimePeriod',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time_period', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Registration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('special_needs', models.TextField(blank=True)),
                ('date_entered', models.DateTimeField()),
                ('payment_type', models.CharField(default=b'cc', max_length=2, choices=[(b'na', b'Not Applicable'), (b'cc', b'Credit Card'), (b'ch', b'Check'), (b'ca', b'Cash'), (b'mo', b'Money Order')])),
                ('entered_by', models.ForeignKey(to=settings.DJANGO_CONFERENCE_USER_MODEL)),
                ('meeting', models.ForeignKey(related_name='registrations', default=django_conference.models.current_meeting_or_none, to='django_conference.Meeting')),
                ('registrant', models.ForeignKey(related_name='registrations', to=settings.DJANGO_CONFERENCE_USER_MODEL)),
            ],
            options={
                'ordering': ['-meeting', 'registrant'],
                'get_latest_by': 'date_entered',
            },
        ),
        migrations.CreateModel(
            name='RegistrationDonation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('total', models.DecimalField(max_digits=6, decimal_places=2)),
                ('donate_type', models.ForeignKey(to='django_conference.MeetingDonation')),
                ('registration', models.ForeignKey(related_name='regdonations', to='django_conference.Registration')),
            ],
            options={
                'ordering': ['-registration', 'donate_type'],
            },
        ),
        migrations.CreateModel(
            name='RegistrationExtra',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('quantity', models.PositiveIntegerField()),
                ('price', models.DecimalField(null=True, verbose_name=b'Price override', max_digits=6, decimal_places=2, blank=True)),
                ('extra', models.ForeignKey(to='django_conference.MeetingExtra')),
                ('registration', models.ForeignKey(related_name='regextras', to='django_conference.Registration')),
            ],
        ),
        migrations.CreateModel(
            name='RegistrationGuest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('first_name', models.CharField(max_length=45)),
                ('last_name', models.CharField(max_length=45)),
                ('registration', models.ForeignKey(related_name='guests', to='django_conference.Registration')),
            ],
        ),
        migrations.CreateModel(
            name='RegistrationOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('option_name', models.CharField(max_length=30)),
                ('early_price', models.DecimalField(max_digits=5, decimal_places=2)),
                ('regular_price', models.DecimalField(max_digits=5, decimal_places=2)),
                ('onsite_price', models.DecimalField(max_digits=5, decimal_places=2)),
                ('admin_only', models.BooleanField(default=False, help_text=b'If checked, this option will only be available when registering through the admin interface.')),
                ('meeting', models.ForeignKey(related_name='regoptions', to='django_conference.Meeting')),
            ],
            options={
                'ordering': ['-meeting', 'option_name', 'regular_price'],
            },
        ),
        migrations.CreateModel(
            name='Session',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_time', models.DateTimeField(null=True, blank=True)),
                ('stop_time', models.DateTimeField(null=True, blank=True)),
                ('room_no', models.CharField(max_length=30, null=True, blank=True)),
                ('title', models.CharField(max_length=300)),
                ('notes', models.TextField(blank=True)),
                ('abstract', models.TextField(blank=True)),
                ('creation_time', models.DateTimeField(auto_now_add=True)),
                ('accepted', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['-meeting', 'start_time', 'stop_time'],
            },
        ),
        migrations.CreateModel(
            name='SessionCadre',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('first_name', models.CharField(max_length=30)),
                ('mi', models.CharField(max_length=30, blank=True)),
                ('last_name', models.CharField(max_length=30)),
                ('gender', models.CharField(default=b'O', max_length=1, choices=[(b'O', b'Other'), (b'M', b'Male'), (b'F', b'Female')])),
                ('type', models.CharField(default=b'O', max_length=1, choices=[(b'O', b'Other'), (b'F', b'Faculty Member'), (b'I', b'Independent Scholar'), (b'G', b'Graduate Student'), (b'A', b'Administrator'), (b'P', b'Post-Doctoral Fellow'), (b'H', b'Public Historian')])),
                ('email', models.EmailField(max_length=100)),
                ('institution', models.CharField(max_length=100)),
            ],
            options={
                'verbose_name_plural': 'Session cadre',
            },
        ),
        migrations.CreateModel(
            name='SessionPapers',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('position', models.PositiveSmallIntegerField()),
                ('paper', models.ForeignKey(to='django_conference.Paper')),
                ('session', models.ForeignKey(to='django_conference.Session')),
            ],
        ),
        migrations.AddField(
            model_name='session',
            name='chairs',
            field=models.ManyToManyField(related_name='sessions_chaired', to='django_conference.SessionCadre', blank=True),
        ),
        migrations.AddField(
            model_name='session',
            name='commentators',
            field=models.ManyToManyField(related_name='sessions_commentated', to='django_conference.SessionCadre', blank=True),
        ),
        migrations.AddField(
            model_name='session',
            name='meeting',
            field=models.ForeignKey(related_name='sessions', default=django_conference.models.current_meeting_or_none, to='django_conference.Meeting'),
        ),
        migrations.AddField(
            model_name='session',
            name='organizers',
            field=models.ManyToManyField(related_name='sessions_organized', to='django_conference.SessionCadre', blank=True),
        ),
        migrations.AddField(
            model_name='session',
            name='papers',
            field=models.ManyToManyField(to='django_conference.Paper', through='django_conference.SessionPapers', blank=True),
        ),
        migrations.AddField(
            model_name='session',
            name='submitter',
            field=models.ForeignKey(blank=True, to=settings.DJANGO_CONFERENCE_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='registration',
            name='sessions',
            field=models.ManyToManyField(related_name='regsessions', to='django_conference.Session', blank=True),
        ),
        migrations.AddField(
            model_name='registration',
            name='type',
            field=models.ForeignKey(to='django_conference.RegistrationOption'),
        ),
        migrations.AddField(
            model_name='paperpresenter',
            name='regions',
            field=models.ManyToManyField(to='django_conference.PaperPresenterRegion', blank=True),
        ),
        migrations.AddField(
            model_name='paperpresenter',
            name='subjects',
            field=models.ManyToManyField(to='django_conference.PaperPresenterSubject', blank=True),
        ),
        migrations.AddField(
            model_name='paperpresenter',
            name='time_periods',
            field=models.ManyToManyField(to='django_conference.PaperPresenterTimePeriod', blank=True),
        ),
        migrations.AddField(
            model_name='paper',
            name='presenter',
            field=models.ForeignKey(to='django_conference.PaperPresenter'),
        ),
        migrations.AddField(
            model_name='paper',
            name='previous_meetings',
            field=models.ManyToManyField(related_name='meeting_papers', verbose_name=b'Presented at the following past meetings', to='django_conference.Meeting', blank=True),
        ),
        migrations.AddField(
            model_name='paper',
            name='sessions',
            field=models.ManyToManyField(to='django_conference.Session', through='django_conference.SessionPapers', blank=True),
        ),
        migrations.AddField(
            model_name='paper',
            name='submitter',
            field=models.ForeignKey(blank=True, to=settings.DJANGO_CONFERENCE_USER_MODEL, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='registrationoption',
            unique_together=set([('meeting', 'option_name')]),
        ),
        migrations.AlterUniqueTogether(
            name='registrationextra',
            unique_together=set([('registration', 'extra')]),
        ),
        migrations.AlterUniqueTogether(
            name='meetingextra',
            unique_together=set([('meeting', 'extra_type')]),
        ),
        migrations.AlterUniqueTogether(
            name='meetingdonation',
            unique_together=set([('meeting', 'donate_type')]),
        ),
    ]
