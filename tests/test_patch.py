from django.test import TestCase

from json_patch.exceptions import PatchException, PointerException
from json_patch.operations import AddOperation
from json_patch.patch import Patch
from tests.models import (
    Author,
    Book,
)


class TestPatch(TestCase):

    def test_patch_exception_raised_when_operation_is_unsupported(self):
        patch = Patch([])
        with self.assertRaises(PatchException):
            patch.get_operation_class('mock')

    def test_add_operation_class_returned_for_operation_add_(self):
        patch = Patch([])
        add_operation_class = patch.get_operation_class('add')
        self.assertEqual(add_operation_class, AddOperation)

    def test_patch_exception_raised_when_operation_type_missing(self):
        invalid_operation = {
            'value': 'mock',
        }

        patch = Patch([])
        with self.assertRaises(PatchException):
            patch.get_operation(invalid_operation)

    def test_patch_exception_raised_when_operation_path_missing(self):
        invalid_operation = {
            'op': 'add',
            'value': 'mock',
        }

        patch = Patch([])
        with self.assertRaises(PatchException):
            patch.get_operation(invalid_operation)

    def test_add_exception_instance_returned_for_operation_add(self):
        operation = {
            'op': 'add',
            'path': '/0',
            'value': 'mock',
        }

        patch = Patch([])
        add_operation = patch.get_operation(operation)
        self.assertIsInstance(add_operation, AddOperation)


class TestPatchAddOperation(TestCase):

    def test_author_is_created_in_list(self):
        add_author_diff = [
            {
                'op': 'add',
                'path': '/0',
                'value': {
                    'id': 1,
                    'name': 'Jane'
                }
            }
        ]

        patch = Patch(add_author_diff)
        authors = Author.objects.all()
        patch.apply(authors)

        author = Author.objects.get(pk=1)
        self.assertEqual(author.name, 'Jane')

    def test_author_is_created_in_single_object(self):
        add_author_diff = [
            {
                'op': 'add',
                'path': '/',
                'value': {
                    'id': 1,
                    'name': 'Jane'
                }
            }
        ]

        patch = Patch(add_author_diff)
        authors = Author.objects.none()
        patch.apply(authors)

        author = Author.objects.get(pk=1)
        self.assertEqual(author.name, 'Jane')

    def test_nested_book_is_created_in_list(self):
        author = Author.objects.create(name='Jane')
        add_book_diff = [
            {
                'op': 'add',
                'path': '/0/books/0',
                'value': {
                    'id': 1,
                    'title': 'Book one',
                    'author': 1
                }
            }
        ]
        patch = Patch(add_book_diff)
        authors = Author.objects.all()
        patch.apply(authors)

        books = Book.objects.filter(author=author).all()
        self.assertEqual(books[0].title, 'Book one')


class TestPatchReplaceOperation(TestCase):

    def test_author_name_is_replaced_in_list(self):
        Author.objects.create(name='Bob')

        update_author_diff = [
            {
                'op': 'replace',
                'path': '/0/name',
                'value': 'Jeff',
            }
        ]

        patch = Patch(update_author_diff)
        authors = Author.objects.all()
        patch.apply(authors)

        author = Author.objects.first()
        self.assertEqual(author.name, 'Jeff')

    def test_author_name_is_replaced_in_single_object(self):
        author = Author.objects.create(name='Bob')

        update_author_diff = [
            {
                'op': 'replace',
                'path': '/name',
                'value': 'Jeff',
            }
        ]

        patch = Patch(update_author_diff)
        patch.apply(author)

        author_lookup = Author.objects.get(pk=author.pk)
        self.assertEqual(author_lookup.name, 'Jeff')

    def test_nested_book_two_name_is_replaced_in_list(self):
        author = Author.objects.create(name='Bob')
        Book.objects.create(author=author, title='Book One')
        Book.objects.create(author=author, title='Book two')

        update_book_diff = [
            {
                'op': 'replace',
                'path': '/0/books/1/title',
                'value': 'Book Two',
            }
        ]

        patch = Patch(update_book_diff)
        authors = Author.objects.all()
        patch.apply(authors)

        books = Book.objects.filter(author=author).all()
        self.assertEqual(books[1].title, 'Book Two')


class TestPatchRemoveOperation(TestCase):

    def test_authors_are_removed_from_queryset(self):
        Author.objects.create(name='Bob')
        Author.objects.create(name='Jeff')
        Author.objects.create(name='Jane')

        delete_all_authors_diff = [
            {
                'op': 'remove',
                'path': '/0'
            },
            {
                'op': 'remove',
                'path': '/0'
            }
        ]

        patch = Patch(delete_all_authors_diff)
        authors = Author.objects.all()
        patch.apply(authors)

        author_count = Author.objects.all().count()
        self.assertEqual(author_count, 1)

    def test_author_is_removed(self):
        author = Author.objects.create(name='Bob')
        Author.objects.create(name='Jeff')

        delete_author_diff = [
            {
                'op': 'remove',
                'path': '/'
            }
        ]

        patch = Patch(delete_author_diff)
        patch.apply(author)

        author_count = Author.objects.all().count()
        self.assertEqual(author_count, 1)

    def test_nested_book_is_removed_in_list(self):
        author = Author.objects.create(name='Jeff')
        Book.objects.create(author=author, title='Book One')

        delete_book_diff = [
            {
                'op': 'remove',
                'path': '/0/books/0'
            }
        ]

        patch = Patch(delete_book_diff)
        authors = list(Author.objects.all())
        patch.apply(authors)

        book_count = Book.objects.all().count()
        self.assertEqual(book_count, 0)


class TestPatchTestOperation(TestCase):

    def test_no_error_when_author_name_matches(self):
        Author.objects.create(name='Jeff')

        test_author_name_diff = [
            {
                'op': 'test',
                'path': '/0/name',
                'value': 'Jeff'
            }
        ]

        patch = Patch(test_author_name_diff)
        authors = Author.objects.all()
        patch.apply(authors)

    def test_exception_thrown_when_author_name_does_not_match(self):
        Author.objects.create(name='Jeff')

        test_author_name_diff = [
            {
                'op': 'test',
                'path': '/0/name',
                'value': 'Bob'
            }
        ]

        patch = Patch(test_author_name_diff)
        authors = Author.objects.all()
        with self.assertRaises(PatchException):
            patch.apply(authors)

    def test_exception_thrown_when_path_does_not_exist(self):
        test_author_name_diff = [
            {
                'op': 'test',
                'path': '/0/name',
                'value': 'Jeff'
            }
        ]

        patch = Patch(test_author_name_diff)
        authors = Author.objects.all()
        with self.assertRaises(PointerException):
            patch.apply(authors)
