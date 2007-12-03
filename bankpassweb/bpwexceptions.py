class BPWException(Exception):
	"""
	Base class for exceptions specific to the bankpassweb module.
	"""
	pass
	
class BPWParmException(BPWException):
	pass
	
class BPWProtocolException(BPWException):
	pass
	
class BPWCryptoException(BPWException):
	pass
