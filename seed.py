"""
Seed script – generates 90 synthetic farmers (30 head / 30 middle / 30 tail),
villages, canals, sensors, historical sensor readings, water allocations, and
sample complaints. Designed to show realistic head-tail inequity for the demo.
"""
import asyncio
import random
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select
from .db import AsyncSessionLocal, init_db
from .models import (
    Village, Farmer, Canal, CanalSensor, SensorReading,
    WaterAllocation, IrrigationSchedule, Complaint, Alert,
    AIRecommendation, User,
    ReachType, SeverityLevel, ComplaintStatus, UserRole
)
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ─── Static data ─────────────────────────────────────────────────────────────

HEAD_VILLAGES = [
    ("Vadnagar", "Section-A", 22.00, 72.63),
    ("Visnagar", "Section-A", 23.70, 72.55),
    ("Kheralu", "Section-A", 23.88, 72.61),
    ("Unjha",   "Section-A", 23.80, 72.38),
    ("Siddhpur", "Section-A", 23.91, 72.38),
]

MIDDLE_VILLAGES = [
    ("Patan",     "Section-B", 23.85, 72.12),
    ("Harij",     "Section-B", 23.69, 71.90),
    ("Chanasma",  "Section-B", 23.72, 72.06),
    ("Radhanpur", "Section-B", 23.84, 71.60),
    ("Santalpur", "Section-B", 24.04, 71.52),
]

TAIL_VILLAGES = [
    ("Vijapur",   "Section-C", 23.55, 72.75),
    ("Mansa",     "Section-C", 23.42, 72.66),
    ("Kadi",      "Section-C", 23.30, 72.33),
    ("Kalol",     "Section-C", 23.24, 72.50),
    ("Mehsana",   "Section-C", 23.60, 72.39),
]

CROPS = [
    ("Wheat",       5.5),
    ("Cotton",      7.0),
    ("Groundnut",   4.5),
    ("Cumin",       3.5),
    ("Mustard",     4.0),
    ("Castor",      4.2),
    ("Sesame",      3.8),
    ("Bajra",       5.0),
    ("Vegetables",  6.5),
    ("Sugarcane",   9.0),
]

GUJARATI_NAMES = [
    "Ramjibhai Patel", "Pravinbhai Desai", "Kantibhai Shah", "Dahyabhai Patel",
    "Jesangbhai Parmar", "Manibhai Suthar", "Bhailalbhai Vasava", "Vitthalbhai Rathod",
    "Harshadbhai Joshi", "Dineshbhai Modi", "Chimanbhai Patel", "Nagjibhai Thakor",
    "Arvindbhai Chaudhary", "Bipinbhai Raval", "Chhaganbhai Bhoi", "Dilipbhai Baria",
    "Fulabhai Tadvi", "Ganpatbhai Nayak", "Hemabhai Solanki", "Indravadan Trivedi",
    "Jagdishbhai Makwana", "Kamleshbhai Pandya", "Laabshankar Vyas", "Mahendrabhai Dave",
    "Naranbhai Gamit", "Omprakash Brahmbhatt", "Prafulbhai Mehta", "Rameshbhai Prajapati",
    "Sureshbhai Barot", "Tulasibhai Choksi", "Umeshbhai Amin", "Vallabhbhai Bhatt",
    "Walaramji Teli", "Yogeshbhai Pandya", "Zankhana Patel", "Aarti Desai",
    "Bina Shah", "Chanda Parmar", "Daksha Suthar", "Ela Vasava",
    "Farida Rathod", "Geeta Joshi", "Hema Modi", "Indira Patel",
    "Jyoti Thakor", "Kanta Chaudhary", "Lata Raval", "Mala Bhoi",
    "Naina Baria", "Ojas Patel", "Priya Desai", "Renu Shah",
    "Savita Parmar", "Tara Suthar", "Uma Vasava", "Varsha Rathod",
    "Yamuna Joshi", "Zeel Modi", "Alpesh Patel", "Bhavesh Thakor",
    "Chirag Chaudhary", "Deep Raval", "Ekta Bhoi", "Falguni Baria",
    "Gaurav Tadvi", "Hitesh Nayak", "Ishaan Solanki", "Jay Trivedi",
    "Kiran Makwana", "Laxman Pandya", "Minesh Vyas", "Nirav Dave",
    "Om Gamit", "Parth Brahmbhatt", "Raj Mehta", "Shyam Prajapati",
    "Tarang Barot", "Uday Choksi", "Vivek Amin", "Wasim Bhatt",
    "Xena Teli", "Yatrik Pandya", "Zuber Patel", "Ajay Desai",
    "Bhargav Shah", "Chintan Parmar", "Darsh Suthar", "Ekal Vasava",
    "Foram Rathod", "Gaurangi Joshi", "Hardik Modi", "Isha Patel",
    "Jigar Thakor", "Keval Chaudhary",
]

COMPLAINT_TEMPLATES = [
    "Pani nathi avyu – Water has not arrived to my farm for {days} days.",
    "Tail-end farmers are being ignored. Head-reach villages receive double the water we get.",
    "My field irrigation slot was missed. No water came during the scheduled window.",
    "Water pressure is very low. Not enough to reach the tail-end of my field.",
    "Head-reach farmers are taking more water than their allocated share.",
    "Canal gate near {village} is leaking and wasting water.",
    "We received only {pct}% of our allocated water this week.",
    "Requested emergency irrigation for cotton crop stress but no response for {days} days.",
    "The distribution schedule changes without any notice to tail-end farmers.",
    "Water arrived {hours} hours late and most of it ran off as the field was dry.",
]


# ─── Helpers ─────────────────────────────────────────────────────────────────

def random_phone():
    return f"+91-9{random.randint(100000000, 999999999)}"


def make_allocation_id():
    return "ALLOC-" + uuid.uuid4().hex[:10].upper()


def make_complaint_id():
    return "CMP-" + uuid.uuid4().hex[:8].upper()


# ─── Seed function ────────────────────────────────────────────────────────────

async def seed():
    await init_db()

    async with AsyncSessionLocal() as db:
        # ── Villages ──────────────────────────────────────────────────────────
        village_objs = {}
        for name, section, lat, lon in HEAD_VILLAGES:
            v = Village(name=name, canal_section=section,
                        reach_type=ReachType.HEAD, latitude=lat, longitude=lon,
                        district="North Gujarat", total_land_area=random.uniform(200, 500))
            db.add(v)
            village_objs[name] = v
        for name, section, lat, lon in MIDDLE_VILLAGES:
            v = Village(name=name, canal_section=section,
                        reach_type=ReachType.MIDDLE, latitude=lat, longitude=lon,
                        district="North Gujarat", total_land_area=random.uniform(200, 500))
            db.add(v)
            village_objs[name] = v
        for name, section, lat, lon in TAIL_VILLAGES:
            v = Village(name=name, canal_section=section,
                        reach_type=ReachType.TAIL, latitude=lat, longitude=lon,
                        district="North Gujarat", total_land_area=random.uniform(200, 500))
            db.add(v)
            village_objs[name] = v
        await db.flush()

        # ── Canal ─────────────────────────────────────────────────────────────
        canal = Canal(
            canal_id="NMC-MAIN-01",
            name="Narmada Main Canal – North Gujarat Branch",
            total_capacity=480.0,
            length_km=320.0,
            is_active=True,
        )
        db.add(canal)
        await db.flush()

        # ── Sensors ───────────────────────────────────────────────────────────
        sensor_defs = [
            ("SNS-H1", "Headworks Inlet – Vadnagar",       ReachType.HEAD,   22.01, 72.64),
            ("SNS-H2", "Head Reach Gate 2 – Visnagar",     ReachType.HEAD,   23.71, 72.56),
            ("SNS-M1", "Middle Reach Entry – Patan",        ReachType.MIDDLE, 23.86, 72.13),
            ("SNS-M2", "Middle Reach Gate 4 – Chanasma",    ReachType.MIDDLE, 23.73, 72.07),
            ("SNS-T1", "Tail Reach Entry – Vijapur",        ReachType.TAIL,   23.56, 72.76),
            ("SNS-T2", "Tail Reach End – Kalol",            ReachType.TAIL,   23.25, 72.51),
        ]
        sensor_objs = []
        for sid, loc, reach, lat, lon in sensor_defs:
            s = CanalSensor(sensor_id=sid, canal_id=canal.id,
                            location=loc, reach_position=reach,
                            latitude=lat, longitude=lon)
            db.add(s)
            sensor_objs.append(s)
        await db.flush()

        # ── Farmers (90 total) ────────────────────────────────────────────────
        farmer_objs = []
        name_idx = 0
        fid_counter = 100

        reach_village_map = {
            ReachType.HEAD:   HEAD_VILLAGES,
            ReachType.MIDDLE: MIDDLE_VILLAGES,
            ReachType.TAIL:   TAIL_VILLAGES,
        }

        for reach in [ReachType.HEAD, ReachType.MIDDLE, ReachType.TAIL]:
            for i in range(30):
                village_info = random.choice(reach_village_map[reach])
                vname = village_info[0]
                crop_name, cwr = random.choice(CROPS)
                land = round(random.uniform(0.5, 5.0), 2)
                expected = round(land * cwr * 10 * random.uniform(0.9, 1.1), 2)  # cubic m

                # Head-reach gets 85-100% of expected; tail-end gets only 55-75%
                if reach == ReachType.HEAD:
                    prev_received_ratio = random.uniform(0.85, 1.00)
                elif reach == ReachType.MIDDLE:
                    prev_received_ratio = random.uniform(0.70, 0.85)
                else:
                    prev_received_ratio = random.uniform(0.55, 0.75)

                prev_received = round(expected * prev_received_ratio, 2)

                f = Farmer(
                    farmer_id=f"F{fid_counter}",
                    farmer_name=GUJARATI_NAMES[name_idx % len(GUJARATI_NAMES)],
                    village=vname,
                    village_id=village_objs[vname].id,
                    canal_section=village_info[1],
                    reach_type=reach,
                    land_area=land,
                    crop=crop_name,
                    crop_water_requirement=cwr,
                    previous_water_received=prev_received,
                    expected_water=expected,
                    contact_number=random_phone(),
                    language_preference=random.choice(["gu", "en"]),
                )
                db.add(f)
                farmer_objs.append(f)
                name_idx += 1
                fid_counter += 1

        await db.flush()

        # ── Historical sensor readings (last 7 days, every hour) ──────────────
        base_time = datetime.utcnow() - timedelta(days=7)
        for hour in range(7 * 24):
            ts = base_time + timedelta(hours=hour)
            day_frac = (hour % 24) / 24.0
            # Simulate daily flow pattern + gradual decline over 7 days
            base_flow = 320.0 * (1 - 0.02 * (hour // 24))  # slight weekly decline
            diurnal = 1.0 + 0.15 * (0.5 - abs(day_frac - 0.5))  # peak at midday

            for sensor in sensor_objs:
                if sensor.reach_position == ReachType.HEAD:
                    flow_factor = 1.0
                    level_factor = 1.0
                elif sensor.reach_position == ReachType.MIDDLE:
                    flow_factor = 0.82
                    level_factor = 0.80
                else:
                    flow_factor = 0.62
                    level_factor = 0.58

                noise = random.uniform(0.96, 1.04)
                flow = round(base_flow * flow_factor * diurnal * noise, 2)
                level = round(2.8 * level_factor * noise, 3)
                gate_pct = round(random.uniform(55, 85), 1)
                temp = round(28 + 6 * abs(day_frac - 0.5) + random.uniform(-1, 1), 1)
                rain = round(random.uniform(0, 3), 2) if random.random() < 0.1 else 0.0
                is_anomaly = False

                # Inject a realistic anomaly on day 5 for tail-end sensor
                if sensor.reach_position == ReachType.TAIL and 4 * 24 <= hour < 4 * 24 + 6:
                    flow *= 0.60
                    is_anomaly = True

                reading = SensorReading(
                    sensor_id=sensor.id,
                    timestamp=ts,
                    water_level=level,
                    flow_rate=flow,
                    gate_open_percentage=gate_pct,
                    temperature=temp,
                    rainfall=rain,
                    is_anomaly=is_anomaly,
                )
                db.add(reading)

        await db.flush()

        # ── Irrigation schedule (today) ───────────────────────────────────────
        total_water = 2_800_000.0  # cubic meters available today
        shortage = 0.18            # 18% shortage scenario
        available = total_water * (1 - shortage)

        schedule = IrrigationSchedule(
            schedule_date=datetime.utcnow().replace(hour=6, minute=0, second=0),
            total_available_water=available,
            shortage_level=shortage,
            head_equity_score=0.92,
            tail_equity_score=0.74,
            overall_fairness=0.83,
            ai_summary=(
                "Today's canal system faces an 18% water deficit due to reduced upstream "
                "inflow. Tail-end farmers in Vijapur and Kalol sections are receiving "
                "approximately 26% less than their expected allocation. The system has "
                "recalculated a fairness-adjusted schedule to bridge the head-tail gap."
            ),
        )
        db.add(schedule)
        await db.flush()

        # ── Water allocations ─────────────────────────────────────────────────
        now = datetime.utcnow()
        for i, farmer in enumerate(farmer_objs):
            if farmer.reach_type == ReachType.HEAD:
                alloc_ratio = random.uniform(0.88, 0.95)
            elif farmer.reach_type == ReachType.MIDDLE:
                alloc_ratio = random.uniform(0.78, 0.88)
            else:
                alloc_ratio = random.uniform(0.68, 0.80)

            allocated = round(farmer.expected_water * alloc_ratio, 2)
            actual = round(allocated * random.uniform(0.92, 1.0), 2)
            fairness = round(actual / farmer.expected_water, 4)
            slot_start = now + timedelta(hours=2 + i * 0.3)
            slot_end = slot_start + timedelta(hours=2)

            alloc = WaterAllocation(
                allocation_id=make_allocation_id(),
                farmer_id=farmer.id,
                date=now,
                allocated_water=allocated,
                actual_water_received=actual,
                irrigation_slot_start=slot_start,
                irrigation_slot_end=slot_end,
                fairness_score=fairness,
                schedule_id=schedule.id,
            )
            db.add(alloc)

        await db.flush()

        # ── Sample complaints ─────────────────────────────────────────────────
        tail_farmers = [f for f in farmer_objs if f.reach_type == ReachType.TAIL]
        complaint_data = [
            (tail_farmers[0],  "Pani nathi avyu – Water has not arrived to my farm for 3 days. Crop stress visible on cotton.",
             "water_shortage", SeverityLevel.HIGH),
            (tail_farmers[1],  "Tail-end farmers are being ignored. Head-reach villages receive double the water we get. This is unfair.",
             "equity_violation", SeverityLevel.HIGH),
            (tail_farmers[2],  "My irrigation slot was missed. No water came during the scheduled 06:00–08:00 window.",
             "missed_slot", SeverityLevel.MEDIUM),
            (tail_farmers[3],  "Water pressure is very low at Kalol tail end. Not enough to reach field.",
             "low_pressure", SeverityLevel.MEDIUM),
            (tail_farmers[4],  "We received only 58% of our allocated water this week. Wheat crop is suffering.",
             "under_allocation", SeverityLevel.HIGH),
            (tail_farmers[5],  "Canal gate near Mansa is leaking and wasting water before it reaches our fields.",
             "gate_leakage", SeverityLevel.CRITICAL),
            (tail_farmers[6],  "Requested emergency irrigation for groundnut crop stress but no response for 2 days.",
             "emergency_denied", SeverityLevel.CRITICAL),
            (tail_farmers[7],  "Distribution schedule changed without notice. We lost our slot.",
             "schedule_change", SeverityLevel.MEDIUM),
            (tail_farmers[8],  "Water arrived 4 hours late and most of it ran off as the field was dry.",
             "late_delivery", SeverityLevel.LOW),
            (tail_farmers[9],  "Head-reach farmers are illegally blocking canal flow at Section-A.",
             "illegal_blocking", SeverityLevel.CRITICAL),
        ]

        for farmer, text, category, severity in complaint_data:
            c = Complaint(
                complaint_id=make_complaint_id(),
                farmer_id=farmer.id,
                complaint_text=text,
                timestamp=now - timedelta(hours=random.randint(1, 48)),
                category=category,
                severity=severity,
                status=ComplaintStatus.OPEN,
                ai_recommendation=None,
            )
            db.add(c)

        # ── Alerts ────────────────────────────────────────────────────────────
        alerts = [
            (SeverityLevel.HIGH,   "low_flow",      "Tail-end flow rate dropped 38% below normal at SNS-T1",
             sensor_objs[4].id),
            (SeverityLevel.CRITICAL,"anomaly",       "Sudden flow drop detected at SNS-T2 (Kalol) – possible blockage",
             sensor_objs[5].id),
            (SeverityLevel.MEDIUM, "equity_gap",    "Head-Tail equity gap exceeded threshold: 0.74 (threshold 0.85)",
             None),
            (SeverityLevel.HIGH,   "shortage",       "18% water shortage detected. Reallocation required.",
             None),
            (SeverityLevel.LOW,    "gate_drift",    "Gate open percentage at SNS-M1 drifted above schedule by 12%",
             sensor_objs[2].id),
        ]
        for sev, atype, msg, sid in alerts:
            db.add(Alert(alert_type=atype, severity=sev, message=msg, sensor_id=sid))

        # ── AI recommendations ────────────────────────────────────────────────
        recs = [
            ("distribution", "Fairness gap detected between head and tail reach farmers",
             "Increase tail-reach irrigation window by 25 minutes and reduce head-reach by 10 minutes for the next 3 days to restore equity balance.",
             True),
            ("gate_control", "Tail-end flow below threshold",
             "Open gate SNS-M1 an additional 8% to improve tail-end delivery. Monitor SNS-T1 flow response for 2 hours.",
             True),
            ("alert_response", "Critical flow anomaly at Kalol",
             "Dispatch field inspector to SNS-T2 location. Possible unauthorized abstraction or silt blockage. Estimated resolution: 4-6 hours.",
             False),
        ]
        for rtype, ctx, rec, needs_approval in recs:
            db.add(AIRecommendation(
                recommendation_type=rtype,
                context=ctx,
                recommendation=rec,
                confidence=random.uniform(0.78, 0.95),
                requires_approval=needs_approval,
            ))

        # ── Default users ─────────────────────────────────────────────────────
        users = [
            ("admin",     "admin@narmada.gov.in",     "admin123",   UserRole.ADMIN,     None),
            ("authority", "auth@narmada.gov.in",      "auth123",    UserRole.AUTHORITY, None),
            ("farmer1",   "f100@farmers.in",          "farmer123",  UserRole.FARMER,    farmer_objs[60].id),
        ]
        for uname, email, pw, role, fid in users:
            db.add(User(
                username=uname,
                email=email,
                hashed_password=pwd_context.hash(pw),
                role=role,
                farmer_id=fid,
            ))

        await db.commit()
        print("✅ Database seeded successfully.")
        print(f"   Farmers: {len(farmer_objs)}")
        print(f"   Villages: {len(village_objs)}")
        print(f"   Sensor readings: {len(sensor_objs) * 7 * 24}")
        print(f"   Complaints: {len(complaint_data)}")


if __name__ == "__main__":
    asyncio.run(seed())
