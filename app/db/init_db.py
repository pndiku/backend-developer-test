import datetime
import json
import os
from csv import DictReader

import redis
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.schema import DropTable

from app import crud, models, schemas
from app.core.config import settings
from app.core.logger import log
from app.db import base  # noqa: F401
from app.db.session import engine
from app.utils import validateMSISDN

redisConn = redis.from_url(settings.REDIS_URL)


@compiles(DropTable, "postgresql")
def _compile_drop_table(element, compiler, **kwargs):
    return compiler.visit_drop_table(element) + " CASCADE"


def init_settings(db):
    log.info("initialising settings")
    # Override SMS settings for DEV servers
    # Create settings
    file_name = f"{os.getcwd()}/csv/setting.csv"
    with open(file_name, "r") as f:
        dict_reader = DictReader(f)
        data = list(dict_reader)

        if settings.APPLICATION_ENVIRONMENT == "development":
            data["SMS_URL"] = "https://messaging-sandbox.fdibiz.com/api/v1"
            data["SMS_KEY"] = "5c671149-3640-4c86-9ab4-6c129829f529"
            data["SMS_SECRET"] = "5776d812-3683-4721-bb86-cc17c545eaab"

        stmt = insert(models.Setting).values(data)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=[models.Setting.id],
        )
        db.execute(stmt)
        db.commit()
        rows = crud.setting.get_multi(db)
        if settings.CONFIG_TYPE != "test":
            for r in rows:
                redisConn.hset("setting", r.id, json.dumps(r.to_dict()))


def init_db(db: Session) -> None:
    init_settings(db)

    log.info("initialising document types")
    # Create document_types
    file_name = f"{os.getcwd()}/csv/document_type.csv"
    data = []
    with open(file_name, "r") as f:
        dict_reader = DictReader(f)
        data = list(dict_reader)
        log.debug(data)
        for d in data:
            d.update((k, False if v == "false" else True) for k, v in d.items() if k == "is_company")
        log.debug(data)
        stmt = insert(models.DocumentType).values(data)
        stmt = stmt.on_conflict_do_update(
            index_elements=[models.DocumentType.id],
            set_=dict(
                name=stmt.excluded.name,
                is_company=stmt.excluded.is_company,
                kyc_level=stmt.excluded.kyc_level,
            ),
        )
        log.debug(stmt)
        db.execute(stmt)
        db.commit()

    log.info("initialising roles")
    # Create roles
    file_name = f"{os.getcwd()}/csv/role.csv"
    with open(file_name, "r") as f:
        dict_reader = DictReader(f)
        data = list(dict_reader)
        stmt = insert(models.Role).values(data)
        stmt = stmt.on_conflict_do_nothing(index_elements=[models.Role.id])
        db.execute(stmt)
        db.commit()

    log.info("initialising presences")
    # Create roles
    file_name = f"{os.getcwd()}/csv/presence.csv"
    with open(file_name, "r") as f:
        dict_reader = DictReader(f)
        data = list(dict_reader)
        stmt = insert(models.Presence).values(data)
        stmt = stmt.on_conflict_do_nothing(index_elements=[models.Presence.id])
        db.execute(stmt)
        db.commit()

    log.info("initialising location classes")
    # Create roles
    file_name = f"{os.getcwd()}/csv/location_class.csv"
    with open(file_name, "r") as f:
        dict_reader = DictReader(f)
        data = list(dict_reader)
        stmt = insert(models.LocationClass).values(data)
        stmt = stmt.on_conflict_do_nothing(index_elements=[models.LocationClass.id])
        db.execute(stmt)
        db.commit()

    log.info("initialising countries")
    # Create countries
    file_name = f"{os.getcwd()}/csv/country.csv"
    with open(file_name, "r") as f:
        dict_reader = DictReader(f)
        data = list(dict_reader)
        stmt = insert(models.Country).values(data)
        stmt = stmt.on_conflict_do_nothing(index_elements=[models.Country.id])
        db.execute(stmt)
        db.commit()

    log.info("initialising regions")
    # Create regions
    file_name = f"{os.getcwd()}/csv/region.csv"
    with open(file_name, "r") as f:
        dict_reader = DictReader(f)
        data = list(dict_reader)
        stmt = insert(models.Region).values(data)
        stmt = stmt.on_conflict_do_nothing(index_elements=[models.Region.id])
        db.execute(stmt)
        db.commit()

    log.info("initialising sub_regions")
    # Create sub_regions
    file_name = f"{os.getcwd()}/csv/sub_region.csv"
    with open(file_name, "r") as f:
        dict_reader = DictReader(f)
        data = list(dict_reader)
        stmt = insert(models.SubRegion).values(data)
        stmt = stmt.on_conflict_do_nothing(index_elements=[models.SubRegion.id])
        db.execute(stmt)
        db.commit()

    log.info("initialising integrator")
    agent = crud.agent.get_aggregator(db)

    if not agent:
        msisdn = validateMSISDN(settings.DEFAULT_AGGREGATOR_MSISDN, settings.DEFAULT_AGGREGATOR_COUNTRY)
        agentview = schemas.AgentViewCreate(
            business_name=settings.DEFAULT_AGGREGATOR_NAME,
            is_company=True,
            country_id=settings.DEFAULT_AGGREGATOR_COUNTRY,
            email=settings.DEFAULT_AGGREGATOR_EMAIL,
            msisdn=msisdn,
            agent_type="aggregator",
            active=True,
            merchant_code="01",
            tin=settings.DEFAULT_AGGREGATOR_TIN,
            sub_region_id=f"{settings.DEFAULT_AGGREGATOR_COUNTRY}-001-01",
            region_id=f"{settings.DEFAULT_AGGREGATOR_COUNTRY}-001",
            status=1,
            statusdate=datetime.datetime.now(),
        )
        agent = crud.agentview.create(db, obj_in=agentview, create_location=False)

    agent_groups = crud.agent_group.list(db, agent.id)
    agent_group = None
    for g in agent_groups:
        if g.roles == ["agent_admin"]:
            agent_group = g

    agent_location = crud.agent_location.list_for_agent(db, agent.id)
    if len(agent_location) == 0:
        agent_location = models.AgentLocation(
            agent_id=agent.id,
            presence_id="fixed",
            location_class_id="main",
            name=settings.DEFAULT_AGGREGATOR_LOCATION,
            shortcode="MAIN",
            status="active",
            address="Main Branch",
            sub_region_id=f"{settings.DEFAULT_AGGREGATOR_COUNTRY}-001-01",
            region_id=f"{settings.DEFAULT_AGGREGATOR_COUNTRY}-001",
        )
        db.add(agent_location)
        db.commit()

    user = crud.user.get_by_email(db, settings.FIRST_SUPERUSER_EMAIL)
    if not user:
        log.info("Creating initial super user")
        # create User
        msisdn = validateMSISDN(settings.FIRST_SUPERUSER_MSISDN, settings.DEFAULT_AGGREGATOR_COUNTRY)
        user_in = schemas.UserViewCreate(
            first_name=settings.FIRST_SUPERUSER_FIRST_NAME,
            last_name=settings.FIRST_SUPERUSER_LAST_NAME,
            email_1=settings.FIRST_SUPERUSER_EMAIL,
            msisdn_1=msisdn,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_company=False,
            dob="2021-01-01",
            status=2,
            active=True,
            gender="M",
            agent_group_id=agent_group.id,
            agent_location_id=agent_location.id,
        )
        crud.userview.create(db, obj_in=user_in)

    # Create initial Merchant for aggregator
    r = crud.agent.get_by_code(db, "100")
    if not r:
        agentview = schemas.AgentViewCreate(
            business_name=f"{settings.DEFAULT_AGGREGATOR_NAME} Self-Service",
            is_company=True,
            country_id=settings.DEFAULT_AGGREGATOR_COUNTRY,
            email=None,
            msisdn=None,
            agent_type="merchant",
            active=True,
            tin=None,
            merchant_code="100",
            sub_region_id=f"{settings.DEFAULT_AGGREGATOR_COUNTRY}-001-01",
            region_id=f"{settings.DEFAULT_AGGREGATOR_COUNTRY}-001",
            status=1,
            statusdate=datetime.datetime.now(),
            upline_id=agent.id,
        )
        merchant = crud.agentview.create(db, obj_in=agentview, create_location=False)

        merchant_location = models.AgentLocation(
            agent_id=merchant.id,
            presence_id="fixed",
            location_class_id="main",
            name=settings.DEFAULT_AGGREGATOR_LOCATION,
            shortcode="MAIN",
            status="active",
            address="Main Branch",
            sub_region_id=f"{settings.DEFAULT_AGGREGATOR_COUNTRY}-001-01",
            region_id=f"{settings.DEFAULT_AGGREGATOR_COUNTRY}-001",
            gps_long=settings.DEFAULT_AGGREGATOR_GPS_LONG,
            gps_lat=settings.DEFAULT_AGGREGATOR_GPS_LAT,
        )
        db.add(merchant_location)
        db.commit()

    stmt = text("CREATE SEQUENCE IF NOT EXISTS merchant_code_seq START WITH 101")
    db.execute(stmt)
    stmt = text("CREATE SEQUENCE IF NOT EXISTS agent_code_seq START WITH 100000")
    db.execute(stmt)
    db.commit()

    if settings.CONFIG_TYPE != "test":
        # Set up redis variables for internet
        if redisConn.sadd("VDS_EMAIL_SET", "seen"):
            record = crud.setting.get(db, id="EMAIL_SERVER")
            setting = crud.setting.update(db, db_obj=record, obj_in={"value": os.environ.get("MAIL_SERVER")})
            redisConn.hset("setting", setting.id, json.dumps(setting.to_dict()))

            record = crud.setting.get(db, id="EMAIL_PORT")
            setting = crud.setting.update(db, db_obj=record, obj_in={"value": os.environ.get("MAIL_PORT")})
            redisConn.hset("setting", setting.id, json.dumps(setting.to_dict()))

            record = crud.setting.get(db, id="EMAIL_SENDER")
            setting = crud.setting.update(db, db_obj=record, obj_in={"value": os.environ.get("MAIL_SENDER")})
            redisConn.hset("setting", setting.id, json.dumps(setting.to_dict()))

            record = crud.setting.get(db, id="EMAIL_USERNAME")
            setting = crud.setting.update(db, db_obj=record, obj_in={"value": os.environ.get("MAIL_USERNAME")})
            redisConn.hset("setting", setting.id, json.dumps(setting.to_dict()))

            record = crud.setting.get(db, id="EMAIL_PASSWORD")
            setting = crud.setting.update(db, db_obj=record, obj_in={"value": os.environ.get("MAIL_PASSWORD")})
            redisConn.hset("setting", setting.id, json.dumps(setting.to_dict()))

            record = crud.setting.get(db, id="EMAIL_SSL")
            if os.environ.get("MAIL_USE_SSL") == "True":
                setting = crud.setting.update(db, db_obj=record, obj_in={"value": "ssl"})
            elif os.environ.get("MAIL_USE_TLS") == "True":
                setting = crud.setting.update(db, db_obj=record, obj_in={"value": "tls"})
            else:
                setting = crud.setting.update(db, db_obj=record, obj_in={"value": "plain"})
            redisConn.hset("setting", setting.id, json.dumps(setting.to_dict()))

    log.info("initialising finished")


def drop_db(db: Session) -> None:
    db.close_all()
    base.Base.metadata.drop_all(bind=engine)
