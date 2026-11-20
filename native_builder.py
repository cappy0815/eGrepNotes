"""Small SDK-free Dalvik host compiler for eGrep Notes.

Only the Android bridge is emitted here. Its readable Java equivalent is in
app/src/main/java. Bytecode instructions, labels, try/catch and API signatures
are constructed explicitly and regression-tested in tests/test_native_camera.py.
No executable third-party code or SDK download is needed for a rebuild.
"""
import hashlib, struct, zlib
from dataclasses import dataclass


def uleb(n):
    out=bytearray()
    while True:
        b=n&127;n>>=7;out.append(b|(128 if n else 0))
        if not n:return bytes(out)

def align(b):
    while len(b)%4:b.append(0)

def shorty(t):return t if len(t)==1 else 'L'

@dataclass(frozen=True)
class Method:
    owner:str
    name:str
    ret:str
    params:tuple
    @property
    def proto(self):return (self.ret,self.params)

@dataclass(frozen=True)
class Field:
    owner:str
    name:str
    kind:str

class Assembly:
    def __init__(self,b,owner,name,ret,params,regs):
        self.b=b;self.method=Method(owner,name,ret,tuple(params));self.regs=regs
        self.ins=1+sum(2 if t in ('J','D') else 1 for t in params)
        self.outs=0;self.ops=[];self.handlers=[]
        b.methods.add(self.method)
    def add(self,*op):self.ops.append(op);return self
    def label(self,name):return self.add('label',name)
    def const(self,r,n):return self.add('const',r,n)
    def text(self,r,s):self.b.strings.add(s);return self.add('text',r,s)
    def move(self,d,s):return self.add('raw',0x07|(d<<8)|(s<<12))
    def new(self,r,kind):self.b.types.add(kind);return self.add('type',0x22|(r<<8),kind)
    def cast(self,r,kind):self.b.types.add(kind);return self.add('type',0x1f|(r<<8),kind)
    def array(self,d,size,kind):self.b.types.add(kind);return self.add('type',0x23|(d<<8)|(size<<12),kind)
    def aput(self,value,array,index):return self.add('raw',0x4d|(value<<8),array|(index<<8))
    def field(self,get,kind,d,instance,owner,name):
        f=Field(owner,name,kind);self.b.fields.add(f)
        op=(0x54 if kind[0] in 'L[' else 0x55 if kind=='Z' else 0x52) if get else (0x5b if kind[0] in 'L[' else 0x5c if kind=='Z' else 0x59)
        return self.add('field',op|(d<<8)|(instance<<12),f)
    def static_object(self,d,owner,name,kind):
        f=Field(owner,name,kind);self.b.fields.add(f)
        return self.add('field',0x62|(d<<8),f)  # sget-object vAA, field@BBBB
    def call(self,dispatch,owner,name,ret,params,*registers):
        m=Method(owner,name,ret,tuple(params));self.b.methods.add(m)
        count=sum(2 if t in ('J','D') else 1 for t in params)+(dispatch!='static')
        assert count==len(registers),(m,count,registers)
        assert len(registers)<=5 and all(0<=r<16 for r in registers),(m,registers)
        self.outs=max(self.outs,len(registers))
        return self.add('call',{'virtual':0x6e,'super':0x6f,'direct':0x70,'static':0x71,'interface':0x72}[dispatch],m,registers)
    def result(self,r,kind='I'):return self.add('raw',(0x0c if kind[0] in 'L[' else 0x0b if kind in ('J','D') else 0x0a)|(r<<8))
    def ret(self,r=None,kind='I'):return self.add('raw',0x0e if r is None else (0x11 if kind[0] in 'L[' else 0x10 if kind in ('J','D') else 0x0f)|(r<<8))
    def ifz(self,r,label,nonzero=False):return self.add('branch',(0x39 if nonzero else 0x38)|(r<<8),label)
    def ifeq(self,a,b,label,equal=True):return self.add('branch',(0x32 if equal else 0x33)|(a<<8)|(b<<12),label)
    def jump(self,label):return self.add('branch',0x29,label)
    def cmp_long(self,d,a,b):return self.add('raw',0x31|(d<<8),a|(b<<8))
    def long_zero(self,r):return self.add('raw',0x16|(r<<8),0)
    def caught(self,r):return self.add('raw',0x0d|(r<<8))
    def throw(self,r):return self.add('raw',0x27|(r<<8))
    def catch(self,start,end,handler,kind):self.b.types.add(kind);self.handlers.append((start,end,handler,kind))
    def encode(self,si,ti,mi,fi):
        code=[];labels={};fix=[]
        for op in self.ops:
            tag=op[0]
            if tag=='label':labels[op[1]]=len(code)
            elif tag=='raw':code.extend(op[1:])
            elif tag=='const':
                r,n=op[1:]
                if -8<=n<=7:code.append(0x12|(r<<8)|((n&15)<<12))
                elif -32768<=n<=32767:code.extend([0x13|(r<<8),n&65535])
                else:code.extend([0x14|(r<<8),n&65535,(n>>16)&65535])
            elif tag=='text':code.extend([0x1a|(op[1]<<8),si[op[2]]])
            elif tag=='type':code.extend([op[1],ti[op[2]]])
            elif tag=='field':code.extend([op[1],fi[op[2]]])
            elif tag=='call':
                opcode,m,rs=op[1:];packed=sum(r<<(4*i) for i,r in enumerate(rs[:4]))
                code.extend([opcode|(len(rs)<<12)|((rs[4] if len(rs)==5 else 0)<<8),mi[m],packed])
            elif tag=='branch':fix.append((len(code),op[2]));code.extend([op[1],0])
            else:raise ValueError(tag)
        for at,label in fix:
            d=labels[label]-at;assert -32768<=d<=32767;code[at+1]=d&65535
        head=struct.pack('<HHHHII',self.regs,self.ins,self.outs,len(self.handlers),0,len(code))
        payload=bytearray(head+struct.pack('<'+'H'*len(code),*code))
        if self.handlers:
            if len(code)%2:payload+=b'\0\0'
            encoded=bytearray(uleb(len(self.handlers)));items=[]
            for start,end,handler,kind in self.handlers:
                at=len(encoded);encoded+=b'\x01'+uleb(ti[kind])+uleb(labels[handler])
                items.append(struct.pack('<IHH',labels[start],labels[end]-labels[start],at))
            payload+=b''.join(items)+encoded
        return bytes(payload)

class Builder:
    def __init__(self):self.methods=set();self.fields=set();self.types=set();self.strings=set();self.classes={};self.code=[]
    def cls(self,name,superclass):self.types.update([name,superclass]);self.classes[name]=superclass
    def method(self,owner,name,ret,params,regs):
        a=Assembly(self,owner,name,ret,params,regs);self.code.append(a);return a
    def build(self):
        for m in self.methods:self.types.update([m.owner,m.ret,*m.params]);self.strings.add(m.name)
        for f in self.fields:self.types.update([f.owner,f.kind]);self.strings.add(f.name)
        protos={m.proto for m in self.methods}
        for r,ps in protos:self.strings.add(shorty(r)+''.join(map(shorty,ps)))
        strings=sorted(self.strings|self.types);si={v:i for i,v in enumerate(strings)}
        types=sorted(self.types,key=si.get);ti={v:i for i,v in enumerate(types)}
        protos=sorted(protos,key=lambda p:(ti[p[0]],tuple(ti[t] for t in p[1])));pi={v:i for i,v in enumerate(protos)}
        methods=sorted(self.methods,key=lambda m:(ti[m.owner],si[m.name],pi[m.proto]));mi={v:i for i,v in enumerate(methods)}
        fields=sorted(self.fields,key=lambda f:(ti[f.owner],si[f.name],ti[f.kind]));fi={v:i for i,v in enumerate(fields)}
        off_s=112;off_t=off_s+4*len(strings);off_p=off_t+4*len(types);off_f=off_p+12*len(protos)
        off_m=off_f+8*len(fields);off_c=off_m+8*len(methods);off_d=off_c+32*len(self.classes)
        data=bytearray();s_offsets=[]
        for s in strings:
            s_offsets.append(off_d+len(data));data+=uleb(len(s.encode('utf-16-le'))//2)+s.encode('utf-8')+b'\0'
        align(data);type_lists={};first_tl=off_d+len(data)
        for ps in sorted({p[1] for p in protos if p[1]}):
            align(data);type_lists[ps]=off_d+len(data);data+=struct.pack('<I',len(ps))+struct.pack('<'+'H'*len(ps),*(ti[x] for x in ps));align(data)
        first_code=off_d+len(data);co={}
        for a in self.code:
            align(data);co[a.method]=off_d+len(data);data+=a.encode(si,ti,mi,fi)
        align(data);first_cd=off_d+len(data);class_data={}
        for cls in sorted(self.classes,key=ti.get):
            class_data[cls]=off_d+len(data)
            fs=[f for f in fields if f.owner==cls]
            direct=sorted([a.method for a in self.code if a.method.owner==cls and a.method.name=='<init>'],key=mi.get)
            virtual=sorted([a.method for a in self.code if a.method.owner==cls and a.method.name!='<init>'],key=mi.get)
            data+=uleb(0)+uleb(len(fs))+uleb(len(direct))+uleb(len(virtual));prev=0
            for f in fs:data+=uleb(fi[f]-prev)+uleb(1);prev=fi[f]
            for group in (direct,virtual):
                prev=0
                for m in group:data+=uleb(mi[m]-prev)+uleb(0x10001 if m.name=='<init>' else 1)+uleb(co[m]);prev=mi[m]
        align(data);mapoff=off_d+len(data)
        entries=[(0x0000,1,0),(0x0001,len(strings),off_s),(0x0002,len(types),off_t),(0x0003,len(protos),off_p),(0x0004,len(fields),off_f),(0x0005,len(methods),off_m),(0x0006,len(self.classes),off_c),(0x1000,1,mapoff),(0x1001,len(type_lists),first_tl),(0x2000,len(self.classes),first_cd),(0x2001,len(self.code),first_code),(0x2002,len(strings),off_d)]
        entries=[x for x in entries if x[1]];data+=struct.pack('<I',len(entries))
        for kind,n,off in sorted(entries,key=lambda x:x[2]):data+=struct.pack('<HHII',kind,0,n,off)
        dex=bytearray(off_d+len(data));dex[:8]=b'dex\n035\0'
        for i,o in enumerate(s_offsets):struct.pack_into('<I',dex,off_s+4*i,o)
        for i,t in enumerate(types):struct.pack_into('<I',dex,off_t+4*i,si[t])
        for i,(r,ps) in enumerate(protos):struct.pack_into('<III',dex,off_p+12*i,si[shorty(r)+''.join(map(shorty,ps))],ti[r],type_lists.get(ps,0))
        for i,f in enumerate(fields):struct.pack_into('<HHI',dex,off_f+8*i,ti[f.owner],ti[f.kind],si[f.name])
        for i,m in enumerate(methods):struct.pack_into('<HHI',dex,off_m+8*i,ti[m.owner],pi[m.proto],si[m.name])
        for i,cls in enumerate(sorted(self.classes,key=ti.get)):struct.pack_into('<IIIIIIII',dex,off_c+32*i,ti[cls],1,ti[self.classes[cls]],0,0xffffffff,0,class_data[cls],0)
        dex[off_d:]=data
        struct.pack_into('<20I',dex,32,len(dex),112,0x12345678,0,0,mapoff,len(strings),off_s,len(types),off_t,len(protos),off_p,len(fields),off_f,len(methods),off_m,len(self.classes),off_c,len(data),off_d)
        dex[12:32]=hashlib.sha1(dex[32:]).digest();struct.pack_into('<I',dex,8,zlib.adler32(dex[12:])&0xffffffff)
        return bytes(dex)


def build_native_dex(package):
    b=Builder()
    MAIN='L'+package.replace('.','/')+'/MainActivity;';LINK=MAIN.replace('MainActivity;','ExternalLinkClient;');CHOOSE=MAIN.replace('MainActivity;','FileChooserClient;');PROVIDER=MAIN.replace('MainActivity;','CaptureProvider;')
    ACT='Landroid/app/Activity;';CTX='Landroid/content/Context;';BUNDLE='Landroid/os/Bundle;';VIEW='Landroid/view/View;';WV='Landroid/webkit/WebView;';WVC='Landroid/webkit/WebViewClient;';WC='Landroid/webkit/WebChromeClient;';PARAM='Landroid/webkit/WebChromeClient$FileChooserParams;';SET='Landroid/webkit/WebSettings;';CB='Landroid/webkit/ValueCallback;'
    STR='Ljava/lang/String;';OBJ='Ljava/lang/Object;';URI='Landroid/net/Uri;';INTENT='Landroid/content/Intent;';FILE='Ljava/io/File;';PFD='Landroid/os/ParcelFileDescriptor;';CP='Landroid/content/ContentProvider;';CUR='Landroid/database/Cursor;';MC='Landroid/database/MatrixCursor;';CV='Landroid/content/ContentValues;';TOAST='Landroid/widget/Toast;';EX='Ljava/lang/Exception;';FNF='Ljava/lang/IllegalArgumentException;';UNSUPPORTED='Ljava/lang/UnsupportedOperationException;'
    UARR='['+URI;SARR='['+STR;OARR='['+OBJ
    uri='content://'+package+'.capture/capture/aufstellung.jpg'
    def m(cls,name,ret,params,regs):return b.method(cls,name,ret,params,regs)
    def call(a,owner,name,ret,params,*rs,kind='virtual'):a.call(kind,owner,name,ret,params,*rs)
    def f(a,get,name,kind,r,who):a.field(get,kind,r,who,MAIN,name)
    for cls,sup in [(MAIN,ACT),(LINK,WVC),(CHOOSE,WC),(PROVIDER,CP)]:
        b.cls(cls,sup);a=m(cls,'<init>','V',[MAIN] if cls==CHOOSE else [],2 if cls==CHOOSE else 1)
        call(a,sup,'<init>','V',[],0,kind='direct')
        if cls==CHOOSE:a.field(False,MAIN,1,0,CHOOSE,'owner')
        a.ret()
    a=m(MAIN,'captureFile',FILE,[],3);call(a,CTX,'getCacheDir',FILE,[],2);a.result(0,FILE);a.text(1,'egrep-aufstellung.jpg');a.new(2,FILE);call(a,FILE,'<init>','V',[FILE,STR],2,0,1,kind='direct');a.ret(2,FILE)
    a=m(MAIN,'captureUri',URI,[],2);a.text(0,uri);call(a,URI,'parse',URI,[STR],0,kind='static');a.result(0,URI);a.ret(0,URI)
    a=m(MAIN,'clearCapture','V',[],2);call(a,MAIN,'captureFile',FILE,[],1);a.result(0,FILE);call(a,FILE,'delete','Z',[],0);a.ret()
    a=m(MAIN,'notify','V',[STR],4);a.const(0,1);call(a,TOAST,'makeText',TOAST,[CTX,'Ljava/lang/CharSequence;','I'],2,3,0,kind='static');a.result(0,TOAST);call(a,TOAST,'show','V',[],0);a.ret()
    a=m(MAIN,'deliver','V',[UARR],4);f(a,True,'fileCallback',CB,0,2);a.const(1,0);f(a,False,'fileCallback',CB,1,2);a.ifz(0,'done');call(a,CB,'onReceiveValue','V',[OBJ],0,3,kind='interface');a.label('done');a.ret()
    a=m(MAIN,'onCreate','V',[BUNDLE],10);call(a,ACT,'onCreate','V',[BUNDLE],8,9,kind='super')
    a.ifz(9,'view');a.text(0,'cameraPending');call(a,BUNDLE,'getBoolean','Z',[STR],9,0);a.result(0);f(a,False,'cameraPending','Z',0,8)
    a.text(0,'cameraRecoveryPending');call(a,BUNDLE,'getBoolean','Z',[STR],9,0);a.result(0);f(a,False,'cameraRecoveryPending','Z',0,8)
    a.label('view');a.new(0,WV);call(a,WV,'<init>','V',[CTX],0,8,kind='direct');f(a,False,'webView',WV,0,8)
    call(a,WV,'getSettings',SET,[],0);a.result(1,SET);a.const(2,1)
    for name in ['setJavaScriptEnabled','setDomStorageEnabled','setAllowFileAccess','setAllowContentAccess','setAllowFileAccessFromFileURLs','setAllowUniversalAccessFromFileURLs']:call(a,SET,name,'V',['Z'],1,2)
    a.new(1,LINK);call(a,LINK,'<init>','V',[],1,kind='direct');call(a,WV,'setWebViewClient','V',[WVC],0,1)
    a.new(1,CHOOSE);call(a,CHOOSE,'<init>','V',[MAIN],1,8,kind='direct');call(a,WV,'setWebChromeClient','V',[WC],0,1)
    call(a,ACT,'setContentView','V',[VIEW],8,0);a.text(1,'file:///android_asset/index.html')
    # 2.9: started from the app shortcut "Schiri-Zeichen" -> open the page with #signs.
    call(a,ACT,'getIntent',INTENT,[],8);a.result(2,INTENT);a.ifz(2,'urlDone');call(a,INTENT,'getDataString',STR,[],2);a.result(2,STR);a.ifz(2,'urlDone')
    a.text(3,'egrep://signs');call(a,STR,'equals','Z',[OBJ],3,2);a.result(2);a.ifz(2,'urlDone');a.text(1,'file:///android_asset/index.html#signs')
    a.label('urlDone');call(a,WV,'loadUrl','V',[STR],0,1)
    # 2.9: dynamic shortcut on long-press of the app icon (API 25+, minSdk is 26). Never blocks the start.
    SM='Landroid/content/pm/ShortcutManager;';SB='Landroid/content/pm/ShortcutInfo$Builder;';SI='Landroid/content/pm/ShortcutInfo;';ICON='Landroid/graphics/drawable/Icon;';CS='Ljava/lang/CharSequence;';LIST='Ljava/util/List;'
    a.label('scTry');a.text(1,'shortcut');call(a,CTX,'getSystemService',OBJ,[STR],8,1);a.result(0,OBJ);a.ifz(0,'scEnd');a.cast(0,SM)
    a.text(2,'egrep://signs');call(a,URI,'parse',URI,[STR],2,kind='static');a.result(3,URI);a.new(1,INTENT);a.text(2,'android.intent.action.VIEW');call(a,INTENT,'<init>','V',[STR,URI],1,2,3,kind='direct')
    a.text(2,MAIN[1:-1].replace('/','.'));call(a,INTENT,'setClassName',INTENT,[CTX,STR],1,8,2)
    a.const(2,0x24000000);call(a,INTENT,'addFlags',INTENT,['I'],1,2)  # SINGLE_TOP|CLEAR_TOP: reuse the running game, no reset
    a.new(2,SB);a.text(3,'signs');call(a,SB,'<init>','V',[CTX,STR],2,8,3,kind='direct')
    a.text(3,'Schiri-Zeichen');call(a,SB,'setShortLabel',SB,[CS],2,3);a.text(3,'Schiri-Zeichen anzeigen');call(a,SB,'setLongLabel',SB,[CS],2,3)
    a.const(3,0x7F010000);call(a,ICON,'createWithResource',ICON,[CTX,'I'],8,3,kind='static');a.result(3,ICON);call(a,SB,'setIcon',SB,[ICON],2,3)
    call(a,SB,'setIntent',SB,[INTENT],2,1);call(a,SB,'build',SI,[],2);a.result(1,SI)
    call(a,'Ljava/util/Collections;','singletonList',LIST,[OBJ],1,kind='static');a.result(1,LIST);call(a,SM,'setDynamicShortcuts','Z',[LIST],0,1)
    a.label('scEnd');a.ret();a.label('scFail');a.caught(0);a.ret();a.catch('scTry','scEnd','scFail',EX)
    a=m(MAIN,'onNewIntent','V',[INTENT],5);call(a,ACT,'onNewIntent','V',[INTENT],3,4,kind='super');a.ifz(4,'done')
    call(a,INTENT,'getDataString',STR,[],4);a.result(0,STR);a.ifz(0,'done');a.text(1,'egrep://signs');call(a,STR,'equals','Z',[OBJ],1,0);a.result(0);a.ifz(0,'done')
    f(a,True,'webView',WV,0,3);a.ifz(0,'done');a.text(1,'javascript:window.egrepOpenSigns&&window.egrepOpenSigns()');call(a,WV,'loadUrl','V',[STR],0,1);a.label('done');a.ret()
    a=m(MAIN,'onSaveInstanceState','V',[BUNDLE],5);call(a,ACT,'onSaveInstanceState','V',[BUNDLE],3,4,kind='super')
    for name in ['cameraPending','cameraRecoveryPending']:
        a.text(0,name);f(a,True,name,'Z',1,3);call(a,BUNDLE,'putBoolean','V',[STR,'Z'],4,0,1)
    a.ret()
    a=m(MAIN,'onBackPressed','V',[],3);f(a,True,'webView',WV,0,2);a.text(1,'javascript:window.egrepBack&&window.egrepBack()');call(a,WV,'loadUrl','V',[STR],0,1);a.ret()
    # Incoming FileChooser capture preference distinguishes both HTML inputs.
    a=m(CHOOSE,'onShowFileChooser','Z',[WV,CB,PARAM],6);a.field(True,MAIN,0,2,CHOOSE,'owner');call(a,MAIN,'openChooser','V',[CB,PARAM],0,4,5);a.const(0,1);a.ret(0)
    a=m(MAIN,'openChooser','V',[CB,PARAM],10);a.const(0,0);call(a,MAIN,'deliver','V',[UARR],7,0);f(a,False,'fileCallback',CB,8,7)
    f(a,False,'cameraRecoveryPending','Z',0,7);f(a,False,'cameraPending','Z',0,7)
    a.label('try');call(a,PARAM,'isCaptureEnabled','Z',[],9);a.result(0);a.ifz(0,'pick')
    call(a,MAIN,'clearCapture','V',[],7);call(a,MAIN,'captureFile',FILE,[],7);a.result(0,FILE);call(a,FILE,'createNewFile','Z',[],0)
    a.new(0,INTENT);a.text(1,'android.media.action.IMAGE_CAPTURE');call(a,INTENT,'<init>','V',[STR],0,1,kind='direct')
    call(a,MAIN,'captureUri',URI,[],7);a.result(2,URI);a.text(1,'output');call(a,INTENT,'putExtra',INTENT,[STR,'Landroid/os/Parcelable;'],0,1,2)
    a.const(1,3);call(a,INTENT,'addFlags',INTENT,['I'],0,1)
    # Explicit ClipData helps camera providers consistently receive temporary URI permissions.
    a.text(1,'Aufstellung');call(a,'Landroid/content/ClipData;','newRawUri','Landroid/content/ClipData;',['Ljava/lang/CharSequence;',URI],1,2,kind='static');a.result(1,'Landroid/content/ClipData;');call(a,INTENT,'setClipData','V',['Landroid/content/ClipData;'],0,1)
    a.const(1,1);f(a,False,'cameraPending','Z',1,7);a.const(1,42);a.jump('launch')
    a.label('pick');call(a,PARAM,'createIntent',INTENT,[],9);a.result(0,INTENT);a.const(1,41)
    a.label('launch');call(a,ACT,'startActivityForResult','V',[INTENT,'I'],7,0,1);a.label('tryEnd');a.ret()
    a.label('failed');a.caught(0);a.const(0,0);f(a,False,'cameraPending','Z',0,7);call(a,MAIN,'deliver','V',[UARR],7,0)
    call(a,MAIN,'clearCapture','V',[],7);a.text(0,'Kamera oder Fotoauswahl nicht verfuegbar. Bitte Foto auswaehlen versuchen.');call(a,MAIN,'notify','V',[STR],7,0);a.ret();a.catch('try','tryEnd','failed',EX)
    # 3.2: backup. saveBackup("name&json") keeps the JSON and asks where to save it (CREATE_DOCUMENT).
    a=m(MAIN,'saveBackup','V',[STR],6);a.label('try')
    a.text(0,'&');call(a,STR,'indexOf','I',[STR],5,0);a.result(0);a.add('branch',0x3a|(0<<8),'fail')
    a.const(1,0);call(a,STR,'substring',STR,['I','I'],5,1,0);a.result(1,STR);call(a,URI,'decode',STR,[STR],1,kind='static');a.result(1,STR)
    a.add('raw',0xd8|(2<<8),0|(1<<8));call(a,STR,'substring',STR,['I'],5,2);a.result(2,STR);call(a,URI,'decode',STR,[STR],2,kind='static');a.result(2,STR)
    f(a,False,'backupData',STR,2,4)
    a.new(3,INTENT);a.text(0,'android.intent.action.CREATE_DOCUMENT');call(a,INTENT,'<init>','V',[STR],3,0,kind='direct')
    a.text(0,'android.intent.category.OPENABLE');call(a,INTENT,'addCategory',INTENT,[STR],3,0)
    a.text(0,'application/json');call(a,INTENT,'setType',INTENT,[STR],3,0)
    a.text(0,'android.intent.extra.TITLE');call(a,INTENT,'putExtra',INTENT,[STR,STR],3,0,1)
    a.const(0,43);call(a,ACT,'startActivityForResult','V',[INTENT,'I'],4,3,0);a.label('tryEnd');a.ret()
    a.label('fail');a.const(0,0);call(a,MAIN,'backupDone','V',['Z'],4,0);a.ret()
    a.label('caught');a.caught(0);a.const(0,0);call(a,MAIN,'backupDone','V',['Z'],4,0);a.ret();a.catch('try','tryEnd','caught',EX)
    a=m(MAIN,'saveBackupResult','V',['I',INTENT],7);a.label('try')
    a.const(0,-1);a.ifeq(5,0,'no',False);a.ifz(6,'no');call(a,INTENT,'getData',URI,[],6);a.result(0,URI);a.ifz(0,'no')
    f(a,True,'backupData',STR,1,4);a.ifz(1,'no')
    CR='Landroid/content/ContentResolver;';OS='Ljava/io/OutputStream;'
    call(a,CTX,'getContentResolver',CR,[],4);a.result(2,CR);call(a,CR,'openOutputStream',OS,[URI],2,0);a.result(2,OS);a.ifz(2,'no')
    a.text(3,'UTF-8');call(a,STR,'getBytes','[B',[STR],1,3);a.result(3,'[B');call(a,OS,'write','V',['[B'],2,3);call(a,OS,'close','V',[],2)
    a.const(0,0);f(a,False,'backupData',STR,0,4);a.const(0,1);call(a,MAIN,'backupDone','V',['Z'],4,0);a.label('tryEnd');a.ret()
    a.label('no');a.const(0,0);f(a,False,'backupData',STR,0,4);call(a,MAIN,'backupDone','V',['Z'],4,0);a.ret()
    a.label('caught');a.caught(0);a.const(0,0);f(a,False,'backupData',STR,0,4);call(a,MAIN,'backupDone','V',['Z'],4,0);a.ret();a.catch('try','tryEnd','caught',EX)
    a=m(MAIN,'backupDone','V',['Z'],4);f(a,True,'webView',WV,0,2);a.ifz(0,'done');a.ifz(3,'bad')
    a.text(1,'javascript:window.egrepBackupSaved&&window.egrepBackupSaved(true)');a.jump('send');a.label('bad');a.text(1,'javascript:window.egrepBackupSaved&&window.egrepBackupSaved(false)')
    a.label('send');call(a,WV,'loadUrl','V',[STR],0,1);a.label('done');a.ret()
    a=m(MAIN,'onActivityResult','V',['I','I',INTENT],10);call(a,ACT,'onActivityResult','V',['I','I',INTENT],6,7,8,9,kind='super')
    a.const(0,43);a.ifeq(7,0,'notBackup',False);call(a,MAIN,'saveBackupResult','V',['I',INTENT],6,8,9);a.ret();a.label('notBackup')
    a.const(0,41);a.ifeq(7,0,'picker');a.const(0,42);a.ifeq(7,0,'done',False)
    f(a,True,'cameraPending','Z',0,6);a.ifz(0,'done');a.const(0,0);f(a,False,'cameraPending','Z',0,6)
    call(a,MAIN,'captureUri',URI,[],6);a.result(0,URI);a.const(1,3);call(a,CTX,'revokeUriPermission','V',[URI,'I'],6,0,1)
    a.const(0,-1);a.ifeq(8,0,'cancel',False)
    call(a,MAIN,'captureFile',FILE,[],6);a.result(0,FILE);call(a,FILE,'length','J',[],0);a.result(0,'J');a.long_zero(2);a.cmp_long(0,0,2);a.ifz(0,'empty')
    f(a,True,'fileCallback',CB,0,6);a.ifz(0,'recover')
    a.const(1,1);a.array(0,1,UARR);call(a,MAIN,'captureUri',URI,[],6);a.result(1,URI);a.const(2,0);a.aput(1,0,2);call(a,MAIN,'deliver','V',[UARR],6,0);a.ret()
    a.label('recover');a.const(0,1);f(a,False,'cameraRecoveryPending','Z',0,6);call(a,MAIN,'tryRecoverPhoto','V',[],6);a.ret()
    a.label('empty');a.text(0,'Kein Foto gespeichert. Bitte erneut aufnehmen oder ein Foto auswaehlen.');call(a,MAIN,'notify','V',[STR],6,0)
    a.label('cancel');call(a,MAIN,'clearCapture','V',[],6);a.const(0,0);call(a,MAIN,'deliver','V',[UARR],6,0);a.ret()
    a.label('picker');call(a,PARAM,'parseResult',UARR,['I',INTENT],8,9,kind='static');a.result(0,UARR);call(a,MAIN,'deliver','V',[UARR],6,0)
    a.label('done');a.ret()
    a=m(MAIN,'tryRecoverPhoto','V',[],4);f(a,True,'cameraRecoveryPending','Z',0,3);a.ifz(0,'done');f(a,True,'pageReady','Z',0,3);a.ifz(0,'done')
    a.const(0,0);f(a,False,'cameraRecoveryPending','Z',0,3)
    call(a,MAIN,'captureFile',FILE,[],3);a.result(0,FILE);call(a,URI,'fromFile',URI,[FILE],0,kind='static');a.result(0,URI);call(a,URI,'toString',STR,[],0);a.result(0,STR)
    a.text(1,"javascript:window.egrepCameraRecovered&&window.egrepCameraRecovered('");call(a,STR,'concat',STR,[STR],1,0);a.result(0,STR);a.text(1,"')");call(a,STR,'concat',STR,[STR],0,1);a.result(1,STR)
    f(a,True,'webView',WV,0,3);call(a,WV,'loadUrl','V',[STR],0,1);a.label('done');a.ret()
    a=m(LINK,'onPageFinished','V',[WV,STR],5);a.text(0,'javascript:window.egrepHostReady&&window.egrepHostReady()');call(a,WV,'loadUrl','V',[STR],3,0)
    call(a,VIEW,'getContext',CTX,[],3);a.result(0,CTX);a.cast(0,MAIN);a.const(1,1);f(a,False,'pageReady','Z',1,0);call(a,MAIN,'tryRecoverPhoto','V',[],0);a.ret()
    a=m(LINK,'shouldOverrideUrlLoading','Z',[WV,STR],10)
    def cmd(s,nextlabel):a.text(0,s);call(a,STR,'equals','Z',[OBJ],9,0);a.result(0);a.ifz(0,nextlabel)
    def done():a.const(0,1);a.ret(0)
    cmd('egrep://screen/on','off');a.const(0,1);call(a,VIEW,'setKeepScreenOn','V',['Z'],8,0);done()
    a.label('off');cmd('egrep://screen/off','power');a.const(0,0);call(a,VIEW,'setKeepScreenOn','V',['Z'],8,0);done()
    a.label('power');cmd('egrep://power','print')
    call(a,VIEW,'getContext',CTX,[],8);a.result(0,CTX);FIL='Landroid/content/IntentFilter;';a.new(1,FIL);a.text(2,'android.intent.action.BATTERY_CHANGED');call(a,FIL,'<init>','V',[STR],1,2,kind='direct')
    a.const(2,0);call(a,CTX,'registerReceiver',INTENT,['Landroid/content/BroadcastReceiver;',FIL],0,2,1);a.result(0,INTENT);a.ifz(0,'powerOff')
    a.text(1,'plugged');a.const(2,0);call(a,INTENT,'getIntExtra','I',[STR,'I'],0,1,2);a.result(0);a.ifz(0,'powerOn',True)
    a.label('powerOff');a.text(0,'javascript:window.egrepPower&&window.egrepPower(false)');a.jump('powerSend')
    a.label('powerOn');a.text(0,'javascript:window.egrepPower&&window.egrepPower(true)')
    a.label('powerSend');call(a,WV,'loadUrl','V',[STR],8,0);done()
    a.label('print');cmd('egrep://print','legacy');a.jump('doPrint');a.label('legacy');cmd('nevprint://report','photo')
    a.label('doPrint');call(a,VIEW,'getContext',CTX,[],8);a.result(0,CTX);a.text(1,'print');call(a,CTX,'getSystemService',OBJ,[STR],0,1);a.result(0,OBJ);a.ifz(0,'blocked')
    PM='Landroid/print/PrintManager;';PA='Landroid/print/PrintAttributes;';PB='Landroid/print/PrintAttributes$Builder;';PD='Landroid/print/PrintDocumentAdapter;';a.cast(0,PM);a.text(1,'eGrep Notes - Spielbericht')
    call(a,WV,'createPrintDocumentAdapter',PD,[STR],8,1);a.result(2,PD);a.new(3,PB);call(a,PB,'<init>','V',[],3,kind='direct')
    # A4 default and 12.7 mm margins match the conservative JS 184 x 263 mm box.
    MS='Landroid/print/PrintAttributes$MediaSize;';MG='Landroid/print/PrintAttributes$Margins;'
    a.static_object(4,MS,'ISO_A4',MS);call(a,PB,'setMediaSize',PB,[MS],3,4)
    a.new(4,MG);a.const(5,500);call(a,MG,'<init>','V',['I','I','I','I'],4,5,5,5,5,kind='direct');call(a,PB,'setMinMargins',PB,[MG],3,4)
    call(a,PB,'build',PA,[],3);a.result(3,PA);call(a,PM,'print','Landroid/print/PrintJob;',[STR,PD,PA],0,1,2,3);done()
    a.label('photo');cmd('egrep://photo/clear','exit');call(a,VIEW,'getContext',CTX,[],8);a.result(0,CTX);a.cast(0,MAIN);call(a,MAIN,'clearCapture','V',[],0);done()
    a.label('exit');cmd('egrep://exit','backup');call(a,VIEW,'getContext',CTX,[],8);a.result(0,CTX);a.cast(0,ACT);call(a,ACT,'finish','V',[],0);done()
    # 2.8: exactly one external link (project page in the Info dialog) opens the browser; everything else stays blocked.
    # 3.2: backup file (payload "name&json", URL-encoded) -> Storage Access Framework dialog.
    a.label('backup');a.text(0,'egrep://backup?');call(a,STR,'startsWith','Z',[STR],9,0);a.result(0);a.ifz(0,'site')
    a.const(0,15);call(a,STR,'substring',STR,['I'],9,0);a.result(1,STR);call(a,VIEW,'getContext',CTX,[],8);a.result(0,CTX);a.cast(0,MAIN);call(a,MAIN,'saveBackup','V',[STR],0,1);done()
    # 2.8/3.2: only pages below https://cappy0815.github.io/ open the browser (project page, update download).
    a.label('site');a.text(0,'https://cappy0815.github.io/');call(a,STR,'startsWith','Z',[STR],9,0);a.result(0);a.ifz(0,'blocked');a.label('siteTry')
    call(a,URI,'parse',URI,[STR],9,kind='static');a.result(1,URI);a.new(0,INTENT);a.text(2,'android.intent.action.VIEW');call(a,INTENT,'<init>','V',[STR,URI],0,2,1,kind='direct')
    a.const(1,0x10000000);call(a,INTENT,'addFlags',INTENT,['I'],0,1);call(a,VIEW,'getContext',CTX,[],8);a.result(1,CTX);call(a,CTX,'startActivity','V',[INTENT],1,0);a.label('siteEnd');done()
    a.label('siteFail');a.caught(0);done();a.catch('siteTry','siteEnd','siteFail',EX)
    a.label('blocked');done()
    # Provider is not exported and serves exactly ONE app-private temporary file.
    a=m(PROVIDER,'onCreate','Z',[],2);a.const(0,1);a.ret(0)
    a=m(PROVIDER,'checkUri','V',[URI],4);a.ifz(3,'bad');call(a,URI,'toString',STR,[],3);a.result(0,STR);a.text(1,uri);call(a,STR,'equals','Z',[OBJ],0,1);a.result(0);a.ifz(0,'ok',True)
    a.label('bad');a.new(0,FNF);a.text(1,'Unknown capture URI');call(a,FNF,'<init>','V',[STR],0,1,kind='direct');a.throw(0);a.label('ok');a.ret()
    a=m(PROVIDER,'captureFile',FILE,[],4);call(a,CP,'getContext',CTX,[],3);a.result(0,CTX);call(a,CTX,'getCacheDir',FILE,[],0);a.result(0,FILE);a.text(1,'egrep-aufstellung.jpg');a.new(2,FILE);call(a,FILE,'<init>','V',[FILE,STR],2,0,1,kind='direct');a.ret(2,FILE)
    a=m(PROVIDER,'openFile',PFD,[URI,STR],6);call(a,PROVIDER,'checkUri','V',[URI],3,4);call(a,PROVIDER,'captureFile',FILE,[],3);a.result(0,FILE);call(a,PFD,'parseMode','I',[STR],5,kind='static');a.result(1);call(a,PFD,'open',PFD,[FILE,'I'],0,1,kind='static');a.result(0,PFD);a.ret(0,PFD)
    a=m(PROVIDER,'getType',STR,[URI],3);call(a,PROVIDER,'checkUri','V',[URI],1,2);a.text(0,'image/jpeg');a.ret(0,STR)
    a=m(PROVIDER,'query',CUR,[URI,SARR,STR,SARR,STR],12);call(a,PROVIDER,'checkUri','V',[URI],6,7)
    a.const(0,2);a.array(1,0,SARR);a.const(2,0);a.text(3,'_display_name');a.aput(3,1,2);a.const(2,1);a.text(3,'_size');a.aput(3,1,2)
    a.new(3,MC);call(a,MC,'<init>','V',[SARR],3,1,kind='direct');a.array(1,0,OARR);a.const(2,0);a.text(0,'aufstellung.jpg');a.aput(0,1,2)
    call(a,PROVIDER,'captureFile',FILE,[],6);a.result(0,FILE);call(a,FILE,'length','J',[],0);a.result(4,'J');call(a,'Ljava/lang/Long;','valueOf','Ljava/lang/Long;',['J'],4,5,kind='static');a.result(0,OBJ);a.const(2,1);a.aput(0,1,2);call(a,MC,'addRow','V',[OARR],3,1);a.ret(3,CUR)
    for name,ret,ps in [('insert',URI,[URI,CV]),('delete','I',[URI,STR,SARR]),('update','I',[URI,CV,STR,SARR])]:
        a=m(PROVIDER,name,ret,ps,len(ps)+3);a.new(0,UNSUPPORTED);a.text(1,'Only temporary camera files are supported');call(a,UNSUPPORTED,'<init>','V',[STR],0,1,kind='direct');a.throw(0)
    return b.build()
