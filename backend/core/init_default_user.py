"""
기본 관리자 사용자 초기화 모듈
Docker Compose 시작 시 자동으로 기본 관리자 계정을 생성합니다.
"""
from sqlalchemy.orm import Session
from models.user import User
from core.security import get_password_hash
from core.database import SessionLocal
import os

# 환경 변수로부터 기본 사용자 정보 로드 (기본값 제공)
DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")


def create_default_user():
    """
    기본 관리자 사용자를 생성합니다.
    이미 존재하는 경우 건너뜁니다.
    """
    db: Session = SessionLocal()
    try:
        # 기본 관리자 계정이 이미 존재하는지 확인
        existing_user = db.query(User).filter(User.username == DEFAULT_ADMIN_USERNAME).first()
        
        if existing_user:
            print(f"ℹ️  기본 관리자 계정 '{DEFAULT_ADMIN_USERNAME}'이(가) 이미 존재합니다.")
            return
        
        # 기본 관리자 계정 생성
        hashed_password = get_password_hash(DEFAULT_ADMIN_PASSWORD)
        default_user = User(
            username=DEFAULT_ADMIN_USERNAME,
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=True,
            failed_login_attempts=0
        )
        
        db.add(default_user)
        db.commit()
        db.refresh(default_user)
        
        print(f"✅ 기본 관리자 계정이 생성되었습니다.")
        print(f"   Username: {DEFAULT_ADMIN_USERNAME}")
        print(f"   Password: {DEFAULT_ADMIN_PASSWORD}")
        print(f"   ⚠️  프로덕션 환경에서는 반드시 비밀번호를 변경하세요!")
        
    except Exception as e:
        print(f"❌ 기본 관리자 계정 생성 중 오류 발생: {e}")
        db.rollback()
    finally:
        db.close()
