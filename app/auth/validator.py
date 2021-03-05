from password_strength import PasswordStats
from wtforms.validators import ValidationError

class PasswordRequirements(object):
    def __call__(self, form, field):
        password_policy = PasswordStats(field.data)
        strength = password_policy.strength()
        length = len(field.data)
        message = u'Your password must contains at least 8 characters with numbers and capital letters'
        if length < 8 or password_policy.letters_uppercase < 1 or password_policy.numbers < 1:
            raise ValidationError(message)

        message = u'Your password is not strong enough'
        if strength < 0.25:
            raise ValidationError(message)