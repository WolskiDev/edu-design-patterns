import asyncio
import aiohttp
import os
from speedtest import Speedtest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, Float, Boolean, DateTime
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database connection parameters
DB_USERNAME = os.getenv('DB_USERNAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')

# Create the database connection URL
DATABASE_URL = f"postgresql+asyncpg://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Define the base class for the models
Base = declarative_base()

# Create the asynchronous engine and session
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)


class ConnectionTestResult(Base):
    __tablename__ = "connection_tests"
    conn_test_id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now())
    is_connected = Column(Boolean, nullable=False)


class SpeedTestResult(Base):
    __tablename__ = "speed_tests"
    speed_test_id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now())
    download_speed = Column(Float, nullable=False)
    upload_speed = Column(Float, nullable=False)
    ping = Column(Float, nullable=True)


async def test_internet_connection():
    test_start_time = datetime.now()
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get('http://www.google.com', timeout=1) as response:
                return test_start_time, response.status == 200
        except:
            return test_start_time, False


async def test_internet_speed():
    test_start_time = datetime.now()
    try:
        st = Speedtest()
        st.download()
        st.upload()
        results = st.results.dict()
        download_speed_mbps = results["download"] / 1_000_000  # Convert to Mbps
        upload_speed_mbps = results["upload"] / 1_000_000      # Convert to Mbps
        ping_ms = results["ping"]
    except:
        download_speed_mbps = 0
        upload_speed_mbps = 0
        ping_ms = None
    return test_start_time, download_speed_mbps, upload_speed_mbps, ping_ms


async def log_connection_status():
    test_start_time, is_connected = await test_internet_connection()
    if not is_connected:
        async with SessionLocal() as session:
            connection_test_result = ConnectionTestResult(timestamp=test_start_time,
                                                          is_connected=is_connected)
            session.add(connection_test_result)
            await session.commit()


async def log_speed_test():
    async with SessionLocal() as session:
        test_start_time, download_speed, upload_speed, ping = await test_internet_speed()
        speed_test_result = SpeedTestResult(timestamp=test_start_time,
                                            download_speed=download_speed,
                                            upload_speed=upload_speed,
                                            ping=ping)
        session.add(speed_test_result)
        await session.commit()


async def connection_test_scheduler():
    while True:
        await log_connection_status()
        await asyncio.sleep(1)


async def speed_test_scheduler():
    while True:
        await log_speed_test()
        await asyncio.sleep(60)


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def run():
    await create_tables()
    asyncio.create_task(connection_test_scheduler())
    asyncio.create_task(speed_test_scheduler())
    while True:
        await asyncio.sleep(600)

if __name__ == "__main__":
    asyncio.run(run())

