from django.core.exceptions import FieldDoesNotExist
from django.db.models import ManyToOneRel, QuerySet

from .exceptions import PointerException


class Pointer(object):

    def __init__(self, path):
        self.path = path

    @property
    def parts(self):
        path_list = self.path.lstrip('/').split('/')
        return [path for path in path_list if path != '']

    def resolve(self, obj):
        for part in self.parts:
            obj = self.process_part(obj, part)
        return obj

    def to_last(self, obj):
        if not self.parts:
            return obj, None
        for part in self.parts[:-1]:
            obj = self.process_part(obj, part)
        return obj, self.parts[-1]

    def process_part(self, obj, part):
        if isinstance(obj, (QuerySet, list)):
            # Get item from queryset / list
            try:
                obj = obj[int(part)]
            except IndexError:
                raise PointerException('Index does not exist: {0}'.format(part))
            except ValueError:
                raise PointerException('Index is not an int: {0}'.format(part))
        else:
            # Navigate relationship
            if not hasattr(obj, '_meta'):
                raise PointerException('process_part: Expected a model, got {0}'.format(
                    type(obj)))

            try:
                field = obj._meta.get_field(part)
            except FieldDoesNotExist:
                field = None

            if isinstance(field, ManyToOneRel):
                obj = getattr(obj, part).all()
            else:
                obj = getattr(obj, part)
        return obj
