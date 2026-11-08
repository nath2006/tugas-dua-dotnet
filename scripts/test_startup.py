"""Test fail-fast security config and Production defaults; requires --dll build output."""
import argparse
import datetime as dt
import html
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/test-results'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dll', required=True)
    args = parser.parse_args()
    base = dict(os.environ, ASPNETCORE_ENVIRONMENT='Development', ASPNETCORE_URLS='http://127.0.0.1:0')
    results = []
    cases = [('JWT key terlalu pendek', {'Jwt__Key':'too-short'}),
             ('Issuer kosong', {'Jwt__Issuer':''}), ('Audience kosong', {'Jwt__Audience':''}),
             ('Expiry nol', {'Jwt__ExpiresMinutes':'0'}), ('Role tidak dikenal', {'Auth__Users__0__Role':'Superuser'}),
             ('Hash plaintext ditolak', {'Auth__Users__0__PasswordHash':'plaintext-is-not-a-valid-hash'}),
             ('Username duplikat', {'Auth__Users__1__Username':os.environ.get('IF133_ADMIN_USERNAME','admin')}),
             ('Username melebihi batas login', {'Auth__Users__0__Username':'U'*101})]
    for name, overrides in cases:
        passed = False
        try:
            run = subprocess.run(['dotnet',args.dll],cwd=ROOT,env={**base,**overrides},text=True,capture_output=True,timeout=8)
            passed = run.returncode != 0 and 'Konfigurasi' in (run.stdout+run.stderr)
        except subprocess.TimeoutExpired:
            pass
        results.append({'name':name,'passed':passed,'expected':'Application fails startup with safe configuration message'})
        print(('PASS ' if passed else 'FAIL ')+name)
    configfile = os.environ.get('IF133_PRODUCTION_CONFIG_FILE')
    if not configfile:
        raise SystemExit('Set IF133_PRODUCTION_CONFIG_FILE to a private flat configuration JSON outside the repo for Production tests.')
    config = json.loads(Path(configfile).read_text(encoding='utf-8-sig'))
    env = dict(os.environ, ASPNETCORE_ENVIRONMENT='Production', ASPNETCORE_URLS='http://127.0.0.1:7290')
    env.update({k.replace(':','__'):str(v) for k,v in config.items()})
    logfile = OUT / 'production-startup.log'
    OUT.mkdir(parents=True,exist_ok=True)
    with logfile.open('w',encoding='utf-8') as log:
        process = subprocess.Popen(['dotnet',args.dll],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
        try:
            for _ in range(50):
                try:
                    urllib.request.urlopen('http://127.0.0.1:7290/api/products',timeout=0.2)
                    break
                except urllib.error.HTTPError:
                    break
                except OSError:
                    time.sleep(0.1)
            for name,method,path,expected,headers in [
                ('Production endpoint terlindungi','GET','/api/products',401,{}),
                ('Production Swagger dinonaktifkan','GET','/swagger/v1/swagger.json',404,{}),
                ('Production CORS deny by default','OPTIONS','/api/products',204,{'Origin':'http://localhost:5173','Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'authorization,content-type'})]:
                req=urllib.request.Request('http://127.0.0.1:7290'+path,method=method,headers=headers)
                try: response=urllib.request.urlopen(req,timeout=5)
                except urllib.error.HTTPError as error: response=error
                with response:
                    passed=response.status==expected and (method!='OPTIONS' or response.headers.get('Access-Control-Allow-Origin') is None)
                    results.append({'name':name,'passed':passed,'actualStatus':response.status,'expectedStatus':expected,'headers':dict(response.headers),'body':response.read().decode()})
                    print(('PASS ' if passed else 'FAIL ')+name)
        finally:
            process.terminate()
            process.wait(timeout=10)
    report={'executedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'total':len(results),'passed':sum(r['passed'] for r in results),'results':results}
    (OUT/'startup-results.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    (OUT/'startup-report.html').write_text('<!doctype html><meta charset="utf-8"><title>IF133 Configuration Tests</title><style>body{font:16px system-ui;margin:32px;background:#f5f7fb;color:#172234}pre{font:14px/1.5 Consolas;white-space:pre-wrap}</style><h1>IF133 · Startup dan Production</h1><p>Hasil nyata proses aplikasi terpisah; bukan mock. Production menggunakan HTTP loopback hanya untuk verifikasi lokal, bukan deployment publik.</p><pre>'+html.escape(json.dumps(report,indent=2,ensure_ascii=False))+'</pre>',encoding='utf-8')
    print(f"Startup/Production: {report['passed']}/{report['total']} PASS")
    raise SystemExit(0 if all(r['passed'] for r in results) else 1)


if __name__=='__main__': main()
