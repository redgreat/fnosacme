#!/bin/bash

# path of this script
BASE_ROOT=$(cd "$(dirname "$0")";pwd)
# date time
DATE_TIME=`date +%Y%m%d%H%M%S`
# base crt path
CRT_BASE_PATH="/usr/trim/var/trim_connect/ssls"
CRT_TEM_PATH="${BASE_ROOT}/certs"
ACME_BIN_PATH=${BASE_ROOT}/acme.sh
TEMP_PATH=${BASE_ROOT}/temp

backupCrt () {
  echo 'begin backupCrt'
  BACKUP_PATH=${BASE_ROOT}/backup/${DATE_TIME}
  mkdir -p ${BACKUP_PATH}
  cp -r ${CRT_BASE_PATH}/* ${BACKUP_PATH}
  echo ${BACKUP_PATH} > ${BASE_ROOT}/backup/latest
  echo 'done backupCrt'
  return 0
}

versionLt () { test "$(echo "$@" | tr " " "\n" | sort -rV | head -n 1)" != "$1"; }
installAcme () {
  ALLOW_INSTALL=false
  ACME_SH_FILE=${ACME_BIN_PATH}/acme.sh
  ACME_SH_NEW_VERSION=$(wget -qO- -t1 -T2 "https://api.github.com/repos/acmesh-official/acme.sh/releases/latest" | grep "tag_name" | head -n 1 | awk -F ":" '{print $2}' | sed 's/\"//g;s/,//g;s/ //g')
  ACME_SH_ADDRESS=https://ghp.ci/https://github.com/acmesh-official/acme.sh/archive/${ACME_SH_NEW_VERSION}.tar.gz
  if [ -z "${ACME_SH_NEW_VERSION}" ]; then
    echo 'unable to get new version number'
    return 0
  fi
  if [ ! -f "${ACME_SH_FILE}" ]; then
    ALLOW_INSTALL=true
    echo 'acme not installed, start install'
  else
    ACME_SH_VERSION=$(cat ${ACME_SH_FILE} | grep "VER=*" | head -n 1 | awk -F "=" '{print $2}' | sed 's/\"//g;s/,//g;s/ //g')
    if versionLt ${ACME_SH_VERSION} ${ACME_SH_NEW_VERSION}; then
      ALLOW_INSTALL=true
      echo 'acme has a new version, start updating'
    else
      echo 'skip acme installation'
    fi
  fi
  if [ $ALLOW_INSTALL = true ]; then
    echo 'in progress...'
    mkdir -p ${TEMP_PATH}
    cd ${TEMP_PATH}
    echo 'begin downloading acme.sh tool...'
    SRC_TAR_NAME=acme.sh.tar.gz
    local retry=0
    local success=false

    while [ $retry -lt 3 ] && [ $success == false ]; do
      if curl -L -o ${SRC_TAR_NAME} ${ACME_SH_ADDRESS}; then
        success=true
      else
        retry=$((retry+1))
        echo "Download attempt ${retry} failed, retrying..."
      fi
    done

    if [ $success == false ]; then
      echo "Failed to download acme.sh after 3 attempts"
      return 1
    fi

    SRC_NAME=`tar -tzf ${SRC_TAR_NAME} | head -1 | cut -f1 -d"/"`
    tar zxvf ${SRC_TAR_NAME}
    echo 'begin installing acme.sh tool...'
    cd ${SRC_NAME}
    ./acme.sh --install --nocron --home ${ACME_BIN_PATH}
    echo 'done installAcme'
    rm -rf ${TEMP_PATH}
  fi
  return 0
}

generateCrt () {
  echo 'begin generateCrt'
  cd ${BASE_ROOT}
  . ./config
  echo 'begin updating default cert by acme.sh tool'
  . ${ACME_BIN_PATH}/acme.sh.env
  ${ACME_BIN_PATH}/acme.sh --force --log --issue --server letsencrypt --dns ${DNS} --dnssleep ${DNS_SLEEP} -d "${DOMAIN}" -d "*.${DOMAIN}" --keylength ec-256
  ${ACME_BIN_PATH}/acme.sh --force --installcert -d ${DOMAIN} -d *.${DOMAIN} --ecc \
    --certpath ${CRT_TEM_PATH}/${DOMAIN}.crt \
    --key-file ${CRT_TEM_PATH}/${DOMAIN}.key \
    --fullchain-file ${CRT_TEM_PATH}/fullchain.crt
  ${ACME_BIN_PATH}/acme.sh --renew -d ${DOMAIN} -d *.${DOMAIN} --force --ecc

  if [ -s "${CRT_TEM_PATH}/${DOMAIN}.crt" ]; then
    echo 'done generateCrt'
    return 0
  else
    echo '[ERR] fail to generateCrt'
    echo "begin revert"
    revertCrt
    exit 1;
  fi
}

updateService () {
  echo 'begin updateService'
  echo 'cp cert path to fnos'
  python3 ${BASE_ROOT}/cert-up.py ${DOMAIN}
  echo 'done updateService'
}

reloadWebService () {
  echo 'begin reloadWebService'
  echo 'reloading new cert...'
  /usr/trim/nginx/sbin/nginx -s reload
  echo 'done reloadWebService'
}

revertCrt () {
  echo 'begin revertCrt'
  BACKUP_PATH=${BASE_ROOT}/backup/$1
  if [ -z "$1" ]; then
    BACKUP_PATH=`cat ${BASE_ROOT}/backup/latest`
  fi
  if [ ! -d "${BACKUP_PATH}" ]; then
    echo "[ERR] backup path: ${BACKUP_PATH} not found."
    return 1
  fi
  echo "Restoring backup from ${BACKUP_PATH}..."
  cp -rf ${BACKUP_PATH}/* ${CRT_BASE_PATH}
  reloadWebService
  echo 'done revertCrt'
}

updateCrt () {
  echo '------ begin updateCrt ------'
  backupCrt
  installAcme
  generateCrt
  updateService
  reloadWebService
  echo '------ end updateCrt ------'
}

case "$1" in
  update)
    echo "begin update cert"
    updateCrt
    ;;

  revert)
    echo "begin revert"
      revertCrt $2
      ;;

    *)
        echo "Usage: $0 {update|revert}"
        exit 1
esac
