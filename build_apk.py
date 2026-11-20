#!/usr/bin/env python3
"""Build the SDK-independent eGrep Notes APK.

The host is deliberately tiny: an Android WebView, external-link handling and
an image file chooser. The complete offline UI and OCR runtime stay as readable
assets below app/src/main/assets.
"""

from __future__ import annotations

import argparse
import json
import base64
import hashlib
import os
import struct
import subprocess
import sys
import zlib
import zipfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ASSET_DIR = ROOT / "app/src/main/assets"
HTML_PATH = ASSET_DIR / "index.html"
LAUNCHER_ICON = ROOT / "app/src/main/res/drawable/nev_spielnotiz.png"
BUILD_DIR = ROOT / "build"
CONFIG = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))
APP_NAME = CONFIG["name"]
APP_VERSION = CONFIG["version"]
VERSION_CODE = CONFIG["versionCode"]
PACKAGE_NAME = CONFIG["package"]
FINAL_APK = ROOT / "dist" / ("eGrep-Notes-v" + APP_VERSION + ".apk")
PRIVATE_KEY = ROOT / "signing/egrep-notes-key.pem"
CERTIFICATE = ROOT / "signing/egrep-notes-cert.pem"
INIT_SIGNING = False

NO_INDEX = 0xFFFFFFFF


def build_embedded_ocr_data() -> bytes:
    """Bundle OCR runtime data without file/network requests from the WebView."""
    worker_path = ASSET_DIR / "worker.min.js"
    core_path = ASSET_DIR / "tesseract-core-lstm.wasm.js"
    language_path = ASSET_DIR / "tessdata/deu.traineddata.gz"
    worker = worker_path.read_text(encoding="utf-8")
    old = '"string"==typeof t?t:t.data'
    if worker.count(old) != 1:
        raise RuntimeError("Unexpected Tesseract worker format")
    worker = worker.replace(old, '"string"==typeof t?t:t.code')
    values = {
        "worker": base64.b64encode(worker.encode("utf-8")).decode("ascii"),
        "core": base64.b64encode(core_path.read_bytes()).decode("ascii"),
        "language": base64.b64encode(language_path.read_bytes()).decode("ascii"),
    }
    return ("window.NEV_OCR_DATA=" + __import__("json").dumps(values, separators=(",", ":")) + ";").encode("ascii")


def uleb128(value: int) -> bytes:
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            byte |= 0x80
        out.append(byte)
        if not value:
            return bytes(out)


def align(buffer: bytearray, boundary: int = 4) -> None:
    while len(buffer) % boundary:
        buffer.append(0)


def build_dex(html: str) -> bytes:
    from native_builder import build_native_dex
    return build_native_dex(PACKAGE_NAME)


class StringPool:
    def __init__(self, resource_names: list[tuple[str, int]], other_strings: list[str]):
        ordered: list[str] = []
        for value, _ in resource_names:
            if value not in ordered:
                ordered.append(value)
        for value in other_strings:
            if value not in ordered:
                ordered.append(value)
        self.values = ordered
        self.index = {value: idx for idx, value in enumerate(ordered)}
        self.resource_ids = [resource_id for _, resource_id in resource_names]

    @staticmethod
    def _len8(value: int) -> bytes:
        if value > 0x7F:
            return bytes(((value >> 8) | 0x80, value & 0xFF))
        return bytes((value,))

    def chunk(self) -> bytes:
        payload = bytearray()
        offsets = []
        for value in self.values:
            offsets.append(len(payload))
            encoded = value.encode("utf-8")
            payload += self._len8(len(value.encode("utf-16-le")) // 2)
            payload += self._len8(len(encoded))
            payload += encoded + b"\0"
        align(payload)
        strings_start = 28 + 4 * len(self.values)
        size = strings_start + len(payload)
        head = struct.pack(
            "<HHIIIIII",
            0x0001, 28, size, len(self.values), 0, 0x100, strings_start, 0,
        )
        return head + struct.pack("<" + "I" * len(offsets), *offsets) + payload

    def resource_map(self) -> bytes:
        size = 8 + 4 * len(self.resource_ids)
        return struct.pack("<HHI", 0x0180, 8, size) + struct.pack(
            "<" + "I" * len(self.resource_ids), *self.resource_ids
        )


def build_resources() -> bytes:
    """Build the minimal resource table for the custom launcher drawable."""
    global_pool = StringPool([], ["res/drawable/nev_spielnotiz.png"]).chunk()
    type_pool = StringPool([], ["drawable"]).chunk()
    key_pool = StringPool([], ["nev_spielnotiz"]).chunk()

    type_spec = struct.pack(
        "<HHIBBHI", 0x0202, 16, 20, 1, 0, 0, 1
    ) + struct.pack("<I", 0x40000000)

    config = struct.pack(
        "<IHH2s2sBBHBBBBHHHH",
        28, 0, 0, b"\0\0", b"\0\0", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    )
    type_header_size = 8 + 12 + len(config)
    entries_start = type_header_size + 4
    entry = struct.pack("<HHI", 8, 0, 0)
    value = struct.pack("<HBBI", 8, 0, 0x03, 0)
    type_size = entries_start + len(entry) + len(value)
    type_chunk = (
        struct.pack("<HHI", 0x0201, type_header_size, type_size)
        + struct.pack("<BBHII", 1, 0, 0, 1, entries_start)
        + config
        + struct.pack("<I", 0)
        + entry
        + value
    )

    package_header_size = 288
    type_strings_off = package_header_size
    key_strings_off = type_strings_off + len(type_pool)
    package_body = type_pool + key_pool + type_spec + type_chunk
    package_size = package_header_size + len(package_body)
    package_name = PACKAGE_NAME.encode("utf-16-le")
    package_name += b"\0" * (256 - len(package_name))
    package_header = (
        struct.pack("<HHII", 0x0200, package_header_size, package_size, 0x7F)
        + package_name
        + struct.pack("<IIIII", type_strings_off, 1, key_strings_off, 1, 0)
    )
    package = package_header + package_body
    table_size = 12 + len(global_pool) + len(package)
    return struct.pack("<HHII", 0x0002, 12, table_size, 1) + global_pool + package


@dataclass(frozen=True)
class XmlAttribute:
    namespace: str | None
    name: str
    value: str | int
    value_type: int = 0x03


def build_manifest() -> bytes:
    resources = [
        ("authorities", 0x01010018),
        ("grantUriPermissions", 0x0101001B),
        ("configChanges", 0x0101001F),
        ("theme", 0x01010000),
        ("label", 0x01010001),
        ("icon", 0x01010002),
        ("name", 0x01010003),
        ("screenOrientation", 0x0101001E),
        ("minSdkVersion", 0x0101020C),
        ("versionCode", 0x0101021B),
        ("versionName", 0x0101021C),
        ("targetSdkVersion", 0x01010270),
        ("exported", 0x01010010),
        ("allowBackup", 0x01010280),
        ("windowSoftInputMode", 0x0101022B),
    ]
    android_uri = "http://schemas.android.com/apk/res/android"
    strings = [
        "android", android_uri, "manifest", "package", "uses-sdk", "application",
        "activity", "intent-filter", "action", "category", "provider",
        ".CaptureProvider", PACKAGE_NAME + ".capture",
        PACKAGE_NAME, APP_VERSION, APP_NAME, ".MainActivity",
        "android.intent.action.MAIN", "android.intent.category.LAUNCHER",
        "uses-permission", "android.permission.INTERNET",
    ]
    pool = StringPool(resources, strings)
    chunks: list[bytes] = [pool.chunk(), pool.resource_map()]

    def node_header(chunk_type: int, size: int) -> bytes:
        return struct.pack("<HHIII", chunk_type, 16, size, 1, NO_INDEX)

    def namespace(chunk_type: int) -> bytes:
        return node_header(chunk_type, 24) + struct.pack(
            "<II", pool.index["android"], pool.index[android_uri]
        )

    def start(name: str, attrs: list[XmlAttribute]) -> bytes:
        size = 36 + 20 * len(attrs)
        out = bytearray(node_header(0x0102, size))
        out += struct.pack(
            "<IIHHHHHH", NO_INDEX, pool.index[name], 20, 20, len(attrs), 0, 0, 0
        )
        for attr in attrs:
            ns = NO_INDEX if attr.namespace is None else pool.index[attr.namespace]
            name_idx = pool.index[attr.name]
            if attr.value_type == 0x03:
                raw = pool.index[str(attr.value)]
                data = raw
            else:
                raw = NO_INDEX
                data = int(attr.value) & 0xFFFFFFFF
            out += struct.pack("<IIIHBBI", ns, name_idx, raw, 8, 0, attr.value_type, data)
        return bytes(out)

    def end(name: str) -> bytes:
        return node_header(0x0103, 24) + struct.pack("<II", NO_INDEX, pool.index[name])

    a = android_uri
    chunks.append(namespace(0x0100))
    chunks.append(start("manifest", [
        XmlAttribute(None, "package", PACKAGE_NAME),
        XmlAttribute(a, "versionCode", VERSION_CODE, 0x10),
        XmlAttribute(a, "versionName", APP_VERSION),
    ]))
    chunks.append(start("uses-sdk", [
        XmlAttribute(a, "minSdkVersion", CONFIG["minSdk"], 0x10),
        XmlAttribute(a, "targetSdkVersion", CONFIG["targetSdk"], 0x10),
    ]))
    chunks.append(end("uses-sdk"))
    # 3.2: internet only for the update check and the optional EHV comparison (no game data is sent).
    chunks.append(start("uses-permission", [XmlAttribute(a, "name", "android.permission.INTERNET")]))
    chunks.append(end("uses-permission"))
    chunks.append(start("application", [
        XmlAttribute(a, "theme", 0x01030006, 0x01),
        XmlAttribute(a, "label", APP_NAME),
        XmlAttribute(a, "icon", 0x7F010000, 0x01),
        XmlAttribute(a, "allowBackup", 0, 0x12),
    ]))
    chunks.append(start("activity", [
        XmlAttribute(a, "name", ".MainActivity"),
        XmlAttribute(a, "configChanges", 0x4A0, 0x10),
        XmlAttribute(a, "windowSoftInputMode", 0x10, 0x10),
        XmlAttribute(a, "screenOrientation", 1, 0x10),  # portrait enum
        XmlAttribute(a, "exported", 0xFFFFFFFF, 0x12),
    ]))
    chunks.append(start("intent-filter", []))
    chunks.append(start("action", [XmlAttribute(a, "name", "android.intent.action.MAIN")]))
    chunks.append(end("action"))
    chunks.append(start("category", [XmlAttribute(a, "name", "android.intent.category.LAUNCHER")]))
    chunks.append(end("category"))
    chunks.append(end("intent-filter"))
    chunks.append(end("activity"))
    chunks.append(start("provider", [
        XmlAttribute(a, "name", ".CaptureProvider"),
        XmlAttribute(a, "authorities", PACKAGE_NAME + ".capture"),
        XmlAttribute(a, "exported", 0, 0x12),
        XmlAttribute(a, "grantUriPermissions", 0xFFFFFFFF, 0x12),
    ]))
    chunks.append(end("provider"))
    chunks.append(end("application"))
    chunks.append(end("manifest"))
    chunks.append(namespace(0x0101))
    body = b"".join(chunks)
    return struct.pack("<HHI", 0x0003, 8, 8 + len(body)) + body


def run(command: list[str]) -> None:
    print("+", " ".join(command))
    subprocess.run(command, check=True)


def sha256_base64(data: bytes) -> str:
    return base64.b64encode(hashlib.sha256(data).digest()).decode("ascii")


def sign_apk(entries: dict[str, bytes]) -> None:
    """Create a classic JAR/APK v1 signature accepted by Android 6+."""
    manifest_main = b"Manifest-Version: 1.0\r\nCreated-By: eGrep Notes builder\r\n\r\n"
    manifest_sections: dict[str, bytes] = {}
    for name, payload in entries.items():
        section = (
            f"Name: {name}\r\n"
            f"SHA-256-Digest: {sha256_base64(payload)}\r\n\r\n"
        ).encode("ascii")
        manifest_sections[name] = section
    jar_manifest = manifest_main + b"".join(manifest_sections.values())

    sf_main = (
        "Signature-Version: 1.0\r\n"
        "Created-By: eGrep Notes builder\r\n"
        f"SHA-256-Digest-Manifest: {sha256_base64(jar_manifest)}\r\n\r\n"
    ).encode("ascii")
    sf_sections = []
    for name, section in manifest_sections.items():
        sf_sections.append(
            (
                f"Name: {name}\r\n"
                f"SHA-256-Digest: {sha256_base64(section)}\r\n\r\n"
            ).encode("ascii")
        )
    signature_file = sf_main + b"".join(sf_sections)

    if not PRIVATE_KEY.exists() or not CERTIFICATE.exists():
        if not INIT_SIGNING:
            raise RuntimeError("Signing key missing. Restore the PRIVATE backup or use --init-signing for a NEW signing identity. Never regenerate for an existing installation.")
        if PRIVATE_KEY.exists() or CERTIFICATE.exists():
            raise RuntimeError("Incomplete signing pair: refusing to overwrite it.")
        PRIVATE_KEY.parent.mkdir(parents=True, exist_ok=True)
        run([
            "openssl", "req", "-x509", "-newkey", "rsa:2048", "-sha256",
            "-nodes", "-days", "3650", "-subj", "/C=DE/O=Michael Nowak/CN=eGrep Notes",
            "-keyout", str(PRIVATE_KEY), "-out", str(CERTIFICATE),
        ])
    PRIVATE_KEY.chmod(0o600)
    sf_path = BUILD_DIR / "CERT.SF"
    rsa_path = BUILD_DIR / "CERT.RSA"
    sf_path.write_bytes(signature_file)
    run([
        "openssl", "cms", "-sign", "-binary", "-noattr", "-nosmimecap",
        "-md", "sha256", "-in", str(sf_path), "-signer", str(CERTIFICATE),
        "-inkey", str(PRIVATE_KEY), "-outform", "DER", "-out", str(rsa_path),
    ])

    with zipfile.ZipFile(FINAL_APK, "w", compression=zipfile.ZIP_DEFLATED) as apk:
        for name, payload in entries.items():
            compression = zipfile.ZIP_STORED if name in {
                "resources.arsc", "res/drawable/nev_spielnotiz.png"
            } else zipfile.ZIP_DEFLATED
            if compression == zipfile.ZIP_STORED:
                info = zipfile.ZipInfo(name)
                info.compress_type = compression
                current_offset = apk.fp.tell()
                padding = (-(current_offset + 30 + len(name.encode("utf-8")) + 4)) % 4
                info.extra = struct.pack("<HH", 0xD935, padding) + b"\0" * padding
                apk.writestr(info, payload)
            else:
                apk.writestr(name, payload, compress_type=compression)
        apk.writestr("META-INF/MANIFEST.MF", jar_manifest)
        apk.writestr("META-INF/NEVNOTE.SF", signature_file)
        apk.writestr("META-INF/NEVNOTE.RSA", rsa_path.read_bytes())

    run([
        "openssl", "cms", "-verify", "-binary", "-inform", "DER",
        "-in", str(rsa_path), "-content", str(sf_path), "-noverify", "-out", os.devnull,
    ])


def main() -> int:
    global FINAL_APK, PRIVATE_KEY, CERTIFICATE, INIT_SIGNING
    args = argparse.ArgumentParser(description="Build eGrep Notes without Android SDK. Requires Python 3 and OpenSSL.")
    args.add_argument("--output", type=Path)
    args.add_argument("--signing-dir", type=Path, default=ROOT / "signing")
    args.add_argument("--init-signing", action="store_true", help="Create a NEW signing identity only if none exists")
    options = args.parse_args()
    if options.output: FINAL_APK = options.output.resolve()
    PRIVATE_KEY = options.signing_dir / "egrep-notes-key.pem"
    CERTIFICATE = options.signing_dir / "egrep-notes-cert.pem"
    INIT_SIGNING = options.init_signing
    if not HTML_PATH.exists() or not LAUNCHER_ICON.exists():
        print("Missing UI source or icon artwork.", file=sys.stderr)
        return 1

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    FINAL_APK.parent.mkdir(parents=True, exist_ok=True)
    html = HTML_PATH.read_text(encoding="utf-8")

    entries = {
        "AndroidManifest.xml": build_manifest(),
        "resources.arsc": build_resources(),
        "res/drawable/nev_spielnotiz.png": LAUNCHER_ICON.read_bytes(),
        "classes.dex": build_dex(html),
        "assets/ocr-data.js": build_embedded_ocr_data(),
    }
    embedded_sources = {
        "ocr-data.js", "worker.min.js", "tesseract-core-lstm.wasm.js", "tessdata/deu.traineddata.gz"
    }
    for asset in sorted(ASSET_DIR.rglob("*")):
        if asset.is_file() and asset.relative_to(ASSET_DIR).as_posix() not in embedded_sources:
            entries[f"assets/{asset.relative_to(ASSET_DIR).as_posix()}"] = asset.read_bytes()
    sign_apk(entries)
    print(f"Built {FINAL_APK} ({FINAL_APK.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
