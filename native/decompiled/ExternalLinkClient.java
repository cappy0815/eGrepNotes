package de.michaelnowak.egrepnotes;
public class ExternalLinkClient extends android.webkit.WebViewClient {

    public ExternalLinkClient()
    {
        return;
    }

    public void onPageFinished(android.webkit.WebView p3, String p4)
    {
        p3.loadUrl("javascript:window.egrepHostReady&&window.egrepHostReady()");
        de.michaelnowak.egrepnotes.MainActivity v0_2 = ((de.michaelnowak.egrepnotes.MainActivity) p3.getContext());
        v0_2.pageReady = 1;
        v0_2.tryRecoverPhoto();
        return;
    }

    public boolean shouldOverrideUrlLoading(android.webkit.WebView p8, String p9)
    {
        if (!p9.equals("egrep://screen/on")) {
            if (!p9.equals("egrep://screen/off")) {
                if (!p9.equals("egrep://power")) {
                    if ((!p9.equals("egrep://print")) && (!p9.equals("nevprint://report"))) {
                        if (!p9.equals("egrep://photo/clear")) {
                            if (!p9.equals("egrep://exit")) {
                                if (p9.equals("https://cappy0815.github.io/")) {
                                    try {
                                        int v0_19 = new android.content.Intent("android.intent.action.VIEW", android.net.Uri.parse(p9));
                                        v0_19.addFlags(268435456);
                                        p8.getContext().startActivity(v0_19);
                                        return 1;
                                    } catch (int v0) {
                                        return 1;
                                    }
                                }
                            } else {
                                ((android.app.Activity) p8.getContext()).finish();
                                return 1;
                            }
                        } else {
                            ((de.michaelnowak.egrepnotes.MainActivity) p8.getContext()).clearCapture();
                            return 1;
                        }
                    } else {
                        int v0_31 = p8.getContext().getSystemService("print");
                        if (v0_31 != 0) {
                            int v0_33 = ((android.print.PrintManager) v0_31);
                            String v2_1 = p8.createPrintDocumentAdapter("eGrep Notes - Spielbericht");
                            android.print.PrintAttributes v3_1 = new android.print.PrintAttributes$Builder();
                            v3_1.setMediaSize(android.print.PrintAttributes$MediaSize.ISO_A4);
                            v3_1.setMinMargins(new android.print.PrintAttributes$Margins(500, 500, 500, 500));
                            v0_33.print("eGrep Notes - Spielbericht", v2_1, v3_1.build());
                            return 1;
                        }
                    }
                    return 1;
                } else {
                    int v0_39;
                    int v0_37 = p8.getContext().registerReceiver(0, new android.content.IntentFilter("android.intent.action.BATTERY_CHANGED"));
                    if ((v0_37 != 0) && (v0_37.getIntExtra("plugged", 0) != 0)) {
                        v0_39 = "javascript:window.egrepPower&&window.egrepPower(true)";
                    } else {
                        v0_39 = "javascript:window.egrepPower&&window.egrepPower(false)";
                    }
                    p8.loadUrl(v0_39);
                    return 1;
                }
            } else {
                p8.setKeepScreenOn(0);
                return 1;
            }
        } else {
            p8.setKeepScreenOn(1);
            return 1;
        }
    }
}
