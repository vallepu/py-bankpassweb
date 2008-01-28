from bpwexceptions import BPWProtocolException
import datatypes
from datatypes import Subclassed
from cards import Card

class Transaction(object):
	@classmethod
	def parse(cls, **kwargs):
		self = cls()
		for parm, value in kwargs.items():
			try:
				getattr(self, '_set_' + parm)(value)
			except:
			# do some LOGGING!
			#	raise BPWProtocolException, 'Unknown parameter %s=%s received from remote' % \
			#		(parm, value)
				pass
		return self
	def _set_NUMORD(self, val):
		self.order_id = val
	def _set_IDNEGOZIO(self, val):
		self.crn = val
	def _set_AUT(self, val):
		self.auth_id = val
	def _set_IMPORTO(self, val):
		self.amount = datatypes.Amount(val)
	def _set_VALUTA(self, val):
		self.currency = datatypes.Currency(val)
	def _set_IDTRANS(self, val):
		self.trans_id = val
	def _set_ESITO(self, val):
		self.outcome = Outcome.parse(val)
	def _set_TAUTOR(self, val):
		self.auth_type = datatypes.AuthType(val)
	def _set_TCONTAB(self, val):
		self.acct_type = datatypes.AcctType(val)
	def _set_BPW_MODPAG(self, val):
		# FIXME: use class
		self.payment_mode = val
	def _set_CARTA(self, val):
		self.card = Card.parse(val)
	def _set_BPW_TIPO_TRANSAZIONE(self, val):
		# FIXME: use class
		self.trans_type = val
	def _set_BPW_ISSUER_COUNTRY(self, val):
		self.card_country = val
	
	def _get_item_summary(self, attr, desc):
		summary = getattr(self, attr, '(unavailable)')
		print summary, type(summary)
		if hasattr(summary, '_val'):
			summary = summary._val()
		elif ((not isinstance(summary, basestring)) and
			hasattr(summary, '__class__')):
			try:
				summary = summary.__class__.__name__
			except AttributeError:
				pass
		elif hasattr(summary, '__name__'):
			summary = symmary.__name__
		return '%s: %s' % (desc, summary)
	
	def _get_summary(self):
		"""
		Provides a plain-text summary of the transaction.
		"""
		attr_map = (
		    ('outcome', 'TRX RESULT'),
			('crn', 'Shop ID (CRN)'),
			('order_id', 'Order ID'),
			('amount', 'Amount paid'),
			('payment_mode', 'Payment mode'),
			('card', 'Card'),
			('card_country', 'Issued in'),
			('currency', 'Currency'),
			('trans_id', 'Transaction ID'),
			('trans_type', 'Transaction type'),
			('auth_id', 'Authorization ID'),
			('auth_type', 'Authorization type'),
			('acct_type', 'Accounting type'),
		)
		return '\n'.join([self._get_item_summary(*x) for x in attr_map] )
	summary = property(_get_summary)
	
class Outcome(Subclassed):
	"""
	Whether or not a Transaction was successful.
	"""
class Success(Outcome):
	code = '00'
class SystemDenied(Outcome):
	code = '01'
class ShopRecordProblemDenied(Outcome):
	code = '02'
class CircuitProblemDenied(Outcome):
	code = '03'
class IssuerDeneid(Outcome):
	code = '04'
class WrongCardNumberDenied(Outcome):
	code = '05'
class OtherErrorDenied(Outcome):
	code = '06'
