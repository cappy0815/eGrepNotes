"""APK integrity and native bridge regression. No Android device test."""
from pathlib import Path
import base64,hashlib,json,struct,sys,tempfile,subprocess,zipfile,zlib
from test_native_camera import Dex, verify_native

def parse_manifest(b):
    strings=[];nodes=[];off=8
    while off<len(b):
        kind,header,size=struct.unpack_from('<HHI',b,off);assert size>=header and size>0
        if kind==1:
            count,styles,flags,start,_=struct.unpack_from('<5I',b,off+8)
            for i in range(count):
                at=off+start+struct.unpack_from('<I',b,off+header+4*i)[0]
                if flags & 0x100:
                    # UTF-8 pool: UTF-16 character count followed by byte count.
                    n=b[at];at+=1
                    if n&128: at+=1
                    n=b[at];at+=1
                    if n&128:n=((n&127)<<8)|b[at];at+=1
                    strings.append(b[at:at+n].decode('utf-8'))
                else:
                    n=struct.unpack_from('<H',b,at)[0];at+=2
                    strings.append(b[at:at+2*n].decode('utf-16-le'))
        elif kind==0x102:
            _,name,attr_start,attr_size,count=struct.unpack_from('<IIHHH',b,off+16)
            attrs={}
            for i in range(count):
                ns,n,raw,_,_,ty,val=struct.unpack_from('<IIIHBBI',b,off+16+attr_start+i*attr_size)
                attrs[strings[n]]=strings[val] if ty==3 else val
            nodes.append((strings[name],attrs))
        off+=size
    return nodes

def main(path):
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        assert len(z.namelist())==len(set(z.namelist()))
        assert not any('key.pem' in n or n.endswith('.jks') for n in z.namelist())
        manifest=z.read('META-INF/MANIFEST.MF');sf=z.read('META-INF/NEVNOTE.SF');rsa=z.read('META-INF/NEVNOTE.RSA')
        assert ('SHA-256-Digest-Manifest: '+base64.b64encode(hashlib.sha256(manifest).digest()).decode()).encode() in sf
        for entry in manifest.split(b'\r\n\r\n')[1:]:
            if not entry:continue
            parts=dict(line.decode().split(': ',1) for line in entry.split(b'\r\n'))
            assert base64.b64encode(hashlib.sha256(z.read(parts['Name'])).digest()).decode()==parts['SHA-256-Digest']
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'CERT.SF').write_bytes(sf);(root/'CERT.RSA').write_bytes(rsa)
            subprocess.run(['openssl','cms','-verify','-binary','-inform','DER','-in',str(root/'CERT.RSA'),'-content',str(root/'CERT.SF'),'-noverify','-out',str(root/'verified')],check=True,capture_output=True)
        nodes=dict(parse_manifest(z.read('AndroidManifest.xml')))
        assert nodes['manifest']['package']=='de.michaelnowak.egrepnotes'
        config=json.loads((Path(__file__).resolve().parents[1]/'version.json').read_text())
        assert nodes['manifest']['versionCode']==config['versionCode'] and nodes['manifest']['versionName']==config['version']
        assert nodes['application']['label']=='eGrep Notes' and nodes['application']['allowBackup']==0
        assert nodes['activity']['exported']==0xffffffff
        assert nodes['uses-sdk']['minSdkVersion']==26
        dex=Dex(z.read('classes.dex'))
    assert nodes['provider']['authorities']=='de.michaelnowak.egrepnotes.capture'
    assert nodes['provider']['exported']==0 and nodes['provider']['grantUriPermissions']==0xffffffff
    assert 'uses-permission' not in nodes, 'Unexpected extra device permissions'
    verify_native(dex)
    print('APK PASS: archive integrity, per-entry SHA-256, CMS signature, version/package, provider permissions, DEX checksums and simulated native paths.')
if __name__=='__main__':main(Path(sys.argv[1]))
