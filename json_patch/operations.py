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
    pass


class CopyOperation(PatchOperation):
    pass


class TestOperation(PatchOperation):
    pass
