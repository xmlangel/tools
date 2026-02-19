#!/bin/bash

#
# Jenkins 아티팩트 다운로드 스크립트
#
# 사용법: ./get.sh <DOWNLOAD_URL>
#
# 예시:
# ./get.sh "http://192.168.1.156:8080/job/AHM_Build_Rocky9/5/artifact/ahm_V3_0_DEV-test_3a5b17c_rocky9.tar.gz"

if [ -z "$1" ]; then
    echo "Usage: ./get.sh <DOWNLOAD_URL>"
    exit 1
fi

# Jenkins 사용자명
JENKINS_USER="kmkim"

# Jenkins API 토큰
JENKINS_TOKEN="11c82084f1112280f8c95a77654ccd588a"

# 다운로드 URL 생성 (두 번째 파라미터)
DOWNLOAD_URL=$1

# 인증 포함 wget 다운로드
wget --auth-no-challenge --user="$JENKINS_USER" --password="$JENKINS_TOKEN" "$DOWNLOAD_URL"
