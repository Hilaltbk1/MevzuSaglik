# backend/logger.py  (yeni dosya)
import logging, json, sys

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log = {
            "level":   record.levelname,
            "message": record.getMessage(),
            "module":  record.module,
            "time":    self.formatTime(record),
        }
        if hasattr(record, "extra"):
            log.update(record.extra)
        return json.dumps(log, ensure_ascii=False)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
logger = logging.getLogger("mevzusaglik")
logger.addHandler(handler)
logger.setLevel(logging.INFO)