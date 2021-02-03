#!/usr/bin/env python3

import os
from datetime import datetime
from datetime import timedelta

import jinja2
import aiohttp_jinja2
from aiohttp import web
from wtforms import Form
from wtforms import FileField
from wtforms import RadioField
from wtforms import IntegerField
from wtforms import DateTimeField
from markupsafe import Markup

from gostcrypto import GostCrypto
from gostcrypto.utils import get_validity_dts
from gostcrypto.utils import generate_serialnumber

from config import CA_LIST, ISSUER_ALT_NAME, STORAGE_PATH

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

# В пути могут быть переменные окружения и ссылки на домашнюю директорию
STORAGE_PATH = os.path.expandvars(os.path.expanduser(STORAGE_PATH))

GOST_CRYPTO = GostCrypto(storage_type='fs', dir_path=STORAGE_PATH)


def markup_labeles_in_choices(choices):
    new_choices = list()
    for row in choices:
        data, label = row
        new_choices.append([data, Markup(label)])
    return new_choices


class PKRBPRequestForm(Form):

    class Meta:
        csrf = False

    NOT_BEFORE_MANUAL_DATE = 'not before manual date'
    NOT_BEFORE_OFFSET = 'not before offset'
    NOT_AFTER_MANUAL_DATE = 'not after manual date'
    NOT_AFTER_OFFSET = 'not after offset'

    req_file = FileField('Выберите REQ файл из ПКРБП:')  # TODO , validators=[FileRequired()])
    # Дата и время выпуска
    not_before_pick = RadioField(choices=[(NOT_BEFORE_MANUAL_DATE, NOT_BEFORE_MANUAL_DATE),
                                          (NOT_BEFORE_OFFSET, NOT_BEFORE_OFFSET)],
                                 default=NOT_BEFORE_OFFSET)
    not_before = DateTimeField('Дата и время выпуска', format=DATETIME_FORMAT, default=datetime.utcnow())
    not_before_offset_years = IntegerField('Годы', default=0)
    not_before_offset_months = IntegerField('Месяцы', default=0)
    not_before_offset_days = IntegerField('Дни', default=-1)
    not_before_offset_hours = IntegerField('Часы', default=0)
    not_before_offset_minutes = IntegerField('Минуты', default=0)
    not_before_offset_seconds = IntegerField('Секунды', default=0)
    # Дата и время окончания
    not_after_pick = RadioField(choices=[(NOT_AFTER_MANUAL_DATE, NOT_AFTER_MANUAL_DATE),
                                         (NOT_AFTER_OFFSET, NOT_AFTER_OFFSET)],
                                default=NOT_AFTER_OFFSET)
    not_after = DateTimeField('Дата и время окончания', format=DATETIME_FORMAT, default=datetime.utcnow())
    not_after_offset_years = IntegerField('Годы', default=5)
    not_after_offset_months = IntegerField('Месяцы', default=0)
    not_after_offset_days = IntegerField('Дни', default=0)
    not_after_offset_hours = IntegerField('Часы', default=0)
    not_after_offset_minutes = IntegerField('Минуты', default=0)
    not_after_offset_seconds = IntegerField('Секунды', default=0)

    ca_key_name = RadioField('Выберите корневой сертификат', choices=markup_labeles_in_choices(CA_LIST),
                             default=CA_LIST[0][0])

    def get_validity(self):
        not_before_offset = {
            'years': self.not_before_offset_years.data,
            'months': self.not_before_offset_months.data,
            'days': self.not_before_offset_days.data,
            'hours': self.not_before_offset_hours.data,
            'minutes': self.not_before_offset_minutes.data,
            'seconds': self.not_before_offset_seconds.data,
        }
        not_before_date = None if self.not_before_pick.data == self.NOT_BEFORE_OFFSET else self.not_before.data
        not_after_offset = {
            'years': self.not_after_offset_years.data,
            'months': self.not_after_offset_months.data,
            'days': self.not_after_offset_days.data,
            'hours': self.not_after_offset_hours.data,
            'minutes': self.not_after_offset_minutes.data,
            'seconds': self.not_after_offset_seconds.data,
        }
        not_after_date = None if self.not_after_pick.data == self.NOT_AFTER_OFFSET else self.not_after.data
        return get_validity_dts(not_before_date, not_before_offset, not_after_date, not_after_offset)


def send_bytes(body: bytes, filename: str, headers: dict = None):
    if headers is None:
        headers = dict()
    headers['Content-Disposition'] = f'inline; filename="{filename}"'
    return web.Response(body=body, headers=headers)


async def get_ca_cert(request: web.Request):
    ca_key_name = request.match_info['ca_key_name']
    cert_file_name = ca_key_name + '.cer'
    cert_bytes = GOST_CRYPTO.get_cert(ca_key_name)
    return send_bytes(cert_bytes, cert_file_name)


@aiohttp_jinja2.template('index.html')
async def index(request: web.Request):
    form = PKRBPRequestForm()
    utc_now = datetime.utcnow()
    form.not_before.data = utc_now
    form.not_after.data = utc_now + timedelta(days=365 * 5)
    return {'form': form}


async def request_cert(request: web.Request):
    post_data = await request.post()
    form = PKRBPRequestForm(post_data)
    if form.validate():
        not_before, not_after = form.get_validity()
        req_file = form.req_file.data
        req_bytes = req_file.file.read()
        ca_key_name = form.ca_key_name.data
        # Создаем сертификат и возвращаем
        serialnumber = generate_serialnumber()
        cert_bytes = GOST_CRYPTO.create_signed_cert_from_req(
            req_bytes,
            ca_key_name=ca_key_name,
            serialnumber=serialnumber,
            not_before_dt=not_before,
            not_after_dt=not_after,
            issuer_alt_name=ISSUER_ALT_NAME
        )
        cert_file_name = os.path.splitext(req_file.filename)[0]+'.cer'
        return send_bytes(cert_bytes, cert_file_name)


app = web.Application()
app.add_routes([
    web.get('/', index),
    web.post('/', request_cert),
    web.get('/get_ca_cert/{ca_key_name}', get_ca_cert, name='get_ca_cert'),
    web.static('/static', 'static'),
])
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('templates'))

if __name__ == '__main__':
    web.run_app(app)
