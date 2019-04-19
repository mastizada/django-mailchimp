from django.urls import path

from mailchimp.settings import VIEWS_INFO, VIEWS_OVERVIEW, VIEWS_SCHEDULE_OBJECT, VIEWS_TEST_OBJECT
from mailchimp.views import webhook, dequeue, cancel, test_real


urlpatterns = [
    path('', VIEWS_OVERVIEW, name='mailchimp_overview', kwargs={'page': '1'}),
    path('(?P<page>\d+)/', VIEWS_OVERVIEW, name='mailchimp_overview'),
    path('send/(?P<content_type>\d+)/(?P<pk>\d+)/', VIEWS_SCHEDULE_OBJECT, name='mailchimp_schedule_for_object'),
    path('test/(?P<content_type>\d+)/(?P<pk>\d+)/', VIEWS_TEST_OBJECT, name='mailchimp_test_for_object'),
    path('test/(?P<content_type>\d+)/(?P<pk>\d+)/real/', test_real, name='mailchimp_real_test_for_object'),
    path('info/(?P<campaign_id>\w+)/', VIEWS_INFO, name='mailchimp_campaign_info'),
    path('dequeue/(?P<id>\d+)/', dequeue, name='mailchimp_dequeue'),
    path('cancel/(?P<id>\d+)/', cancel, name='mailchimp_cancel'),
    path('webhook/(?P<key>\w+)/', webhook, name='mailchimp_webhook'),
]
