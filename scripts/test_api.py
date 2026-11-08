"""Integration tests against a real local API; stdlib only. Never export tokens/passwords."""
import base64
import datetime as dt
import hashlib
import hmac
import html
import json
import os
from pathlib import Path
import ssl
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'test-results'
BASE = os.environ.get('IF133_BASE_URL', 'https://localhost:7266').rstrip('/')
RESULTS = []
SKIPPED_GROUPS = []
TOKENS = []
SENSITIVE = {'password', 'accessToken', 'refreshToken', 'authorization', 'key', 'passwordHash'}


def redact(value):
    if isinstance(value, dict):
        return {k: '[REDACTED]' if k.lower() in {x.lower() for x in SENSITIVE} else redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(x) for x in value]
    if isinstance(value, str):
        for secret in TOKENS:
            if secret:
                value = value.replace(secret, '[REDACTED]')
    return value


def call(name, method, path, expected, body=None, token=None, headers=None, check=None, base=BASE, raw=False):
    request_headers = {'Accept': 'application/json', **(headers or {})}
    if token:
        request_headers['Authorization'] = 'Bearer ' + token
    data = None
    if body is not None:
        data = body.encode() if raw else json.dumps(body).encode()
        request_headers.setdefault('Content-Type', 'application/json')
    start = time.perf_counter()
    response_headers = {}
    status, response_text, parsed = 0, '', None
    checks = []
    try:
        req = urllib.request.Request(base + path, data=data, headers=request_headers, method=method)
        try:
            response = urllib.request.urlopen(req, timeout=20, context=ssl.create_default_context())
        except urllib.error.HTTPError as error:
            response = error
        with response:
            status = response.status
            response_headers = dict(response.headers.items())
            response_text = response.read().decode('utf-8')
        try:
            parsed = json.loads(response_text)
        except ValueError:
            parsed = response_text
        if isinstance(parsed, dict) and parsed.get('accessToken'):
            TOKENS.append(parsed['accessToken'])
        checks.append(('HTTP status', status == expected))
        if expected >= 400:
            checks.extend([
                ('ProblemDetails status/title/traceId', isinstance(parsed, dict) and parsed.get('status') == expected and bool(parsed.get('title')) and bool(parsed.get('traceId'))),
                ('No stack trace to client', all(x not in response_text for x in ['System.Exception', 'StackTrace', ' at Microsoft.', 'Password='])),
                ('ProblemDetails content type', 'application/problem+json' in response_headers.get('Content-Type', '')),
            ])
        if expected == 204:
            checks.append(('Empty response body', response_text == ''))
        if check:
            checks.extend(check(parsed, {k.lower(): v for k, v in response_headers.items()}))
    except Exception as error:
        checks.append(('Transport', False))
        response_text = str(error)
    record = {'id': f'{len(RESULTS)+1:02}', 'name': name, 'timestamp': dt.datetime.now(dt.timezone.utc).isoformat(),
              'request': {'method': method, 'url': base + path, 'headers': redact(request_headers), 'body': '[REDACTED login body]' if path == '/api/auth/login' else redact(body)},
              'expectedStatus': expected, 'actualStatus': status, 'response': {'headers': redact(response_headers), 'body': redact(parsed if parsed is not None else response_text)},
              'checks': [{'name': n, 'passed': bool(ok)} for n, ok in checks], 'passed': all(ok for _, ok in checks),
              'durationMs': round((time.perf_counter() - start)*1000, 2)}
    RESULTS.append(record)
    print(f"{record['id']} {'PASS' if record['passed'] else 'FAIL'} {name}: {status} expected {expected}")
    return parsed, status


def sign_jwt(payload, key):
    def enc(obj):
        return base64.urlsafe_b64encode(json.dumps(obj, separators=(',', ':')).encode()).decode().rstrip('=')
    message = enc({'alg': 'HS256', 'typ': 'JWT'}) + '.' + enc(payload)
    signature = base64.urlsafe_b64encode(hmac.new(key.encode(), message.encode(), hashlib.sha256).digest()).decode().rstrip('=')
    return message + '.' + signature


def same_products(before, after):
    return sorted(before, key=lambda product: product['id']) == sorted(after, key=lambda product: product['id'])


def write_report(before, after):
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {'baseUrl': BASE, 'executedAt': dt.datetime.now(dt.timezone.utc).isoformat(), 'total': len(RESULTS),
               'passed': sum(r['passed'] for r in RESULTS), 'failed': sum(not r['passed'] for r in RESULTS),
               'existingProductsUnchanged': same_products(before, after) if before is not None and after is not None else None,
               'skippedGroups': SKIPPED_GROUPS, 'results': RESULTS}
    (OUT / 'api-results.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    suite = ET.Element('testsuite', name='IF133 real HTTP integration', tests=str(len(RESULTS)), failures=str(summary['failed']))
    for r in RESULTS:
        case = ET.SubElement(suite, 'testcase', name=r['name'], time=str(r['durationMs']/1000))
        if not r['passed']:
            ET.SubElement(case, 'failure', message='; '.join(c['name'] for c in r['checks'] if not c['passed'])).text = json.dumps(r, ensure_ascii=False)
    ET.ElementTree(suite).write(OUT / 'api-results.junit.xml', encoding='utf-8', xml_declaration=True)
    cards = []
    for r in RESULTS:
        escaped = html.escape(json.dumps(r, indent=2, ensure_ascii=False))
        cards.append(f'<section id="case-{r["id"]}" class="case"><h2>{r["id"]} · {html.escape(r["name"])}</h2><p class="status">{"PASS" if r["passed"] else "FAIL"} · HTTP {r["actualStatus"]} · expected {r["expectedStatus"]}</p><pre>{escaped}</pre></section>')
    page = '<!doctype html><html lang="id"><meta charset="utf-8"><title>IF133 — Bukti HTTP aktual</title><style>body{font:16px system-ui;background:#f5f7fb;color:#172234;margin:24px}h1,h2{margin-top:0}.case{background:white;border:1px solid #cbd5e1;border-radius:12px;padding:24px;margin-bottom:24px;max-width:1080px}pre{font:13px/1.5 Consolas,monospace;white-space:pre-wrap;overflow-wrap:anywhere}.status{font-weight:700;color:#176642}.note{max-width:1080px}body.single .case{display:none}body.single .case.selected{display:block}</style><h1>IF133 P6 · Bukti pengujian HTTP aktual</h1><p class="note">Hasil dari server ASP.NET Core dan MySQL nyata, bukan mock. Tampilan ini merender rekaman request/response dari scripts/test_api.py; bukan antarmuka Postman/Swagger. Password dan token disensor.</p><p>' + html.escape(f"{summary['executedAt']} | {summary['passed']}/{summary['total']} PASS | Produk awal tidak berubah: {summary['existingProductsUnchanged']}") + '</p>' + ''.join(cards) + '<script>function selectCase(id){document.body.classList.add("single");document.querySelectorAll(".case").forEach(x=>x.classList.toggle("selected",x.id==="case-"+id));window.scrollTo(0,0)}if(location.hash)selectCase(location.hash.slice(1));</script></html>'
    (OUT / 'api-report.html').write_text(page, encoding='utf-8')
    print(json.dumps({k: v for k, v in summary.items() if k != 'results'}))
    return summary


def main():
    for variable, group in [('IF133_JWT_KEY', 'Signed JWT claim/signature negative cases (5)'),
                            ('IF133_FAULT_BASE_URL', 'Isolated unexpected database failure (1)')]:
        if not os.environ.get(variable):
            SKIPPED_GROUPS.append({'group': group, 'reason': variable + ' not configured'})
            print('SKIP: ' + group + ' — ' + variable + ' not configured')
    admin_user = os.environ.get('IF133_ADMIN_USERNAME', 'admin')
    reader_user = os.environ.get('IF133_READER_USERNAME', 'reader')
    admin_password = os.environ['IF133_ADMIN_PASSWORD']
    reader_password = os.environ['IF133_READER_PASSWORD']
    TOKENS.extend([admin_password, reader_password])
    call('GET tanpa token', 'GET', '/api/products', 401, check=lambda b,h:[('Bearer challenge', h.get('www-authenticate', '').startswith('Bearer'))])
    call('GET dengan token rusak', 'GET', '/api/products', 401, token='invalid.jwt.token')
    call('Login password salah', 'POST', '/api/auth/login', 401, {'username': admin_user, 'password': 'invalid-password-for-test'})
    call('Login username tidak dikenal', 'POST', '/api/auth/login', 401, {'username': 'unknown-test-user', 'password': 'invalid-password-for-test'})
    call('Login field kosong', 'POST', '/api/auth/login', 400, {})
    a, _ = call('Login Admin valid', 'POST', '/api/auth/login', 200, {'username': admin_user, 'password': admin_password}, check=lambda b,h:[('Token contract', bool(b.get('accessToken')) and b.get('tokenType', '').lower() == 'bearer' and b.get('expiresIn', 0) > 0)])
    r, _ = call('Login Reader valid', 'POST', '/api/auth/login', 200, {'username': reader_user, 'password': reader_password}, check=lambda b,h:[('Token issued', bool(b.get('accessToken')))])
    admin, reader = (a or {}).get('accessToken'), (r or {}).get('accessToken')
    if not admin or not reader:
        write_report(None, None)
        raise SystemExit('Login failed: stopping mutation tests')
    before, _ = call('Admin GET semua produk', 'GET', '/api/products', 200, token=admin, check=lambda b,h:[('Array response', isinstance(b,list))])
    call('Reader GET semua produk', 'GET', '/api/products', 200, token=reader)
    good = {'name': 'IF133 automated evidence ' + str(time.time_ns()), 'description': 'Data sementara pengujian', 'price': 350000, 'stock': 5}
    call('POST tanpa token', 'POST', '/api/products', 401, good)
    call('Reader POST ditolak', 'POST', '/api/products', 403, good, reader)
    product, _ = call('Admin POST produk valid', 'POST', '/api/products', 201, good, admin, check=lambda b,h:[('Location and DTO fields', '/api/products/' in h.get('location','') and set(b)=={'id','name','description','price','stock'})])
    product_id = product.get('id') if isinstance(product,dict) else None
    if not product_id:
        write_report(before, None)
        raise SystemExit('Create failed: stopping mutation tests')
    path = '/api/products/' + str(product_id)
    try:
        call('Admin GET detail produk', 'GET', path, 200, token=admin, check=lambda b,h:[('Created values persisted', b.get('name')==good['name'] and b.get('stock')==5 and b.get('price')==350000)])
        call('Reader GET detail produk', 'GET', path, 200, token=reader)
        call('Reader PUT ditolak', 'PUT', path, 403, good, reader)
        call('Reader DELETE ditolak', 'DELETE', path, 403, token=reader)
        invalids = [('Nama kosong', {**good, 'name':''}, 'Name'), ('Nama spasi', {**good,'name':'   '}, 'Name'),
                    ('Nama >100 karakter', {**good,'name':'N'*101}, 'Name'), ('Deskripsi >500 karakter',{**good,'description':'D'*501},'Description'),
                    ('Harga negatif',{**good,'price':-1},'Price'), ('Harga di atas maksimum',{**good,'price':1000000000},'Price'),
                    ('Harga hilang',{k:v for k,v in good.items() if k!='price'},'Price'), ('Harga null',{**good,'price':None},'Price'),
                    ('Stok negatif',{**good,'stock':-1},'Stock'), ('Stok hilang',{k:v for k,v in good.items() if k!='stock'},'Stock'),
                    ('Stok null',{**good,'stock':None},'Stock'), ('Stok overflow',{**good,'stock':2147483648},None)]
        for name, body, field in invalids:
            call('POST invalid: '+name,'POST','/api/products',400,body,admin,check=lambda b,h,f=field:[('Validation errors', isinstance(b.get('errors'),dict) and (not f or f in b['errors']))])
        call('PUT invalid harga negatif','PUT',path,400,{**good,'price':-1},admin)
        call('PUT invalid field hilang','PUT',path,400,{},admin)
        call('POST malformed JSON','POST','/api/products',400,'{"name":',admin,raw=True)
        call('POST unsupported Content-Type','POST','/api/products',415,'plain text',admin,headers={'Content-Type':'text/plain'},raw=True)
        call('POST body kosong','POST','/api/products',400,'',admin,raw=True)
        call('Nilai tetap setelah request ditolak','GET',path,200,token=admin,check=lambda b,h:[('No unauthorized/invalid mutation',b.get('name')==good['name'] and b.get('stock')==good['stock'])])
        updated = {**good,'name':good['name']+' updated','price':375000,'stock':8}
        call('Admin PUT produk valid','PUT',path,204,updated,admin)
        call('Verifikasi hasil PUT tersimpan','GET',path,200,token=admin,check=lambda b,h:[('Updated values',b.get('name')==updated['name'] and b.get('stock')==8 and b.get('price')==375000)])
        # A signed token with invalid claims tests actual validation, not merely signature rejection.
        key = os.environ.get('IF133_JWT_KEY')
        if key:
            now = int(time.time())
            payload = {'sub':admin_user,'role':'Admin','iss':os.environ.get('IF133_JWT_ISSUER','IF133.Tugas1.Api'),'aud':os.environ.get('IF133_JWT_AUDIENCE','IF133.Tugas1.Client'),'nbf':now-600,'exp':now+3600}
            for label, changes in [('expired',{'exp':now-300}),('wrong issuer',{'iss':'wrong-issuer'}),('wrong audience',{'aud':'wrong-audience'}),('future not-before',{'nbf':now+3600})]:
                forged = sign_jwt({**payload,**changes},key)
                TOKENS.append(forged)
                call('JWT '+label+' ditolak','GET','/api/products',401,token=forged)
            forged = sign_jwt(payload, 'different-signing-key-for-test-at-least-32-bytes')
            TOKENS.append(forged)
            call('JWT wrong signature ditolak','GET','/api/products',401,token=forged)
        for origin, allowed in [('http://localhost:5173',True),('http://localhost:9999',False)]:
            call('CORS preflight '+('diizinkan' if allowed else 'ditolak'),'OPTIONS','/api/products',204,headers={'Origin':origin,'Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'authorization,content-type'},check=lambda b,h,o=origin,a=allowed:[('CORS origin permission', h.get('access-control-allow-origin')==o if a else 'access-control-allow-origin' not in h)])
        call('CORS header pada GET valid','GET',path,200,token=admin,headers={'Origin':'http://localhost:5173'},check=lambda b,h:[('Allowed origin echoed',h.get('access-control-allow-origin')=='http://localhost:5173')])
        call('Route tidak dikenal','GET','/api/route-tidak-ada',404,token=admin)
        call('ID route bukan integer','GET','/api/products/abc',404,token=admin)
        call('Method PATCH tidak didukung','PATCH',path,405,good,admin)
        call('Swagger runtime tersedia','GET','/swagger/v1/swagger.json',200,check=lambda b,h:[('Auth path documented','/api/auth/login' in b.get('paths',{})), ('Bearer scheme documented', b.get('components',{}).get('securitySchemes',{}).get('Bearer',{}).get('scheme')=='bearer'), ('Login is anonymous',b['paths']['/api/auth/login']['post'].get('security')==[]), ('CRUD statuses match runtime', '201' in b['paths']['/api/products']['post']['responses'] and all('204' in b['paths']['/api/products/{id}'][m]['responses'] for m in ['put','delete']))])
        fault_base = os.environ.get('IF133_FAULT_BASE_URL')
        if fault_base:
            call('Unexpected database failure disanitasi','GET','/api/products',500,token=admin,base=fault_base,check=lambda b,h:[('Generic error message',b.get('title')=='Terjadi kesalahan pada server')])
    finally:
        call('Admin DELETE hanya produk uji','DELETE',path,204,token=admin)
        call('GET produk terhapus','GET',path,404,token=admin)
        call('PUT produk terhapus','PUT',path,404,good,admin)
        call('DELETE produk terhapus','DELETE',path,404,token=admin)
        after, _ = call('Verifikasi produk awal tidak berubah','GET','/api/products',200,token=admin,check=lambda b,h:[('Existing data preserved',same_products(b,before))])
        summary = write_report(before, after)
    raise SystemExit(1 if summary['failed'] else 0)


if __name__ == '__main__':
    main()
