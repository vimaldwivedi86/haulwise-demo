import uuid

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Float,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from db import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Driver(Base):
    __tablename__ = "drivers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    dl_number = Column(String, nullable=False)
    face_image_key = Column(String, nullable=True)
    face_embedding = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("drivers.id"), nullable=True)
    reg_number = Column(String, nullable=False)
    route_name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Position(Base):
    __tablename__ = "positions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    speed_kmh = Column(Float, nullable=False, default=0)
    heading = Column(Float, nullable=False, default=0)
    ts = Column(DateTime(timezone=True), server_default=func.now())


class VideoEvent(Base):
    __tablename__ = "video_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("drivers.id"), nullable=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    type = Column(String, nullable=False)
    severity = Column(String, nullable=False, default="medium")
    clip_key = Column(String, nullable=True)
    face_snapshot_key = Column(String, nullable=True)
    ts = Column(DateTime(timezone=True), server_default=func.now())


class ShareLink(Base):
    __tablename__ = "share_links"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    token = Column(String, unique=True, nullable=False)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Consent(Base):
    __tablename__ = "consents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("drivers.id"), nullable=False)
    purpose = Column(String, nullable=False)
    status = Column(String, nullable=False)
    receipt_id = Column(String, nullable=True)
    ts = Column(DateTime(timezone=True), server_default=func.now())


class DprRequest(Base):
    __tablename__ = "dpr_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cmp_request_id = Column(String, nullable=False)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("drivers.id"), nullable=False)
    trigger = Column(String, nullable=False)
    status = Column(String, nullable=False, default="open")
    opened_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)


class DprStep(Base):
    __tablename__ = "dpr_steps"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    dpr_id = Column(UUID(as_uuid=True), ForeignKey("dpr_requests.id"), nullable=False)
    step = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    evidence = Column(JSON, nullable=True)
    ts = Column(DateTime(timezone=True), server_default=func.now())


class VendorCall(Base):
    __tablename__ = "vendor_calls"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    vendor = Column(String, nullable=False)
    endpoint = Column(String, nullable=False)
    method = Column(String, nullable=False)
    payload_preview = Column(JSON, nullable=True)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("drivers.id"), nullable=True)
    ts = Column(DateTime(timezone=True), server_default=func.now())
