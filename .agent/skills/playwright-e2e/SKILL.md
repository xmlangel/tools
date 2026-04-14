---
name: Playwright E2E Testing
description: Playwright E2E 테스트 작성 및 실행을 위한 지침 가이드
---

# E2E 테스트 (Playwright) 가이드

이 스킬은 프로젝트에서 Playwright를 활용한 E2E(End-to-End) 테스트를 작성하고 실행할 때 준수해야 할 일반적인 규칙을 정의합니다. 

## 1. 전제 조건 (Prerequisites)
E2E 테스트를 실행하거나 새로운 테스트를 작성하기 전, 
프로젝트의 필수 백엔드 서버 인프라 및 앱이 구동되고 있는지 반드시 확인하세요.
- **백엔드/프론트엔드 환경**: `localhost:8080`(일반적인 Spring Boot 포트 등) 서버가 정상 응답하는지 테스트 시작 전 체크
- **관련 DB/서비스(Docker 등)**: 앱과 연결된 데이터베이스와 인프라 의존성이 컨테이너로 실행 중인지 확인

## 2. 테스트 작성 가이드 (Best Practices)

### 2.1. 디렉토리 구조 및 명명 규칙
- E2E 관련 테스트는 `src/test/e2e` 혹은 프로젝트 구조 상 E2E 지정 폴더 하위에 위치합니다.
- 테스트 파일명은 `{구현기능}.spec.js` (또는 `.ts`) 형식을 따릅니다.
- **분류 체계**: 관련된 기능별 하위 디렉토리를 두어 모듈화합니다. (예: `authentication/`, `dashboard/`, `regression/`)

### 2.2. Page Object Model (POM) 및 Fixture 패턴 보장
UI 변경에 강건한 테스트를 만들기 위해, 컴포넌트의 셀렉터와 비즈니스 기능은 Page Object Model(POM) 클래스를 생성해 분리해야 합니다.
- **BasePage 상속**: 자주 사용되는 탐색(`goto`), 캡처(`screenshot`), 대기 로직은 `BasePage.js`에 공통으로 두고, 다른 페이지들이 이를 상속하게 하세요.
- **Fixture를 통한 주입**: 테스트 파일 안에서 Playwright 기본 모듈을 원시적으로 부르기보다는, `test-fixtures.js` (또는 동급 설정파일)를 통해 페이지 객체들이 자동 주입되도록 구현합니다.

```javascript
// 나쁜 예 (X): 기본 test, expect만 사용하고 Page 객체를 직접 선언
const { test, expect } = require('@playwright/test');

// 좋은 예 (O): 커스텀 픽스처에서 주입된 페이지 객체 활용
const { test, expect } = require('../fixtures/test-fixtures.js');

test('성공적인 로그인 시나리오', async ({ loginPage, projectListPage }) => {
    // 주입받은 페이지 내장 로직과 캡슐화를 온전히 활용
});
```

### 2.3. 인증 정보 및 민감 데이터 중앙화 규칙 (Critical)
**절대** 테스트 코드나 Page Object 내부에 로그인 계정(`admin`/`password` 등)을 하드코딩해서는 안 됩니다.
인증 정보나 반복되는 테스트 데이터는 별도의 설정 파일(예: `config/credentials.js` 등)에서 관리하고 로드해야 합니다.
- 이는 차후 CI/CD 파이프라인에서 환경 변수(Environment Variables)를 통한 오버라이딩을 용이하게 합니다.

```javascript
// 외부 구성 파일에서 가져오는 형태
const { ADMIN_USERNAME, ADMIN_PASSWORD } = require('../config/credentials.js');

test('어드민 동작 검증', async ({ loginPage }) => {
    await loginPage.login(ADMIN_USERNAME, ADMIN_PASSWORD);
});
```

### 2.4. 안정적인 셀렉터 사용 우선순위
선택자(Selector) 지정 시 우선순위는 다음과 같습니다. 
순위가 높을수록 UI 요소 재배치에도 테스트가 깨질 확률이 낮습니다.
1. 태그된 속성 활용 (예: `data-testid`, `getByTestId()`)
2. Role 텍스트 기반 (접근성 트리 기준 역할과 접근 이름)
3. Text 값 매칭
4. CSS Selector (DOM 구조에 종속적이므로 최후 수단으로 제한적 사용)

### 2.5. 동작 검증 및 디버깅 (Screen 캡처)
주요 탐색 흐름, 폼 처리 저장 로직, 화면 렌더링 검사가 끝난 후엔 POM 내에 구현된 스크린샷 캡처 매서드나 `page.screenshot()`을 사용해 수행 결과를 시각적으로 남깁니다.

## 3. 테스트 실행 명령어 예시 (Execution)

### 전체 테스트 실행 (CLI)
```bash
npx playwright test src/test/e2e
```

### 단일 스펙 실행 및 UI 모드 
```bash
npx playwright test src/test/e2e/regression/login.spec.js --headed --workers=1
```

## 4. 트러블슈팅 가이드
- **연결 거부 (ECONNREFUSED) / 타임아웃**: 대상 서버 포트가 제대로 열려있는지 확인하세요. E2E 테스트 이전에 실제 로컬 서버가 먼저 실행 상태여야 합니다.
- **모듈 로드 에러**: E2E 스위트 전용 `package.json` 이 루트와 분리되어 있는 경우, `npm install` 실행 디렉토리가 맞는지 확인하세요.
- **브라우저 드라이버 없음**: Playwright 패키지 설치 후 `npx playwright install` 명령어로 필수 브라우저 바이너리가 내려받아졌는지 확인하세요.
