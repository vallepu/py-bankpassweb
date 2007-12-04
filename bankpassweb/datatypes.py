from bpwexceptions import *
from mx.DateTime.ISO import ParseDate
from datetime import date
class Parsable(object):
	"""
	Base class for all types that can be parsed. By default, the
	'parse' method returns a specific subclass.
	"""
	lookup_attribute = 'code'
	@classmethod
	def parse(cls, *args, **kwargs):
		return general_parser(cls, *args, **kwargs)
	@classmethod
	def parse_init(cls, *args, **kwargs):
		return cls(*args, **kwargs)
	def __repr__(self):
		if hasattr(self, self.lookup_attribute):
			return self.__class__.__name__ + '()'
		elif hasattr(self, '_val'):
			return str(self._val())
		else:
			return '%s.parse(%s)' % (self.__class__.__name__,
				self._value)

def general_parser(cls, value, attr=None, 
	builder='parse_init', *args, **kwargs):
	"""
	Take 'lookup_attribute' as the name of the attribute which,
	in subclasses, holds the value to be matched.
	Then, build a queue with all the subclasses and look for it.
	When the subclass is found, build an instance.
	"""
	if not attr:
		attr = cls.lookup_attribute
	class_queue = [cls]
	while len(class_queue) > 0:
		klass = class_queue[0]
		class_queue = class_queue[1:]
		match = getattr(klass, attr, None)
		if (match == value or isinstance(match, tuple) and
			value in match):
			if builder:
				return getattr(klass, builder)(*args, **kwargs)
			else:
				return klass
		class_queue.extend(klass.__subclasses__())
		
	for klass in cls.__subclasses__():
		if getattr(klass, 'default_option', None):
			return klass(*args, **kwargs)
	raise BPWParmException("Missing default option for class %s, and cannot find" \
		" subclass with value %s" % (cls, value))

#def general_typelist_generator(cls, attr):
#	return dict([(getattr(klass, attr), klass) for klass in
#		cls.__subclasses__()])

class BPWDataType(Parsable):
	"""
	Base class for data types exchanged in BankPass Web HTTP messages.
	Subclasses provide the _val() method, returning a useful expression
	for further manipulation, and the _encoded() method, returning
	the value in a format for HTTP exchange.
	"""
	default_lookup = 'fieldname'
	@classmethod
	def parse(cls, *args, **kwargs):
		"Initialize normally"
		return super(BPWDataType, cls).parse(*args, **kwargs)
	def _encoded(self):
		return self._value
	def __getattr__(self, attr, *args):
		if attr == 'val':
			return self._val()
		elif attr == 'encoded':
			return self._encoded()
		else:
			return super(BPWDataType, self).__getattribute__(attr, *args)

class Subclassed(BPWDataType):
	"""
	Base class for data types that are parsed by picking a certain
	subclass.
	"""
	lookup_attribute = 'code'
	@classmethod
	def parse(cls, *args, **kwargs):
		"Look for subclass"
		return general_parser(cls, *args, **kwargs)
	def _encoded(self):
		return getattr(self, self.lookup_attribute)
	def __init__(self, value=None):
		if value:
			assert value == getattr(self, self.lookup_attribute)
	def __eq__(self, other):
		return self.__class__ == other.__class__
		
		
class Valued(BPWDataType):
	"""
	Base class for types that are parsed by initializing the instance
	with the provided values.
	"""
	@classmethod
	def parse(cls, *args, **kwargs):
		return cls(*args, **kwargs)

class Date(Valued):
	"""
	A date. The encoded format is the ISO format.
	"""
	fieldname = ('DATAINIZIO', 'DATAFINE')	
	
	def __init__(self, ini):
		if isinstance(ini, str):
			self._value = ini
		elif isinstance(ini, date):
			self._value = ini.isoformat()
		else:
			raise TypeError('%s not recognized as a date' % ini)
	def _val(self):
		return ParseDate(self._value)
			

class DataTree(Parsable):
	"""
	Base class for an XML tree representing some kind of data.
	"""
	lookup_attribute = 'xmltag'
	def __init__(self, xml, engine):
		self.xml = xml
		self.engine = engine
		if hasattr(self, 'macfields'):
			self.engine.mac_ok([getattr(self.xml, field) for field in 
				self.macfields], mac=str(self.xml.MAC))
	@classmethod
	def parse(cls, xml, **kwargs):
		"""
		Default parser. Just parse the string, if not already done,
		and use it to build a class instance.
		"""
		import xmltramp
		if not isinstance(xml, xmltramp.Element):
			xml = xmltramp.parse(xml)
		kwargs['xml'] = xml
		return general_parser(cls, xml._name, 'xmltag', **kwargs)
				
	def _debugging_dict(self):
		tmp = self.__dict__
		try:
			del tmp['xml']
		except KeyError:
			from apirequests import Request
			if not isinstance(self, Request):
				raise TypeError('xml attribute missing in %s instance' %
					self.__class__.__name__)
		return tmp
	def __repr__(self):
		return '<%s: %s>' % (self.__class__.__name__,
			self._debugging_dict())
	
		

class Amount(Valued):
	"""
	An amount of money.  The encoded form is a string with an integer
	representing the smallest admissible value (e.g. cents).
	"""
	fieldname = 'IMPORTO'
	def __init__(self, amount):
		from decimal import Decimal
		if isinstance(amount, float):
			self._value = str(int(amount*100))
		elif isinstance(amount, Decimal):
			self._value = str(int(amount*Decimal(100)))
		elif isinstance(amount, str):
			self._value = amount
		else:
			raise TypeError('Invalid argument %s for Amount' % amount)
	def _val(self):
		return float(self._value)/100.0

class Currency(BPWDataType):
	"""
	A currency.  The encoded form is the ISO numeric code.
	"""
	fieldname = 'VALUTA'
	ISOCURR = {'EUR': 978}
	@classmethod
	def parse(cls, value):
		return cls(value)
	def __init__(self, currency):
		if isinstance(currency, str) and currency.isalpha():
			try:
				self._value = self.ISOCURR[currency]
			except KeyError:
				raise TypeError('Unknown code %s for Currency' % currency)
		elif isinstance(currency, int) or currency.isdigit():
			self._value = currency
		else:
			raise TypeError('Invalid argument %s for Currency' % currency)
	def _val(self):
		return self._value

def auth_acct_init(self, char=None, immediate=None, deferred=None):
	if immediate and deferred:
		raise TypeError
	if char and (immediate or deferred):
		raise TypeError
	if char in ('I', 'D'):
		self._value = char
	elif char is not None:
		raise TypeError
	elif immediate:
		self._value = 'I'
	elif deferred:
		self._value = 'D'
	else:	
		raise TypeError


class AcctType(Subclassed):
	"""
	An accounting type. The encoded form is 'I' for immediate,
	'D' for deferred.
	"""
	fieldname = 'TCONTAB'
	default_lookup = 'code'
#	@classmethod
#	def parse(cls, *args, **kwargs):
#		try:
#			auth_acct_init(self, self.code, *args, **kwargs)
#		except AttributeError:
#			auth_acct_init(self, *args, **kwargs)
#	def __init__(self):
#		if not hasattr(self, 'code'):
#			raise TypeError
class DeferredAcct(AcctType):
	code = 'D'
class ImmediateAcct(AcctType):
	code = 'I'

class PaymentType(Subclassed):
	"""
	A type of payment.
	"""
	xmltag='TipoPag'
	fieldname = 'TIPOPAG'
	shop_vbv = False
	customer_vbv = False
	shop_securecode = False
	customer_securecode = False
class BankpassWebB2C(PaymentType):
	code = '01'
class BankpassMobileB2C(PaymentType):
	code = '02'
class SSLPayment(PaymentType):
	code = '03'
class BothVBV(PaymentType):
	code = '04'
	shop_vbv = True
	customer_vbv = True
class BothSecureCode(PaymentType):
	code = '05'
	shop_securecode = True
	customer_securecode = True
class ShopVBV(PaymentType):
	code = '06'
	shop_vbv = True
class ShopSecureCode(PaymentType):
	code = '07'
	shop_securecode = True
class IncorrectCustomerAuthVBV(PaymentType):
	code = '08'
	customer_vbv = 'Incorrect'
class UnknownPaymentType(PaymentType):
	default_option = True
	
class AuthType(Subclassed):
	"""
	A type of payment authorization. The encoded form is the same as
	in AcctType.
	"""
	xmltag = 'Tautor'
	fieldname = 'TAUTOR'
	def __init__(self, *args, **kwargs):
		try:
			auth_acct_init(self, self.code, *args, **kwargs)
		except AttributeError:
			auth_acct_init(self, *args, **kwargs)
class ImmediateAuth(AuthType):
	code = 'I'
class DeferredAuth(AuthType):
	code = 'D'

class TransResult(Parsable):
	"""
	The result for an authorization transaction, as found in an
	Authorization class.
	"""
	pass
class TransSuccess(TransResult):
	code = '00'
class TransDeniedReqProblems(TransResult):
	code = '01'
class TransDeniedServiceProblems(TransResult):
	code = '02'
class TransDeniedCircuitDown(TransResult):
	code = '03'
class TransDeniedByIssuer(TransResult):
	code = '04'
class TransDeniedWrongCardNumber(TransResult):
	code = '05'
class TransWTF(TransResult):
	code = '06'
	
class AuthStatus(Parsable):
	"""
	The status of an authorization request.
	"""
	lookup_attribute = 'code'
class AuthGranted(AuthStatus):
	code = '00'
class AuthDenied(AuthStatus):
	code = '01'
class AuthAccountedNotProcessed(AuthStatus):
	code = '02'
class AuthAccountedCleared(AuthStatus):
	code = '03'
class AuthRevoked(AuthStatus):
	code = '04'
class RevokingDenied(AuthStatus):
	code = '05'
class RevokingNotProcessed(AuthStatus):
	code = '20'
class AuthErrorMustRevoke(AuthStatus):
	code = '21'
class DeferredAuthOpened(AuthStatus):
	code = '10'
class DeferredAuthClosed(AuthStatus):
	code = '11'
	

class ResultType(Subclassed):
	"""
	The result of an API Request.
	"""
	pass
class Success(ResultType):
	code = '00'
class DataNotFound(ResultType):
	code = '01'
class DuplicateReqID(ResultType):
	code = '02'
class RequestFormatError(ResultType):
	code = '03'
class AuthenticationError(ResultType):
	code = '04'
class DateError(ResultType):
	code = '05'
class ProcessingError(ResultType):
	code = '06'
class TransIDNotFound(ResultType):
	code = '07'
class OperatorNotFound(ResultType):
	code = '08'
class TransactionOrderMismatch(ResultType):
	code = '09'
class AmountTooHigh(ResultType):
	code = '10'
class StateError(ResultType):
	code = '11'
class ShopRecordError(ResultType):
	code = '12'
class DuplicateOrder(ResultType):
	code = '13'
class B2COrderNotFound(ResultType):
	code = '32'
class WalletNotFound(ResultType):
	code = '33'
class InactiveWallet(ResultType):
	code = '34'
class ValidPaymentNotFound(ResultType):
	code = '35'
class OrderDateRangeError(ResultType):
	code = '36'
class ApplicationError(ResultType):
	code = '98'
class OpFailure(ResultType):
	code = '99'

class OperationType(Parsable):
	"""
	The type of an accounting operation, as found in an AccountingOp
	instance.
	"""
	pass
class AuthWriteOff(OperationType):
	code = '01'
class Credit(OperationType):
	code = '02'
class AcctCancellation(OperationType):
	code = '03'
class AcctOperation(OperationType):
	code = '04'
	
class AcctStatus(Parsable):
	"""
	The status of an accounting operation.
	"""
	pass
class AcctSuccess(AcctStatus):
	code = '00'
class AcctFailure(AcctStatus):
	code = '01'
		
class AuthFilterType(Subclassed):
	"""
	The filter for an AuthorizationList request.
	"""
	fieldname = 'FILTRO'
	xmltag = 'Filtro'
class GrantedAuths(AuthFilterType):
	code = '1'
class DeniedAuths(AuthFilterType):
	code = '2'
class CancelledAuths(AuthFilterType):
	code = '3'
class AllAuths(AuthFilterType):
	code = '4'
