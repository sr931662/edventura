class FaceRecognitionService:
    async def verify_face(self, image_bytes, student_id):
        # In real: load embedding from DB, compare with image using face_recognition library, check liveness
        return {"match": True, "confidence": 0.95, "liveness": True}

    async def register_face(self, user_id, image_bytes):
        # In real: extract embedding, store in biometric_templates
        template = "encrypted_embedding_placeholder"
        # await self.store_template(user_id, template)
        return template