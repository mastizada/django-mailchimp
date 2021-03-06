from django import template
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

from mailchimp.utils import is_queued_or_sent


register = template.Library()


def dummy_function(param):
    return True


def mailchimp_send_for_object(context, obj):
    is_sent = is_queued_or_sent(obj)
    sent_date = None
    campaign_id = None
    if is_sent and hasattr(is_sent, 'sent_date'):
        sent_date = is_sent.sent_date
        campaign_id = is_sent.campaign_id
    if hasattr(obj, 'mailchimp_allow_send'):
        objchck = obj.mailchimp_allow_send
    else:
        objchck = dummy_function
    request = context['request']
    return {
        'content_type': ContentType.objects.get_for_model(obj).pk,
        'primary_key': obj.pk,
        'allow': request.user.has_perm('mailchimp.can_send') and objchck(request),
        'is_sent': is_sent,
        'sent_date': sent_date,
        'campaign_id': campaign_id,
        'can_view': sent_date and request.user.has_perm('mailchimp.can_view'),
        'admin_prefix': getattr(settings, 'ADMIN_MEDIA_PREFIX', None) or ''.join([settings.STATIC_URL, 'admin/']),
        'can_test': bool(request.user.email),
    }


register.inclusion_tag('mailchimp/send_button.html', takes_context=True)(mailchimp_send_for_object)
