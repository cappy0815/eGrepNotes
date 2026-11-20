package de.michaelnowak.egrepnotes;
import android.content.ContentProvider;
import android.content.ContentValues;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import java.io.File;
import java.io.FileNotFoundException;

/** Non-exported, one-file provider. Only temporary URI grants allow camera access.
 * No filesystem path supplied by another app is ever resolved or trusted. */
public final class CaptureProvider extends ContentProvider {
    @Override public boolean onCreate() { return true; }
    public void checkUri(Uri uri) {
        if (uri == null || !uri.toString().equals("content://de.michaelnowak.egrepnotes.capture/capture/aufstellung.jpg"))
            throw new IllegalArgumentException("Unknown capture URI");
    }
    public File captureFile() { return new File(getContext().getCacheDir(), "egrep-aufstellung.jpg"); }
    @Override public ParcelFileDescriptor openFile(Uri uri, String mode) throws FileNotFoundException {
        checkUri(uri);
        return ParcelFileDescriptor.open(captureFile(), ParcelFileDescriptor.parseMode(mode));
    }
    @Override public String getType(Uri uri) { checkUri(uri); return "image/jpeg"; }
    @Override public Cursor query(Uri uri, String[] projection, String selection, String[] args, String order) {
        checkUri(uri);
        MatrixCursor cursor = new MatrixCursor(new String[]{"_display_name", "_size"});
        cursor.addRow(new Object[]{"aufstellung.jpg", Long.valueOf(captureFile().length())});
        return cursor;
    }
    @Override public Uri insert(Uri uri, ContentValues values) { throw new UnsupportedOperationException("Only temporary camera files are supported"); }
    @Override public int delete(Uri uri, String where, String[] args) { throw new UnsupportedOperationException("Only temporary camera files are supported"); }
    @Override public int update(Uri uri, ContentValues values, String where, String[] args) { throw new UnsupportedOperationException("Only temporary camera files are supported"); }
}
