from django.db.models import Model, QuerySet
from django.forms import modelform_factory

from .exceptions import PatchException
from .pointers import Pointer


class PatchOperation(object):

    def __init__(self, patch, path, value=None):
        self.patch = patch
        self.path = path
        self.value = value
        self.pointer = Pointer(self.path)

    def get_form_class(self, obj, fields=None):
        if not fields:
            fields = '__all__'
        if not isinstance(obj, Model):
            raise PatchException(
                'get_model_form: obj should be an '
                'instance of django.db.models.Model. Instead found {0}'.format(type(obj)))
        return modelform_factory(obj.__class__, fields=fields)

    def get_form(self, obj, form_fields=None, form_kwargs={}):
        form_class = self.get_form_class(obj, fields=form_fields)
        form_kwargs = self.get_form_kwargs(obj, **form_kwargs)
        return form_class(**form_kwargs)

    def get_form_kwargs(self, obj, **kwargs):
        kwargs.update({
            'instance': obj
        })
        return kwargs

    def apply(self, obj, save=True):
        raise NotImplementedError('Logic to implement patch')


class ReplaceOperation(PatchOperation):
    """
    The "replace" operation replaces the value at the target location
    with a new value. The operation object MUST contain a "value" member
    whose content specifies the replacement value.

    { "op": "replace", "path": "/a/b/c", "value": 42 }
    """

    def apply(self, obj, save=True):
        obj, attribute = self.pointer.to_last(obj)

        form_kwargs = {
            'data': {
                attribute: self.value
            }
        }

        form_fields = [attribute, ]

        form = self.get_form(obj, form_fields=form_fields, form_kwargs=form_kwargs)
        if form.is_valid():
            if save:
                form.save()
        else:
            raise PatchException('Failed validation in form save: {0}'.format(form.errors))
        return obj


class AddOperation(PatchOperation):
    """
    The "add" operation performs one of the following functions,
    depending upon what the target location references:

        - If the target location specifies an array index, a new value is
          inserted into the array at the specified index.

        - If the target location specifies an object member that does not
          already exist, a new member is added to the object.

        - If the target location specifies an object member that does exist,
          that member's value is replaced.

    { "op": "add", "path": "/a/b/c", "value": [ "foo", "bar" ] }
    """

    def apply(self, obj, save=True):
        obj, attribute = self.pointer.to_last(obj)

        if attribute:
            try:
                # Validate index does not already exist
                obj[int(attribute)]
            except IndexError:
                pass
            else:
                raise PatchException('Entry exists at position: {0}'.format(attribute))

        if isinstance(obj, QuerySet):
            model = obj.model
            obj = model()

        form_kwargs = {
            'data': self.value
        }

        form = self.get_form(obj, form_kwargs=form_kwargs)
        if form.is_valid():
            if save:
                form.save()
        else:
            raise PatchException('Failed validation in form save: {0}'.format(form.errors))
        return obj


class RemoveOperation(PatchOperation):
    """
    The "remove" operation removes the value at the target location.

    { "op": "remove", "path": "/a/b/c" }
    """

    def apply(self, obj, save=True):
        obj, attribute = self.pointer.to_last(obj)

        if isinstance(obj, (QuerySet, list)):
            try:
                item = obj[int(attribute)]
            except IndexError:
                raise PatchException('Index does not exist: {0}'.format(attribute))
            except ValueError:
                raise PatchException('Index is not an int: {0}'.format(attribute))
            else:
                item.delete()
                if isinstance(obj, list):
                    # Special case for lists: Need to manually remove the item
                    del obj[int(attribute)]
        else:
            # Re-use existing lookup logic here
            obj = self.pointer.resolve(obj)
            obj.delete()
        return None


class MoveOperation(PatchOperation):
    """
    The "move" operation removes the value at a specified location and
    adds it to the target location.

    The operation object MUST contain a "from" member, which is a string
    containing a JSON Pointer value that references the location in the
    target document to move the value from.

    { "op": "move", "from": "/a/b/c", "path": "/a/b/d" }
    """
    pass


class CopyOperation(PatchOperation):
    """
    The "copy" operation copies the value at a specified location to the
    target location.

    The operation object MUST contain a "from" member, which is a string
    containing a JSON Pointer value that references the location in the
    target document to copy the value from.

    { "op": "copy", "from": "/a/b/c", "path": "/a/b/e" }
    """
    pass


class TestOperation(PatchOperation):
    """
    The "test" operation tests that a value at the target location is
    equal to a specified value.

    { "op": "test", "path": "/a/b/c", "value": "foo" }
    """

    def apply(self, obj, save=True):
        obj = self.pointer.resolve(obj)

        if obj != self.value:
            raise PatchException('Value does not match: Expected {0}, got {1}'.format(
                obj, self.value))
