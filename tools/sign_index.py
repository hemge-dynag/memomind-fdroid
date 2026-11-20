#!/usr/bin/env python3
"""Genere un index-v1.jar signe (format jarsigner/F-Droid) sans JDK.

Usage: sign_index.py <repo_dir> <keystore.jks> <storepass> [alias]

Ecrit repo_dir/index-v1.jar a partir de repo_dir/index-v1.json.
Le bloc PKCS#7 est construit a la main avec `cryptography` (RSA/SHA-256).
"""
import base64
import hashlib
import pathlib
import sys
import zipfile

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives.serialization import Encoding


def der(tag: int, body: bytes) -> bytes:
    n = len(body)
    if n < 0x80:
        return bytes([tag, n]) + body
    lb = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return bytes([tag, 0x80 | len(lb)]) + lb + body


def b64(b: bytes) -> str:
    return base64.b64encode(b).decode()


def build_sf(entries):
    mf_main = b"Manifest-Version: 1.0\r\nCreated-By: MemoMind\r\n\r\n"
    mf = mf_main
    for name, data in entries:
        mf += b"Name: " + name.encode() + b"\r\n"
        mf += b"SHA-256-Digest: " + b64(hashlib.sha256(data).digest()).encode() + b"\r\n\r\n"
    sf = b"Signature-Version: 1.0\r\nCreated-By: 1.0 (MemoMind)\r\n"
    sf += b"SHA-256-Digest-Manifest: " + b64(hashlib.sha256(mf).digest()).encode() + b"\r\n"
    sf += b"SHA-256-Digest-Manifest-Main-Attributes: " + b64(hashlib.sha256(mf_main).digest()).encode() + b"\r\n\r\n"
    for name, data in entries:
        sf += b"Name: " + name.encode() + b"\r\n"
        sf += b"SHA-256-Digest: " + b64(hashlib.sha256(data).digest()).encode() + b"\r\n\r\n"
    return mf, sf


def _der_elem(buf: bytes, off: int):
    """Retourne (tag, header_len, body_len, total_len) pour l'element DER a `off`."""
    tag = buf[off]
    n = buf[off + 1]
    if n < 0x80:
        return tag, 2, n, 2 + n
    ln = n & 0x7F
    size = int.from_bytes(buf[off + 2:off + 2 + ln], "big")
    return tag, 2 + ln, size, 2 + ln + size


def cert_name_serial(cert_der: bytes):
    """Retourne (name_der, serial_der) d'un certificat X.509 DER."""
    _tag, hdr, _body, total = _der_elem(cert_der, 0)
    p = hdr
    _tag, hdr, _body, total = _der_elem(cert_der, p)      # TBSCertificate
    p += hdr
    if cert_der[p] == 0xA0:                               # [0] EXPLICIT version
        _tag, hdr, _body, total = _der_elem(cert_der, p)
        p += total
    _tag, hdr, _body, total = _der_elem(cert_der, p)      # serialNumber
    serial_der = cert_der[p:p + total]
    p += total
    _tag, hdr, _body, total = _der_elem(cert_der, p)      # signature AlgorithmIdentifier
    p += total
    _tag, hdr, _body, total = _der_elem(cert_der, p)      # issuer Name
    name_der = cert_der[p:p + total]
    return name_der, serial_der


def build_pkcs7(sf: bytes, key, cert_der: bytes, cert_pem: bytes) -> bytes:
    sig = key.sign(sf, padding.PKCS1v15(), hashes.SHA256())
    oid_data = bytes.fromhex("06092a864886f70d010701")
    oid_signed = bytes.fromhex("06092a864886f70d010702")
    oid_sha256 = bytes.fromhex("0609608648016503040201")
    oid_rsa = bytes.fromhex("06092a864886f70d010101")

    algid_sha256 = der(0x30, oid_sha256 + der(0x05, b""))
    enc_alg = der(0x30, oid_rsa + der(0x05, b""))

    name_der, serial_der = cert_name_serial(cert_der)
    signer_info = der(
        0x30,
        der(0x02, b"\x01")
        + der(0x30, name_der + serial_der)   # IssuerAndSerialNumber
        + algid_sha256
        + enc_alg
        + der(0x04, sig),
    )
    signed_data = der(
        0x30,
        der(0x02, b"\x01")
        + der(0x31, algid_sha256)
        + der(0x30, oid_data)                                    # contentInfo: pas de contenu
        + der(0xA0, cert_der)                                    # [0] certificates
        + der(0x31, signer_info),
    )
    return der(0x30, oid_signed + der(0xA0, signed_data))



def main(repo: pathlib.Path, ks_path: pathlib.Path, storepass: str, alias: str = None) -> int:
    index = repo / "index-v1.json"
    if not index.is_file():
        print(f"{index} introuvable", file=sys.stderr)
        return 2
    data = index.read_bytes()
    entries = [(index.name, data)]
    mf, sf = build_sf(entries)

    key, cert, _ = pkcs12.load_key_and_certificates(ks_path.read_bytes(), storepass.encode())
    if key is None or cert is None:
        print("cle/cert introuvables dans le keystore", file=sys.stderr)
        return 3
    cert_der = cert.public_bytes(Encoding.DER)
    p7 = build_pkcs7(sf, key, cert_der, cert.public_bytes(Encoding.PEM))

    out = repo / "index-v1.jar"
    z = zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED)
    z.writestr("META-INF/MANIFEST.MF", mf)
    z.writestr("META-INF/FDROID.SF", sf)
    z.writestr("META-INF/FDROID.RSA", p7)
    z.writestr(index.name, data)
    z.close()
    print(f"{out}: {out.stat().st_size} o (pkcs7 {len(p7)} o)")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    repo = pathlib.Path(sys.argv[1])
    ks = pathlib.Path(sys.argv[2])
    alias = sys.argv[4] if len(sys.argv) > 4 else None
    sys.exit(main(repo, ks, sys.argv[3], alias))
