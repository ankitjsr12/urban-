import asyncio
from app.db.session import AsyncSessionLocal, engine, Base
from app.models.models import User,Route,Bus,BusStatus,Role
from app.core.security import hash_password
async def main():
    async with engine.begin() as conn: await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        admin=User(name='System Admin',email='admin@urbansense.local',password_hash=hash_password('ChangeMe123!'),role=Role.ADMIN); db.add(admin)
        routes=[Route(name=f'Route {i}',code=f'R{i:02d}',origin=f'Origin {i}',destination=f'Destination {i}') for i in range(1,6)]; db.add_all(routes); await db.flush()
        db.add_all([Bus(bus_number=f'BUS-{i:03d}',registration_number=f'WB{i:02d}AB{i:04d}',route_id=routes[(i-1)%5].id,status=BusStatus.ACTIVE if i<8 else BusStatus.INACTIVE) for i in range(1,11)]); await db.commit()
    print('Seeded admin, 5 routes, and 10 buses. Login: admin@urbansense.local / ChangeMe123!')
if __name__=='__main__': asyncio.run(main())
