from datatypes import Parsable, DataTree, ResultType
from mx.DateTime.ISO import ParseDateTime
from datatypes import *


class ResultFactory(object):
	"""
	Generates Result (sub)classes that already know their Engine.
	"""
	def __init__(self, engine):
		self.engine = engine
	def __getattr__(self, attr, default=None):
		for klass in Result.__subclasses__():
			if attr == klass.__name__:
				kls = klass
				continue
		if not kls:
			if attr == 'Result':
				kls = Result
		if not kls:
			raise AttributeError, 'Result class %s not found' % attr
		newclass = kls.copy()
		newclass.engine = self
		return newclass

class Result(DataTree):
	"""
	This is the base class for any result coming from the XML API's.
	
	Its parse() classmethod automatically creates an instance of the most
	specific matching classtype.
	"""
	macfields = ('Timestamp', 'Esito')
	def __init__(self, xml, engine=None):
		self.xml = xml
		self.engine = engine
		self.type = ResultType.parse(str(xml.Esito))
		self.timestamp = ParseDateTime(str(xml.Timestamp))
		self.check_mac()
		for el in xml.Dati:
			self.add_data(el)
				
	def add_data(self, el):
		"""
		Turn a XML element into a class attribute as needed.
		"""
		from apirequests import Request
		node = DataTree.parse(el._name, xml=el, engine=self.engine)
		if isinstance(node, Request):
			self.request = node
		elif isinstance(node, Authorization):
			if hasattr(self, 'auth_list'):
				self.auths.append(node)
			else:
				assert not hasattr(self, 'auth')
				self.auth = node
		elif isinstance(node, AccountingOp):
			if hasattr(self, 'op_list'):
				self.ops.append(node)
			else:
				assert not hasattr(self, 'op')
				self.op = node
		elif isinstance(node, CreditRestoreResult):
			self.credit_restore = node
		elif isinstance(node, FormerResultCheck):
			self.former_req = node
		elif isinstance(node, AcctOpList):
			self.op_list = node
			self.ops = []
		elif isinstance(node, AuthListTag) or isinstance(
			node, OrderStatus):
			self.auth_list = node
			self.auths = []
		else:
			raise "Not implemented yet", el._name
			
	def check_mac(self):
		"""
		Make sure that the MAC for the root element is correct.
		"""
		self.engine.mac_ok('%s&%s' % (str(self.xml.Timestamp), str(self.xml.Esito)),
			mac=str(self.xml.MAC))
	

class Authorization(DataTree):
	"""
	This class represents an <Autorizzazione/> XML node.
	"""
	xmltag = 'Autorizzazione'
#	@classmethod
#	def parse(cls, xml, **kwargs):
#		return cls(xml, **kwargs)
		
	macfields = ('Tautor', 'IDtrans', 'Circuito', 'NumOrdine', 'ImportoTrans',
		'ImportoAutor', 'Valuta', 'ImportoContab', 'EsitoTrans',
		'Timestamp', 'NumAut', 'AcqBIN', 'CodiceEsercente', 'Stato')
	
	
	def __init__(self, *args, **kwargs):
		super(Authorization, self).__init__(*args, **kwargs)

		auth = self.xml
		from cards import Card
		self.payment_type = PaymentType.parse(str(auth.TipoPag))
		self.type = AuthType.parse(str(auth.Tautor))
		self.id = str(auth.IDtrans)
		self.circuit = Card.parse(str(auth.Circuito))
		self.order_id = str(auth.NumOrdine)
		self.trans_amount = Amount.parse(str(auth.ImportoTrans))
		self.auth_amount = Amount.parse(str(auth.ImportoAutor))
		self.currency = Currency.parse(str(auth.Valuta))
		self.acct_amount = Amount.parse(str(auth.ImportoContab))
		self.result = TransResult.parse(str(auth.EsitoTrans))
		self.timestamp = ParseDateTime(str(auth.Timestamp))
		self.auth_num = str(auth.NumAut)
		self.acquirer_bin = str(auth.AcqBIN)
		self.merchant = str(auth.CodiceEsercente)
		self.status = AuthStatus.parse(str(auth.Stato))
	
class AccountingOp(DataTree):
	"""
	This class represents an accounting transaction.
	"""
	xmltag = 'OperazioneContabile'
	macfields = ('IDtrans', 'TimestampRic', 'TimestampElab',
		'TipoOp', 'Importo', 'Esito', 'Stato')
	
	def __init__(self, *args, **kwargs):
		super(AccountingOp, self).__init__(*args, **kwargs)
		xml = self.xml
		self.id = str(xml.IDtrans)
		self.request_ts = ParseDateTime(str(xml.TimestampRic))
		self.processing_ts = ParseDateTime(str(xml.TimestampElab))
		self.type = OperationType.parse(str(xml.TipoOp))
		self.amount = Amount.parse(str(xml.Importo))
		self.status = AcctStatus.parse(str(xml.Stato))
		self.auth = DataTree.parse(xml.Autorizzazione._name,
			xml=xml.Autorizzazione, engine=self.engine)
			
class CreditRestoreResult(DataTree,BPWDataType):
	"""
	Whether the credit card's limit was correctly restored.
	"""
	xmltag = 'EsitoRipristinoPlafond'
	lookup_attribute = 'code'
		
class RestoreSuccessful(CreditRestoreResult):
	code = '00'

class FormerResultCheck(DataTree):
	"""
	The result code for a former request.
	"""
	xmltag = 'Verifica'
	macfields = ('TipoRichiesta', 'Esito', 'IDTrans')
	@classmethod
	def parse(cls, xml, **kwargs):
		return cls(xml, **kwargs)
	def __init__(self, *args, **kwargs):
		super(FormerResultCheck, self).__init__(*args, **kwargs)
		xml = self.xml
		self.type = FormerRequestType.parse(str(xml.TipoRichiesta))
		self.result = ResultType.parse(str(xml.Esito))
		self.id = str(xml.IDTrans)

class FormerRequestType(DataTree):
	"""
	The type for a former request.
	"""
	xmltag = 'TipoRichiesta'
	lookup_attribute = 'code'
	@classmethod
	def parse(cls, xml, **kwargs):
		from apirequests import (Authorize, CloseAuth, WriteOff,
			Account, CancelAccounting, Split)
		return {'01': Authorize, '02': CloseAuth, '03': WriteOff,
			'04': Account, '05': CancelAccounting, '06': Split}[
			str(xml)]
	def __init__(self):
		pass
		
class QuantityTag(DataTree):
	"""
	Base class for tags whose 'NumeroElementi' attribute indicates
	how many nodes of a given kind must be expected.
	"""
	def __init__(self, xml, **kwargs):
		super(QuantityTag, self).__init__(xml, **kwargs)
		self.qty = self.xml('NumeroElementi')
class AcctOpList(QuantityTag):
	xmltag = 'ElencoOperazioniContabili'
class AuthListTag(QuantityTag):
	xmltag = 'ElencoAutorizzazioni'
class OrderStatus(QuantityTag):
	xmltag = 'SituazioneOrdine'
