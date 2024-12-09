#!/usr/bin/python3

import sys
import shutil
import json
import hashlib
from OpenSSL import crypto

# 入参
domain = sys.argv[1]
files_to_copy = [
    '/path/to/source/cert.crt',  # 假设这些文件名是通用的，需要根据实际情况替换
    '/path/to/source/cert.key',
    '/path/to/source/fullchain.crt',
]
destination_dir = f'/usr/trim/var/trim_connect/ssls/{domain}/'
config_files = ['network_cert_all.conf', 'network_gateway_cert.conf']

def get_cert_dates(cert_path):
    with open(cert_path, "rb") as cert_file:
        cert = crypto.load_certificate(crypto.FILETYPE_PEM, cert_file.read())
        start_date = cert.get_notBefore()
        end_date = cert.get_notAfter()
        return int(start_date.timestamp() * 1000), int(end_date.timestamp() * 1000)

def calculate_md5(file_path):
    with open(file_path, "rb") as f:
        md5 = hashlib.md5()
        md5.update(f.read())
        return md5.hexdigest()

def modify_config_files(domain, files_to_copy, destination_dir, config_files):
    for file in files_to_copy:
        shutil.copy(file, destination_dir)

    cert_path = f"{destination_dir}cert.crt"  # 假设证书文件名是 cert.crt
    start_date, end_date = get_cert_dates(cert_path)
    sum_value = calculate_md5(cert_path)

    for config_file in config_files:
        with open(config_file, 'r+') as file:
            data = json.load(file)
            # 检查新的域名配置是否已经存在
            existing_cert_found = False
            for item in data:
                if item["domain"] == f"*.{domain}":
                    item["certificate"] = f"{destination_dir}cert.crt"
                    item["fullchain"] = f"{destination_dir}fullchain.crt"
                    item["privateKey"] = f"{destination_dir}cert.key"
                    item["validFrom"] = start_date
                    item["validTo"] = end_date
                    item["sum"] = sum_value
                    item["used"] = True  # 将指定的domain的"used"属性设置为True
                    existing_cert_found = True
                    break
            if not existing_cert_found:
                new_cert = {
                    "domain": f"*.{domain}",
                    "san": [f"*.{domain}", domain],
                    "certificate": f"{destination_dir}cert.crt",
                    "fullchain": f"{destination_dir}fullchain.crt",
                    "privateKey": f"{destination_dir}cert.key",
                    "validFrom": start_date,
                    "validTo": end_date,
                    "sum": sum_value,
                    "used": True,
                    "appFlag": 0
                }
                data.append(new_cert)
            file.seek(0)
            json.dump(data, file, indent=4)
            file.truncate()

modify_config_files(domain, files_to_copy, destination_dir, config_files)
