from datetime import date
from sqlalchemy import select
from app.models.attendance_models import AttendanceRecord

class AnomalyDetectionService:
    def __init__(self, db, tenant_id):
        self.db = db
        self.tenant_id = tenant_id

    async def detect_proxy(self):
        today = date.today()
        stmt = select(AttendanceRecord).where(
            AttendanceRecord.tenant_id == self.tenant_id,
            AttendanceRecord.date == today,
            AttendanceRecord.verification_method == 'biometric',
            AttendanceRecord.status == 'present'
        ).order_by(AttendanceRecord.in_time)
        records = (await self.db.execute(stmt)).scalars().all()
        anomalies = []
        for i in range(len(records)-1):
            r1 = records[i]
            r2 = records[i+1]
            if r1.student_id != r2.student_id and r1.device_id == r2.device_id:
                if r1.in_time and r2.in_time:
                    diff = abs((r1.in_time.hour*60 + r1.in_time.minute) - (r2.in_time.hour*60 + r2.in_time.minute))
                    if diff <= 2:
                        anomalies.append({"student1": str(r1.student_id), "student2": str(r2.student_id)})
        return anomalies