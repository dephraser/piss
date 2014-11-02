# -*- coding: utf-8 -*-

def validate_service(post, entity, post_type):
    '''
    Determines if a post belongs to a service, based on a given entity and post
    type.

    :param post: the post to analyze.
    :param service: the service we are checking for.
    :param entity: the entity for the service.
    :param post_type: the post type for the service.
    '''
    errors = []
    # TODO: below would be better as a Cerberus validation
    if not post['entity'] == entity:
        errors.append('Incorrect entity for service.')
    if not post['type'] == post_type:
        errors.append('Incorrect post type for service.')
    if 'post' not in post['links'][0]:
        errors.append('Post ID not specified.')
    return errors


def is_duplicate_syndication(links, entity):
    '''
    Determines if a syndication link to the given entity already exists in a
    links list.

    :param links: the list of links to analyze.
    :param entity: the entity we are checking for.
    '''
    for link in links:
        if link['entity'] == entity and link['type'] == 'syndication':
            return True
    return False