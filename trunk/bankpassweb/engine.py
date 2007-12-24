from urllib import urlencode, unquote_plus

from bpwexceptions import *

class Engine(object):
	"""
	The main class to generate payment links, send API requests and
	process answers.
	
	It should always know the shop ID, the operator username for
	API operations, and the secret keys for processing MACs.
	"""
	
	def __init__(self, urlback=None, urldone=None, urlms=None, 
		urlapi=None, email=None, alg=None, settings=None):
		
		# Settings
		import types
		if not settings:
			settings = __import__('settings')
		if isinstance(settings, types.ModuleType):
			settings = settings.__dict__
		for attr in ('env', 'start_secret', 'result_secret', 'env_api', 'crn', 'operator'):
			setattr(self, attr, settings[attr])
			
		# API requests
		from apirequests import RequestFactory
		from apiresults import ResultFactory
		self.req = RequestFactory(self)
		self.res = ResultFactory(self)
		
		# Shop data
		self.urlback_pattern = urlback
		self.urldone_pattern = urldone
		self.urlms_pattern = urlms
		self.email = email
		# Defaults
		if not alg:
			import sha
			self.alg=sha
		
	def compute_mac(self, params, reqfields, optfields=None,
		secret=None, alg=None, api=False):
		"Compute the MAC for an order URL."

		# Choose secret
		if not secret:
			secret = self.start_secret

		# Choose hash alg
		if not alg:
			alg=self.alg
		textparams = []
		for parm in reqfields:
			textparams.append((parm, params[parm]),)
		if optfields:
			for parm in optfields:
				if parm in params:
					textparams.append((parm, params[parm]),)
		text = urlencode(textparams)
		if api:
			text = unquote_plus(text)
		text += '&' + secret
		return alg.new(text).hexdigest()
	
	def mac_ok(self, message, reqfields=None, mac=None, optfields=None):
		"Check the MAC in an answer."
		# Do we have one?
		if mac:
			assert isinstance(message, str) or isinstance(message, list)
			string_mode = True
		else:
			try:
				mac = message['MAC']
			except KeyError:
				raise BPWCryptoException('Missing MAC in query string')
		
		# Check length to infer algorithm
		mac_length = len(mac)
		if mac_length == 32:
			import md5
			alg = md5
		elif mac_length == 40:
			import sha
			alg = sha
		else:
			raise BPWCryptoException('The MAC length is wrong, cannot'
				' guess algorithm')
		
		if string_mode:
			if isinstance(message, str):
				sigtext = message
			elif isinstance(message, list):
				sigtext = '&'.join([str(el) for el in message])
			else:
				raise TypeError, 'Unknown message type %s: %s' % (
					type(message), message)
		else:
			textparams = []
			for field in reqfields:
				try:
					textparams.append('='.join([field, params[field]]))
				except KeyError:
					raise BPWProtocolException('Required field %s is missing '
						'in the remote server''s answer' % field)
			if optfields:
				for field in optfields:
					try:
						textparams.append('='.join([field, params[field]]))
					except KeyError:
						pass
			sigtext = '&'.join(textparams)

		# Secret key
		sigtext += '&' + self.result_secret
		
		# Generate MAC
		signature = alg.new(sigtext).hexdigest()
		if signature.lower() == mac.lower():
			return True
		else:
			raise BPWCryptoException('The MAC does not match: '
				'sigtext=%s, received=%s, '
				'generated=%s' % (sigtext, mac, signature))
	
	import datatypes
	def generate_start(self, amount, order_id,
	    currency=datatypes.Currency('EUR'), # Currency. By default, Euro
		tcontab=datatypes.ImmediateAcct(),
		tautor=datatypes.ImmediateAuth(),
		language=None, customer_email=None,
		urlback=None, urldone=None, urlms=None,
		get_modpag=True, first_name=None, last_name=False,
		cc_only=False, bankpass_only=False, get_trans_type=True, 
		get_issuer_country=True):
		"Generate an order URL."
		
		# Check T-options
		if tcontab not in ('I', 'D'):
			raise BPWParmException('TCONTAB errato')
		if tautor not in ('I', 'D'):
			raise BPWParmException('TAUTOR errato')
		
		# Check URLs
		if not urlback:
			urlback = self.urlback_pattern % order_id
		if not urldone:
			urldone = self.urldone_pattern % order_id
		if not urlms:
			urlms = self.urlms_pattern % order_id
			
		# Misc options
		options = ''
		if get_modpag:
			options += 'A'
		if first_name and last_name:
			options += 'B'
		if cc_only and bankpass_only:
			raise BPWParmException(
				'Only one of cc_only and bankpass_only is allowed')
		if cc_only:
			options += 'C'
		if bankpass_only:
			options += 'D'
		if get_trans_type:
			options += 'E'
		if get_issuer_country:
			options += 'I'

		url = self.env
		params = {'IMPORTO': amount, 'VALUTA': currency,
			'NUMORD': order_id, 'IDNEGOZIO': self.crn,
			'URLBACK': urlback,
			'URLDONE': urldone,
			'URLMS': urlms,
			'TCONTAB': tcontab, 'TAUTOR': tautor}
		if first_name and last_name:
			params['NOME'] = first_name
			params['COGNOME'] = last_name
		if language:
			params['LINGUA'] = language
		if customer_email:
			params['EMAIL'] = customer_email
		if options:
			params['OPTIONS'] = options
		params['MAC'] = self.compute_mac(params,
			reqfields=('NUMORD', 'IDNEGOZIO', 'IMPORTO', 'VALUTA',
				'TCONTAB', 'TAUTOR'),
			optfields=('OPTIONS', 'NOME', 'COGNOME', 'LOCKCARD'))
		return url + '&' + urlencode(params)
		
	def parse_answer(self, qs):
		"Parse a provided result for an order operation."
		# Split query string without url-decoding
		parms = dict([pair.split('=') for pair in qs.split('&')])
		
		if not self.mac_ok(parms,
			reqfields=('NUMORD', 'IDNEGOZIO', 'AUT', 'IMPORTO', 'VALUTA',
				'IDTRANS', 'TCONTAB', 'TAUTOR', 'ESITO'),
			optfields=('BPW_MODPAG', 'BPW_TIPO_TRANSAZIONE',
				'BPW_ISSUER_COUNTRY')):
			raise BPWCryptoException('Wrong MAC received')
		from cgi import parse_qs
		from transaction import Transaction
		return Transaction.parse(parms)
		
