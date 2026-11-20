package de.michaelnowak.egrepnotes;
public class CaptureProvider extends android.content.ContentProvider {

    public CaptureProvider()
    {
        return;
    }

    public java.io.File captureFile()
    {
        return new java.io.File(this.getContext().getCacheDir(), "egrep-aufstellung.jpg");
    }

    public void checkUri(android.net.Uri p3)
    {
        if ((p3 != null) && (p3.toString().equals("content://de.michaelnowak.egrepnotes.capture/capture/aufstellung.jpg"))) {
            return;
        } else {
            throw new IllegalArgumentException("Unknown capture URI");
        }
    }

    public int delete(android.net.Uri p3, String p4, String[] p5)
    {
        throw new UnsupportedOperationException("Only temporary camera files are supported");
    }

    public String getType(android.net.Uri p2)
    {
        this.checkUri(p2);
        return "image/jpeg";
    }

    public android.net.Uri insert(android.net.Uri p3, android.content.ContentValues p4)
    {
        throw new UnsupportedOperationException("Only temporary camera files are supported");
    }

    public boolean onCreate()
    {
        return 1;
    }

    public android.os.ParcelFileDescriptor openFile(android.net.Uri p4, String p5)
    {
        this.checkUri(p4);
        return android.os.ParcelFileDescriptor.open(this.captureFile(), android.os.ParcelFileDescriptor.parseMode(p5));
    }

    public android.database.Cursor query(android.net.Uri p7, String[] p8, String p9, String[] p10, String p11)
    {
        this.checkUri(p7);
        Object[] v1_1 = new String[2];
        v1_1[0] = "_display_name";
        v1_1[1] = "_size";
        android.database.MatrixCursor v3_0 = new android.database.MatrixCursor(v1_1);
        Object[] v1_0 = new Object[2];
        v1_0[0] = "aufstellung.jpg";
        v1_0[1] = Long.valueOf(this.captureFile().length());
        v3_0.addRow(v1_0);
        return v3_0;
    }

    public int update(android.net.Uri p3, android.content.ContentValues p4, String p5, String[] p6)
    {
        throw new UnsupportedOperationException("Only temporary camera files are supported");
    }
}
