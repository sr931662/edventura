# This would be a separate process, but we can add a route to manually test.
# For completeness, we'll define a class that could be used by a Celery task.
class ParentNotificationService:
    def __init__(self, db, tenant_id):
        pass

    async def send_absent_alert(self, student_id, date, status):
        # fetch parent contact from student guardians
        # push notification, SMS, email via integration gateways
        pass

    async def send_transport_update(self, student_id, event_type):
        pass