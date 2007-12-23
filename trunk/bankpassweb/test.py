from apiresults import Result
from engine import Engine
from datatypes import AcctType, DeferredAcct, ImmediateAcct
from decimal import Decimal

"""
This package only contains tests.
"""

# Scaletta:
# - ordine con aut. e cont. immediate
# - chiedi split
# - autorizza e contabilizza 10 euro (A1)
# - autorizza ma non contabilizzare altri 20 euro (A2)
# - storna A1
# - storna A2
# - autorizza e contabilizza 30 euro (A3)
# - autorizza ma non contabilizzare 40 euro (A4)
# - annulla contab. A3
# - contabilizza A4
# - chiudi differita

def writenext(dirname='test/', pattern='%s.xml'):
	from os.path import join
	try:
		idx_file = open(join(dirname, 'idx'), "r")
		idx = int(idx_file.read())
	except IOError:
		idx = 0
	idx += 1
	idx_file = open(join(dirname, 'idx'), 'w')
	idx_file.write(str(idx))
	return open(join(dirname, pattern % idx), 'w')

def saved(idx):
	print api_process(None, saved=idx)

def fetch_saved(idx):
	f = open('test/%s.xml' % idx)
	r = Result.parse(f.read(), engine=e)
	return r

urlpattern = 'http://lighthouse.ath.cx/%s/%%s/'
e = Engine(urlback=urlpattern % 'back', urldone = urlpattern % 'done',
	urlms = urlpattern % 'ms')

def api_process(r, comment=None, trace=False, saved=None, expect=None):
	try:
		if saved:
			r = fetch_saved(saved)
			if expect:
				assert expect == r.type
			return r
	except IOError:
		pass
	ans = r.send()
	f = writenext()
	if comment:
		f.write('<!-- %s -->\n' % comment)
	f.write(ans.__repr__(recursive=True,multiline=True))
	r = Result.parse(ans, engine=e)
	if expect:
		assert expect == r.type
	return r



def shop(order, tautor='I', tcontab='I'):
	from engine import Engine
	print e.generate_start('12345', order, first_name='A',
		last_name='B', tautor=tautor, tcontab=tcontab)


def step2(order):
	from datatypes import Success, StateError
	status = api_process(e.req.OrderStatus(order), saved=1,
		expect=Success())
	from datetime import date
	d = date.today()
	acctlist = api_process(e.req.TransactionList(d, d), saved=2,
		expect=Success())
	first_auth = status.auths[0].id
	ops = filter(lambda op: op.auth.id == first_auth, acctlist.ops)
	my_op = ops[0].id
	r = api_process(e.req.CancelAccounting(my_op, order), saved=3,
		expect=Success())
	# Split dell'aut. immediata
	split = api_process(e.req.Split(first_auth, order), saved=4,
		expect=Success()) # n.4
	# Aut. e cont. 10 euro
	errr = api_process(e.req.Authorize(first_auth, order, 10.0, 'EUR',
		cont_type=ImmediateAcct()), saved=5, expect=StateError())
	ord1 = api_process(e.req.Authorize(split.auth.id, order, 10.0,
		'EUR', cont_type=ImmediateAcct()), saved=6, expect=Success())
	ord2 = api_process(e.req.Authorize(split.auth.id, order, 20.0,
		'EUR', cont_type=DeferredAcct()), saved=7, expect=Success())
	storno1 = api_process(e.req.WriteOff(ord1.auth.id, order,
		10.0, 'EUR'), saved=8, expect=Success())
	storno2 = api_process(e.req.WriteOff(ord2.auth.id, order,
		ord2.auth.trans_amount, 'EUR'), saved=9, expect=Success())
	ord3 = api_process(e.req.Authorize(split.auth.id, order, 30.0,
		'EUR', cont_type=ImmediateAcct()), saved=10,
		expect=Success())
	ord4 = api_process(e.req.Authorize(split.auth.id, order, 40.0,
		'EUR', cont_type=DeferredAcct()), saved=11, expect=Success())
	acctlist = api_process(e.req.TransactionList(d, d), saved=12,
			expect=Success())
	ops = filter(lambda op: op.auth.id == ord3.auth.id, acctlist.ops)
	my_op = ops[0].id
	canc3 = api_process(e.req.CancelAccounting(my_op, order), saved=13,
		expect=Success())
	conf4 = api_process(e.req.Account(ord4.auth.id, order,
		ord4.auth.auth_amount, 'EUR'), saved=14,
			expect=Success())
	close = api_process(e.req.CloseAuth(split.auth.id, order), saved=15,
				expect=Success())
	
	print close
		
if __name__ == '__main__':
	from sys import argv, modules
	import test
	getattr(modules['test'], argv[1])(*argv[2:])

