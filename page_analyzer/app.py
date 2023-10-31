import os
import requests
from datetime import datetime
from flask import (
    Flask, render_template, request,
    flash, redirect, get_flashed_messages,
    url_for,
)
import validators
from urllib.parse import urlparse
from dotenv import load_dotenv
import psycopg2
from bs4 import BeautifulSoup
# import html.parser


load_dotenv()

app = Flask(__name__)
app.config['DATABASE_URL'] = os.getenv('DATABASE_URL')
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")


def create_db():
    db_connection = get_db()

    with app.open_resource('../database.sql', mode='r') as f:
        db_connection.cursor().execute(f.read())

    db_connection.commit()
    db_connection.close()


def get_db():
    return psycopg2.connect(app.config['DATABASE_URL'])


def validate_url(url):
    return validators.url(url) and len(url) <= 255


def normalize_url(url):
    url = urlparse(url)
    return f'{url.scheme}://{url.netloc}'


def get_site_id(name):
    connection = get_db()

    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT id FROM urls
            WHERE name = %s
        ''', (name,))
        id = cursor.fetchone()[0]

    connection.close()

    return id


def get_site_data(id):
    connection = get_db()

    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT * FROM urls
            WHERE id = %s
        ''', (id,))
        data = cursor.fetchone()

    connection.close()

    return data


def is_valid_status_code(code):
    return code < 400


def get_site_checks(id):
    connection = get_db()

    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT * FROM url_checks WHERE url_id = %s ORDER BY id DESC;
        ''', (id,))
        checks = cursor.fetchall()

    connection.close()

    return checks


def does_url_exists(url):
    connection = get_db()
    with connection.cursor() as cursor:
        try:
            cursor.execute('''
                SELECT * FROM urls
                WHERE name = %s;
            ''', (url,))
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)

        exist = cursor.fetchone()

    connection.close()

    return exist is not None


@app.route('/', methods=['GET'])
def index():
    create_db()
    messages = get_flashed_messages(with_categories=True)

    return render_template(
            'index.html',
            messages=messages
        )


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

    is_valid = validate_url(prompt_data)

    if not is_valid:
        flash('Некорректный URL', 'danger')
        messages = get_flashed_messages(with_categories=True)
        return render_template(
            'index.html',
            messages=messages
        ), 422

    valid_url = normalize_url(prompt_data)

    does_exist = does_url_exists(valid_url)

    if does_exist:
        site_id = get_site_id(valid_url)
        flash('Страница уже существует', 'success')
        return redirect(
            url_for('get_site', id=site_id), code=302)
    else:
        created_at = datetime.now()
        connection = get_db()

        with connection.cursor() as cursor:
            cursor.execute('''
                INSERT INTO urls(name, created_at) VALUES (
                    %s, %s
                );
            ''', (valid_url, created_at,))

        connection.commit()
        connection.close()

    site_id = get_site_id(valid_url)
    flash('Страница успешно добавлена', 'success')

    return redirect(
        url_for('get_site', id=site_id), code=302)


@app.route('/urls', methods=['GET'])
def get_sites():
    data = []
    connection = get_db()

    with connection.cursor() as cursor:
        try:
            cursor.execute('''
                    SELECT urls.id, urls.name, 
                    MAX(url_checks.created_at), url_checks.status_code 
                    FROM urls JOIN url_checks
                    ON url_checks.url_id = urls.id
                    GROUP BY urls.id, urls.name, url_checks.status_code
                    ORDER BY urls.id DESC;
                ''')
            sites_and_checks_data = cursor.fetchall()
            print(type(sites_and_checks_data))
            print(sites_and_checks_data)

        except (Exception, psycopg2.DatabaseError) as error:
            connection.rollback()
            print(error)

    connection.close()

    return render_template(
        'urls.html',
        data=sites_and_checks_data,
    )


@app.route('/urls/<int:id>', methods=['GET'])
def get_site(id):
    messages = get_flashed_messages(True)
    site_data = get_site_data(id)
    site = {
        'id': site_data[0],
        'name': site_data[1],
        'created_at': site_data[2]
    }

    checks = get_site_checks(id)

    return render_template(
        'url.html',
        site=site,
        messages=messages,
        checks=checks
    )


@app.route('/urls/<int:id>/checks', methods=['POST'])
def url_checks(id):
    site_data = get_site_data(id)
    print(site_data)
    url = site_data[1]

    try:
        response = requests.get(url)
    except (Exception, requests.exceptions.ConnectionError) as error:
        print(error)
        flash('Произошла ошибка при проверке', 'danger')

        return redirect(url_for('get_site', id=id), code=302)

    response_status_code = response.status_code
    valid_status_code = is_valid_status_code(response_status_code)

    if not valid_status_code:
        flash('Произошла ошибка при проверке', 'danger')
        messages = get_flashed_messages(with_categories=True)

        return render_template(
            url_for('url_checks', id=id),
            messages=messages
        ), 422

    html_doc = response.content
    soup = BeautifulSoup(html_doc, 'html.parser')
    heading = soup.find('h1')

    if heading is None:
        heading = ''
    else:
        heading = heading.string

    title = soup.title.string

    if title is None:
        title = ''

    description = soup.find('meta', attrs={'name': 'description'})

    if description is None:
        description = ''
    else:
        description = description['content']

    print(heading, title, description)

    connection = get_db()
    created_at = datetime.now()

    with connection.cursor() as cursor:

        cursor.execute('''
            INSERT INTO url_checks(
                url_id, h1, description, title, status_code, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s);
        ''', (
            id, heading,
            description, title,
            response_status_code, created_at,
        ))

    connection.commit()
    connection.close()
    flash('Страница успешно проверена', 'success')

    return redirect(
        url_for('get_site', id=id), code=302
    )
