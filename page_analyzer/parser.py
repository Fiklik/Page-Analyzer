def parse_info_for_check(content):
    heading = content.find('h1')

    if heading is None:
        heading = ''
    else:
        heading = heading.string

    title = content.title.string

    if title is None:
        title = ''
    else:
        title = title

    description = content.find('meta', attrs={'name': 'description'})

    if description is None:
        description = ''
    else:
        description = description['content']

    return heading, title, description
