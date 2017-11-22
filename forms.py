from wtforms import StringField, SelectField
from flask_wtf import FlaskForm
from flask_babel import lazy_gettext as __
import wtforms.validators as validators

__all__ = [
    'SearchForm'
]


class SearchForm(FlaskForm):
    where = [
        ('a', __('All')),
        ('t', __('Title')),
        ('ar', __('Artist')),
        ('al', __('Album'))
    ]

    q = StringField(__('Search term'), [validators.DataRequired()], default=None)
    w = SelectField(__('Where to search'), choices=where, default='a')
