from .item import Item

class EnumerationMeta(type):
    def __new__(mcs, name, bases, attrs):
        used_values = set()
        used_slugs = set()
        items = []

        # Inherit items from parent classes
        for base in bases:
            if hasattr(base, 'items'):
                items.extend(base.items.items())

        for n, item in list(attrs.items()):
            if isinstance(item, Item):
                if item.value in used_values:
                    raise ValueError(
                        "Item value %d has been used more than once (%s)" % \
                            (item.value, item)
                    )
                used_values.add(item.value)
                if item.slug in used_slugs:
                    raise ValueError(
                        "Item slug %r has been used more than once" % item.slug
                    )
                used_slugs.add(item.slug)

                items.append((n, item))

        items.sort(key=lambda i: i[1].creation_counter)
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
            assert k not in attrs, "%r is a forbidden Item name" % k

        attrs.update(specials)

        init_class = attrs.pop('init_class', None)
        cls = super(EnumerationMeta, mcs).__new__(mcs, name, bases, attrs)

        if init_class:
            init_class(cls)

        return cls

    def init_class(mcs):
        pass

    def __iter__(mcs):
        return iter(mcs.get_items())

    def __getitem__(mcs, prop):
        return mcs.items[prop]

class EnumerationBase(object):
    @classmethod
    def from_value(cls, value):
        try:
            return cls.items_by_val[value]
        except KeyError:
            raise ValueError(
                "%r is not a valid value for the enumeration" % value
            )

    @classmethod
    def from_slug(cls, slug):
        try:
            return cls.items_by_slug[slug]
        except KeyError:
            raise ValueError(
                "%r is not a valid slug for the enumeration" % slug
            )

    @classmethod
    def get_items(cls):
        return [x[1] for x in cls.sorted_items]

    @classmethod
    def get_choices(cls):
        return [(item, item.display) for item in cls.get_items()]

    @classmethod
    def to_item(cls, value):
        if value in (None, '', u''):
            return None

        if isinstance(value, Item):
            return value

        item = None

        try:
            value = int(value)
            item = cls.from_value(value)
        except ValueError:
            try:
                item = cls.from_slug(value)
            except ValueError:
                pass

        if item:
            return item

        raise ValueError(
            "%r is not a valid slug or value for the enumeration" % value
        )

class Enumeration(EnumerationBase):
    __metaclass__ = EnumerationMeta

def make_enum(name, *items):
    """
    Returns an enumeration type compatible with Enumeration. Example:

    >>> FunnelStageEnum = make_enum('FunnelStageEnum',
        Item(10, 'landing'),
        Item(20, 'email'),
    )
    """

    return type(
        name,
        (Enumeration,),
        dict((i.slug.upper(), i) for i in items),
    )

