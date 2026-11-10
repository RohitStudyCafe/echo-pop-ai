import time
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("alexa_ai.latency")

class LatencyTracker:
    def __init__(self, alexa_timestamp: Optional[str] = None):
        self.alexa_timestamp = alexa_timestamp
        self.t_start = time.perf_counter()
        self.t_ai_start: Optional[float] = None
        self.t_ai_end: Optional[float] = None
        self.t_end: Optional[float] = None
        self.provider: Optional[str] = None
        self.model: Optional[str] = None
        self.fallback_triggered: bool = False

    def mark_ai_start(self, provider: str, model: str):
        self.provider = provider
        self.model = model
        self.t_ai_start = time.perf_counter()

    def mark_ai_end(self):
        self.t_ai_end = time.perf_counter()

    def mark_fallback(self):
        self.fallback_triggered = True

    def finish(self) -> Dict[str, Any]:
        self.t_end = time.perf_counter()
        total_ms = (self.t_end - self.t_start) * 1000.0
        ai_ms = ((self.t_ai_end - self.t_ai_start) * 1000.0) if (self.t_ai_start and self.t_ai_end) else 0.0
        overhead_ms = max(0.0, total_ms - ai_ms)
        
        metrics = {
            "total_latency_ms": round(total_ms, 2),
            "ai_latency_ms": round(ai_ms, 2),
            "overhead_latency_ms": round(overhead_ms, 2),
            "provider": self.provider,
            "model": self.model,
            "fallback_triggered": self.fallback_triggered,
            "alexa_timestamp": self.alexa_timestamp
        }
        
        logger.info(
            f"[LATENCY] Total: {metrics['total_latency_ms']}ms | "
            f"AI ({self.provider}/{self.model}): {metrics['ai_latency_ms']}ms | "
            f"Overhead: {metrics['overhead_latency_ms']}ms | "
            f"Fallback: {self.fallback_triggered}"
        )
        return metrics

