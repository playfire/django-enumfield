from django.db import models

class EnumField(models.Field):
    __metaclass__ = models.SubfieldBase

    def __init__(self, enumeration, *args, **kwargs):
        self.enumeration = enumeration
        kwargs.setdefault('choices', enumeration.get_choices())

        super(EnumField, self).__init__(*args, **kwargs)

    def get_internal_type(self):
        return 'IntegerField'

    def to_python(self, value):
        return self.enumeration.to_item(value)

    def get_db_prep_save(self, value, connection=None):
        if hasattr(value, 'value'):
            return value.value
        return value

    def get_db_prep_lookup(self, lookup_type, value, connection=None, prepared=False):
        def prepare(value):
            v = self.to_python(value)
            return self.get_db_prep_save(v, connection=connection)

        if lookup_type == 'exact':
            return [prepare(value)]
        elif lookup_type == 'in':
            return [prepare(v) for v in value]
        elif lookup_type == 'isnull':
            return []

        raise TypeError("Lookup type %r not supported." % lookup_type)
