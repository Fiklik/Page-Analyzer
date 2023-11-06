import os
import psycopg2
from dotenv import load_dotenv


load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')


def get_db():
    return psycopg2.connect(DATABASE_URL)


def get_site_id(connection, name):

    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT id FROM urls
            WHERE name = %s
        ''', (name,))
        id = cursor.fetchone()[0]

    return id


def get_site_data(connection, id):

    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT * FROM urls
            WHERE id = %s
        ''', (id,))
        data = cursor.fetchone()

    site_data = {
        'id': data[0],
        'name': data[1],
        'created_at': data[2]
    }

    return site_data


def get_site_checks(connection, id):
    checks = []

    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT * FROM url_checks WHERE url_id = %s ORDER BY id DESC;
        ''', (id,))
        data = cursor.fetchall()

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


def does_url_exists(connection, url):
    with connection.cursor() as cursor:
        try:
            cursor.execute('''
                SELECT * FROM urls
                WHERE name = %s;
            ''', (url,))
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)

        exist = cursor.fetchone()

    return exist is not None


def insert_check_into_db(connection, check):

    with connection.cursor() as cursor:

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

    return sites


def insert_site_into_db(connection, data):

    with connection.cursor() as cursor:
        cursor.execute('''
            INSERT INTO urls(name, created_at) VALUES (
                %s, %s
            );
        ''', (data['url'], data['created_at']))

    connection.commit()
