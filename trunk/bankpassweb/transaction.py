class Transaction(object):
	@classmethod
	def parse(cls, params):
		return Transaction(params)
		
	def __init__(self, params):
		try:
			from result import Result
			from cards import Card
			self.order_id = params['NUMORD']
			self.crn = params['IDNEGOZIO']
			self.auth = params['AUT']
			if self.auth == 'NULL':
				self.auth = None
			self.amount = params['IMPORTO']
			self.currency = params['VALUTA']
			self.trans_id = params['IDTRANS']
			self.result = Result.parse(params['ESITO'])
			self.auth_type = params['TAUTOR']
			self.cont_type = params['TCONTAB']
			self.card = Card.parse(params['CARTA'])
		except KeyError, e:
			raise BPWProtocolException(e)
		if 'BPW_TRANSACTION_TYPE' in params:
			from transtypes import TransType
			self.trans_type = TransType.parse(
				params['BPW_TRANSACTION_TYPE'])
		if 'BPW_ISSUER_COUNTRY' in params:
			self.issuer_country = params['BPW_ISSUER_COUNTRY']
	
	def verbose(self):
		return unicode(self.__dict__)