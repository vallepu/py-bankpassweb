"""
This package only contains tests.
"""
from urllib import urlencode
from apiresults import Result
from engine import Engine
from datatypes import AcctType, DeferredAcct, ImmediateAcct
from decimal import Decimal
e = Engine()

import pdb

order = 'gutentag'

def shop(tautor='I', tcontab='I'):
	from engine import Engine
	urlpattern = 'http://lighthouse.ath.cx/%s/%%s/'
	e = Engine(urlback=urlpattern % 'back', urldone = urlpattern % 'done',
		urlms = urlpattern % 'ms')
	print e.generate_start('12345', order, first_name='A',
		last_name='B', tautor=tautor, tcontab=tcontab)
		
def api_test():
	from engine import Engine
	from datatypes import AcctType
	e = Engine()
	r = e.req.AuthRequest('myshop2', 15.50, 'EUR', '8032180310SL1b9hhar9tcrci',
		cont_type=AcctType(deferred=True))
	ans = r.send()
	print ans.__repr__(recursive=True,multiline=True)

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

def api_process(r, comment=None, trace=False, saved=None):
	try:
		if saved:
			r = fetch_saved(saved)
			return r
	except IOError:
		pass
	ans = r.send()
	f = writenext()
	if comment:
		f.write('<!-- %s -->\n' % comment)
	f.write(ans.__repr__(recursive=True,multiline=True))
	r = Result.parse(ans, engine=e)
	if trace:
		pdb.set_trace()
	return r

transaction = '8032180310SL1j638yx2v1rsr'

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

def passo():
	status = api_process(e.req.OrderStatus(order), saved=1)
	from datetime import date
	d = date(2007,12,1)
	acctlist = api_process(e.req.TransactionList(d, d), saved=2)
	first_auth = status.auths[0].id
	ops = filter(lambda op: op.auth.id == first_auth, acctlist.ops)
	my_op = ops[0].id
	r = api_process(e.req.CancelAccounting(my_op, order), saved=3)
	# Split dell'aut. immediata
	split = api_process(e.req.Split(first_auth, order), saved=4) # n.4
	# Aut. e cont. 10 euro
	errr = api_process(e.req.Authorize(first_auth, order, 10.0, 'EUR',
		cont_type=ImmediateAcct()), saved=5)
	ord1 = api_process(e.req.Authorize(split.auth.id, order, 10.0,
		'EUR', cont_type=ImmediateAcct()), saved=6)
	ord2 = api_process(e.req.Authorize(split.auth.id, order, 20.0,
		'EUR', cont_type=DeferredAcct()), saved=7)
	storno1 = api_process(e.req.WriteOff(ord1.auth.id, order,
		10.0, 'EUR'), saved=8)
	storno2 = api_process(e.req.WriteOff(ord2.auth.id, order,
		ord2.auth.trans_amount, 'EUR'), saved=9)
	ord3 = api_process(e.req.Authorize(split.auth.id, order, 30.0,
		'EUR', cont_type=ImmediateAcct()), saved=10)
	ord4 = api_process(e.req.Authorize(split.auth.id, order, 40.0,
		'EUR', cont_type=DeferredAcct()), saved=11)
	acctlist = api_process(e.req.TransactionList(d, d), saved=12)
	ops = filter(lambda op: op.auth.id == ord3.auth.id, acctlist.ops)
	my_op = ops[0].id
	canc3 = api_process(e.req.CancelAccounting(my_op, order), saved=13)
	conf4 = api_process(e.req.Account(ord4.auth.id, order,
		ord4.auth.auth_amount, 'EUR'), saved=14)
	close = api_process(e.req.CloseAuth(split.auth.id, order), saved=16)
	
	print close
		
	
def passo2():
	api_process(e.req.Split(transaction, order), 'Richiesta di SPLIT')

def passo3():
	t = '191mttj5ub3qo1f832a2trrAD'
	api_process(e.req.Authorize(t, order, Decimal('10'), 'EUR'),
		'Autorizza e contabilizza')
		
def passo4():
	t = '191mttj5ub3qo1f832a2trrAD'
	api_process(e.req.Authorize(t, order, Decimal('20'), 'EUR',
		cont_type=DeferredAcct()),'Autorizza e non contabilizzare')
		
def passo5():
	t = 'xap0sv1dywz316w7mca37grCD'
	api_process(e.req.WriteOff(t, order, Decimal(10), 'EUR'), 'Storno 1')
	
def passo6():
	t = '10yk653pvc57815zclw5oqrCD'
	api_process(e.req.WriteOff(t, order, Decimal(10), 'EUR'),	
		'Storno 2 (contabilizzato)')
		
def passo7():
	t = '191mttj5ub3qo1f832a2trrAD'
	api_process(e.req.Authorize(t, order, Decimal('30'), 'EUR'),
		'Autorizza e contabilizza')

def passo8():
	t = '191mttj5ub3qo1f832a2trrAD'
	api_process(e.req.Authorize(t, order, Decimal('40'), 'EUR',
		cont_type=DeferredAcct()),'Autorizza e non contabilizzare')

def passo9():
	t = '1up8rqm8vwjhz172g9j0c7rCD'
	api_process(e.req.Split(t, order))
	
def ec1():
	from datetime import date
	d = date(2007, 12, 1)
	api_process(e.req.TransactionList(d, d))
	
def ec2():
	api_process(e.req.AuthList('q41yl7eml6461189sr94jkrCD'))
	
def ec3():
	api_process(e.req.OrderStatus(order))
	
def api_t3():
	from engine import Engine
	e = Engine()
	r = e.req.AuthRequest('8032180310SLybjfchmji8nfr', 'myshop3',
		1.00, 'EUR', cont_type=AcctType(deferred=True))
	ans = r.send()
	f = writenext()
	f.write(ans.__repr__(recursive=True,multiline=True))
	r = result.parse(ans, engine=e)
	pdb.set_trace()

def api_t4():
	r = e.req.Account('18jd7hmxkqnwt134l74r3nrCD', 'myshop3',
		1.00, 'EUR')
	ans = r.send()
	f = writenext()
	f.write(ans.__repr__(recursive=True,multiline=True))
	r = result.parse(ans, engine=e)
	pdb.set_trace()

def api_t5():
	r = e.req.CancelAccounting('1k3g6crrprC', 'myshop3')
	ans = r.send()
	f = writenext()
	f.write(ans.__repr__(recursive=True,multiline=True))
	r = Result.parse(ans, engine=e)
	pdb.set_trace()
	
def api_t6():
	r = e.req.WriteOff('18jd7hmxkqnwt134l74r3nrCD', 'myshop3',
		1.00, 'EUR')
	ans = r.send()
	f = writenext()
	f.write(ans.__repr__(recursive=True,multiline=True))
	r = Result.parse(ans, engine=e)
	pdb.set_trace()
	
def api_t7():
	r = e.req.Split('8032180310SL1hg98kr6ll7hr', 'myshop4')
	ans = r.send()
	f = writenext()
	f.write(ans.__repr__(recursive=True,multiline=True))
	r = Result.parse(ans, engine=e)
	pdb.set_trace()


def api_t8():
	api_process(e.req.FormerResult('85753805047161270102207947079680'))	

def api_t9():
	from datetime import datetime
	d = datetime(2007,11,30)
	api_process(e.req.TransactionList(d, d))

def api_t2():
	text = """
	<BPWXmlRisposta>
		<Timestamp>2007-11-28T14:00:44</Timestamp>
		<Esito>00</Esito>
		<MAC>AF0B53CDA6CC9E7A1761997AE8B43FF3648F3E65</MAC>
		<Dati>
			<RicAutorizzazione>
				<TestataRichiesta>
					<IDnegozio>010500000000001</IDnegozio>
					<Operatore>PROVA001</Operatore>
					<ReqRefNum>27399817044878079530787649093632</ReqRefNum>
				</TestataRichiesta>
				<IDtrans>8032180310SL1b9hhar9tcrci</IDtrans>
				<Importo>1550</Importo>
				<Valuta>978</Valuta>
				<Tcontab>D</Tcontab>
				<FineOrdine>N</FineOrdine>
			</RicAutorizzazione>
			<Autorizzazione>
				<TipoPag>03</TipoPag>
				<Tautor>I</Tautor>
				<IDtrans>bkt8s51f7055gbkt8s51f70CD</IDtrans>
				<Circuito>02</Circuito>
				<NumOrdine>myshop2</NumOrdine>
				<ImportoTrans>1550</ImportoTrans>
				<ImportoAutor>1550</ImportoAutor>
				<Valuta>978</Valuta>
				<ImportoContab>0</ImportoContab>
				<EsitoTrans>00</EsitoTrans>
				<Timestamp>2007-11-28T14:00:44</Timestamp>
				<NumAut>402205</NumAut>
				<AcqBIN>525500</AcqBIN>
				<CodiceEsercente>020228163806560</CodiceEsercente>
				<Stato>00</Stato>
				<MAC>BFB86FB6674BA4961428C36FDCABC1D4186EE1D6</MAC>
			</Autorizzazione>
		</Dati>
	</BPWXmlRisposta>
	"""




	e = Engine()
	import xmltramp

	xml = xmltramp.parse(text)
	r = Result.parse(xml, engine=e)
	import pdb
	pdb.set_trace()
	print r.trans_id 
	
def fetch_saved(idx):
	f = open('test/%s.xml' % idx)
	r = Result.parse(f.read(), engine=e)
	return r

def saved_loop(idx=1):
	while True:
		saved(idx)
		idx += 1
	
if __name__ == '__main__':
	from sys import argv, modules
	getattr(modules['__main__'], argv[1])(*argv[2:])