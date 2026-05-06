class SentimentService:
    async def analyze_engagement(self, payload: dict) -> dict:
        mouse = payload.get("mouse_movements", 0)
        keys = payload.get("keystrokes", 0)
        # Simple heuristic: each mouse move = 0.1 point, each keystroke = 0.5 point
        score = min(100, mouse * 0.1 + keys * 0.5)
        disengaged = score < 30
        # If camera frame available, would use facial expression analysis
        return {"score": round(score, 2), "disengaged": disengaged}