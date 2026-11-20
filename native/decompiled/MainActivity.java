package de.michaelnowak.egrepnotes;
public class MainActivity extends android.app.Activity {
    public boolean cameraPending;
    public boolean cameraRecoveryPending;
    public android.webkit.ValueCallback fileCallback;
    public boolean pageReady;
    public android.webkit.WebView webView;

    public MainActivity()
    {
        return;
    }

    public java.io.File captureFile()
    {
        java.io.File v2_1 = new java.io.File;
        v2_1(this.getCacheDir(), "egrep-aufstellung.jpg");
        return v2_1;
    }

    public android.net.Uri captureUri()
    {
        return android.net.Uri.parse("content://de.michaelnowak.egrepnotes.capture/capture/aufstellung.jpg");
    }

    public void clearCapture()
    {
        this.captureFile().delete();
        return;
    }

    public void deliver(android.net.Uri[] p3)
    {
        android.webkit.ValueCallback v0 = this.fileCallback;
        this.fileCallback = 0;
        if (v0 != null) {
            v0.onReceiveValue(p3);
        }
        return;
    }

    public void notify(String p3)
    {
        android.widget.Toast.makeText(this, p3, 1).show();
        return;
    }

    public void onActivityResult(int p7, int p8, android.content.Intent p9)
    {
        super.onActivityResult(p7, p8, p9);
        if (p7 == 41) {
            this.deliver(android.webkit.WebChromeClient$FileChooserParams.parseResult(p8, p9));
        } else {
            if ((p7 == 42) && (this.cameraPending)) {
                this.cameraPending = 0;
                this.revokeUriPermission(this.captureUri(), 3);
                if (p8 == -1) {
                    if (this.captureFile().length() == 0) {
                        this.notify("Kein Foto gespeichert. Bitte erneut aufnehmen oder ein Foto auswaehlen.");
                    } else {
                        if (this.fileCallback == null) {
                            this.cameraRecoveryPending = 1;
                            this.tryRecoverPhoto();
                            return;
                        } else {
                            int v0_11 = new android.net.Uri[1];
                            v0_11[0] = this.captureUri();
                            this.deliver(v0_11);
                            return;
                        }
                        return;
                    }
                }
                this.clearCapture();
                this.deliver(0);
                return;
            }
        }
        return;
    }

    public void onBackPressed()
    {
        this.webView.loadUrl("javascript:window.egrepBack&&window.egrepBack()");
        return;
    }

    public void onCreate(android.os.Bundle p9)
    {
        super.onCreate(p9);
        if (p9 != null) {
            this.cameraPending = p9.getBoolean("cameraPending");
            this.cameraRecoveryPending = p9.getBoolean("cameraRecoveryPending");
        }
        android.content.pm.ShortcutManager v0_1 = new android.webkit.WebView(this);
        this.webView = v0_1;
        java.util.List v1_0 = v0_1.getSettings();
        v1_0.setJavaScriptEnabled(1);
        v1_0.setDomStorageEnabled(1);
        v1_0.setAllowFileAccess(1);
        v1_0.setAllowContentAccess(1);
        v1_0.setAllowFileAccessFromFileURLs(1);
        v1_0.setAllowUniversalAccessFromFileURLs(1);
        v0_1.setWebViewClient(new de.michaelnowak.egrepnotes.ExternalLinkClient());
        v0_1.setWebChromeClient(new de.michaelnowak.egrepnotes.FileChooserClient(this));
        this.setContentView(v0_1);
        java.util.List v1_5 = "file:///android_asset/index.html";
        android.content.pm.ShortcutInfo$Builder v2_1 = this.getIntent();
        if (v2_1 != null) {
            android.content.pm.ShortcutInfo$Builder v2_2 = v2_1.getDataString();
            if ((v2_2 != null) && ("egrep://signs".equals(v2_2))) {
                v1_5 = "file:///android_asset/index.html#signs";
            }
        }
        v0_1.loadUrl(v1_5);
        try {
            android.content.pm.ShortcutManager v0_4 = this.getSystemService("shortcut");
        } catch (android.content.pm.ShortcutManager v0) {
            return;
        }
        if (v0_4 != null) {
            android.content.pm.ShortcutManager v0_5 = ((android.content.pm.ShortcutManager) v0_4);
            java.util.List v1_8 = new android.content.Intent("android.intent.action.VIEW", android.net.Uri.parse("egrep://signs"));
            v1_8.setClassName(this, "de.michaelnowak.egrepnotes.MainActivity");
            v1_8.addFlags(603979776);
            android.content.pm.ShortcutInfo$Builder v2_9 = new android.content.pm.ShortcutInfo$Builder(this, "signs");
            v2_9.setShortLabel("Schiri-Zeichen");
            v2_9.setLongLabel("Schiri-Zeichen anzeigen");
            v2_9.setIcon(android.graphics.drawable.Icon.createWithResource(this, 2130771968));
            v2_9.setIntent(v1_8);
            v0_5.setDynamicShortcuts(java.util.Collections.singletonList(v2_9.build()));
        }
        return;
    }

    public void onNewIntent(android.content.Intent p4)
    {
        super.onNewIntent(p4);
        if (p4 != null) {
            android.webkit.WebView v0_0 = p4.getDataString();
            if ((v0_0 != null) && ("egrep://signs".equals(v0_0))) {
                android.webkit.WebView v0_2 = this.webView;
                if (v0_2 != null) {
                    v0_2.loadUrl("javascript:window.egrepOpenSigns&&window.egrepOpenSigns()");
                }
            }
        }
        return;
    }

    public void onSaveInstanceState(android.os.Bundle p4)
    {
        super.onSaveInstanceState(p4);
        p4.putBoolean("cameraPending", this.cameraPending);
        p4.putBoolean("cameraRecoveryPending", this.cameraRecoveryPending);
        return;
    }

    public void openChooser(android.webkit.ValueCallback p8, android.webkit.WebChromeClient$FileChooserParams p9)
    {
        this.deliver(0);
        this.fileCallback = p8;
        this.cameraRecoveryPending = 0;
        this.cameraPending = 0;
        try {
            android.content.Intent v0_3;
            int v1_0;
            if (!p9.isCaptureEnabled()) {
                v0_3 = p9.createIntent();
                v1_0 = 41;
            } else {
                this.clearCapture();
                this.captureFile().createNewFile();
                v0_3 = new android.content.Intent("android.media.action.IMAGE_CAPTURE");
                android.net.Uri v2 = this.captureUri();
                v0_3.putExtra("output", v2);
                v0_3.addFlags(3);
                v0_3.setClipData(android.content.ClipData.newRawUri("Aufstellung", v2));
                this.cameraPending = 1;
                v1_0 = 42;
            }
        } catch (android.content.Intent v0) {
            this.cameraPending = 0;
            this.deliver(0);
            this.clearCapture();
            this.notify("Kamera oder Fotoauswahl nicht verfuegbar. Bitte Foto auswaehlen versuchen.");
            return;
        }
        this.startActivityForResult(v0_3, v1_0);
        return;
    }

    public void tryRecoverPhoto()
    {
        if ((this.cameraRecoveryPending) && (this.pageReady)) {
            this.cameraRecoveryPending = 0;
            this.webView.loadUrl("javascript:window.egrepCameraRecovered&&window.egrepCameraRecovered(\'".concat(android.net.Uri.fromFile(this.captureFile()).toString()).concat("\')"));
        }
        return;
    }
}
