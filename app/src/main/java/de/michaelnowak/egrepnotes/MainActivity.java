package de.michaelnowak.egrepnotes;

import android.app.Activity;
import android.content.ClipData;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.widget.Toast;
import java.io.File;

/** Local WebView host. Keep in sync with native_builder.py (the delivered build). */
public final class MainActivity extends Activity {
    public ValueCallback<Uri[]> fileCallback;
    public WebView webView;
    public boolean cameraPending, cameraRecoveryPending, pageReady;

    public File captureFile() { return new File(getCacheDir(), "egrep-aufstellung.jpg"); }
    public Uri captureUri() { return Uri.parse("content://de.michaelnowak.egrepnotes.capture/capture/aufstellung.jpg"); }
    public void clearCapture() { captureFile().delete(); }
    public void notify(String message) { Toast.makeText(this, message, Toast.LENGTH_LONG).show(); }
    public void deliver(Uri[] result) {
        ValueCallback<Uri[]> cb = fileCallback;
        fileCallback = null; // Clear first: callbacks may initiate another action.
        if (cb != null) cb.onReceiveValue(result);
    }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        if (state != null) {
            cameraPending = state.getBoolean("cameraPending");
            cameraRecoveryPending = state.getBoolean("cameraRecoveryPending");
        }
        webView = new WebView(this);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        settings.setAllowFileAccessFromFileURLs(true);
        settings.setAllowUniversalAccessFromFileURLs(true);
        webView.setWebViewClient(new ExternalLinkClient());
        webView.setWebChromeClient(new FileChooserClient(this));
        setContentView(webView);
        webView.loadUrl("file:///android_asset/index.html");
    }
    @Override public void onSaveInstanceState(Bundle state) {
        super.onSaveInstanceState(state);
        state.putBoolean("cameraPending", cameraPending);
        state.putBoolean("cameraRecoveryPending", cameraRecoveryPending);
    }
    @Override public void onBackPressed() {
        webView.loadUrl("javascript:window.egrepBack&&window.egrepBack()");
    }

    public void openChooser(ValueCallback<Uri[]> callback, WebChromeClient.FileChooserParams params) {
        deliver(null);
        fileCallback = callback;
        cameraRecoveryPending = cameraPending = false;
        try {
            Intent intent;
            int request;
            if (params.isCaptureEnabled()) {
                clearCapture();
                captureFile().createNewFile();
                intent = new Intent("android.media.action.IMAGE_CAPTURE");
                Uri output = captureUri();
                intent.putExtra("output", output);
                intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
                intent.setClipData(ClipData.newRawUri("Aufstellung", output));
                cameraPending = true;
                request = 42;
            } else {
                intent = params.createIntent();
                request = 41;
            }
            startActivityForResult(intent, request);
        } catch (Exception e) {
            cameraPending = false;
            deliver(null);
            clearCapture();
            notify("Kamera oder Fotoauswahl nicht verfuegbar. Bitte Foto auswaehlen versuchen.");
        }
    }

    @Override public void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (request == 41) {
            deliver(WebChromeClient.FileChooserParams.parseResult(result, data));
            return;
        }
        if (request != 42 || !cameraPending) return;
        cameraPending = false;
        revokeUriPermission(captureUri(), Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
        if (result == RESULT_OK && captureFile().length() > 0) {
            // Full-sized photo is written to EXTRA_OUTPUT; camera result Intent may be null.
            if (fileCallback != null) deliver(new Uri[]{captureUri()});
            else { cameraRecoveryPending = true; tryRecoverPhoto(); }
            return;
        }
        if (result == RESULT_OK)
            notify("Kein Foto gespeichert. Bitte erneut aufnehmen oder ein Foto auswaehlen.");
        clearCapture();
        deliver(null);
    }
    public void tryRecoverPhoto() {
        if (!cameraRecoveryPending || !pageReady) return;
        cameraRecoveryPending = false;
        String script = "javascript:window.egrepCameraRecovered&&window.egrepCameraRecovered('"
                + Uri.fromFile(captureFile()).toString() + "')";
        webView.loadUrl(script);
    }
}
