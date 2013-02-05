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
        if value is None:
            return value
        return self.to_python(value).value

    def get_db_prep_lookup(self, lookup_type, value, connection=None, prepared=False):
        def prepare(value):
            v = self.to_python(value)
            return self.get_db_prep_save(v, connection=connection)

        if lookup_type in ('exact', 'lt', 'lte', 'gt', 'gte'):
            return [prepare(value)]
        elif lookup_type == 'in':
            return [prepare(v) for v in value]
        elif lookup_type == 'isnull':
            return []

        raise TypeError("Lookup type %r not supported." % lookup_type)

    def south_field_triple(self):
        from south.modelsinspector import introspector, NOT_PROVIDED
        args, kwargs = introspector(self)

        # repr(Item) is not only invalid as an lookup value, it actually causes
        # South to generate invalid Python
        if self.default != NOT_PROVIDED:
            kwargs['default'] = None

            # Cannot set a real default if the "default" kwarg is a callable.
            if not callable(self.default):
                kwargs['default'] = self.default and self.default.value

        return ('django.db.models.fields.IntegerField', args, kwargs)

    def value_to_string(self, obj):
        item = self._get_val_from_obj(obj)
        return str(item.value)
