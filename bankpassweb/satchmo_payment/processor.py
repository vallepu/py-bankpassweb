import logging

from django.core import urlresolvers
from django.contrib.sites.models import Site
from django.utils.translation import get_language

from bankpassweb.datatypes import Currency
from bankpassweb.engine import Engine

log = logging.getLogger('bankpassweb.satchmo_payment.processor')


class PaymentProcessor(object):
	"""
	PaymentProcessor handles transactions with BankPass Web.
	"""
	def __init__(self, settings):
		"""
		Check if we are in test or live mode, and build a suitable
		transaction engine.
		"""
		self.settings = settings
		if settings.LIVE.value:
			init = {
				'env': settings.CONNECTION.value,
				'crn': settings.CRN.value,
				'start_secret': settings.TRANKEY.value,
				'result_secret': settings.RESULTKEY.value,
			}
		else:
			init = {
				'env': settings.CONNECTION_TEST.value,
				'crn': settings.CRN_TEST.value,
			 	'start_secret': settings.TRANKEY_TEST.value,
				'result_secret': settings.RESULTKEY_TEST.value,
			}
		self.engine = Engine(settings=init)
		
	def _is_live(self):
		return self.settings.LIVE.value
	live = property(_is_live)
	
	def id_prefix(self, order):
		"""
		Adds a custom prefix (taken from the configuration) to the
		order ID.  This is useful to distinguish our orders when
		using BankPass Web's backoffice website and tools.
		"""
		
		return self.settings.ORDER_PREFIX.value + unicode(order.id)
	
	def string_from_amount(self, amount):
		"""
		Takes the Decimal representing the amount and turns it into
		a string after shifting the decimal point according to the
		configuration.
		"""
		return str(int(amount * (10**self.settings.SHIFT_DIGITS.value)))
	
	def prepare_data(self, data):
		"""
		Prepare all data for the payment system. Order and Amount are
		generated beforehand for clarity:
		``order`` is made out of the chosen prefix and the order's ID;
		``amount`` is a string representation of the Decimal ``balance``
		after appropriately shifting the decimal point.
		"""
		amount = str(int(data.balance * 
			(10**self.settings.SHIFT_DIGITS.value)))
		self.transaction_data = {
			'first_name': data.contact.first_name,
			'last_name': data.contact.last_name,
			'order_id': self.id_prefix(data),
			'amount': self.string_from_amount(data.balance),
			'currency': Currency(self.settings.CURRENCY.value),
			'customer_email': data.contact.email,
		}
	
	def _get_start_url(self):
		def complete_url(partial_url):
			return 'http://%s%s' % (Site.objects.get_current(), partial_url)
		def rurl(name):
			"""
			Returns the resolution of a config parameter value, taken as
			a view name, into an URL.
			"""
			try:
				view_name = getattr(self.settings, name).value
			except AttributeError:
				view_name = name
			return complete_url(urlresolvers.reverse(view_name))

		data = self.transaction_data.copy()

		# Pick a language.  BankPass Web has a few of them available,
		# and their names are completely non-standard.
		bankpassweb_lang_map = {
			'en': 'EN',
			'it': 'ITA',
			'es': 'SPA',
			'de': 'DEU',
			'fr': 'FRA',
		}
		try:
			language = bankpassweb_lang_map[get_language()]
		except KeyError:
			language = 'EN'

		data.update({
			'urldone': rurl('SUCCESS_RETURN_ADDRESS'),
			'urlback': rurl('FAILURE_RETURN_ADDRESS'),
			'urlms': rurl('BANKPASSWEB_satchmo_checkout-ipn'),
			'tcontab': 'I',
			'tautor': 'I',
			'language': language,
			})
		return self.engine.generate_start(**data)
	start_url = property(_get_start_url)
	
	def parse_answer(self, query_string):
		return self.engine.parse_answer(query_string)