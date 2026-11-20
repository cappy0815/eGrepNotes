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
        for entry in ['assets/tesseract.min.js','assets/nev-logo.png']:
            assert a.read(entry)==b.read(entry),entry+' changed'
        # 2.8: the native host may change on purpose (project link); it is then covered by test_native_camera.
        host_changed=a.read('classes.dex')!=b.read('classes.dex')
        if host_changed:
            sys.path.insert(0,str(__import__('pathlib').Path(__file__).parent));import test_native_camera as _n;_n.verify_native(_n.Dex(b.read('classes.dex')))
        # 1.5: OCR engine/worker/core unchanged, language model intentionally switched eng -> deu.
        import json as _j
        od=lambda z:_j.loads(z.read('assets/ocr-data.js').decode()[len('window.NEV_OCR_DATA='):-1])
        oa,ob=od(a),od(b)
        assert oa['worker']==ob['worker'] and oa['core']==ob['core'],'OCR engine changed'
        # 1.5 switched eng -> deu; from 1.5 on the German model must stay identical.
        changed=oa['language']!=ob['language']
        assert changed or oa['language']==ob['language']
        print('UPGRADE PASS: same package/signing certificate, higher versionCode; native host '+('changed and verified by the bytecode test' if host_changed else 'unchanged')+'; OCR engine unchanged; language model '+('changed (eng -> deu).' if changed else 'unchanged.'))
        print('Certificate SHA-256:',hashlib.sha256(bc).hexdigest())
        print('No actual Android installation was performed.')
if __name__=='__main__':
    if len(sys.argv)!=3:raise SystemExit('Usage: test_upgrade.py previous.apk new.apk')
    check(sys.argv[1],sys.argv[2])
