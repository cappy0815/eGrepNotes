package de.michaelnowak.egrepnotes;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.BatteryManager;
import android.print.PrintAttributes;
import android.print.PrintManager;
import android.webkit.WebView;
import android.webkit.WebViewClient;

/** Deliberately small local-only command interface; all external navigation is blocked. */
public final class ExternalLinkClient extends WebViewClient {
    @Override
    public boolean shouldOverrideUrlLoading(WebView view, String url) {
        switch (url) {
            case "egrep://screen/on": view.setKeepScreenOn(true); break;
            case "egrep://screen/off": view.setKeepScreenOn(false); break;
            case "egrep://power": {
                // Null receiver reads a sticky broadcast, no receiver registration to leak.
                Intent status = view.getContext().registerReceiver(null,
                        new IntentFilter(Intent.ACTION_BATTERY_CHANGED));
                boolean plugged = status != null
                        && status.getIntExtra(BatteryManager.EXTRA_PLUGGED, 0) != 0;
                view.loadUrl("javascript:window.egrepPower&&window.egrepPower(" + plugged + ")");
                break;
            }
            case "egrep://print":
            case "nevprint://report": {
                PrintManager manager = (PrintManager) view.getContext().getSystemService(Context.PRINT_SERVICE);
                if (manager != null) {
                    String title = "eGrep Notes - Spielbericht";
                    manager.print(title, view.createPrintDocumentAdapter(title),
                            new PrintAttributes.Builder()
                                    .setMediaSize(PrintAttributes.MediaSize.ISO_A4)
                                    .setMinMargins(new PrintAttributes.Margins(500, 500, 500, 500))
                                    .build());
                }
                break;
            }
            case "egrep://photo/clear": ((MainActivity) view.getContext()).clearCapture(); break;
            case "egrep://exit": ((Activity) view.getContext()).finish(); break;
            default: break;
        }
        return true;
    }
    @Override
    public void onPageFinished(WebView view, String url) {
        view.loadUrl("javascript:window.egrepHostReady&&window.egrepHostReady()");
        MainActivity owner = (MainActivity) view.getContext();
        owner.pageReady = true;
        owner.tryRecoverPhoto();
    }
}
