"""
Confluence 페이지 자동 생성 스크립트

Usage:
    python create_page.py [parent_page_id]

Environment Variables:
    ATLASSIAN_URL: Atlassian 인스턴스 URL
    ATLASSIAN_USERNAME: 사용자 이름
    ATLASSIAN_API_TOKEN: API 토큰
    CONFLUENCE_SPACE_KEY: Space 키
"""

import os
import sys
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from atlassian import Confluence


# ============================================================
# 설정
# ============================================================

@dataclass(frozen=True)
class Config:
    """Confluence 연결 설정"""
    url: str
    username: str
    api_token: str
    space_key: str
    is_cloud: bool = True

    @classmethod
    def from_env(cls) -> "Config":
        """환경 변수에서 설정을 로드합니다."""
        load_dotenv()
        
        required_vars = {
            "ATLASSIAN_URL": os.getenv("ATLASSIAN_URL"),
            "ATLASSIAN_USERNAME": os.getenv("ATLASSIAN_USERNAME"),
            "ATLASSIAN_API_TOKEN": os.getenv("ATLASSIAN_API_TOKEN"),
            "CONFLUENCE_SPACE_KEY": os.getenv("CONFLUENCE_SPACE_KEY"),
        }
        
        missing_vars = [key for key, value in required_vars.items() if not value]
        if missing_vars:
            raise ConfigurationError(
                f"필수 환경 변수가 설정되지 않았습니다: {', '.join(missing_vars)}"
            )
        
        return cls(
            url=required_vars["ATLASSIAN_URL"],
            username=required_vars["ATLASSIAN_USERNAME"],
            api_token=required_vars["ATLASSIAN_API_TOKEN"],
            space_key=required_vars["CONFLUENCE_SPACE_KEY"],
        )


# ============================================================
# 예외 클래스
# ============================================================

class ConfluencePageError(Exception):
    """Confluence 페이지 관련 기본 예외"""
    pass


class ConfigurationError(ConfluencePageError):
    """설정 오류"""
    pass


class PageCreationError(ConfluencePageError):
    """페이지 생성 오류"""
    pass


# ============================================================
# 로깅 설정
# ============================================================

def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """로깅을 설정하고 로거를 반환합니다."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger(__name__)


logger = setup_logging()


# ============================================================
# Confluence 클라이언트
# ============================================================

def create_confluence_client(config: Config) -> Confluence:
    """Confluence 클라이언트를 생성합니다."""
    try:
        client = Confluence(
            url=config.url,
            username=config.username,
            password=config.api_token,
            cloud=config.is_cloud,
        )
        logger.info("Confluence 연결 성공: %s", config.url)
        return client
    except Exception as e:
        raise ConfigurationError(f"Confluence 클라이언트 초기화 실패: {e}") from e


# ============================================================
# 페이지 콘텐츠 생성
# ============================================================

def generate_page_title(prefix: str = "Python API 자동 생성 테스트") -> str:
    """타임스탬프가 포함된 페이지 제목을 생성합니다."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"{prefix} - {timestamp}"


def generate_page_body() -> str:
    """페이지 본문 HTML을 생성합니다."""
    return """
    <h2>Confluence API Test</h2>
    <p>이 페이지는 <strong>Python 스크립트</strong>를 통해 자동으로 생성되었습니다.</p>
    <ul>
        <li>작성자: Python Bot</li>
        <li>상태: 성공</li>
    </ul>
    <p>내용을 원하는대로 수정하여 테스트해보세요.</p>
    """


# ============================================================
# 페이지 생성 로직
# ============================================================

@dataclass
class PageCreationResult:
    """페이지 생성 결과"""
    page_id: str
    page_link: str
    title: str


def create_page(
    confluence: Confluence,
    space_key: str,
    title: str,
    body: str,
    parent_id: Optional[str] = None,
) -> PageCreationResult:
    """
    Confluence 페이지를 생성합니다.

    Args:
        confluence: Confluence 클라이언트
        space_key: Space 키
        title: 페이지 제목
        body: 페이지 본문 (HTML)
        parent_id: 부모 페이지 ID (선택)

    Returns:
        PageCreationResult: 생성된 페이지 정보

    Raises:
        PageCreationError: 페이지 생성 실패 시
    """
    # 중복 페이지 확인
    if confluence.page_exists(space=space_key, title=title):
        raise PageCreationError(f"'{title}' 제목의 페이지가 이미 존재합니다.")

    try:
        response = confluence.create_page(
            space=space_key,
            title=title,
            body=body,
            parent_id=parent_id,
            representation="storage",
            full_width=False,
        )
        
        page_id = response.get("id")
        base_url = response.get("_links", {}).get("base", "")
        web_ui = response.get("_links", {}).get("webui", "")
        page_link = f"{base_url}{web_ui}"

        return PageCreationResult(
            page_id=page_id,
            page_link=page_link,
            title=title,
        )

    except Exception as e:
        raise PageCreationError(f"페이지 생성 실패: {e}") from e


# ============================================================
# CLI 인터페이스
# ============================================================

def parse_args() -> Optional[str]:
    """명령줄 인수를 파싱하여 부모 페이지 ID를 반환합니다."""
    if len(sys.argv) > 1:
        parent_id = sys.argv[1]
        logger.info("부모 페이지 ID: %s", parent_id)
        return parent_id
    return None


def main() -> int:
    """메인 진입점"""
    try:
        # 설정 로드
        config = Config.from_env()
        
        # 클라이언트 생성
        confluence = create_confluence_client(config)
        
        # 인수 파싱
        parent_id = parse_args()
        
        # 페이지 콘텐츠 생성
        title = generate_page_title()
        body = generate_page_body()
        
        logger.info("페이지 생성 중... (Space: %s, Title: %s)", config.space_key, title)
        
        # 페이지 생성
        result = create_page(
            confluence=confluence,
            space_key=config.space_key,
            title=title,
            body=body,
            parent_id=parent_id,
        )
        
        # 결과 출력
        logger.info("-" * 50)
        logger.info("✅ 페이지 생성 성공!")
        logger.info("Page ID: %s", result.page_id)
        logger.info("Link: %s", result.page_link)
        logger.info("-" * 50)
        
        return 0

    except ConfigurationError as e:
        logger.error("설정 오류: %s", e)
        return 1
    
    except PageCreationError as e:
        logger.error("❌ %s", e)
        return 1
    
    except Exception as e:
        logger.exception("예상치 못한 오류 발생: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
