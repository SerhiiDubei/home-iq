from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import os

Base = declarative_base()


class Site(Base):
    __tablename__ = "sites"
    id = Column(Integer, primary_key=True)
    domain = Column(String(255), unique=True, nullable=False, index=True)
    niche = Column(String(50), nullable=False, index=True)
    seed_url = Column(Text)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_scraped = Column(DateTime)
    next_scrape_at = Column(DateTime)
    extractor_type = Column(String(50))
    fetcher_tier = Column(Integer)
    status = Column(String(20), default="active")  # active/blocked/dead/discovered
    pages = relationship("Page", back_populates="site")


class Page(Base):
    __tablename__ = "pages"
    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey("sites.id"))
    url = Column(Text, unique=True, nullable=False, index=True)
    last_scraped = Column(DateTime)
    html_hash = Column(String(64))
    image_count = Column(Integer, default=0)
    site = relationship("Site", back_populates="pages")
    photos = relationship("Photo", back_populates="page")


class Photo(Base):
    __tablename__ = "photos"
    id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey("pages.id"), nullable=True)  # null for imported photos
    sha256_hash = Column(String(64), unique=True, nullable=False, index=True)
    file_path = Column(Text, nullable=False)
    original_url = Column(Text, nullable=True)   # null for manually imported
    niche = Column(String(50), nullable=False, index=True)
    section_tag = Column(String(50), index=True)  # ba/hero/project/finished/unknown
    width = Column(Integer)
    height = Column(Integer)
    file_size = Column(Integer)
    format = Column(String(10))
    alt_text = Column(Text)
    source = Column(String(20), default="scraped")  # scraped / imported / generated
    approved = Column(Boolean, nullable=True)        # null=pending, True=approved, False=rejected
    detected_at = Column(DateTime, default=datetime.utcnow)
    extra = Column(JSON)
    page = relationship("Page", back_populates="photos")


class ScrapeRun(Base):
    __tablename__ = "scrape_runs"
    id = Column(Integer, primary_key=True)
    site_id = Column(Integer)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime)
    pages_scraped = Column(Integer, default=0)
    photos_added = Column(Integer, default=0)
    error_msg = Column(Text)


_engine = None
SessionLocal = None


def get_engine(db_path: str = None):
    global _engine, SessionLocal
    if _engine is None:
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "photos.db")
        _engine = create_engine(
            f"sqlite:///{db_path}",
            echo=False,
            connect_args={"timeout": 30, "check_same_thread": False},
        )
        # Enable WAL mode for better concurrency
        from sqlalchemy import event
        @event.listens_for(_engine, "connect")
        def set_wal_mode(dbapi_conn, connection_record):
            dbapi_conn.execute("PRAGMA journal_mode=WAL")
            dbapi_conn.execute("PRAGMA busy_timeout=30000")
        SessionLocal = sessionmaker(bind=_engine)
    return _engine


def get_session():
    if SessionLocal is None:
        init_db()
    return SessionLocal()


def init_db(db_path: str = None):
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    return engine
