from .operations import (
    AddOperation,
    CopyOperation,
    MoveOperation,
    RemoveOperation,
    ReplaceOperation,
    TestOperation
)
from .exceptions import PatchException


class Patch(object):
    operation_types = {
        'add': AddOperation,
        'copy': CopyOperation,
        'move': MoveOperation,
        'remove': RemoveOperation,
        'replace': ReplaceOperation,
        'test': TestOperation,
    }

    def __init__(self, patch):
        self.patch = patch

    def get_operations(self):
        return [self.get_operation(operation) for operation in self.patch]

    def get_operation(self, operation):
        if 'op' not in operation:
            raise PatchException('Missing operation type')
        if 'path' not in operation:
            raise PatchException('Missing operation path')

        operation_class = self.get_operation_class(operation['op'])
        return operation_class(self, operation['path'], operation.get('value'))

    def get_operation_class(self, op):
        if op not in self.operation_types:
            raise PatchException('Unsupported operation: {0}'.format(op))
        return self.operation_types[op]

    def apply(self, obj, save=True):
        for operation in self.get_operations():
            operation.apply(obj)
        return obj
