from uuid import UUID
from datetime import date, datetime, timedelta
from typing import Optional, List
import numpy as np
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.models.finance_models import (
    FeeComponent, FeeStructure, Transaction, Invoice, StudentFeeAccount, PaymentDefaultPrediction,
    AnomalyLog, RevenueForecast, AIModelMetadata, AutoCategoryRule
)
from app.models.student import Student
from app.modules.attendance.event_publisher import publish_event
import re
from prophet import Prophet
import os
import pickle

class AIFinanceService:
    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    # ---------------------------------------------------------------
    # Payment Default Prediction
    # ---------------------------------------------------------------
    async def predict_payment_default(self, student_id: UUID) -> dict:
        """
        Rule‑based: uses overdue days, total due amount, and past payment timeliness.
        If a trained model exists, it overrides with ML score.
        """
        # Fetch student fee account
        account = await self.db.get(StudentFeeAccount, student_id)
        if not account:
            return {"student_id": student_id, "risk_score": 0, "probability": 0, "factors": {}}

        # Rule‑based features
        overdue_days = 0
        last_invoice = (await self.db.execute(
            select(Invoice).where(Invoice.student_id == student_id, Invoice.tenant_id == self.tenant_id)
            .order_by(Invoice.due_date.desc()).limit(1)
        )).scalar_one_or_none()
        if last_invoice and last_invoice.due_date < date.today():
            overdue_days = (date.today() - last_invoice.due_date).days

        due_amount = float(account.due_amount or 0)
        total_fee = float(account.total_fee or 1)

        # Past payment score: average days between due date and paid date for past invoices
        past_payment_timeliness = 0
        past_invoices = (await self.db.execute(
            select(Invoice).where(Invoice.student_id == student_id, Invoice.tenant_id == self.tenant_id, Invoice.status == 'paid')
        )).scalars().all()
        if past_invoices:
            delays = [(inv.paid_at.date() - inv.due_date).days for inv in past_invoices if inv.paid_at]
            past_payment_timeliness = np.mean(delays) if delays else 0

        # Simple logistic‑style score (0‑100)
        risk_score = min(100, (overdue_days * 2) + (due_amount / total_fee * 50) + max(0, past_payment_timeliness * 2))
        probability = risk_score / 100.0

        # Check for trained model
        model_meta = await self._get_latest_model('payment_default')
        if model_meta and model_meta.model_path and os.path.exists(model_meta.model_path):
            with open(model_meta.model_path, 'rb') as f:
                model = pickle.load(f)
            features = np.array([[overdue_days, due_amount/total_fee, past_payment_timeliness]])
            if hasattr(model, 'predict_proba'):
                proba = model.predict_proba(features)[0][1]
                risk_score = proba * 100
                probability = proba

        # Save prediction
        prediction = PaymentDefaultPrediction(
            tenant_id=self.tenant_id,
            student_id=student_id,
            risk_score=risk_score,
            probability=probability,
            factors={
                'overdue_days': overdue_days,
                'due_amount_ratio': due_amount / total_fee,
                'past_timeliness': past_payment_timeliness
            }
        )
        self.db.add(prediction)
        await self.db.commit()

        return {
            "student_id": student_id,
            "risk_score": round(risk_score, 2),
            "probability": round(probability, 2),
            "factors": {
                "overdue_days": overdue_days,
                "due_amount_ratio": round(due_amount / total_fee, 2),
                "past_timeliness": round(past_payment_timeliness, 2)
            }
        }

    async def train_payment_default_model(self):
        """Train a simple Logistic Regression model on all tenants' data (or per tenant)."""
        from sklearn.linear_model import LogisticRegression
        # Gather features from all students of this tenant
        accounts = (await self.db.execute(
            select(StudentFeeAccount).where(StudentFeeAccount.tenant_id == self.tenant_id)
        )).scalars().all()
        X, y = [], []
        for acc in accounts:
            # compute features similar to predict method
            overdue_days = 0
            last_inv = (await self.db.execute(
                select(Invoice).where(Invoice.student_id == acc.student_id)
                .order_by(Invoice.due_date.desc()).limit(1)
            )).scalar_one_or_none()
            if last_inv and last_inv.due_date < date.today():
                overdue_days = (date.today() - last_inv.due_date).days
            due_amount = float(acc.due_amount or 0)
            total_fee = float(acc.total_fee or 1)
            past_delays = []
            invoices = (await self.db.execute(
                select(Invoice).where(Invoice.student_id == acc.student_id, Invoice.status == 'paid')
            )).scalars().all()
            for inv in invoices:
                if inv.paid_at:
                    past_delays.append((inv.paid_at.date() - inv.due_date).days)
            timeliness = np.mean(past_delays) if past_delays else 0
            # Label: default = due_amount > 0 and overdue_days > 30 (or was ever defaulted)
            defaulted = 1 if (due_amount > 0 and overdue_days > 30) else 0
            X.append([overdue_days, due_amount/total_fee, timeliness])
            y.append(defaulted)
        if len(X) < 10:
            return   # not enough data
        model = LogisticRegression()
        model.fit(X, y)
        os.makedirs(f"/tmp/ai_models/{self.tenant_id}", exist_ok=True)
        path = f"/tmp/ai_models/{self.tenant_id}/payment_default.pkl"
        with open(path, 'wb') as f:
            pickle.dump(model, f)
        # Update metadata
        meta = AIModelMetadata(
            tenant_id=self.tenant_id,
            model_type='payment_default',
            model_path=path,
            accuracy=model.score(X, y),
            trained_at=datetime.utcnow()
        )
        self.db.add(meta)
        await self.db.commit()

    # ---------------------------------------------------------------
    # Smart Reminder Timing
    # ---------------------------------------------------------------
    async def suggest_reminder_timing(self, invoice_ids: List[UUID]) -> List[dict]:
        """
        Heuristic: based on student's past payment times, suggest an hour when they are most likely to pay.
        """
        results = []
        for inv_id in invoice_ids:
            invoice = await self.db.get(Invoice, inv_id)
            if not invoice:
                continue
            # Get past payment hours for this student
            past_payments = (await self.db.execute(
                select(Transaction.paid_at).where(
                    Transaction.student_id == invoice.student_id,
                    Transaction.tenant_id == self.tenant_id
                )
            )).scalars().all()
            if past_payments:
                hours = [t.hour for t in past_payments if t]
                optimal_hour = max(set(hours), key=hours.count) if hours else 9
            else:
                optimal_hour = 9
            results.append({
                "invoice_id": inv_id,
                "optimal_time": f"{optimal_hour:02d}:00",
                "expected_response_rate": 0.75 if past_payments else 0.5
            })
        return results

    # ---------------------------------------------------------------
    # Anomaly Detection
    # ---------------------------------------------------------------
    async def detect_anomalies(self) -> List[dict]:
        """
        Rule‑based anomaly detection:
        - Duplicate receipts for same transaction reference
        - Amount outlier (e.g., payment > 3x average monthly fee)
        - Same student paying multiple times on same day with different modes? (unusual)
        """
        anomalies = []
        # Duplicate references
        dupes = await self.db.execute(
            select(Transaction.transaction_reference, func.count(Transaction.id))
            .where(Transaction.tenant_id == self.tenant_id)
            .group_by(Transaction.transaction_reference)
            .having(func.count(Transaction.id) > 1)
        )
        for ref, cnt in dupes:
            anomalies.append({
                "type": "duplicate_reference",
                "reference": ref,
                "count": cnt,
                "severity": "high"
            })
            # Log
            self.db.add(AnomalyLog(
                tenant_id=self.tenant_id,
                description=f"Duplicate transaction reference: {ref} ({cnt} occurrences)",
                severity='high'
            ))

        # Amount outliers (very large payments)
        avg_total = (await self.db.execute(
            select(func.avg(StudentFeeAccount.total_fee)).where(StudentFeeAccount.tenant_id == self.tenant_id)
        )).scalar()
        if avg_total:
            large_txs = await self.db.execute(
                select(Transaction).where(
                    Transaction.tenant_id == self.tenant_id,
                    Transaction.amount > avg_total * 3
                )
            )
            for tx in large_txs.scalars():
                anomalies.append({
                    "type": "large_amount",
                    "transaction_id": str(tx.id),
                    "amount": float(tx.amount),
                    "severity": "medium"
                })
                self.db.add(AnomalyLog(
                    tenant_id=self.tenant_id,
                    transaction_id=tx.id,
                    description=f"Large payment {tx.amount} exceeds 3x average fee",
                    severity='medium'
                ))

        await self.db.commit()
        return anomalies

    # ---------------------------------------------------------------
    # Revenue Forecasting
    # ---------------------------------------------------------------
    async def forecast_revenue(self, months_ahead: int = 6) -> List[dict]:
        """
        Use Prophet (or average trend) to forecast monthly fee collection.
        """
        # Aggregate monthly revenue from past transactions
        stmt = select(
            func.date_trunc('month', Transaction.paid_at).label('month'),
            func.sum(Transaction.amount)
        ).where(
            Transaction.tenant_id == self.tenant_id
        ).group_by('month').order_by('month')
        rows = (await self.db.execute(stmt)).all()
        if len(rows) < 3:
            return []   # not enough data

        df = pd.DataFrame(rows, columns=['ds', 'y'])
        df['ds'] = pd.to_datetime(df['ds'])
        df['y'] = df['y'].astype(float)

        # Check for trained Prophet model
        model_path = f"/tmp/ai_models/{self.tenant_id}/revenue_forecast.pkl"
        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
        else:
            model = Prophet()
            model.fit(df[['ds', 'y']])

        future = model.make_future_dataframe(periods=months_ahead * 30, freq='D')
        forecast = model.predict(future)
        # Aggregate to monthly
        forecast['month'] = forecast['ds'].dt.to_period('M')
        monthly = forecast.groupby('month').agg({'yhat': 'sum', 'yhat_lower': 'sum', 'yhat_upper': 'sum'}).reset_index()
        # Save forecast to DB
        self.db.add(RevenueForecast(
            tenant_id=self.tenant_id,
            forecast_date=monthly.iloc[-1]['month'].to_timestamp(),
            predicted_revenue=monthly.iloc[-1]['yhat'],
            lower_bound=monthly.iloc[-1]['yhat_lower'],
            upper_bound=monthly.iloc[-1]['yhat_upper']
        ))
        await self.db.commit()

        results = []
        for _, row in monthly.tail(months_ahead).iterrows():
            results.append({
                "date": row['month'].to_timestamp().date(),
                "predicted_revenue": round(float(row['yhat']), 2),
                "lower_bound": round(float(row['yhat_lower']), 2),
                "upper_bound": round(float(row['yhat_upper']), 2)
            })
        return results

    async def train_revenue_forecast_model(self):
        """Save trained Prophet model."""
        stmt = select(
            func.date_trunc('month', Transaction.paid_at).label('month'),
            func.sum(Transaction.amount)
        ).where(Transaction.tenant_id == self.tenant_id).group_by('month').order_by('month')
        rows = (await self.db.execute(stmt)).all()
        if len(rows) < 3:
            return
        df = pd.DataFrame(rows, columns=['ds', 'y'])
        df['ds'] = pd.to_datetime(df['ds'])
        df['y'] = df['y'].astype(float)
        model = Prophet()
        model.fit(df[['ds', 'y']])
        os.makedirs(f"/tmp/ai_models/{self.tenant_id}", exist_ok=True)
        path = f"/tmp/ai_models/{self.tenant_id}/revenue_forecast.pkl"
        with open(path, 'wb') as f:
            pickle.dump(model, f)
        meta = AIModelMetadata(
            tenant_id=self.tenant_id,
            model_type='revenue_forecast',
            model_path=path,
            trained_at=datetime.utcnow()
        )
        self.db.add(meta)
        await self.db.commit()

    # ---------------------------------------------------------------
    # Auto‑Categorization
    # ---------------------------------------------------------------
    async def auto_categorize_transaction(self, description: str) -> str:
        """Match against tenant's rules or a simple built‑in list."""
        rules = (await self.db.execute(
            select(AutoCategoryRule).where(AutoCategoryRule.tenant_id == self.tenant_id)
        )).scalars().all()
        for rule in rules:
            if re.search(rule.pattern, description, re.IGNORECASE):
                return rule.category
        # Fallback: simple keyword mapping
        desc_lower = description.lower()
        if any(kw in desc_lower for kw in ['tuition', 'fees', 'school']):
            return 'Tuition Fee'
        elif any(kw in desc_lower for kw in ['transport', 'bus']):
            return 'Transport Fee'
        elif any(kw in desc_lower for kw in ['hostel', 'mess']):
            return 'Hostel Fee'
        elif any(kw in desc_lower for kw in ['exam', 'test']):
            return 'Examination Fee'
        elif any(kw in desc_lower for kw in ['library', 'book']):
            return 'Library Fee'
        else:
            return 'Other Income'

    async def categorize_all_transactions(self):
        """Apply categorization to all uncategorized transactions for the tenant."""
        txs = (await self.db.execute(
            select(Transaction).where(Transaction.tenant_id == self.tenant_id, Transaction.category == None)
        )).scalars().all()
        for tx in txs:
            desc = tx.notes or tx.transaction_reference or "Fee Payment"
            tx.category = await self.auto_categorize_transaction(desc)
        await self.db.commit()

    # ---------------------------------------------------------------
    # Fee Optimization Suggestions
    # ---------------------------------------------------------------
    async def suggest_fee_optimization(self) -> List[dict]:
        """
        Compare fee structures with enrollment and collection rates to suggest adjustments.
        """
        structures = (await self.db.execute(
            select(FeeStructure).where(FeeStructure.tenant_id == self.tenant_id, FeeStructure.is_active == True)
        )).scalars().all()
        suggestions = []
        for struct in structures:
            # Get number of assigned students
            count = (await self.db.execute(
                select(func.count(StudentFeeAccount.id)).where(
                    StudentFeeAccount.fee_structure_id == struct.id,
                    StudentFeeAccount.tenant_id == self.tenant_id
                )
            )).scalar()
            # For each component, compare to a benchmark (e.g., average of similar classes) – simplified.
            # Here we'll just check if any component fee is above twice the median across all structures
            # Not implemented fully; return placeholder suggestion based on simple heuristic.
            components = (await self.db.execute(
                select(FeeComponent).where(FeeComponent.fee_structure_id == struct.id)
            )).scalars().all()
            for comp in components:
                median_all = (await self.db.execute(
                    select(func.percentile_cont(0.5).within_group(FeeComponent.amount))
                    .where(FeeComponent.name == comp.name, FeeComponent.tenant_id == self.tenant_id)
                )).scalar()
                if median_all and comp.amount > median_all * 1.5:
                    suggestions.append({
                        "class_id": struct.class_id,
                        "component": comp.name,
                        "current_fee": float(comp.amount),
                        "suggested_fee": round(float(median_all) * 1.5, 2),
                        "confidence": 0.7
                    })
        return suggestions

    # Helper
    async def _get_latest_model(self, model_type: str) -> Optional[AIModelMetadata]:
        stmt = select(AIModelMetadata).where(
            AIModelMetadata.tenant_id == self.tenant_id,
            AIModelMetadata.model_type == model_type
        ).order_by(AIModelMetadata.trained_at.desc()).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()