from datatypes import Parsable

class Card(Parsable):
	def __init__(self):
		self.name = self.__class__.__name__

class Visa(Card):
	code = '01'

class Mastercard(Card):
	code = '02'

class Amex(Card):
	code = '03'
	
class Diners(Card):
	code = '06'
	
class JCB(Card):
	code = '08'

class PagoBancomat(Card):
	code = '09'
	
class CartaAura(Card):
	code = '10'
	
class UnknownCard(Card):
	def __init__(self, code):
		self.code = code
		self.name = 'Unknown card %s' % code

	