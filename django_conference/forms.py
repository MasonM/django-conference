from datetime import date, datetime
from decimal import Decimal
from calendar import monthrange
import re

from django import forms
from django.db.models import get_model

from django_conference import settings
from django_conference.models import (Meeting, Paper, Session, SessionCadre,
    RegistrationDonation, Registration, RegistrationExtra,
    RegistrationGuest, RegistrationOption)


class MeetingSessions(forms.Form):
    """
    Form for selecting meeting sessions. All fields are dynamically generated
    by querying for the sessions associated with a given meeting.
    """
    WEEKDAY_MAP = {
        0: "Monday",
        1: "Tuesday",
        2: "Wednesday",
        3: "Thursday",
        4: "Friday",
        5: "Saturday",
        6: "Sunday",
    }

    def __init__(self, meeting, *args, **kwargs):
        super(MeetingSessions, self).__init__(*args, **kwargs)
        self.meeting = meeting
        self.set_session_fields()

    def set_session_fields(self):
        # add multi-select fields for choosing which sessions to attend
        meeting_sessions = self.meeting.sessions.filter(accepted=True)
        # categorize sessions by the day of the week
        days = [s['start_time'].weekday()
                for s in meeting_sessions.values("start_time")
                if s['start_time']]
        days.sort()
        for day in days:
            # @todo change to use filter(start_time__weekday) when Django
            # supports it
            sessions = [s for s in meeting_sessions.order_by("start_time")
                        if s.start_time and s.start_time.weekday() == day]
            # cut off title so the multi-select fields don't take up the
            # whole page
            def trim_title(title):
                return title if len(title) < 30 else title[:27]+"..."
            choices = [(s.pk, trim_title(unicode(s))) for s in sessions]
            field_name = "sessions_%i" % day
            self.fields[field_name] = forms.MultipleChoiceField(
                choices=choices, label=self.WEEKDAY_MAP[day], required=False)

    def get_sessions(self):
        clean = self.clean()
        # go through and split off session-related values into a separate list,
        # since they have to be combined together
        sessions = []
        for item in clean.keys():
            if item.startswith("sessions_"):
                if clean[item]:
                    sessions.append(clean[item])
                clean.pop(item)
        # flatten list
        sessions = sum(sessions, [])
        return [Session.objects.get(pk=int(x)) for x in sessions]


class MeetingRegister(forms.Form):
    """
    Main form for meeting registrations.
    """
    guest_name = forms.CharField(required=False, max_length=45)
    special_needs = forms.CharField(required=False, widget=forms.Textarea)

    def __init__(self, meeting, *args, **kwargs):
        super(MeetingRegister, self).__init__(*args, **kwargs)
        self.meeting = meeting
        self.set_type_field()

    def set_type_field(self):
        """
        Generate list of available registration type (e.g. HSS Member, student)
        based on current date and deadlines associated with the meeting.
        """
        early_reg_passed = date.today() > self.meeting.early_reg_deadline
        TYPES = [("", "Please select")] + \
                [(x.id, x.option_name+"\t$"+
                  str(x.regular_price if early_reg_passed else x.early_price))
                 for x in self.meeting.regoptions.filter(admin_only=False)]
        type_field = forms.ChoiceField(choices=TYPES, required=True,
            label="Registration Type")
        self.fields.insert(0, 'type', type_field)

    def get_guest(self):
        """
        Returns unsaved RegistrationGuest object if user entered something
        for the guest_name field, else returns None.
        """
        clean = self.clean()
        if not clean.get('guest_name'):
            return None
        return RegistrationGuest(name=clean['guest_name'])

    def get_registration(self, registrant):
        """
        Returns unsaved Registration object corresponding to cleaned form data
        and the given registrant.
        """
        clean = self.clean()
        user_model = get_model(*settings.DJANGO_CONFERENCE_USER_MODEL)
        reg_username = 'OnlineRegistration'
        kwargs = {
            'meeting': self.meeting,
            'type': RegistrationOption.objects.get(id=clean['type']),
            'special_needs': clean.get('special_needs', ''),
            'date_entered': datetime.today(),
            'payment_type': 'cc',
            'registrant': registrant,
            'entered_by': user_model.objects.get(username=reg_username),
        }
        return Registration(**kwargs)


class MeetingExtras(forms.Form):
    """
    Form for fixed-price meeting extra (e.g. abstracts). All fields are
    dynamically generated from the MeetingExtra model.
    """
    def __init__(self, meeting, *args, **kwargs):
        super(MeetingExtras, self).__init__(*args, **kwargs)
        self.meeting = meeting
        extras = meeting.extras.all()
        for extra in extras:
            field = extra.extra_type
            if extra.max_quantity == 1:
                self.fields[field.name] = forms.BooleanField(required=False,
                    label=field.label, help_text=extra.help_text)
            else:
                self.fields[field.name] = forms.IntegerField(required=False,
                    initial=0, min_value=0, max_value=extra.max_quantity,
                    label=field.label, help_text=extra.help_text)

    def get_extras(self, registrant):
        """
        Returns list of RegistrationExtra objects
        """
        clean = self.clean()
        extras = []
        for name, qty in clean.items():
            if qty is True:
                qty = 1
            if not qty:
                continue
            extra = self.meeting.extras.get(extra_type__name=name)
            price = None
            reg_extra = RegistrationExtra(extra=extra, quantity=qty,
                price=price)
            extras.append(reg_extra)
        return extras


class MeetingDonations(forms.Form):
    """
    Form for donations that registrants can make. All fields are
    dynamically generated from the MeetingDonation model.
    """
    def __init__(self, meeting, *args, **kwargs):
        super(MeetingDonations, self).__init__(*args, **kwargs)
        self.meeting = meeting
        donations = meeting.donations.all()
        for donation in donations:
            field = donation.donate_type
            self.fields[field.name] = forms.DecimalField(required=False,
                decimal_places=2, min_value=Decimal("0.0"), max_digits=6,
                label=field.label, help_text=donation.help_text, initial=0)

    def get_donations(self):
        """
        Returns list of RegistrationDonation objects
        """
        clean = self.clean()
        donations = []
        for name, total in clean.items():
            if not total:
                continue
            total = Decimal(total)
            donate_type = self.meeting.donations.get(donate_type__name=name)
            donation = RegistrationDonation(total=total,
                donate_type=donate_type)
            donations.append(donation)
        return donations


class SessionCadreForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        """
        Special form for the SessionCadre model that accepts a "optional"
        keyword, which indicates that validation should only happen
        if the user enters something in
        """
        optional = kwargs.pop('optional', True)
        super(SessionCadreForm, self).__init__(*args, **kwargs)
        if optional:
            for f in self.fields.values():
                f.required = False

    def has_entered_info(self):
        data = self.cleaned_data
        return any([data.get('first_name'), data.get('last_name'),
            data.get('mi'), data.get('email'), data.get('institution')])

    def clean(self):
        clean = super(SessionCadreForm, self).clean()
        if self.has_entered_info():
            #i.e. User Entered Some Data
            #lets ensure all necessary data is present
            if not all([clean.get('first_name'), clean.get('last_name'),
                clean.get('email'), clean.get('institution')]):
                err = "Please fill in all the first name, last name, email,"+\
                      " and institution fields for this person."
                raise forms.ValidationError(err)
        return clean

    class Meta:
        model = SessionCadre


class PaperForm(forms.ModelForm):
    class Meta:
        model = Paper
        exclude = ['creation_time', 'presenter', 'accepted', 'sessions']

    def clean_paper_abstract(self):
        data = self.cleaned_data['paper_abstract']
        num_words = len(data.split())
        if num_words > 250:
            message = "Abstract can contain max 250 words. "+\
                      "You supplied %i words."
            raise forms.ValidationError(message % num_words)
        return data

    def save(self, presenter, commit=True):
        self.instance.presenter = presenter
        return super(PaperForm, self).save(commit)


class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ['title', 'notes', 'abstract']

    def save(self, meeting, commit=True):
        self.instance.meeting = meeting
        return super(SessionForm, self).save(commit)


class CreditCardField(forms.IntegerField):
    @staticmethod
    def get_cc_type(number):
        """
        Gets credit card type given number. Based on values from Wikipedia page
        "Credit card number".
        http://en.wikipedia.org/w/index.php?title=Credit_card_number
        """
        number = str(number)
        #group checking by ascending length of number
        if len(number) == 13:
            if number[0] == "4":
                return "Visa"
        elif len(number) == 14:
            if number[:2] == "36":
                return "MasterCard"
        elif len(number) == 15:
            if number[:2] in ("34", "37"):
                return "American Express"
        elif len(number) == 16:
            if number[:4] == "6011":
                return "Discover"
            if number[:2] in ("51", "52", "53", "54", "55"):
                return "MasterCard"
            if number[0] == "4":
                return "Visa"
        return "Unknown"

    def clean(self, value):
        """Check if given CC number is valid and one of the
           card types we accept"""
        if value and (len(value) < 13 or len(value) > 16):
            raise forms.ValidationError("Please enter in a valid "+\
                "credit card number.")
        elif self.get_cc_type(value) not in ("Visa", "MasterCard",
                                             "American Express"):
            raise forms.ValidationError("Please enter in a Visa, "+\
                "Master Card, or American Express credit card number.")
        return super(CreditCardField, self).clean(value)


class CCExpWidget(forms.MultiWidget):
    """ Widget containing two select boxes for selecting the month and year"""
    def decompress(self, value):
        return [value.month, value.year] if value else [None, None]

    def format_output(self, rendered_widgets):
        html = u' / '.join(rendered_widgets)
        return u'<span style="white-space: nowrap">%s</span>' % html


class CCExpField(forms.MultiValueField):
    EXP_MONTH = [(x, x) for x in xrange(1, 13)]
    EXP_YEAR = [(x, x) for x in xrange(date.today().year,
                                       date.today().year + 15)]
    default_error_messages = {
        'invalid_month': u'Enter a valid month.',
        'invalid_year': u'Enter a valid year.',
    }

    def __init__(self, *args, **kwargs):
        errors = self.default_error_messages.copy()
        if 'error_messages' in kwargs:
            errors.update(kwargs['error_messages'])
        fields = (
            forms.ChoiceField(choices=self.EXP_MONTH,
                error_messages={'invalid': errors['invalid_month']}),
            forms.ChoiceField(choices=self.EXP_YEAR,
                error_messages={'invalid': errors['invalid_year']}),
        )
        super(CCExpField, self).__init__(fields, *args, **kwargs)
        self.widget = CCExpWidget(widgets =
            [fields[0].widget, fields[1].widget])

    def clean(self, value):
        exp = super(CCExpField, self).clean(value)
        if date.today() > exp:
            raise forms.ValidationError(
            "The expiration date you entered is in the past.")
        return exp

    def compress(self, data_list):
        if data_list:
            if data_list[1] in forms.fields.EMPTY_VALUES:
                error = self.error_messages['invalid_year']
                raise forms.ValidationError(error)
            if data_list[0] in forms.fields.EMPTY_VALUES:
                error = self.error_messages['invalid_month']
                raise forms.ValidationError(error)
            year = int(data_list[1])
            month = int(data_list[0])
            # find last day of the month
            day = monthrange(year, month)[1]
            return date(year, month, day)
        return None


class PaymentForm(forms.Form):
    number = CreditCardField(required = True, label = "Card Number")
    holder = forms.CharField(required = True, label = "Card Holder Name",
        max_length = 60)
    expiration = CCExpField(required = True, label = "Expiration")
    ccv_number = forms.RegexField(required = True, label = "CCV Number",
        regex = r'^\d{2,4}$', widget = forms.TextInput(attrs={'size': '4'}))

    def __init__(self, *args, **kwargs):
        self.payment_data = kwargs.pop('payment_data', None)
        super(PaymentForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned = super(PaymentForm, self).clean()
        if not self.errors:
            result = self.process_payment()
            if not result:
                email = settings.DJANGO_CONFERENCE_CONTACT_EMAIL
                err = """
                    We encountered an error while processing your credit card.
                    Please contact <a href="mailto:%s">%s</a> for assistance.
                """
                raise forms.ValidationError(err % (email, email))
            if result and result[0] == 'Card declined':
                raise forms.ValidationError('Your credit card was declined.')
            elif result and result[0] == 'Processing error':
                raise forms.ValidationError(
                    'We encountered the following error while processing '+\
                    'your credit card: '+result[1])
        return cleaned

    def process_payment(self):
        auth_func_loc = settings.DJANGO_CONFERENCE_PAYMENT_AUTH_FUNCTION
        if not self.payment_data or not auth_func_loc:
            return
        auth_func = __import__(name=auth_func_loc[1],
            fromlist=[auth_func_loc[0]])
        datadict = self.cleaned_data
        datadict.update(self.payment_data)
        return auth_func(datadict)


class AddressForm(forms.Form):
    address_line1 = forms.CharField(required=True, max_length=45)
    address_line2 = forms.CharField(required=False, max_length=45)
    city = forms.CharField(required=True, max_length=50)
    country = forms.CharField(required=True, max_length=2, initial = "US")
    state_province = forms.CharField(required = False, max_length = 40,
        label = "State/Province")
    city = forms.CharField(required = True, max_length = 50)
    postal_code = forms.CharField(required = True, max_length = 10)

    def __init_(self, user, *args, **kwargs):
        super(AddressForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        pass
