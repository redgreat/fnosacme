#!/bin/python3

import shutil
import json
import os
import sys
from datetime import datetime
import hashlib
from OpenSSL import crypto

# 入参
domain = sys.argv[1]
files_to_copy = [
    f'certs/{domain}_ecc/{domain}.cer',
    f'certs/{domain}_ecc/{domain}.key',
    f'certs/{domain}_ecc/fullchain.cer',
]
cert_file = f'certs/{domain}_ecc/{domain}.cer'
cert_all = f'/usr/trim/etc/network_cert_all.conf'
cert_gateway = f'/usr/trim/etc/network_gateway_cert.conf'


def get_cert_dates(in_file):
    with open(in_file, "rb") as in_file:
        cert = crypto.load_certificate(crypto.FILETYPE_PEM, in_file.read())
        start_date = cert.get_notBefore().decode('ascii')
        end_date = cert.get_notAfter().decode('ascii')

        start_date_dt = datetime.strptime(start_date, '%Y%m%d%H%M%SZ')
        end_date_dt = datetime.strptime(end_date, '%Y%m%d%H%M%SZ')

        start_timestamp = int(start_date_dt.timestamp())
        end_timestamp = int(end_date_dt.timestamp())

        return start_timestamp, end_timestamp


def calculate_md5(file_path):
    with open(file_path, "rb") as f:
        md5 = hashlib.md5()
        md5.update(f.read())
        return md5.hexdigest()


def calculate_sha256(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def modify_config_files(domain, files_to_copy):
    start_date, end_date = get_cert_dates(cert_file)
    sum_value = calculate_md5(cert_file)
    cert_dir = f'/usr/trim/var/trim_connect/ssls/{domain}/{end_date}/'

    if os.path.exists(f'/usr/trim/var/trim_connect/ssls/{domain}'):
        shutil.rmtree(f'/usr/trim/var/trim_connect/ssls/{domain}')
    if not os.path.exists(cert_dir):
        os.makedirs(cert_dir)
    for file in files_to_copy:
        shutil.move(file, cert_dir)

    # network_cert_all.conf
    if os.path.exists(f'{cert_all}.old'):
        os.remove(f'{cert_all}.old')
    shutil.copyfile(cert_all, f'{cert_all}.old')
    with open(cert_all, 'r+') as file:
        data = json.load(file)
        new_cert = {
            "domain": f"*.{domain}",
            "san": [f"*.{domain}", domain],
            "certificate": f"{cert_dir}{domain}.cer",
            "fullchain": f"{cert_dir}fullchain.cer",
            "privateKey": f"{cert_dir}{domain}.key",
            "validFrom": start_date * 1000,
            "validTo": end_date * 1000,
            "sum": sum_value,
            "used": True,
            "appFlag": 0
        }
        data = [item for item in data if item.get("domain", "") != f"*.{domain}"]
        data.append(new_cert)
        for item in data:
            if item["domain"] != f"*.{domain}":
                item["used"] = False
        file.seek(0)
        json.dump(data, file, indent=4)
        file.truncate()

    # network_gateway_cert.conf
    if os.path.exists(f'{cert_gateway}.old'):
        os.remove(f'{cert_gateway}.old')
    shutil.copyfile(cert_gateway, f'{cert_gateway}.old')
    with open(cert_gateway, 'r+') as file:
        data = json.load(file)
        new_cert = {
            "host": domain,
            "cert": f"{cert_dir}{domain}.cer",
            "key": f"{cert_dir}{domain}.key"
        }
        data = [item for item in data if item.get("host", "") != {domain}]
        data.append(new_cert)
        for item in data:
            if item["host"] == "fallback":
                item["cert"] = f"{cert_dir}{domain}.cer"
                item["key"] = f"{cert_dir}{domain}.key"
        file.seek(0)
        json.dump(data, file, indent=4)
        file.truncate()
    return cert_dir

modify_config_files(domain, files_to_copy)
