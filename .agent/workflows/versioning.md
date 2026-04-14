---
description: 애플리케이션 버전 관리 및 태깅 프로세스
---

# 버전 관리 워크플로우

이 프로젝트는 `Major.Minor.Build-SNAPSHOT` 형식을 사용하여 버전을 관리하며, Gradle 태스크를 통해 자동화된 버전 증가를 지원합니다.

## 버전 규칙

- **형식:** `X.Y.Z-SNAPSHOT` (예: `1.0.35-SNAPSHOT`)
- **버전 구성:**
  - `Major (X)`: 중대한 아키텍처 변경 또는 대규모 기능 개편.
  - `Minor (Y)`: 새로운 기능 추가 또는 주요 리팩토링.
  - `Build/Patch (Z)`: 버그 수정, 소규모 개선, 단순 배포.

## 버전 관리 파일

버전 정보는 다음 파일들에 동기화되어 관리됩니다:
1.  **Backend**: `build.gradle` (`version = 'X.Y.Z-SNAPSHOT'`)
2.  **Frontend**: `src/main/frontend/package.json` (`"version": "X.Y.Z"`)
3.  **Docker 빌드 스크립트**: `docker-compose-build/` 내의 `.sh` 파일들 (`VERSION="X.Y.Z"`)
4.  **Docker Compose**: `docker-compose-build/docker-compose.yml` (이미지 태그)

## 버전 업데이트 가이드

### 1. 자동 버전 증가 (Patch/Build)
가장 빈번하게 사용되는 Build 번호(Z) 증가는 수동 수정 없이 다음 명령어로 자동 수행됩니다. 이 명령은 `build.gradle`의 버전을 직접 읽어 Patch 번호를 1 증가시키고 다른 파일들에 전파합니다.

```bash
# build.gradle 포함 모든 파일의 Patch 버전(+1) 자동 증가 및 동기화
./gradlew incrementVersion
```

### 2. Major/Minor 버전 변경
Major(X) 또는 Minor(Y) 버전을 변경(예: 1.0.35 -> 1.1.0)해야 할 경우에만 수동 작업이 병행됩니다.

1.  `build.gradle` 파일의 `version = 'X.Y.Z-SNAPSHOT'` 부분을 원하는 버전(예: `1.1.0-SNAPSHOT`)으로 수동 수정합니다.
2.  `./gradlew incrementVersion`을 실행합니다. 
    *   **주의**: 이때 태스크 로직상 Patch 번호가 다시 1 증가하여 최종적으로 `1.1.1`이 각 파일에 전파됩니다. 
    *   만약 정확히 `1.1.0`을 맞추고 싶다면 `build.gradle`에 `1.0.99`와 같이 이전 상태의 패치 번호를 입력한 후 실행하거나, 태스크 로직을 참고하십시오.

### 3. 배포 및 태깅
버전 업데이트가 완료되면 Git 태그를 생성하여 릴리스 시점을 기록합니다.

```bash
# 현재 버전 확인 (예: 1.0.35)
git add .
git commit -m "chore: bump version to 1.0.35"
git tag -a v1.0.35 -m "Release version 1.0.35"
git push origin main --tags
```

## 주의사항
- **일관성 유지**: 반드시 Gradle 태스크를 사용하여 모든 파일의 버전이 일치하도록 관리하십시오.
- **SNAPSHOT**: `build.gradle`에서는 개발 중임을 나타내기 위해 `-SNAPSHOT` 접미사를 유지하지만, `package.json`이나 Docker 태그에는 숫자 버전만 사용됩니다.
