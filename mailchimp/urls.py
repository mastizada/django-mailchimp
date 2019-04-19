from django.urls import path

from mailchimp.settings import VIEWS_INFO, VIEWS_OVERVIEW, VIEWS_SCHEDULE_OBJECT, VIEWS_TEST_OBJECT
from mailchimp.views import webhook, dequeue, cancel, test_real


app_name = 'mailchimp'


urlpatterns = [
    path('', VIEWS_OVERVIEW, name='mailchimp_overview', kwargs={'page': '1'}),
    path('<int:page>/', VIEWS_OVERVIEW, name='mailchimp_overview'),
    path('send/<int:content_type>/<int:pk>/', VIEWS_SCHEDULE_OBJECT, name='mailchimp_schedule_for_object'),
    path('test/<int:content_type>/<int:pk>/', VIEWS_TEST_OBJECT, name='mailchimp_test_for_object'),
    path('test/<int:content_type>/<int:pk>/real/', test_real, name='mailchimp_real_test_for_object'),
    path('info/<campaign_id>/', VIEWS_INFO, name='mailchimp_campaign_info'),
    path('dequeue/<int:id>/', dequeue, name='mailchimp_dequeue'),
    path('cancel/<int:id>/', cancel, name='mailchimp_cancel'),
    path('webhook/<key>/', webhook, name='mailchimp_webhook'),
]
