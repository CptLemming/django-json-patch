=================
django-json-patch
=================

.. image:: https://travis-ci.org/CptLemming/django-json-patch.png?branch=master
    :target: https://travis-ci.org/CptLemming/django-json-patch

`JSON Patch <http://jsonpatch.com/>`_ support for Django models.

Documentation
-------------

The full documentation is at https://django-json-patch.readthedocs.org.

Install
-------

Install django-json-patch::

    pip install django-json-patch

Usage
-----

::

    from json_patch.patch import Patch
    from models import Author

    authors = Author.objects.all()

    add_author = [
        {
            'op': 'add',
            'path': '/0',
            'value': {
                'id': 1,
                'name': 'Bob'
            }
        }
    ]

    patch = Patch(add_author_diff)
    patch.apply(authors)
