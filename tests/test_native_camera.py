"""Execute shipped Dalvik instructions with simulated Android APIs.
This validates bytecode control flow and API descriptors, not a real Android VM.
Camera/device vendor behavior and Android verifier still require a device test.
"""
from pathlib import Path
import hashlib,struct,zlib,zipfile,sys
P='Lde/michaelnowak/egrepnotes/'
MAIN=P+'MainActivity;';CHOOSE=P+'FileChooserClient;';LINK=P+'ExternalLinkClient;';PROVIDER=P+'CaptureProvider;'
URI='content://de.michaelnowak.egrepnotes.capture/capture/aufstellung.jpg'

def signed(n):return n-65536 if n&32768 else n
class JavaError(Exception):
    def __init__(self,kind,message=''):self.kind=kind;super().__init__(message)
class Dex:
    def __init__(self,b):
        self.b=b;assert b[:8]==b'dex\n035\0';assert self.u(32)==len(b);assert self.u(36)==112
        assert self.u(8)==zlib.adler32(b[12:])&0xffffffff and b[12:32]==hashlib.sha1(b[32:]).digest()
        self.strings=[]
        for i in range(self.u(56)):
            off=self.u(self.u(60)+4*i);_,off=self.uleb(off);self.strings.append(b[off:b.index(0,off)].decode('utf-8'))
        self.types=[self.strings[self.u(self.u(68)+4*i)] for i in range(self.u(64))]
        self.protos=[]
        for i in range(self.u(72)):
            _,r,off=struct.unpack_from('<III',b,self.u(76)+12*i)
            ps=[self.types[struct.unpack_from('<H',b,off+4+2*k)[0]] for k in range(self.u(off))] if off else []
            self.protos.append((self.types[r],ps))
        self.fields=[]
        for i in range(self.u(80)):
            c,t,n=struct.unpack_from('<HHI',b,self.u(84)+8*i);self.fields.append((self.types[c],self.strings[n],self.types[t]))
        self.methods=[]
        for i in range(self.u(88)):
            c,p,n=struct.unpack_from('<HHI',b,self.u(92)+8*i);self.methods.append((self.types[c],self.strings[n],p))
        self.codes={}
        for i in range(self.u(96)):
            off=self.u(self.u(100)+32*i+24);counts=[]
            for _ in range(4):n,off=self.uleb(off);counts.append(n)
            for _ in range(counts[0]+counts[1]):_,off=self.uleb(off);_,off=self.uleb(off)
            for n in counts[2:]:
                idx=0
                for _ in range(n):
                    d,off=self.uleb(off);idx+=d;_,off=self.uleb(off);co,off=self.uleb(off)
                    regs,ins,outs,tries,debug,size=struct.unpack_from('<HHHHII',b,co);assert regs>=ins
                    code=list(struct.unpack_from('<'+'H'*size,b,co+16));handlers=[]
                    if tries:
                        to=co+16+2*size+(2 if size%2 else 0);base=to+8*tries
                        for j in range(tries):
                            start,length,ho=struct.unpack_from('<IHH',b,to+j*8);count,h=self.uleb(base+ho)
                            assert count==1
                            typ,h=self.uleb(h);addr,h=self.uleb(h);handlers.append((start,start+length,self.types[typ],addr))
                    self.codes[self.methods[idx][:2]]=(regs,ins,outs,code,handlers)
    def u(self,o):return struct.unpack_from('<I',self.b,o)[0]
    def uleb(self,o):
        n=sh=0
        while True:
            v=self.b[o];o+=1;n|=(v&127)<<sh
            if v<128:return n,o
            sh+=7
    def run(self,owner,name,args,env=None):
        env={} if env is None else env;calls=[]
        env.setdefault('files',{});env.setdefault('calls',[])
        def execute(owner,name,args):
            regs,ins,outs,c,handlers=self.codes[(owner,name)];r=[None]*regs;r[-ins:]=args
            pc=0;result=None;exception=None;steps=0
            def invoke(i,rs):
                cl,n,proto=self.methods[i];ret,ps=self.protos[proto];argv=[r[j] for j in rs]
                calls.append((cl,n,argv));env['calls'].append((cl,n,argv))
                if (cl,n) in self.codes:return execute(cl,n,argv)
                if n=='equals':return argv[0]==argv[1]
                if n=='<init>':
                    if cl=='Ljava/io/File;':argv[0]['path']=argv[1]['path']+'/'+argv[2]
                    if cl=='Landroid/content/Intent;':argv[0]['action']=argv[1];argv[0]['extras']={}
                    if cl=='Landroid/content/Intent;' and len(argv)>2:argv[0]['data']=argv[2]
                    if cl=='Landroid/webkit/WebView;':argv[0]['context']=argv[1]
                    if cl=='Landroid/database/MatrixCursor;':argv[0]['columns']=argv[1]
                    if cl=='Landroid/content/pm/ShortcutInfo$Builder;':argv[0]['context']=argv[1];argv[0]['id']=argv[2]
                    if cl=='Landroid/print/PrintAttributes$Margins;':argv[0]['margins']=argv[1:]
                    return None
                if n=='getCacheDir':return {'path':'/private/cache'}
                if n=='getContext':return argv[0].get('context',env.get('owner',{}))
                if n=='delete':env['files'].pop(argv[0]['path'],None);return 1
                if n=='length':return env['files'].get(argv[0]['path'],0)
                if n=='createNewFile':env['files'][argv[0]['path']]=0;return 1
                if n=='parse':return argv[0]
                if n=='fromFile':return 'file://'+argv[0]['path']
                if n=='toString':return argv[0]
                if n=='concat':return argv[0]+argv[1]
                if n=='isCaptureEnabled':return argv[0].get('capture',False)
                if n=='createIntent':return {'action':'PICK','extras':{}}
                if n=='putExtra':argv[0]['extras'][argv[1]]=argv[2];return argv[0]
                if n=='addFlags':argv[0]['flags']=argv[1];return argv[0]
                if n=='newRawUri':return {'uri':argv[1]}
                if n=='setClipData':argv[0]['clip']=argv[1];return None
                if n=='startActivityForResult':
                    if env.get('launch_error'):raise JavaError('Ljava/lang/Exception;','No camera')
                    env['intent'],env['request']=argv[1:];return None
                if n=='parseResult':return ['content://gallery/photo'] if argv[0]==-1 else None
                if n=='onReceiveValue':env.setdefault('deliveries',[]).append((argv[0],argv[1]));return None
                if n=='makeText':return {'toast':argv[1]}
                if n=='show':env.setdefault('toasts',[]).append(argv[0]['toast']);return None
                if n=='getSettings':return {'class':'settings'}
                if n=='getBoolean':return argv[0].get(argv[1],False)
                if n=='putBoolean':argv[0][argv[1]]=bool(argv[2]);return None
                if n=='registerReceiver':return None if env.get('plugged') is None else {'plugged':env['plugged']}
                if n=='getIntExtra':return argv[0].get(argv[1],argv[2])
                if n=='getSystemService' and argv[1]=='shortcut':
                    if env.get('shortcut_error'):raise JavaError('Ljava/lang/SecurityException;','No shortcuts')
                    return env.setdefault('shortcut_manager',{'class':'ShortcutManager'})
                if n=='getSystemService':return {'class':'print'} if env.get('print_available',True) else None
                if n=='getIntent':return env.get('start_intent')
                if n=='getDataString':return argv[0].get('data') if argv[0] else None
                if n=='setClassName':argv[0]['component']=argv[2];return argv[0]
                if n=='createWithResource':return {'icon':argv[1]}
                if n in ['setShortLabel','setLongLabel','setIcon','setIntent']:argv[0][n]=argv[1];return argv[0]
                if n=='build' and cl=='Landroid/content/pm/ShortcutInfo$Builder;':return dict(argv[0])
                if n=='singletonList':return [argv[0]]
                if n=='setDynamicShortcuts':argv[0]['shortcuts']=argv[1];return 1
                if n in ['build','createPrintDocumentAdapter']:return {'class':n}
                if n in ['setMediaSize','setMinMargins']:argv[0][n]=argv[1];return argv[0]
                if n=='parseMode':
                    if argv[0] not in ['r','w','wt','wa','rw','rwt']:raise JavaError('Ljava/lang/IllegalArgumentException;','Bad mode')
                    return argv[0]
                if n=='open':return {'file':argv[0]['path'],'mode':argv[1]}
                if n=='valueOf':return argv[0]
                if n=='addRow':argv[0]['row']=argv[1];return None
                return None
            while pc<len(c):
                steps+=1;assert steps<1500,(owner,name,pc)
                w=c[pc];op=w&255;aa=w>>8;a=aa&15;bb=aa>>4
                try:
                    if op==0x12:r[a]=bb if bb<8 else bb-16;pc+=1
                    elif op==0x13:r[aa]=signed(c[pc+1]);pc+=2
                    elif op==0x14:r[aa]=c[pc+1]|(c[pc+2]<<16);pc+=3
                    elif op==0x16:r[aa]=signed(c[pc+1]);r[aa+1]=None;pc+=2
                    elif op==0x1a:r[aa]=self.strings[c[pc+1]];pc+=2
                    elif op==0x22:r[aa]={'class':self.types[c[pc+1]]};pc+=2
                    elif op==0x23:r[a]=[None]*r[bb];pc+=2
                    elif op==0x4d:r[c[pc+1]&255][r[c[pc+1]>>8]]=r[aa];pc+=2
                    elif op==0x1f:pc+=2
                    elif op==0x62:
                        field=self.fields[c[pc+1]];assert field[1]=='ISO_A4',field
                        r[aa]={'class':field[0],'id':'ISO_A4'};pc+=2
                    elif op==0x07:r[a]=r[bb];pc+=1
                    elif op in [0x52,0x54,0x55]:
                        assert 0<=a<regs and 0<=bb<regs
                        r[a]=r[bb].get(self.fields[c[pc+1]][1],None if op==0x54 else 0);pc+=2
                    elif op in [0x59,0x5b,0x5c]:r[bb][self.fields[c[pc+1]][1]]=r[a];pc+=2
                    elif op in [0x6e,0x6f,0x70,0x71,0x72]:
                        count=w>>12;g=(w>>8)&15;packed=c[pc+2];rs=[(packed>>(4*i))&15 for i in range(min(count,4))]+([g] if count==5 else [])
                        assert count<=outs and all(i<regs for i in rs)
                        ret,ps=self.protos[self.methods[c[pc+1]][2]]
                        expected=sum(2 if t in ('J','D') else 1 for t in ps)+(op!=0x71)
                        assert count==expected,(self.methods[c[pc+1]],count,expected)
                        result=invoke(c[pc+1],rs);pc+=3
                    elif op in [0x0a,0x0b,0x0c]:r[aa]=result;pc+=1
                    elif op==0x0d:r[aa]=exception;pc+=1
                    elif op==0x0e:return None
                    elif op in [0x0f,0x10,0x11]:return r[aa]
                    elif op==0x31:
                        x,y=r[c[pc+1]&255],r[c[pc+1]>>8];r[aa]=(x>y)-(x<y);pc+=2
                    elif op in [0x38,0x39]:
                        zero=r[aa] is None or r[aa]==0
                        pc+=signed(c[pc+1]) if zero==(op==0x38) else 2
                    elif op in [0x32,0x33]:pc+=signed(c[pc+1]) if (r[a]==r[bb])==(op==0x32) else 2
                    elif op==0x29:pc+=signed(c[pc+1])
                    elif op==0x27:raise JavaError(r[aa]['class'])
                    else:raise AssertionError((owner,name,pc,hex(op)))
                except JavaError as e:
                    handler=next((h for h in handlers if h[0]<=pc<h[1] and (h[2]==e.kind or h[2]=='Ljava/lang/Exception;')),None)
                    if not handler:raise
                    exception=e;pc=handler[3]
            raise AssertionError('Method fell through')
        return execute(owner,name,args),calls

def verify_native(dex):
    # Fresh Android host setup and WebView security posture remain equivalent.
    owner={};e={'owner':owner};_,c=dex.run(MAIN,'onCreate',[owner,None],e)
    assert owner['webView']['context'] is owner
    loads=[x[2][1] for x in c if x[1]=='loadUrl'];assert loads==['file:///android_asset/index.html'],loads
    # 2.9: app shortcut "Schiri-Zeichen" (long-press on the icon), reusing the running activity.
    sc=e['shortcut_manager']['shortcuts'];assert len(sc)==1,sc;sc=sc[0]
    assert sc['id']=='signs' and sc['setShortLabel']=='Schiri-Zeichen' and sc['setLongLabel']=='Schiri-Zeichen anzeigen' and sc['setIcon']=={'icon':0x7F010000},sc
    it=sc['setIntent'];assert it['action']=='android.intent.action.VIEW' and it['data']=='egrep://signs' and it['component']=='de.michaelnowak.egrepnotes.MainActivity' and it['flags']==0x24000000,it
    for start,url in [({'data':'egrep://signs'},'file:///android_asset/index.html#signs'),({'data':'egrep://other'},'file:///android_asset/index.html'),({},'file:///android_asset/index.html')]:
        o2={};_,c2=dex.run(MAIN,'onCreate',[o2,None],{'owner':o2,'start_intent':start});assert [x[2][1] for x in c2 if x[1]=='loadUrl']==[url],(start,c2[-3:])
    o3={};e3={'owner':o3,'shortcut_error':True};_,c3=dex.run(MAIN,'onCreate',[o3,None],e3)
    assert [x[2][1] for x in c3 if x[1]=='loadUrl']==['file:///android_asset/index.html'] and 'shortcut_manager' not in e3,'start never blocked by shortcuts'
    _,c4=dex.run(MAIN,'onNewIntent',[owner,{'data':'egrep://signs'}],e);assert [x[2][1] for x in c4 if x[1]=='loadUrl']==['javascript:window.egrepOpenSigns&&window.egrepOpenSigns()'],c4
    for other in [{'data':'egrep://x'},{},None]:
        _,c5=dex.run(MAIN,'onNewIntent',[owner,other],e);assert not any(x[1]=='loadUrl' for x in c5),other
    assert any(x[1]=='setDomStorageEnabled' and x[2][1]==1 for x in c)
    view=owner['webView'];client={'owner':owner}
    for cmd,val in [('egrep://screen/on',1),('egrep://screen/off',0)]:
        ret,c=dex.run(LINK,'shouldOverrideUrlLoading',[{},view,cmd],e);assert ret==1 and any(x[1]=='setKeepScreenOn' and x[2][1]==val for x in c)
    for plug in [None,0,1,2,4]:
        e['plugged']=plug;_,c=dex.run(LINK,'shouldOverrideUrlLoading',[{},view,'egrep://power'],e)
        assert ('true' if plug else 'false') in next(x[2][1] for x in c if x[1]=='loadUrl')
    for cmd in ['egrep://print','nevprint://report']:
        _,c=dex.run(LINK,'shouldOverrideUrlLoading',[{},view,cmd],e);assert sum(x[1]=='print' for x in c)==1
        assert next(x[2][1] for x in c if x[1]=='setMediaSize')['id']=='ISO_A4'
        assert next(x[2][1] for x in c if x[1]=='setMinMargins')['margins']==[500]*4
    e['print_available']=False;_,c=dex.run(LINK,'shouldOverrideUrlLoading',[{},view,'egrep://print'],e);assert not any(x[1]=='print' for x in c)
    _,c=dex.run(LINK,'shouldOverrideUrlLoading',[{},view,'https://untrusted.example'],e);assert all(x[1]=='equals' for x in c)
    dex.run(LINK,'onPageFinished',[{},view,'file:///android_asset/index.html'],e);assert owner['pageReady']==1
    # Selecting a gallery photo is a distinct action, never forces the camera.
    ret,c=dex.run(CHOOSE,'onShowFileChooser',[client,view,'cb1',{'capture':False}],e)
    assert ret==1 and e['request']==41 and e['intent']['action']=='PICK'
    dex.run(MAIN,'onActivityResult',[owner,41,-1,{}],e);assert e['deliveries'][-1]==('cb1',['content://gallery/photo']) and owner['fileCallback']==0
    # Full resolution output URI, read+write grant, null camera return Intent.
    dex.run(CHOOSE,'onShowFileChooser',[client,view,'cam1',{'capture':True}],e)
    assert e['request']==42 and e['intent']['action']=='android.media.action.IMAGE_CAPTURE'
    assert e['intent']['extras']['output']==URI and e['intent']['clip']['uri']==URI and e['intent']['flags']==3
    e['files']['/private/cache/egrep-aufstellung.jpg']=4000000
    dex.run(MAIN,'onActivityResult',[owner,42,-1,None],e)
    assert e['deliveries'][-1]==('cam1',[URI]);assert owner['cameraPending']==0
    assert e['files']['/private/cache/egrep-aufstellung.jpg']==4000000
    # Cancelling never supplies a thumbnail or stale image.
    dex.run(CHOOSE,'onShowFileChooser',[client,view,'cam2',{'capture':True}],e)
    dex.run(MAIN,'onActivityResult',[owner,42,0,None],e);assert e['deliveries'][-1]==('cam2',0) and not e['files']
    dex.run(CHOOSE,'onShowFileChooser',[client,view,'cam3',{'capture':True}],e)
    dex.run(MAIN,'onActivityResult',[owner,42,-1,None],e);assert e['deliveries'][-1]==('cam3',0) and e['toasts']
    # Missing camera / permission issue cancels callback and leaves image picker usable.
    e['launch_error']=True;dex.run(CHOOSE,'onShowFileChooser',[client,view,'cam4',{'capture':True}],e)
    assert e['deliveries'][-1]==('cam4',0) and owner['cameraPending']==0 and not e['files'];e['launch_error']=False
    # Previous callback cancelled exactly once when a new request replaces it.
    owner['fileCallback']='old';dex.run(CHOOSE,'onShowFileChooser',[client,view,'new',{'capture':False}],e);assert e['deliveries'][-1]==('old',0)
    n=len(e['deliveries']);dex.run(MAIN,'onActivityResult',[owner,99,-1,{}],e);assert len(e['deliveries'])==n
    dex.run(MAIN,'onActivityResult',[owner,41,0,None],e);assert e['deliveries'][-1]==('new',None)
    # Activity recreation while camera is in foreground. Deliver only when WebView is ready.
    dex.run(CHOOSE,'onShowFileChooser',[client,view,'old-host-callback',{'capture':True}],e)
    saved={};dex.run(MAIN,'onSaveInstanceState',[owner,saved],e);assert saved['cameraPending']
    fresh={};e2={'owner':fresh,'files':{'/private/cache/egrep-aufstellung.jpg':123456}}
    dex.run(MAIN,'onCreate',[fresh,saved],e2);dex.run(MAIN,'onActivityResult',[fresh,42,-1,None],e2)
    assert fresh['cameraRecoveryPending']==1
    _,c=dex.run(LINK,'onPageFinished',[{},fresh['webView'],'file:///android_asset/index.html'],e2)
    assert fresh['cameraRecoveryPending']==0 and any(x[1]=='loadUrl' and "egrepCameraRecovered('file:///private/cache/egrep-aufstellung.jpg')" in x[2][1] for x in c)
    # Reset / remove photo erases the native temporary file as well.
    dex.run(LINK,'shouldOverrideUrlLoading',[{},fresh['webView'],'egrep://photo/clear'],e2);assert not e2['files']
    # Provider never resolves caller-supplied paths; serves one permitted JPEG with metadata.
    provider={'context':owner};e['files']['/private/cache/egrep-aufstellung.jpg']=876543
    ret,_=dex.run(PROVIDER,'getType',[provider,URI],e);assert ret=='image/jpeg'
    ret,_=dex.run(PROVIDER,'query',[provider,URI,None,None,None,None],e);assert ret['columns']==['_display_name','_size'] and ret['row']==['aufstellung.jpg',876543]
    for mode in ['r','w','rw','rwt']:
        ret,_=dex.run(PROVIDER,'openFile',[provider,URI,mode],e);assert ret=={'file':'/private/cache/egrep-aufstellung.jpg','mode':mode}
    for bad in [None,URI+'/../signing',URI+'?file=secrets','file:///etc/passwd',URI.replace('.capture','.other')]:
        try:dex.run(PROVIDER,'openFile',[provider,bad,'r'],e);raise AssertionError('Unsafe URI accepted')
        except JavaError as ex:assert ex.kind=='Ljava/lang/IllegalArgumentException;'
    for method,args in [('insert',[provider,URI,{}]),('delete',[provider,URI,None,None]),('update',[provider,URI,{},None,None])]:
        try:dex.run(PROVIDER,method,args,e);raise AssertionError('Write endpoint accepted')
        except JavaError as ex:assert ex.kind=='Ljava/lang/UnsupportedOperationException;'
    print('PASS native bytecode: gallery, full-size camera, null result, cancellation, missing camera, stale callbacks, activity recovery, reset, isolated provider, keep-screen-on, print, app shortcut Schiri-Zeichen (start with #signs, running app via onNewIntent, start never blocked) and blocked navigation. Simulated Android APIs only.')

if __name__=='__main__':
    with zipfile.ZipFile(sys.argv[1]) as z:verify_native(Dex(z.read('classes.dex')))
