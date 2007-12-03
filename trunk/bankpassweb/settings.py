# import local settings overriding the defaults
try:
    from local_settings import *
except ImportError:
	pass