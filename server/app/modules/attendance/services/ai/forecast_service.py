import pandas as pd
from prophet import Prophet
from datetime import date, timedelta
from uuid import UUID
from sqlalchemy import select
from app.models.attendance_models import AttendanceComputation
import os

class ForecastService:
    def __init__(self, db, tenant_id):
        self.db = db
        self.tenant_id = tenant_id

    async def train_class_model(self, class_id: UUID):
        # Fetch historical data for the tenant
        stmt = select(AttendanceComputation.date, AttendanceComputation.attendance_percent).where(
            AttendanceComputation.tenant_id == self.tenant_id,
        )
        # For simplicity, we'll predict for the whole tenant. In real app, add a virtual table.
        # Placeholder: use dummy data
        df = pd.DataFrame({
            'ds': [date.today() - timedelta(days=i) for i in range(90, 0, -1)],
            'y': [85.0 + (i % 10) for i in range(90)]
        })
        m = Prophet()
        m.fit(df)
        os.makedirs(f"/tmp/forecast_models/{self.tenant_id}", exist_ok=True)
        from prophet.serialize import model_to_json
        import json
        with open(f"/tmp/forecast_models/{self.tenant_id}/class_{class_id}.json", 'w') as fout:
            json.dump(model_to_json(m), fout)
        return {"status": "trained"}

    async def predict(self, class_id: UUID, days: int = 7):
        model_path = f"/tmp/forecast_models/{self.tenant_id}/class_{class_id}.json"
        if not os.path.exists(model_path):
            return []
        from prophet.serialize import model_from_json
        import json
        with open(model_path, 'r') as fin:
            m = model_from_json(json.load(fin))
        future = m.make_future_dataframe(periods=days)
        forecast = m.predict(future)
        predictions = forecast[['ds', 'yhat']].tail(days)
        import pandas as pd
        return [{"date": pd.Timestamp(row[1]).date(), "predicted_percent": round(float(row[2]), 2)} for row in predictions.itertuples()]