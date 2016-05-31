from django.contrib import admin
from solo.admin import SingletonModelAdmin
from .models import SiteConfiguration
from .models import TransferApproval, Qap, Country, Supplier, Species, Imagetype, Location, Wastetype, Deathtype
from .forms import SiteConfigurationForm
# Register your models here.
class QapInline(admin.TabularInline):
    model = Qap

class TransferApprovalAdmin(admin.ModelAdmin):
    #inlines = [QapInline,]

    pass

class SiteConfigurationAdmin(SingletonModelAdmin):
    form = SiteConfigurationForm
    fieldsets = [
        ('Site', {'fields': ('site_name', 'maintenance_mode')}),
        ('Operations', {'fields': ('max_ops', 'op_interval')}),
        ('Report', { 'fields': ('report_location','report_contact_details', 'report_general_notes',)})
    ]


admin.site.register(SiteConfiguration, SiteConfigurationAdmin)
admin.site.register(TransferApproval, TransferApprovalAdmin)
admin.site.register(Qap)
admin.site.register(Country)
admin.site.register(Supplier)
admin.site.register(Species)
admin.site.register(Imagetype)
admin.site.register(Location)
admin.site.register(Wastetype)
admin.site.register(Deathtype)
