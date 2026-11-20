package de.michaelnowak.egrepnotes;
public class FileChooserClient extends android.webkit.WebChromeClient {
    public de.michaelnowak.egrepnotes.MainActivity owner;

    public FileChooserClient(de.michaelnowak.egrepnotes.MainActivity p1)
    {
        this.owner = p1;
        return;
    }

    public boolean onShowFileChooser(android.webkit.WebView p3, android.webkit.ValueCallback p4, android.webkit.WebChromeClient$FileChooserParams p5)
    {
        this.owner.openChooser(p4, p5);
        return 1;
    }
}
