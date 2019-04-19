import re
import warnings
from django.core.cache import cache
from django.contrib.contenttypes.models import ContentType
from mailchimp.models import Queue, Campaign
from mailchimp.settings import REAL_CACHE, CACHE_TIMEOUT


class KeywordArguments(dict):
    def __getattr__(self, attr):
        return self[attr]


class Cache(object):
    def __init__(self, prefix=''):
        self._data = {}
        self._clear_lock = False
        self._prefix = prefix
        if REAL_CACHE:
            self._set = getattr(self, '_real_set')
            self._get = getattr(self, '_real_get')
            self._del = getattr(self, '_real_del')
        else:
            self._set = getattr(self, '_fake_set')
            self._get = getattr(self, '_fake_get')
            self._del = getattr(self, '_fake_del')

    def get(self, key, obj, *args, **kwargs):
        if self._clear_lock:
            self.flush(key)
            self._clear_lock = False
        value = self._get(key)
        if value is None:
            value = obj(*args, **kwargs) if callable(obj) else obj
            self._set(key, value)
        return value

    def _real_set(self, key, value):
        cache.set(key, value, CACHE_TIMEOUT)

    def _real_get(self, key):
        return cache.get(key, None)

    def _real_del(self, key):
        cache.delete(key)

    def _fake_set(self, key, value):
        self._data[key] = value

    def _fake_get(self, key):
        return self._data.get(key, None)

    def _fake_del(self, key):
        if key in self._data:
            del self._data[key]

    def get_child_cache(self, key):
        return Cache('%s_%s_' % (self._prefix, key))

    def flush(self, *keys):
        for key in keys:
            if key in self._data:
                self._del(key)

    def lock(self):
        self._clear_lock = True

    def clear(self, call):
        self.lock()
        return call()


def wrap(base, parent, name, *baseargs, **basekwargs):
    def _wrapped(*args, **kwargs):
        fullargs = baseargs + args
        kwargs.update(basekwargs)
        return getattr(parent, '%s_%s' % (base, name))(*fullargs, **kwargs)
    return _wrapped


def build_dict(master, klass, data, key='id'):
    return dict([(info[key], klass(master, info)) for info in data])


def _convert(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


class Bullet(object):
    def __init__(self, number, link, active):
        self.number = number
        self.link = link
        self.active = active


class Paginator(object):
    def __init__(self, objects, page, get_link, per_page=20, bullets=5):
        page = int(page)
        self.page = page
        self.get_link = get_link
        self.all_objects = objects
        self.objects_count = objects.count()
        per_page = per_page() if callable(per_page) else per_page
        self.pages_count = int(float(self.objects_count) / float(per_page)) + 1
        self.bullets_count = 5
        self.per_page = per_page
        self.start = (page - 1) * per_page
        self.end = page * per_page
        self.is_first = page == 1
        self.first_bullet = Bullet(1, self.get_link(1), False)
        self.is_last = page == self.pages_count
        self.last_bullet = Bullet(self.pages_count, self.get_link(self.pages_count), False)
        self.has_pages = self.pages_count != 1
        self._objects = None
        self._bullets = None

    @property
    def bullets(self):
        if self._bullets is None:
            pre = int(float(self.bullets_count) / 2)
            bullets = [Bullet(self.page, self.get_link(self.page), True)]
            diff = 0
            for i in range(1, pre + 1):
                this = self.page - i
                if this:
                    bullets.insert(0, Bullet(this, self.get_link(this), False))
                else:
                    diff = pre - this
                    break
            for i in range(1, pre + 1 + diff):
                this = self.page + i
                if this <= self.pages_count:
                    bullets.append(Bullet(this, self.get_link(this), False))
                else:
                    break
            self._bullets = bullets
        return self._bullets

    @property
    def objects(self):
        if self._objects is None:
            self._objects = self.all_objects[self.start:self.end]
        return self._objects


class InternalRequest(object):
    def __init__(self, request, args, kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs

    def contribute_to_class(self, cls):
        cls.request = self.request
        cls.args = self.args
        cls.kwargs = self.kwargs


class WarningProxy(object):
    __stuff = {}

    def __init__(self, logger, obj):
        WarningProxy.__stuff[self] = {}
        WarningProxy.__stuff[self]['logger'] = logger
        WarningProxy.__stuff[self]['obj'] = obj

    def __getattr__(self, attr):
        WarningProxy.__stuff[self]['logger'].lock()
        val = getattr(WarningProxy.__stuff[self]['obj'], attr)
        WarningProxy.__stuff[self]['logger'].release()
        return WarningProxy(WarningProxy.__stuff[self]['logger'], val)

    def __setattr__(self, attr, value):
        WarningProxy.__stuff[self]['logger'].lock()
        setattr(WarningProxy.__stuff[self]['obj'], attr)
        WarningProxy.__stuff[self]['logger'].release()

    def __call__(self, *args, **kwargs):
        WarningProxy.__stuff[self]['logger'].lock()
        val = WarningProxy.__stuff[self]['obj'](*args, **kwargs)
        WarningProxy.__stuff[self]['logger'].release()
        return val


class WarningLogger(object):
    def __init__(self):
        self.proxies = []
        self.queue = []
        self._old = warnings.showwarning

    def proxy(self, obj):
        return WarningProxy(self, obj)

    def lock(self):
        warnings.showwarning = self._showwarning

    def _showwarning(self, message, category, filename, lineno, fileobj=None):
        self.queue.append((message, category, filename, lineno))
        self._old(message, category, filename, lineno, fileobj)

    def release(self):
        warnings.showwarning = self._old

    def get(self):
        queue = list(self.queue)
        self.queue = []
        return queue

    def reset(self):
        self.queue = []


class Lazy(object):
    def __init__(self, real):
        self.__real = real
        self.__cache = {}

    def __getattr__(self, attr):
        if attr not in self.__cache:
            self.__cache[attr] = getattr(self.__real, attr)
        return self.__cache[attr]


def dequeue(limit=None):
    from mailchimp.models import Queue
    for camp in Queue.objects.dequeue(limit):
        yield camp


def is_queued_or_sent(obj):
    object_id = obj.pk
    content_type = ContentType.objects.get_for_model(obj)
    q = Queue.objects.filter(content_type=content_type, object_id=object_id)
    if q.count():
        return q[0]
    c = Campaign.objects.filter(content_type=content_type, object_id=object_id)
    if c.count():
        return c[0]
    return False
