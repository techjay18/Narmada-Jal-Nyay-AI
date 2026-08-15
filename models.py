"""
SQLAlchemy ORM models for Narmada Jal Nyay AI
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Text, Index, Enum as SAEnum
)
from sqlalchemy.orm import DeclarativeBase, relationship
import enum


class Base(DeclarativeBase):
    pass


class ReachType(str, enum.Enum):
    HEAD = "head"
    MIDDLE = "middle"
    TAIL = "tail"


class SeverityLevel(str, enum.Enum):
    NORMAL = "normal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplaintStatus(str, enum.Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    AUTHORITY = "authority"
    FARMER = "farmer"


# ─────────────────────────────────────────────────────────────────────────────
class Village(Base):
    __tablename__ = "villages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    district = Column(String(100), default="Anand")
    canal_section = Column(String(50))
    reach_type = Column(SAEnum(ReachType), nullable=False)
    latitude = Column(Float, default=22.5)
    longitude = Column(Float, default=72.9)
    total_land_area = Column(Float, default=0.0)  # hectares

    farmers = relationship("Farmer", back_populates="village_obj")


# ─────────────────────────────────────────────────────────────────────────────
class Farmer(Base):
    __tablename__ = "farmers"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(String(20), unique=True, index=True, nullable=False)
    farmer_name = Column(String(150), nullable=False)
    village = Column(String(100))
    village_id = Column(Integer, ForeignKey("villages.id"), nullable=True)
    canal_section = Column(String(50))
    reach_type = Column(SAEnum(ReachType), nullable=False)
    land_area = Column(Float, nullable=False)          # hectares
    crop = Column(String(100))
    crop_water_requirement = Column(Float, default=0.0)  # mm/day
    previous_water_received = Column(Float, default=0.0) # cubic meters
    expected_water = Column(Float, default=0.0)          # cubic meters
    contact_number = Column(String(20))
    language_preference = Column(String(10), default="gu")  # gu / en
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    village_obj = relationship("Village", back_populates="farmers")
    allocations = relationship("WaterAllocation", back_populates="farmer")
    complaints = relationship("Complaint", back_populates="farmer")

    __table_args__ = (
        Index("ix_farmers_reach_type", "reach_type"),
        Index("ix_farmers_canal_section", "canal_section"),
    )


# ─────────────────────────────────────────────────────────────────────────────
class Canal(Base):
    __tablename__ = "canals"

    id = Column(Integer, primary_key=True, index=True)
    canal_id = Column(String(20), unique=True, index=True)
    name = Column(String(150))
    total_capacity = Column(Float)   # cubic meters/sec
    length_km = Column(Float)
    is_active = Column(Boolean, default=True)

    sensors = relationship("CanalSensor", back_populates="canal")


# ─────────────────────────────────────────────────────────────────────────────
class CanalSensor(Base):
    __tablename__ = "canal_sensors"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String(20), unique=True, index=True)
    canal_id = Column(Integer, ForeignKey("canals.id"))
    location = Column(String(150))
    reach_position = Column(SAEnum(ReachType))
    latitude = Column(Float)
    longitude = Column(Float)
    is_active = Column(Boolean, default=True)

    canal = relationship("Canal", back_populates="sensors")
    readings = relationship("SensorReading", back_populates="sensor")


# ─────────────────────────────────────────────────────────────────────────────
class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(Integer, ForeignKey("canal_sensors.id"))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    water_level = Column(Float)          # meters
    flow_rate = Column(Float)            # cumecs (m3/s)
    gate_open_percentage = Column(Float) # 0-100
    temperature = Column(Float)          # Celsius
    rainfall = Column(Float, default=0.0) # mm
    is_anomaly = Column(Boolean, default=False)

    sensor = relationship("CanalSensor", back_populates="readings")

    __table_args__ = (
        Index("ix_sensor_readings_timestamp", "timestamp"),
        Index("ix_sensor_readings_sensor_id", "sensor_id"),
    )


# ─────────────────────────────────────────────────────────────────────────────
class WaterAllocation(Base):
    __tablename__ = "water_allocations"

    id = Column(Integer, primary_key=True, index=True)
    allocation_id = Column(String(30), unique=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"))
    date = Column(DateTime, default=datetime.utcnow, index=True)
    allocated_water = Column(Float, default=0.0)      # cubic meters
    actual_water_received = Column(Float, default=0.0)
    irrigation_slot_start = Column(DateTime, nullable=True)
    irrigation_slot_end = Column(DateTime, nullable=True)
    fairness_score = Column(Float, default=1.0)       # actual/expected
    schedule_id = Column(Integer, ForeignKey("irrigation_schedules.id"), nullable=True)

    farmer = relationship("Farmer", back_populates="allocations")
    schedule = relationship("IrrigationSchedule", back_populates="allocations")


# ─────────────────────────────────────────────────────────────────────────────
class IrrigationSchedule(Base):
    __tablename__ = "irrigation_schedules"

    id = Column(Integer, primary_key=True, index=True)
    schedule_date = Column(DateTime, default=datetime.utcnow)
    total_available_water = Column(Float)
    shortage_level = Column(Float, default=0.0)  # 0-1, 0=no shortage
    head_equity_score = Column(Float, default=1.0)
    tail_equity_score = Column(Float, default=1.0)
    overall_fairness = Column(Float, default=1.0)
    ai_summary = Column(Text, nullable=True)
    approved_by = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    allocations = relationship("WaterAllocation", back_populates="schedule")


# ─────────────────────────────────────────────────────────────────────────────
class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(String(30), unique=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"))
    complaint_text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    category = Column(String(100))
    severity = Column(SAEnum(SeverityLevel), default=SeverityLevel.NORMAL)
    status = Column(SAEnum(ComplaintStatus), default=ComplaintStatus.OPEN)
    ai_recommendation = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    resolved_by = Column(String(100), nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    farmer = relationship("Farmer", back_populates="complaints")


# ─────────────────────────────────────────────────────────────────────────────
class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(100))
    severity = Column(SAEnum(SeverityLevel), default=SeverityLevel.LOW)
    message = Column(Text)
    details = Column(Text, nullable=True)
    sensor_id = Column(Integer, ForeignKey("canal_sensors.id"), nullable=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"), nullable=True)
    is_acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


# ─────────────────────────────────────────────────────────────────────────────
class AIRecommendation(Base):
    __tablename__ = "ai_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_type = Column(String(100))
    context = Column(Text)
    recommendation = Column(Text)
    confidence = Column(Float, default=0.8)
    requires_approval = Column(Boolean, default=False)
    approved = Column(Boolean, nullable=True)
    approved_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True)
    email = Column(String(200), unique=True, index=True)
    hashed_password = Column(String(200))
    role = Column(SAEnum(UserRole), default=UserRole.FARMER)
    farmer_id = Column(Integer, ForeignKey("farmers.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
