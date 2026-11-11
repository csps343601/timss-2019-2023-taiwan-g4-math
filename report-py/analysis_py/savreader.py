"""純 Python 的 SPSS .sav 讀取器（無需 pyreadstat）。
支援：位元組壓縮（compression=1）、未壓縮（0）、長變項名稱（subtype 13）、
變項標籤、值標籤、使用者定義遺漏值。
"""
import struct, zlib
import numpy as np
import pandas as pd


class Sav:
    pass


def read_sav(path):
    buf = open(path, "rb").read()
    if buf[:4] not in (b"$FL2", b"$FL3"):
        raise ValueError("不是 .sav：" + repr(buf[:4]))
    zsav = buf[:4] == b"$FL3"
    layout = struct.unpack("<i", buf[64:68])[0]
    end = "<" if layout in (2, 3) else ">"
    case_size, compression, weight_idx, ncases = struct.unpack(end + "iiii", buf[68:84])
    bias = struct.unpack(end + "d", buf[84:92])[0]
    pos = 176
    vars_ = []          # 每個「變項紀錄」：dict(name, typ, label, miss, idx)
    slots = []          # 每個 8-byte slot 對應的變項索引 或 None（續行）
    vlabels = []        # (值->標籤 dict, [變項記錄索引])
    longnames = {}
    sysmis = -1.7976931348623157e308
    while True:
        rt = struct.unpack(end + "i", buf[pos:pos + 4])[0]
        pos += 4
        if rt == 2:
            typ, has_lab, nmiss, pr, wr = struct.unpack(end + "iiiii", buf[pos:pos + 20]); pos += 20
            name = buf[pos:pos + 8].decode("latin1").strip(); pos += 8
            label = ""
            if has_lab:
                ln = struct.unpack(end + "i", buf[pos:pos + 4])[0]; pos += 4
                label = buf[pos:pos + ln].decode("utf-8", "replace"); pos += (ln + 3) // 4 * 4
            miss = []
            if nmiss:
                n = abs(nmiss)
                miss = list(struct.unpack(end + "%dd" % n, buf[pos:pos + 8 * n])); pos += 8 * n
                miss_kind = "range" if nmiss < 0 else "discrete"
            else:
                miss_kind = None
            if typ == -1:
                slots.append(None)
            else:
                vars_.append(dict(name=name, typ=typ, label=label, miss=miss, miss_kind=miss_kind, slot=len(slots)))
                slots.append(len(vars_) - 1)
        elif rt == 3:
            n = struct.unpack(end + "i", buf[pos:pos + 4])[0]; pos += 4
            d = []
            for _ in range(n):
                val = buf[pos:pos + 8]; pos += 8
                ln = buf[pos]; pos += 1
                lab = buf[pos:pos + ln].decode("utf-8", "replace"); pos += ln
                pos += (8 - (1 + ln) % 8) % 8
                d.append((val, lab))
            rt4 = struct.unpack(end + "i", buf[pos:pos + 4])[0]; pos += 4
            assert rt4 == 4
            m = struct.unpack(end + "i", buf[pos:pos + 4])[0]; pos += 4
            idx = struct.unpack(end + "%di" % m, buf[pos:pos + 4 * m]); pos += 4 * m
            vlabels.append((d, [slots[i - 1] for i in idx]))
        elif rt == 6:
            n = struct.unpack(end + "i", buf[pos:pos + 4])[0]; pos += 4 + 80 * n
        elif rt == 7:
            sub, size, count = struct.unpack(end + "iii", buf[pos:pos + 12]); pos += 12
            data = buf[pos:pos + size * count]; pos += size * count
            if sub == 13:
                for kv in data.decode("utf-8", "replace").split("\t"):
                    if "=" in kv:
                        k, v = kv.split("=", 1); longnames[k.strip()] = v.strip()
            elif sub == 4 and len(data) >= 24:
                sysmis = struct.unpack(end + "d", data[:8])[0]
        elif rt == 999:
            pos += 4
            break
        else:
            raise ValueError("未知紀錄類型 %d @%d" % (rt, pos))
    # 長變項名稱
    for v in vars_:
        v["short"] = v["name"]
        v["name"] = longnames.get(v["name"], v["name"])
    # ---- 資料區 ----
    raw = buf[pos:]
    if zsav:
        raise NotImplementedError("zsav")
    if compression == 0:
        arr = np.frombuffer(raw[:ncases * case_size * 8], dtype=end + "f8").reshape(ncases, case_size) if ncases >= 0 else None
        items = [arr[:, j] for j in range(case_size)]
        data_f = arr
        strs = raw
        cells = None
    else:
        cmd_blocks = []
        out = np.empty(0)
        # 展開位元組壓縮：回傳 (float array, string-bytes dict)
        vals = []          # float 值（字串 slot 填 nan）
        sraw = {}          # 全域 slot 序號 -> 8 bytes（僅字串 slot 需要）
        n = len(raw)
        p = 0
        k = 0
        ctrl = b""
        ci = 8
        total = (ncases if ncases >= 0 else 10 ** 9) * case_size
        raw8 = raw
        f8 = np.empty(total if ncases >= 0 else 0, dtype="f8")
        isstr = np.zeros(total, dtype=bool) if ncases >= 0 else None
        strbytes = {}
        while k < total:
            if ci == 8:
                ctrl = raw8[p:p + 8]; p += 8; ci = 0
                if len(ctrl) < 8:
                    break
            c = ctrl[ci]; ci += 1
            if c == 0:
                continue
            elif 1 <= c <= 251:
                f8[k] = c - bias; k += 1
            elif c == 252:
                break
            elif c == 253:
                chunk = raw8[p:p + 8]; p += 8
                f8[k] = struct.unpack(end + "d", chunk)[0]
                strbytes[k] = chunk
                k += 1
            elif c == 254:
                strbytes[k] = b"        "; f8[k] = np.nan; k += 1
            elif c == 255:
                f8[k] = sysmis; k += 1
        if k != total:
            raise ValueError("資料長度不符：讀到 %d slots，預期 %d" % (k, total))
        data_f = f8.reshape(ncases, case_size)
        strs = strbytes
    # ---- 組成 DataFrame ----
    cols = {}
    for v in vars_:
        j = v["slot"]
        if v["typ"] == 0:
            col = data_f[:, j].copy()
            col[col == sysmis] = np.nan
            cols[v["name"]] = col
        else:
            nseg = (v["typ"] + 7) // 8
            out = []
            for i in range(ncases):
                b = b"".join(strs.get(i * case_size + j + s, b"        ") for s in range(nseg)) if compression != 0 else b"".join(raw[(i * case_size + j + s) * 8:(i * case_size + j + s) * 8 + 8] for s in range(nseg))
                out.append(b[:v["typ"]].decode("utf-8", "replace").rstrip())
            cols[v["name"]] = out
    df = pd.DataFrame(cols)
    s = Sav()
    s.df = df
    s.labels = {v["name"]: v["label"] for v in vars_}
    s.missing = {v["name"]: (v["miss_kind"], v["miss"]) for v in vars_ if v["miss"]}
    vl = {}
    for d, idxs in vlabels:
        for i in idxs:
            nm = vars_[i]["name"]
            for val, lab in d:
                key = struct.unpack(end + "d", val)[0] if vars_[i]["typ"] == 0 else val.decode("latin1").rstrip()
                vl.setdefault(nm, {})[key] = lab
    s.vlabels = vl
    s.sysmis = sysmis
    s.order = [v["name"] for v in vars_]
    return s


if __name__ == "__main__":
    import sys
    s = read_sav(sys.argv[1])
    print(s.df.shape)
    print(s.df.iloc[:3, :8])
