package de.michaelnowak.egrepnotes;
import android.net.Uri;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebView;
/** Separate capture input requests native camera; normal input keeps the image picker. */
public final class FileChooserClient extends WebChromeClient {
    public MainActivity owner;
    public FileChooserClient(MainActivity owner) { this.owner = owner; }
    @Override public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback, FileChooserParams params) {
        owner.openChooser(callback, params);
        return true;
    }
}
