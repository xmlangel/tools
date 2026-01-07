#!/bin/bash
#
# 릴리즈 노트 생성 및 번역 통합 스크립트
# Git 저장소로부터 릴리즈 노트를 생성하고 한글로 번역합니다.
#

set -e  # 에러 발생 시 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 사용법 출력
usage() {
    echo -e "${BLUE}=== 릴리즈 노트 생성 및 번역 도구 ===${NC}"
    echo ""
    echo "사용법: $0 [옵션]"
    echo ""
    echo "옵션:"
    echo "  -r, --repo PATH          Git 저장소 경로 (필수)"
    echo "  -v, --version VERSION    릴리즈 버전 (예: 1.0.0)"
    echo "  -o, --output FILE        출력 파일명 (기본: RELEASE_NOTES)"
    echo "  --since DATE            시작 날짜 (예: 2024-01-01, 1 week ago)"
    echo "  --until DATE            종료 날짜"
    echo "  --branch BRANCH         대상 브랜치 (기본: HEAD)"
    echo "  --skip-translate        번역 건너뛰기"
    echo "  -h, --help              도움말 출력"
    echo ""
    echo "환경변수 (.env 파일):"
    echo "  OPENWEBUI_URL           OpenWebUI API 주소"
    echo "  OPENWEBUI_API_KEY       API 인증 키"
    echo "  OPENWEBUI_MODEL         사용할 LLM 모델"
    echo ""
    echo "예시:"
    echo "  # 기본 사용"
    echo "  $0 --repo /path/to/project"
    echo ""
    echo "  # 버전 및 날짜 범위 지정"
    echo "  $0 --repo /path/to/project -v 1.0.0 --since \"2024-01-01\""
    echo ""
    echo "  # 번역 없이 생성만"
    echo "  $0 --repo /path/to/project --skip-translate"
    exit 1
}

# 기본값 설정
REPO_PATH=""
VERSION=""
OUTPUT_BASE="RELEASE_NOTES"
SINCE=""
UNTIL=""
BRANCH="HEAD"
SKIP_TRANSLATE=false

# 인자 파싱
while [[ $# -gt 0 ]]; do
    case $1 in
        -r|--repo)
            REPO_PATH="$2"
            shift 2
            ;;
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_BASE="$2"
            shift 2
            ;;
        --since)
            SINCE="$2"
            shift 2
            ;;
        --until)
            UNTIL="$2"
            shift 2
            ;;
        --branch)
            BRANCH="$2"
            shift 2
            ;;
        --skip-translate)
            SKIP_TRANSLATE=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo -e "${RED}❌ 알 수 없는 옵션: $1${NC}"
            usage
            ;;
    esac
done

# 필수 인자 확인
if [[ -z "$REPO_PATH" ]]; then
    echo -e "${RED}❌ 저장소 경로가 지정되지 않았습니다.${NC}"
    usage
fi

# 저장소 존재 확인
if [[ ! -d "$REPO_PATH" ]]; then
    echo -e "${RED}❌ 저장소를 찾을 수 없습니다: $REPO_PATH${NC}"
    exit 1
fi

# 스크립트 디렉토리 찾기
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

# 생성 스크립트 경로
GENERATOR_SCRIPT="$PARENT_DIR/generate_release_notes.py"
TRANSLATOR_SCRIPT="$SCRIPT_DIR/translate_release_notes.py"

# 스크립트 존재 확인
if [[ ! -f "$GENERATOR_SCRIPT" ]]; then
    echo -e "${RED}❌ 릴리즈 노트 생성 스크립트를 찾을 수 없습니다: $GENERATOR_SCRIPT${NC}"
    exit 1
fi

if [[ "$SKIP_TRANSLATE" = false ]] && [[ ! -f "$TRANSLATOR_SCRIPT" ]]; then
    echo -e "${RED}❌ 번역 스크립트를 찾을 수 없습니다: $TRANSLATOR_SCRIPT${NC}"
    exit 1
fi

# 출력 파일명 설정
if [[ -n "$VERSION" ]]; then
    OUTPUT_EN="${OUTPUT_BASE}_v${VERSION}.md"
    OUTPUT_KO="${OUTPUT_BASE}_v${VERSION}_ko.md"
else
    OUTPUT_EN="${OUTPUT_BASE}.md"
    OUTPUT_KO="${OUTPUT_BASE}_ko.md"
fi

echo -e "${BLUE}=== 릴리즈 노트 생성 및 번역 ===${NC}"
echo ""
echo -e "${YELLOW}📋 설정 정보:${NC}"
echo "  - 저장소: $REPO_PATH"
[[ -n "$VERSION" ]] && echo "  - 버전: $VERSION"
[[ -n "$SINCE" ]] && echo "  - 시작: $SINCE"
[[ -n "$UNTIL" ]] && echo "  - 종료: $UNTIL"
echo "  - 브랜치: $BRANCH"
echo "  - 출력 (영문): $OUTPUT_EN"
[[ "$SKIP_TRANSLATE" = false ]] && echo "  - 출력 (한글): $OUTPUT_KO"
echo ""

# Step 1: 릴리즈 노트 생성
echo -e "${GREEN}▶ Step 1: 릴리즈 노트 생성 중...${NC}"

GENERATOR_CMD="python \"$GENERATOR_SCRIPT\" --repo \"$REPO_PATH\" -o \"$OUTPUT_EN\" --branch \"$BRANCH\""
[[ -n "$VERSION" ]] && GENERATOR_CMD="$GENERATOR_CMD -v \"$VERSION\""
[[ -n "$SINCE" ]] && GENERATOR_CMD="$GENERATOR_CMD --since \"$SINCE\""
[[ -n "$UNTIL" ]] && GENERATOR_CMD="$GENERATOR_CMD --until \"$UNTIL\""

eval $GENERATOR_CMD

if [[ $? -ne 0 ]]; then
    echo -e "${RED}❌ 릴리즈 노트 생성 실패${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 릴리즈 노트 생성 완료: $OUTPUT_EN${NC}"
echo ""

# Step 2: 번역 (옵션)
if [[ "$SKIP_TRANSLATE" = false ]]; then
    echo -e "${GREEN}▶ Step 2: 한글 번역 중...${NC}"

    python "$TRANSLATOR_SCRIPT" "$OUTPUT_EN" -o "$OUTPUT_KO"

    if [[ $? -ne 0 ]]; then
        echo -e "${YELLOW}⚠️  번역 실패 (영문 릴리즈 노트는 생성됨)${NC}"
    else
        echo -e "${GREEN}✅ 번역 완료: $OUTPUT_KO${NC}"
    fi
else
    echo -e "${YELLOW}⏭️  Step 2: 번역 건너뛰기${NC}"
fi

echo ""
echo -e "${BLUE}=== 작업 완료 ===${NC}"
echo ""
echo -e "${GREEN}생성된 파일:${NC}"
echo "  📄 영문: $OUTPUT_EN"
[[ "$SKIP_TRANSLATE" = false ]] && [[ -f "$OUTPUT_KO" ]] && echo "  📄 한글: $OUTPUT_KO"
echo ""
