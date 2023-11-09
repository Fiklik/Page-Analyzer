import os
import psycopg2
from psycopg2.extras import NamedTupleCursor
from dotenv import load_dotenv


load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')


def get_db():
    return psycopg2.connect(DATABASE_URL)


def get_site_id(connection, name):

    with connection.cursor(cursor_factory=NamedTupleCursor) as cursor:
        cursor.execute('''
            SELECT id FROM urls
            WHERE name = %s
        ''', (name,))
        id = cursor.fetchone().id

    return id


def get_site_data(connection, id):

    with connection.cursor(cursor_factory=NamedTupleCursor) as cursor:
        cursor.execute('''
            SELECT * FROM urls
            WHERE id = %s
        ''', (id,))
        data = cursor.fetchone()

    site_data = {
        'id': data.id,
        'name': data.name,
        'created_at': data.created_at
    }

    return site_data


def get_site_checks(connection, id):
    checks = []

    with connection.cursor(cursor_factory=NamedTupleCursor) as cursor:
        cursor.execute('''
            SELECT * FROM url_checks WHERE url_id = %s ORDER BY id DESC;
        ''', (id,))
        data = cursor.fetchall()

    for elem in data:
        checks.append(
            {
                'id': elem.id,
                'url_id': elem.url_id,
                'status_code': elem.status_code,
                'h1': elem.h1,
                'title': elem.title,
                'description': elem.description,
                'created_at': elem.created_at
            }
        )

    return checks


def does_url_exists(connection, url):
    with connection.cursor(cursor_factory=NamedTupleCursor) as cursor:
        try:
            cursor.execute('''
                SELECT * FROM urls
                WHERE name = %s;
            ''', (url,))
        except (Exception, psycopg2.DatabaseError) as error:
            return exist

        exist = cursor.fetchone()

    return exist is not None


def insert_check_into_db(connection, check):

    with connection.cursor(cursor_factory=NamedTupleCursor) as cursor:

        cursor.execute('''
            INSERT INTO url_checks(
                url_id, status_code, h1, description, title, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s);
        ''', (
            check['id'],
            check['status_code'],
            check['heading'],
            check['description'],
            check['title'],
            check['created_at']
        ))

    connection.commit()


def get_sites_info(connection):
    sites = []

    with connection.cursor(cursor_factory=NamedTupleCursor) as cursor:
        try:
            cursor.execute('''
                    SELECT id, name FROM urls
                    ORDER BY id DESC;
                ''')
            data = cursor.fetchall()

        except (Exception, psycopg2.DatabaseError) as error:
            connection.rollback()

    for elem in data:
        sites.append(
            {
                'id': elem.id,
                'name': elem.name
            }
        )

    for site in sites:
        with connection.cursor(cursor_factory=NamedTupleCursor) as cursor:
            try:
                cursor.execute('''
                    SELECT created_at, status_code
                    FROM url_checks
                    WHERE url_id = %s
                    ORDER BY id DESC
                    LIMIT 1;
                ''', (site['id'],))
                data = cursor.fetchone()
                site['last_check'] = data.created_at
                site['status_code'] = data.status_code
            except (Exception, psycopg2.DatabaseError) as error:
                connection.rollback()
                site['last_check'] = ''
                site['status_code'] = ''

    return sites


def insert_site_into_db(connection, data):

    with connection.cursor(cursor_factory=NamedTupleCursor) as cursor:
        cursor.execute('''
            INSERT INTO urls(name, created_at) VALUES (
                %s, %s
            );
        ''', (data['url'], data['created_at']))

    connection.commit()
