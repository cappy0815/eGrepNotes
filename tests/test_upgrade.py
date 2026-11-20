"""Verify update identity and unchanged OCR payload. Not an Android installation test.
Usage: python tests/test_upgrade.py previous.apk new.apk
"""
from pathlib import Path
import hashlib, subprocess, sys, tempfile, zipfile
from test_apk import parse_manifest

def cert_der(payload):
    with tempfile.TemporaryDirectory() as t:
        p=Path(t)/'certificate.rsa';p.write_bytes(payload)
        pem=subprocess.check_output(['openssl','pkcs7','-inform','DER','-in',str(p),'-print_certs'])
        return subprocess.check_output(['openssl','x509','-outform','DER'],input=pem)

def check(old,new):
    with zipfile.ZipFile(old) as a,zipfile.ZipFile(new) as b:
        am=dict(parse_manifest(a.read('AndroidManifest.xml')))['manifest']
        bm=dict(parse_manifest(b.read('AndroidManifest.xml')))['manifest']
        assert am['package']==bm['package']=='de.michaelnowak.egrepnotes'
        assert bm['versionCode']>am['versionCode']
        ac=cert_der(a.read('META-INF/NEVNOTE.RSA'));bc=cert_der(b.read('META-INF/NEVNOTE.RSA'))
        assert ac==bc,'Signing identity changed: incompatible update'
        for entry in ['assets/ocr.js','assets/tesseract.min.js','assets/ocr-data.js','assets/nev-logo.png']:
            assert a.read(entry)==b.read(entry),entry+' changed'
        print('UPGRADE PASS: same package/signing certificate, higher versionCode; OCR payload unchanged.')
        print('Certificate SHA-256:',hashlib.sha256(bc).hexdigest())
        print('No actual Android installation was performed.')
if __name__=='__main__':
    if len(sys.argv)!=3:raise SystemExit('Usage: test_upgrade.py previous.apk new.apk')
    check(sys.argv[1],sys.argv[2])
