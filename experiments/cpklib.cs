using System;
using System.IO;
using System.Text;
using System.Collections.Generic;
using System.Security.Cryptography;

// Бинарные патчи DRVP (формат tools/mkdelta.py)
public static class DrvPatch {
    public static string Hex(byte[] b) { return BitConverter.ToString(b).Replace("-", "").ToLowerInvariant(); }
    public static string Sha1(byte[] d) { using (var h = SHA1.Create()) return Hex(h.ComputeHash(d)); }
    static void Check(byte[] p) {
        if (p.Length < 64 || p[0] != 'D' || p[1] != 'R' || p[2] != 'V' || p[3] != 'P') throw new Exception("bad patch");
    }
    public static string NewSha(byte[] p) { Check(p); return Hex(Sub(p, 44, 20)); }
    public static string OrigSha(byte[] p) { Check(p); return Hex(Sub(p, 16, 20)); }
    // null = исходный файл не той версии
    public static byte[] Apply(byte[] orig, byte[] p) {
        Check(p);
        int pos = 8;
        long origSize = BitConverter.ToInt64(p, pos); pos += 8;
        string origSha = Hex(Sub(p, pos, 20)); pos += 20;
        long newSize = BitConverter.ToInt64(p, pos); pos += 8;
        string newSha = Hex(Sub(p, pos, 20)); pos += 20;
        if (orig == null || orig.LongLength != origSize || Sha1(orig) != origSha) return null;
        byte[] o = new byte[newSize];
        long w = 0;
        while (true) {
            byte t = p[pos];
            if (t == 0) break;
            if (t == 1) {
                long off = BitConverter.ToInt64(p, pos + 1); int len = BitConverter.ToInt32(p, pos + 9);
                Array.Copy(orig, off, o, w, len); w += len; pos += 13;
            } else if (t == 2) {
                int len = BitConverter.ToInt32(p, pos + 1);
                Array.Copy(p, pos + 5, o, w, len); w += len; pos += 5 + len;
            } else throw new Exception("bad op");
        }
        if (w != newSize || Sha1(o) != newSha) throw new Exception("checksum");
        return o;
    }
    public static byte[] Sub(byte[] a, int o, int n) { byte[] r = new byte[n]; Array.Copy(a, o, r, 0, n); return r; }
}

// Таблица @UTF (CRI), значения big-endian. Только чтение.
public class Utf {
    public List<string> Cols = new List<string>();
    public List<Dictionary<string, object>> Rows = new List<Dictionary<string, object>>();
    byte[] raw; int strOff;
    public static int Size(int ty) {
        switch (ty) {
            case 0: case 1: return 1;
            case 2: case 3: return 2;
            case 4: case 5: case 8: case 10: return 4;
            case 6: case 7: case 9: case 11: return 8;
        }
        throw new Exception("unknown @UTF column type " + ty);
    }
    public static ulong BE(byte[] b, int p, int n) { ulong v = 0; for (int i = 0; i < n; i++) v = (v << 8) | b[p + i]; return v; }
    string Str(int off) {
        int a = strOff + off; int e = a;
        while (raw[e] != 0) e++;
        return Encoding.UTF8.GetString(raw, a, e - a);
    }
    object Val(int p, int ty) {
        if (ty == 10) return Str((int)BE(raw, p, 4));
        if (ty == 8 || ty == 9 || ty == 11) return null;
        return (long)BE(raw, p, Size(ty));
    }
    public Utf(byte[] r) {
        raw = r;
        if (r.Length < 32 || r[0] != '@' || r[1] != 'U' || r[2] != 'T' || r[3] != 'F') throw new Exception("unsupported CPK table (encrypted?)");
        int rowsOff = (int)(BE(r, 8, 4) & 0xffff) + 8;
        strOff = (int)BE(r, 12, 4) + 8;
        int ncol = (int)BE(r, 24, 2);
        int rowLen = (int)BE(r, 26, 2);
        int nrows = (int)BE(r, 28, 4);
        var st = new List<int>(); var ty = new List<int>(); var cv = new List<object>();
        int p = 32;
        for (int c = 0; c < ncol; c++) {
            int fl = r[p]; p++;
            Cols.Add(Str((int)BE(r, p, 4))); p += 4;
            st.Add(fl & 0xf0); ty.Add(fl & 0x0f);
            object v = null;
            if ((fl & 0xf0) == 0x30 || (fl & 0xf0) == 0x70) { v = Val(p, fl & 0x0f); p += Size(fl & 0x0f); }
            cv.Add(v);
        }
        for (int i = 0; i < nrows; i++) {
            p = rowsOff + i * rowLen;
            var row = new Dictionary<string, object>();
            for (int c = 0; c < ncol; c++) {
                if (st[c] == 0x50) { row[Cols[c]] = Val(p, ty[c]); p += Size(ty[c]); }
                else row[Cols[c]] = cv[c];
            }
            Rows.Add(row);
        }
    }
}

public class CpkEntry {
    public string Dir, Name, Path;
    public long Offset, Size;
    public bool Compressed;
    public Cpk Owner;
}

// Архив CRI CPK (без шифрования и сжатия). Только чтение и распаковка.
public class Cpk : IDisposable {
    public string FilePath;
    public long Length, TocOffset, ContentOffset, BaseOff, SumSize;
    public List<CpkEntry> Entries = new List<CpkEntry>();
    public Dictionary<string, CpkEntry> ByPath = new Dictionary<string, CpkEntry>(StringComparer.OrdinalIgnoreCase);
    FileStream fs;

    static void ReadFull(Stream s, byte[] b, int n) {
        int r = 0;
        while (r < n) { int k = s.Read(b, r, n - r); if (k <= 0) throw new EndOfStreamException(); r += k; }
    }
    static Utf ReadPacket(Stream f, long off, string magic) {
        f.Seek(off, SeekOrigin.Begin);
        byte[] h = new byte[16]; ReadFull(f, h, 16);
        if (Encoding.ASCII.GetString(h, 0, 4) != magic) throw new Exception("CPK: no " + magic + " at " + off);
        long size = BitConverter.ToInt64(h, 8);
        if (size <= 0 || size > (256L << 20)) throw new Exception("CPK: bad " + magic + " size");
        byte[] u = new byte[size]; ReadFull(f, u, (int)size);
        return new Utf(u);
    }
    static long L(Dictionary<string, object> d, string k) {
        object v;
        if (d.TryGetValue(k, out v) && v is long) return (long)v;
        return 0;
    }
    public static Cpk Open(string path) {
        var c = new Cpk(); c.FilePath = path;
        using (var f = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read)) {
            c.Length = f.Length;
            var H = ReadPacket(f, 0, "CPK ").Rows[0];
            c.TocOffset = L(H, "TocOffset"); c.ContentOffset = L(H, "ContentOffset");
            if (c.TocOffset <= 0) throw new Exception("CPK without TOC");
            if (L(H, "ItocOffset") > 0 || L(H, "GtocOffset") > 0) throw new Exception("unsupported CPK (ITOC/GTOC)");
            c.BaseOff = (c.ContentOffset > 0 && c.ContentOffset < c.TocOffset) ? c.ContentOffset : c.TocOffset;
            var t = ReadPacket(f, c.TocOffset, "TOC ");
            foreach (var r in t.Rows) {
                var e = new CpkEntry(); e.Owner = c;
                e.Dir = r["DirName"] as string; e.Name = r["FileName"] as string;
                if (string.IsNullOrEmpty(e.Name)) continue;
                e.Path = string.IsNullOrEmpty(e.Dir) ? e.Name : e.Dir + "/" + e.Name;
                e.Offset = L(r, "FileOffset"); e.Size = L(r, "FileSize");
                e.Compressed = L(r, "ExtractSize") != e.Size;
                if (e.Path.Contains("..") || e.Path.StartsWith("/") || e.Path.Contains(":")) throw new Exception("CPK: bad path " + e.Path);
                if (c.BaseOff + e.Offset + e.Size > c.Length) throw new Exception("CPK: entry outside archive " + e.Path);
                c.SumSize += e.Size;
                c.Entries.Add(e);
                c.ByPath[e.Path] = e;
            }
        }
        return c;
    }
    FileStream S() {
        if (fs == null) fs = new FileStream(FilePath, FileMode.Open, FileAccess.Read, FileShare.Read, 1 << 16, FileOptions.SequentialScan);
        return fs;
    }
    // исходное содержимое файла из архива (null — если файл сжат)
    public byte[] Read(CpkEntry e) {
        if (e.Compressed) return null;
        var f = S();
        byte[] b = new byte[e.Size]; f.Seek(BaseOff + e.Offset, SeekOrigin.Begin); ReadFull(f, b, (int)e.Size);
        return b;
    }
    // распаковать файл; не перезаписывает существующий (FileMode.CreateNew)
    public void Extract(CpkEntry e, string dst, byte[] buf) {
        if (e.Compressed) throw new Exception("compressed entry " + e.Path);
        var f = S();
        string dir = System.IO.Path.GetDirectoryName(dst);
        if (!string.IsNullOrEmpty(dir)) Directory.CreateDirectory(dir);
        using (var o = new FileStream(dst, FileMode.CreateNew, FileAccess.Write, FileShare.None, 1 << 16)) {
            o.SetLength(e.Size);
            f.Seek(BaseOff + e.Offset, SeekOrigin.Begin);
            long left = e.Size;
            while (left > 0) {
                int n = f.Read(buf, 0, (int)Math.Min(buf.Length, left));
                if (n <= 0) throw new EndOfStreamException();
                o.Write(buf, 0, n); left -= n;
            }
        }
    }
    public void Dispose() { if (fs != null) { fs.Dispose(); fs = null; } }
}
