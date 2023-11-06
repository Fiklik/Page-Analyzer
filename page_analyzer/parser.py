from bs4 import BeautifulSoup


def parse_response(response):
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
    else:
        title = title

    description = soup.find('meta', attrs={'name': 'description'})

    if description is None:
        description = ''
    else:
        description = description['content']

    check = {
        'heading': heading,
        'title': title,
        'description': description
    }

    return check
