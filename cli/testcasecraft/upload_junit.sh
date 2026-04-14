#!/bin/bash

# ==============================================================================
# TestCaseCraft (TCC) JUnit Result Uploader
# ==============================================================================
# 사용법: ./upload_junit.sh <base_url> <project_id> <junit_file> <user_id> <password>
# 예시: ./upload_junit.sh https://tc.qaspecialist.uk 539b1952-627f-4aca-875c-cbc6cd765ff0 result.xml myid mypass
# ==============================================================================

# 0. 입력 파라미터 체크
if [ "$#" -ne 5 ]; then
    echo "Usage: $0 <base_url> <project_id> <junit_file> <user_id> <password>"
    echo "Example: $0 https://tc.qaspecialist.uk 539b1952-627f-4aca-875c-cbc6cd765ff0 junit.xml id password"
    exit 1
fi

BASE_URL=$1
PROJECT_ID=$2
JUNIT_FILE=$3
USER_ID=$4
PASSWORD=$5

# 의존성 체크 (jq)
if ! command -v jq &> /dev/null; then
    echo "Error: 'jq' command is not installed. Please install jq to use this script."
    exit 1
fi

# 파일 존재 여부 체크
if [ ! -f "$JUNIT_FILE" ]; then
    echo "Error: JUnit file '$JUNIT_FILE' not found."
    exit 1
fi

echo "--- Step 1: Login to TCC ---"
# 1. 로그인하여 토큰 발급
# /api/auth/login 호출
LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{
        \"username\": \"${USER_ID}\",
        \"password\": \"${PASSWORD}\"
    }")

# 응답에서 accessToken 추출
TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.accessToken // empty')

if [ -z "$TOKEN" ]; then
    echo "Error: Login failed. Please check your credentials and Base URL."
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

echo "Successfully logged in. Token acquired."

echo "--- Step 2: Upload JUnit XML ---"
# 2. JUnit XML 파일 업로드
# /api/junit-results/upload?projectId=<projectId> 호출
# -F "file=@<path>" 옵션으로 multipart/form-data 전송
UPLOAD_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/junit-results/upload?projectId=${PROJECT_ID}" \
    -H "Authorization: Bearer ${TOKEN}" \
    -F "file=@${JUNIT_FILE}")

# 응답 결과 확인
SUCCESS_FLAG=$(echo "$UPLOAD_RESPONSE" | jq -r '.testResultId // empty')

if [ -n "$SUCCESS_FLAG" ]; then
    echo "Successfully uploaded JUnit results!"
    echo "Result ID: $SUCCESS_FLAG"
else
    echo "Error: Upload failed."
    echo "Response: $UPLOAD_RESPONSE"
    exit 1
fi

echo "Done."
