from django.db import models

class Item(object):
    def __init__(self, value, slug, display=None):
        if not isinstance(value, int):
            raise TypeError('item value should be an integer, not %r' \
                % type(value))

        if not isinstance(slug, str):
            raise TypeError('item slug should be a string, not %r' \
                % type(slug))

        if display != None and not isinstance(display, (basestring)):
            raise TypeError('item display name should be a basestring, not %r' \
                % type(display))

        super(Item, self).__init__()

        self.value = value
        self.slug = slug

        if display is None:
            self.display = slug.capitalize()
        else:
            self.display = display

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        # This is not pretty, but it makes the django admin work right when it
        # renders a select box
        return self.slug

    def __repr__(self):
        return u'<enum.Item: %d %s %r>' % (self.value, self.slug, self.display)

    def __hash__(self):
        return self.value

    def __eq__(self, other):
        if isinstance(other, Item):
            return self.value == other.value
        if isinstance(other, (int, str, long, unicode)):
            try:
                return self.value == int(other)
            except ValueError:
                return unicode(self.slug) == unicode(other)
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

class EnumerationMeta(type):
    def __new__(mcs, name, bases, attrs):
        used_values = set()
        used_slugs = set()
        items = []

        for n, item in list(attrs.items()):
            if isinstance(item, Item):
                if item.value in used_values:
                    raise ValueError(
                        'Item value %d has been used more than once (%s)' % \
                            (item.value, item))
                used_values.add(item.value)
                if item.slug in used_slugs:
                    raise ValueError(
                        'Item slug "%s" has been used more than once' % item.slug
                    )
                used_slugs.add(item.slug)

                items.append((n, item))

        items.sort(key=lambda i: i[1].value)
        item_objects = [i[1] for i in items]

        by_val = dict((i.value, i) for i in item_objects)
        by_slug = dict((i.slug, i) for i in item_objects)

        specials = {
            'items': dict(items),
            'sorted_items': items,
            'items_by_val': by_val,
            'items_by_slug': by_slug,
            }

        for k in specials.keys():
            assert k not in attrs, '"%s" is a forbidden Item name' % k
        attrs.update(specials)

        init_class = attrs.pop('init_class', None)
        cls = super(EnumerationMeta, mcs).__new__(mcs, name, bases, attrs)
        if init_class:
            init_class(cls)
        return cls

    def init_class(mcs):
        pass

    def __iter__(mcs):
        return (key_val for key_val in mcs.sorted_items)

    def __getitem__(mcs, prop):
        return mcs.items[prop]

class Enumeration(object):
    __metaclass__ = EnumerationMeta

    @classmethod
    def from_value(cls, value):
        return cls.items_by_val.get(value)

    @classmethod
    def from_slug(cls, slug):
        return cls.items_by_slug.get(slug)

    @classmethod
    def get_items(cls):
        return [i for n, i in cls]

    @classmethod
    def get_choices(cls):
        return [(item, item.display) for item in cls.get_items()]

    @classmethod
    def to_item(cls, value):
        if value in (None, '', u''):
            return None

        if isinstance(value, Item):
            return value

        try:
            value = int(value)
            item = cls.from_value(value)
        except ValueError:
            item = cls.from_slug(value)

        if item:
            return item

        raise ValueError, '%s is not a valid value for the enumeration' % value


class EnumField(models.Field):
    __metaclass__ = models.SubfieldBase

    def __init__(self, enumeration, *args, **kwargs):
        kwargs.setdefault('choices', enumeration.get_choices())
        super(EnumField, self).__init__(*args, **kwargs)
        self.enumeration = enumeration

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

        raise TypeError('Lookup type %r not supported.' % lookup_type)
