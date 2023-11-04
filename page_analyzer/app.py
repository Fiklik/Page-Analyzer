import os
import requests
from datetime import datetime
from flask import (
    Flask, render_template, request,
    flash, redirect, get_flashed_messages,
    url_for,
)
from dotenv import load_dotenv
import psycopg2
from bs4 import BeautifulSoup
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

    does_exist = db.does_url_exists(valid_url)

    if does_exist:
        site_id = db.get_site_id(valid_url)
        flash('Страница уже существует', 'success')
        return redirect(
            url_for('get_site', id=site_id), code=302)
    else:
        created_at = datetime.now()
        connection = db.get_db()

        with connection.cursor() as cursor:
            cursor.execute('''
                INSERT INTO urls(name, created_at) VALUES (
                    %s, %s
                );
            ''', (valid_url, created_at,))

        connection.commit()
        connection.close()

    site_id = db.get_site_id(valid_url)
    flash('Страница успешно добавлена', 'success')

    return redirect(
        url_for('get_site', id=site_id), code=302)


@app.route('/urls', methods=['GET'])
def get_sites():
    sites = []
    connection = db.get_db()

    with connection.cursor() as cursor:
        try:
            cursor.execute('''
                    SELECT id, name FROM urls
                    ORDER BY id DESC;
                ''')
            data = cursor.fetchall()

        except (Exception, psycopg2.DatabaseError) as error:
            connection.rollback()
            print(error)

    for elem in data:
        sites.append(
            {
                'id': elem[0],
                'name': elem[1]
            }
        )

    for site in sites:
        with connection.cursor() as cursor:
            try:
                cursor.execute('''
                    SELECT created_at, status_code
                    FROM url_checks
                    WHERE url_id = %s
                    ORDER BY id DESC
                    LIMIT 1;
                ''', (site['id'],))
                data = cursor.fetchone()
                site['last_check'] = data[0]
                site['status_code'] = data[1]
            except (Exception, psycopg2.DatabaseError) as error:
                print(error)
                connection.rollback()
                site['last_check'] = ''
                site['status_code'] = ''

    connection.close()

    return render_template(
        'urls.html',
        sites=sites
    )


@app.route('/urls/<int:id>', methods=['GET'])
def get_site(id):
    messages = get_flashed_messages(True)
    site_data = db.get_site_data(id)

    checks = db.get_site_checks(id)

    return render_template(
        'url.html',
        site=site_data,
        messages=messages,
        checks=checks
    )


@app.route('/urls/<int:id>/checks', methods=['POST'])
def url_checks(id):
    site_data = db.get_site_data(id)
    url = site_data['name']

    try:
        response = requests.get(url)
    except (
        Exception, requests.exceptions.ConnectionError, ConnectionError
    ) as error:
        print(error)
        flash('Произошла ошибка при проверке', 'danger')

        return redirect(url_for('get_site', id=id), code=302)

    response_status_code = response.status_code
    valid_status_code = utils.is_valid_status_code(response_status_code)

    if not valid_status_code:
        flash('Произошла ошибка при проверке', 'danger')

        return redirect(url_for('get_site', id=id), code=302)

    html_doc = response.content
    soup = BeautifulSoup(html_doc, 'html.parser')
    h1, title, description = parser.parse_info_for_check(soup)

    connection = db.get_db()
    created_at = datetime.now()

    with connection.cursor() as cursor:

        cursor.execute('''
            INSERT INTO url_checks(
                url_id, status_code, h1, description, title, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s);
        ''', (id, response_status_code, h1, description, title, created_at,))

    connection.commit()
    connection.close()
    flash('Страница успешно проверена', 'success')

    return redirect(
        url_for('get_site', id=id), code=302
    )
