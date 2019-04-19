from django.contrib import admin
from mailchimp.models import Campaign


class MailchimpAdmin(admin.ModelAdmin):
    list_display = ('campaign_id', 'name', 'sent_date', 'content_type')
    list_filter = ('sent_date',)
    search_fields = ('name',)


admin.site.register(Campaign, MailchimpAdmin)
