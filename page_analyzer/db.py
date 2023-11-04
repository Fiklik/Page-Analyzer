import os
import psycopg2
from dotenv import load_dotenv


load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')


def get_db():
    return psycopg2.connect(DATABASE_URL)


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

    site_data = {
        'id': data[0],
        'name': data[1],
        'created_at': data[2]
    }

    return site_data


def get_site_checks(id):
    checks = []
    connection = get_db()

    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT * FROM url_checks WHERE url_id = %s ORDER BY id DESC;
        ''', (id,))
        data = cursor.fetchall()

    connection.close()

    for elem in data:
        checks.append(
            {
                'id': elem[0],
                'url_id': elem[1],
                'status_code': elem[2],
                'h1': elem[3],
                'title': elem[4],
                'description': elem[5],
                'created_at': elem[6]
            }
        )

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
