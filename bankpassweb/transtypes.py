class TransType(object):
	@classmethod
	def parse(self, code):
		for tt_class in self.__subclasses__():
			try:
				if tt_class.code == code:
					return tt_class(code)
			except AttributeError:
				pass
		return UnknownTransType(code)
		
	def __init__(self):
		name = self.__name__
		
class SSL(TransType):
	code = '01'

class SSL(TransType):
	code = 'TT01'

class BPPagoBancomat(TransType):
	code = 'TT04'

class BPCreditCard(TransType):
	code = 'TT05'

class VBV(TransType):
	code = 'TT06'

class SecureCode(TransType):
	code = 'TT07'

class VBV_Shop(TransType):
	code = 'TT08'

class SecureCode_Shop(TransType):
	code = 'TT09'

class VBV_Unident_Owner(TransType):
	code = 'TT10'

class MailPhoneOrder(TransType):
	code = 'TT11'
	
class UnknownTransType(TransType):
	def __init__(self, code):
		self.code = code
		self.name = 'Unknown transaction type %s' % code
