#!/bin/python3

import shutil
import json
import os
import hashlib
from OpenSSL import crypto

# 入参
domain = sys.argv[1]
files_to_copy = [
    f'{domain}.crt',
    f'{domain}.key',
    'fullchain.crt',
]
cert_file = f'{domain}.cn.crt'
cert_all = f'/usr/trim/etc/network_cert_all.conf'
cert_gateway = f'network_gateway_cert.conf'


def get_cert_dates():
    with open(cert_file, "rb") as cert_file:
        cert = crypto.load_certificate(crypto.FILETYPE_PEM, cert_file.read())
        start_date = cert.get_notBefore()
        end_date = cert.get_notAfter()
        return int(start_date.timestamp() * 1000), int(end_date.timestamp() * 1000)

def calculate_md5(file_path):
    with open(file_path, "rb") as f:
        md5 = hashlib.md5()
        md5.update(f.read())
        return md5.hexdigest()

def modify_config_files(domain, files_to_copy):
    
    start_date, end_date = get_cert_dates()
    sum_value = calculate_md5(cert_file)
    cert_dir = f'/usr/trim/var/trim_connect/ssls/{domain}/{start_date}/'

    if not os.path.exists(cert_dir):
        os.makedirs(cert_dir)

    for file in files_to_copy:
        shutil.copy(file, cert_dir)

    # network_cert_all.conf
    if os.path.exists(f'{cert_all}.old'):
        os.remove(f'{cert_all}.old')
    shutil.copyfile(cert_all, f'{cert_all}.old')
    with open(cert_all, 'r+') as file:
        data = json.load(file)
        new_cert = {
            "domain": f"*.{domain}",
            "san": [f"*.{domain}", domain],
            "certificate": f"{cert_dir}{domain}.crt",
            "fullchain": f"{cert_dir}fullchain.crt",
            "privateKey": f"{cert_dir}{domain}.key",
            "validFrom": start_date,
            "validTo": end_date,
            "sum": sum_value,
            "used": true,
            "appFlag": 0
        }
        data.append(new_cert)
        for item in data:
            if item["domain"] != domain:
                item["used"] = false
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
            "cert": f"{cert_dir}{domain}.crt",
            "key": f"{cert_dir}{domain}.key"
        }
        data.append(new_cert)
        for item in data:
            if item["domain"] == fallback:
                item["cert"] = f"{cert_dir}{domain}.crt"
                item["key"] = f"{cert_dir}{domain}.key"
        file.seek(0)
        json.dump(data, file, indent=4)
        file.truncate()


modify_config_files(domain, files_to_copy)

