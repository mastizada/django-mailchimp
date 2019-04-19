from mailchimp.settings import API_KEY, SECURE
from mailchimp.chimp import Connection


# open a non-connected connection (lazily connect on first get_connection call)
CONNECTION = Connection(secure=SECURE)


def get_connection():
    if not CONNECTION.is_connected:
        CONNECTION.connect(API_KEY)
    return CONNECTION
