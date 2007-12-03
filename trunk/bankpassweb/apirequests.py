from datatypes import Parsable, DataTree, general_parser, BPWDataType, Date
from bpwexceptions import *

class RequestFactory(object):
	"""
	This class is used in the Engine to generate effortlessly
	new Request classes (actually, subclasses of Request, which
	perform actual tasks). These classes already have the 'engine'
	parameter set in their constructor.
	"""
	def __init__(self, engine):
		self.engine = engine
	def __getattr__(self, attr, default=None):
		klass= general_parser(Request, attr, '__name__', 
			builder=None)
		def wrapper(*args, **kwargs):
			kwargs['engine'] = self.engine
			return klass(*args, **kwargs)
		return wrapper
			
		
class Request(DataTree):
	"""
	Request is the base class for all API requests to BankPass Web.
	No actual request is performed by constructing a Request object.
	Nevertheless, 
	- kwmappings acts as a repository for mappings that
	are valid across all requests;
	- macfields only those field names that make up the first fields
	of most MAC calculations, and they are taken advantage of in base
	classes.
	"""
	# These are the first fields for most MACs
	macfields = ('OPERAZIONE', 'TIMESTAMP', 'IDNEGOZIO', 'OPERATORE',
		'REQREFNUM')
	reqfields = []
	optfields = []
	kwmappings = {'req_id': 'REQREFNUM', 'trans_id': 'IDTRANS', 'order_id':
		'NUMORD', 'amount': 'IMPORTO', 'cont_type': 'TCONTAB',
		'former_req_id': 'REQREFNUMORIG', 'start': 'DATAINIZIO', 
		'end': 'DATAFINE', 'currency': 'VALUTA',
		'close_order': 'FINEORDINE', 'filter': 'FILTRO'}
	lookup_attribute = 'xmltag'
	def add_if_missing(self, fieldtag, value):
		"""
		Adds a parameter to the class instance iff it has not been
		already specified.
		"""
		if not fieldtag in self.params:
			self.params[fieldtag] = value
			

	def __prepare_for_req(self, fieldname, val):
		"""
		Converts a single value into a string, ready for being sent
		over HTTP.
		If the value is already an instance of BPWDataType, then its
		encoded form is returned.
		If it isn't, then we try to find its appropriate class based
		on 'fieldname'; we build an instance and then return the encoded
		form.
		If we can't build a BPWDataType instance, then we just return
		the value itself.
		"""
		# Discover data type
		if isinstance(val, BPWDataType):
			return val.encoded
		from bpwexceptions import BPWParmException
		try:
			k = None				
			k = BPWDataType.parse(fieldname, attr='fieldname',
				builder=None)
		except BPWParmException:
			pass
		if k:
			return k.parse(val).encoded
		return val

	def __init__(self, engine=None, params=None, xml=None,
		blankfields=[], **kwargs):
		"""
		__init__() takes arguments provided by the subclasses and builds
		the relevant data structures.
		The 'engine' kw parameter is always set.
		If we have a 'xml' keyword parameter, then the request is a
		'receipt' object returned by the application server.
		Otherwise, we clear blank fields and we process each remaining
		kw parameter by looking up the matching HTTP query string
		parameter and preparing it.
		"""
		self.engine = engine
		
		if xml:
			self.__init_from_xml(xml)
			return
		
		# This seems silly, but it does not work otherwise
		if params:
			self.params = params
		else:
			self.params = {}
			
		for f in blankfields:
			self.params[f] = ''
		
		# Process arguments
		for arg in kwargs:
			try:
				fieldname = self.kwmappings[arg]
			except KeyError:
				raise TypeError('%s parameter unknown to Request '
					'classes' % arg)
			
			if not self._has_field(fieldname):
				raise TypeError('%s got an unexpected '
					'keyword parameter ''%s''' % (self.__class__.__name__,
					arg))
			assert fieldname not in self.params, \
				"%s is already here -- why?" % fieldname
			self.params[fieldname] = self.__prepare_for_req(fieldname,
				kwargs[arg])
		
		# Take care of standard fields
		self.add_if_missing('OPERAZIONE', self.opname)
		from datetime import datetime
		self.add_if_missing('TIMESTAMP', 
			datetime.now().isoformat()[:23])
		self.add_if_missing('IDNEGOZIO', self.engine.crn)
		self.add_if_missing('OPERATORE', self.engine.operator)
		from uuid import uuid4
		self.add_if_missing('REQREFNUM', 
			('0'*32 + str(int(uuid4().int % 10E31)))[-32:]
		)		

	def __set_if_present(self, tag, attr, valtype=None):
		"""
		Sets an instance attribute from a XML tree.
		If 'tag' is present in self.xml, then we extract its value,
		parse it as a 'valtype' object if possible, and set the
		'attr' attribute in our instance.
		"""
		try:
			val = str(getattr(self.xml, tag))
		except AttributeError:
			return
		if valtype:
			try:
				val = valtype.parse(val)
			except AttributeError:
				raise ("Parse method not available for object %s, "
					"type %s" % (val, valtype))
		setattr(self, attr, val)
		self.parsedtags.append(tag)

	@classmethod
	def parse_init(cls, xml, engine=None, *args, **kwargs):
		"""
		Create a new instance from a XML tree.
		"""
		o = object.__new__(cls)
		o.engine = engine
		o.__init_from_xml(xml=xml, *args, **kwargs)
		return o

	def __init_from_xml(self, xml):
		"""
		Create a new instance from a XML tree.
		Each mapping is made of a XML tag, an attribute name and
		an optional class.  (This is not done directly through
		classes, since some elements contain strings and have no
		specific class.)
		"""
		self.xml = xml
		header = xml.TestataRichiesta
		self.crn = str(header.IDnegozio)
		self.operator = str(header.Operatore)
		self.req_id = str(header.ReqRefNum)
		self.parsedtags = ['TestataRichiesta']
		from datatypes import (Amount, Currency, AcctType,
			AuthFilterType)
		
		mappings = (
			('IDtrans', 'trans_id'),
			('Importo', 'amount', Amount),
			('Valuta', 'currency', Currency),
			('Tcontab', 'cont_type', AcctType),
			('FineOrdine', 'close_order'),
			('DataInizio', 'start', Date),
			('DataFine', 'end', Date),
			('NumOrdine', 'order_id'),
			('ReqRefNumOrig', 'former_req_id'),
			('Filtro', 'filter', AuthFilterType),
		)
		for mapping in mappings:
			self.__set_if_present(*mapping)
		for el in self.xml:
			try:
				assert el._name in self.parsedtags
			except AssertionError:
				raise BPWException('Tag %s was not parsed '
					'in receipt for request %s' % (el._name,
					self.__class__.__name__))
										
	def _qs(self):
		"""
		Add the MAC parameter and return the final, NOT urlencoded,
		querystring.
		"""
		self.params['MAC'] = self.engine.compute_mac(self.params,
			self.reqfields, self.optfields, api=True,
			secret=self.engine.result_secret)
		return '&'.join(['='.join((par, str(self.params[par])),)
			for par in self.params])
		
	def send(self):
		"""
		Send the request over HTTP to the designated server, and return
		a parsed XML tree of the answer.
		"""
		self._validate_params()
		from urllib import urlopen
		qs = self._qs()
		call = urlopen(self.engine.env_api + '?' + qs)
		from xmltramp import parse
		return parse(call.read())
	
	def _validate_params(self):
		"""
		Check that all parameters in the dictionary belong
		to the request.
		"""
		for fieldlist in (self.reqfields, self.optfields):
			for fieldname in fieldlist:
				assert fieldname in self.params, '%s is missing' % fieldname
	
	def _has_field(self, name):
		"""
		Check that the given field name is actually one of the
		designated request fields.
		"""
		return name in self.reqfields or name in self.optfields
			
class Authorize(Request):
	"""
	After a deferred authorization has been requested, ask for a certain
	amount of money to be authorized.
	"""
	opname = 'RICHIESTAAUTORIZZAZIONE'
	xmltag = 'RicAutorizzazione'
	macfields = Request.macfields + ('IDTRANS', 'NUMORD', 'IMPORTO',
		'VALUTA', 'TCONTAB', 'FINEORDINE')
	reqfields = macfields
	
	@classmethod
	def parse(cls, xml, **kwargs):
		req = cls(xml.IDtrans, xml.Importo, xml.Valuta, 
			cont_type=xml.Tcontab, close_order=xml.FineOrdine)
	
	def __init__(self, trans_id, order_id, amount, currency, **kwargs):
		kwargs['order_id'] = order_id
		kwargs['amount'] = amount
		kwargs['trans_id'] = trans_id
		kwargs['currency'] = currency
		if not 'cont_type' in kwargs:
			kwargs['cont_type'] = 'I'
		if not 'close_order' in kwargs:
			kwargs['close_order'] = 'N'
		super(Authorize, self).__init__(**kwargs)

class ReqTransOrder(Request):
	"""
	Base class for all requests involving a transaction ID and
	an order ID.
	"""
	macfields = Request.macfields + ('IDTRANS', 'NUMORD')
	reqfields = macfields
	
	def __init__(self, trans_id, order_id, **kwargs):
		"""
		@param trans_id: Transaction ID (provided by the acquirer)
		@param order_id: Order ID (generated by the merchant)
		"""
		kwargs['trans_id'] = trans_id
		kwargs['order_id'] = order_id
		super(ReqTransOrder, self).__init__(**kwargs)

class ReqTransOrderAmount(Request):
	"""
	Base class for all requests involving a transaction ID,
	an order ID, an amount of money and a currency.
	"""
	macfields = Request.macfields + ('IDTRANS', 'NUMORD', 'IMPORTO',
		'VALUTA')
	reqfields = macfields
	def __init__(self, trans_id, order_id, amount, currency, **kwargs):
		kwargs['trans_id'] = trans_id
		kwargs['order_id'] = order_id
		kwargs['amount'] = amount
		kwargs['currency'] = currency
		super(ReqTransOrderAmount, self).__init__(**kwargs)

class CloseAuth(ReqTransOrder):
	"""
	Close an order so that no more money can be authorized.
	"""
	opname = 'CHIUSURADIFFERITA'
	xmltag = 'RicChiusuraAutorizzazione'

class Account(ReqTransOrderAmount):
	"""
	Account an amount of money belonging to a successful authorization.
	The transaction ID is that of the authorization to be charged.
	"""
	opname = 'CONTABILIZZAZIONE'
	xmltag = 'RicContabilizzazione'

class CancelAccounting(ReqTransOrder):
	"""
	Cancel an accounting operation. The transaction ID is that of the
	accounting operation itself.
	"""
	opname = 'ANNULLAMENTOCONTABILIZZAZIONE'
	xmltag = 'RicAnnullamentoContabilizzazione'
		
class WriteOff(ReqTransOrderAmount):
	"""
	Write off, totally of partially, a sum of money that was authorized
	or authorized and accounted.
	"""
	opname = 'STORNO'
	xmltag = 'RicStorno'

class Split(ReqTransOrder):
	"""
	Split an existing order. Any immediate authorization is changed
	into a deferred one.
	"""
	opname = 'SPLIT'
	xmltag = 'RicSplit'
	
class FormerResult(Request):
	"""
	Get the result code for a former operation.
	"""
	opname = 'VERIFICA'
	xmltag = 'RicVerifica'
	macfields = Request.macfields + ('REQREFNUMORIG',)
	reqfields = macfields
	def __init__(self, former_req_id, **kwargs):
		kwargs['former_req_id'] = former_req_id
		super(FormerResult, self).__init__(**kwargs)
		
class TransactionList(Request):
	"""
	Get a list of the accounting operations performed within the
	requested date range.
	"""
	opname = 'ELENCOCONTABILE'
	xmltag = 'RicElencoOperazioniContabili'
	macfields = Request.macfields + ('DATAINIZIO', 'DATAFINE')
	reqfields = macfields
	def __init__(self, start, end, **kwargs):
		kwargs['start'] = start
		kwargs['end'] = end
		super(TransactionList, self).__init__(**kwargs)
		
class AuthList(Request):
	"""
	Get the list of the authorizations issued or denied. They may be
	filtered by date range or by type.  Otherwise, an authorization ID
	can be requested; the other parameteres will be ignored.
	"""
	opname = 'ELENCOAUTORIZZAZIONI'
	xmltag = 'RicElencoAutorizzazioni'
	macfields = Request.macfields + ('DATAINIZIO', 'DATAFINE', 'FILTRO', 'IDTRANS')
	reqfields = macfields
	def __init__(self, start, end, filter_n='4', **kwargs):
		kwargs['start'] = start
		kwargs['end'] = end
		kwargs['filter'] = filter_n
		kwargs['blankfields'] = ('IDTRANS',)
		super(AuthList, self).__init__(**kwargs)
	def __init__(self, trans_id, **kwargs):
		from datetime import date
		kwargs['start'] = date(2000, 12, 1)
		kwargs['end'] = date(2000,12,1)
		kwargs['filter'] = '1'
		kwargs['trans_id'] = trans_id
		super(AuthList, self).__init__(**kwargs)

class OrderStatus(Request):
	"""
	Request the status for an order This returns the relevant
	authorizations.
	"""
	opname = 'SITUAZIONEORDINE'
	xmltag = 'RicSituazioneOrdine'
	macfields = Request.macfields + ('NUMORD',)
	reqfields = macfields
	def __init__(self, order_id, **kwargs):
		kwargs['order_id'] = order_id
		super(OrderStatus, self).__init__(**kwargs)

	