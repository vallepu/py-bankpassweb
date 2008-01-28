from django.conf.urls.defaults import *

from satchmo.configuration import config_get_group

# Import our own module's views
import views

config = config_get_group('PAYMENT_BANKPASSWEB')

urlpatterns = patterns('satchmo',
     (r'^$', views.pay_ship_info, {'SSL': config.SSL.value}, 'BANKPASSWEB_satchmo_checkout-step2'),
     (r'^confirm/$', views.confirm_info, {'SSL': config.SSL.value}, 'BANKPASSWEB_satchmo_checkout-step3'),
     (r'^success/$', views.success, {'SSL': config.SSL.value}, 'BANKPASSWEB_satchmo_checkout-success'),
     (r'^ipn/$', views.ipn, {'SSL': config.SSL.value}, 'BANKPASSWEB_satchmo_checkout-ipn'),
)
