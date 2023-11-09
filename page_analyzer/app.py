import os
import requests
from datetime import datetime
from flask import (
    Flask, render_template, request,
    flash, redirect, get_flashed_messages,
    url_for,
)
from dotenv import load_dotenv
from page_analyzer import parser, utils, db


load_dotenv()

app = Flask(__name__)
app.config['DATABASE_URL'] = os.getenv('DATABASE_URL')
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")


@app.route('/', methods=['GET'])
def index():
    messages = get_flashed_messages(with_categories=True)

    return render_template('index.html', messages=messages)


@app.route('/urls', methods=['POST'])
def post_urls():
    connection = db.get_db()
    prompt_data = request.form.get('url')

    if not prompt_data:
        flash('URL обязателен', 'danger')
        messages = get_flashed_messages(with_categories=True)

        return render_template(
            'index.html',
            messages=messages
        ), 422

    is_valid = utils.validate_url(prompt_data)

    if not is_valid:
        flash('Некорректный URL', 'danger')
        messages = get_flashed_messages(with_categories=True)

        return render_template(
            'index.html',
            messages=messages
        ), 422

    valid_url = utils.normalize_url(prompt_data)

    is_exists = db.does_url_exists(connection, valid_url)

    if is_exists:
        site_id = db.get_site_id(connection, valid_url)
        flash('Страница уже существует', 'success')

        return redirect(
            url_for('get_site', id=site_id), code=302)
    else:
        created_at = datetime.now()

        data = {
            'url': valid_url,
            'created_at': created_at
        }

        db.insert_site_into_db(connection, data)

    site_id = db.get_site_id(connection, valid_url)
    flash('Страница успешно добавлена', 'success')
    connection.close()

    return redirect(
        url_for('get_site', id=site_id), code=302)


@app.route('/urls', methods=['GET'])
def get_sites():
    connection = db.get_db()
    sites = db.get_sites_info(connection)
    connection.close()

    return render_template(
        'urls.html',
        sites=sites
    )


@app.route('/urls/<int:id>', methods=['GET'])
def get_site(id):
    connection = db.get_db()
    messages = get_flashed_messages(True)
    site_data = db.get_site_data(connection, id)

    checks = db.get_site_checks(connection, id)
    connection.close()

    return render_template(
        'url.html',
        site=site_data,
        messages=messages,
        checks=checks
    )


@app.route('/urls/<int:id>/checks', methods=['POST'])
def url_checks(id):
    connection = db.get_db()
    site_data = db.get_site_data(connection, id)
    url = site_data['name']

    try:
        response = requests.get(url)
    except (
        Exception, requests.exceptions.ConnectionError, ConnectionError
    ):
        flash('Произошла ошибка при проверке', 'danger')

        return redirect(url_for('get_site', id=id), code=302)

    response_status_code = response.status_code
    valid_status_code = utils.is_valid_status_code(response_status_code)

    if not valid_status_code:
        flash('Произошла ошибка при проверке', 'danger')

        return redirect(url_for('get_site', id=id), code=302)

    check = parser.parse_response(response)
    check['id'] = id
    check['status_code'] = response_status_code
    check['created_at'] = datetime.now()

    db.insert_check_into_db(connection, check)
    connection.close()
    flash('Страница успешно проверена', 'success')

    return redirect(
        url_for('get_site', id=id), code=302
    )
