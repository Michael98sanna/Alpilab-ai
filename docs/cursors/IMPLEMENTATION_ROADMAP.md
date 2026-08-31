# ALPILAB AI — FULL IMPLEMENTATION ROADMAP FOR CURSOR

## CONTESTO
- **Progetto:** Assistente tecnico AI per riparazioni smartphone
- **Branch:** main (V0.4)
- **Stack:** FastAPI + React/TypeScript + Python PC Agent + SQLite
- **Status:** Funzionante, ma architettura carente in persistenza, diagnostica, sicurezza
- **Goal:** Implementare 8 priority in 4 sessioni (1-2 giorni dev)

---

## 🎯 PRIORITY 1: PERSISTENT SESSION STORAGE

### Cosa fare:
- [ ] Creare `app/models/database.py` con SQLAlchemy + SQLite
- [ ] Creare `app/models/orm_models.py` per schemi ORM
- [ ] Creare `app/session/persistent_store.py` (PersistentSessionStore)
- [ ] Update `app/session/session_manager.py` per usare persistent store
- [ ] Migrazioni alembic (opzionale per V0.4)
- [ ] Test: session persiste dopo riavvio server

### Requisiti tecnici:

#### app/models/database.py
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Database configuration
DATABASE_URL = "sqlite:///./data/alpilab.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### app/models/orm_models.py
```python
from sqlalchemy import Column, String, DateTime, Text, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class SessionModel(Base):
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=True)
    device_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    state_json = Column(JSON)  # Intero RepairSessionContext serializzato
    deleted_at = Column(DateTime, nullable=True)

class SessionEventModel(Base):
    __tablename__ = "session_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, nullable=False)
    event_type = Column(String)  # CHAT_MESSAGE, DIAGNOSTIC_UPDATE, etc
    payload_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
```

#### app/session/persistent_store.py
```python
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.orm_models import SessionModel, SessionEventModel
from app.schemas.repair import RepairSessionContext
import json

class PersistentSessionStore:
    """Thread-safe persistent session storage with SQLite backend."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def save_session(self, session_id: str, session_data: RepairSessionContext):
        """Salva o aggiorna una sessione."""
        existing = self.db.query(SessionModel).filter(
            SessionModel.id == session_id
        ).first()
        
        state_dict = session_data.dict(exclude_none=True)
        
        if existing:
            existing.state_json = state_dict
            existing.updated_at = datetime.utcnow()
        else:
            model = SessionModel(
                id=session_id,
                user_id=getattr(session_data, 'user_id', None),
                device_id=getattr(session_data, 'device_id', None),
                state_json=state_dict
            )
            self.db.add(model)
        
        self.db.commit()
    
    def load_session(self, session_id: str) -> Optional[RepairSessionContext]:
        """Carica una sessione da DB."""
        model = self.db.query(SessionModel).filter(
            SessionModel.id == session_id,
            SessionModel.deleted_at.is_(None)
        ).first()
        
        if not model:
            return None
        
        return RepairSessionContext(**model.state_json)
    
    def delete_session(self, session_id: str):
        """Soft delete."""
        model = self.db.query(SessionModel).filter(
            SessionModel.id == session_id
        ).first()
        if model:
            model.deleted_at = datetime.utcnow()
            self.db.commit()
    
    def list_active_sessions(self) -> List[str]:
        """Lista session attive."""
        sessions = self.db.query(SessionModel.id).filter(
            SessionModel.deleted_at.is_(None)
        ).all()
        return [s[0] for s in sessions]
    
    def add_event(self, session_id: str, event_type: str, payload: dict):
        """Aggiungi evento a session history."""
        event = SessionEventModel(
            session_id=session_id,
            event_type=event_type,
            payload_json=payload
        )
        self.db.add(event)
        self.db.commit()
    
    def get_session_history(self, session_id: str, limit: int = 100) -> List[dict]:
        """Carica storico eventi."""
        events = self.db.query(SessionEventModel).filter(
            SessionEventModel.session_id == session_id
        ).order_by(SessionEventModel.created_at.desc()).limit(limit).all()
        
        return [
            {
                "event_type": e.event_type,
                "payload": e.payload_json,
                "created_at": e.created_at.isoformat()
            }
            for e in events
        ]
    
    def cleanup_old_sessions(self, days: int = 90):
        """Elimina sessioni deletedate da N giorni."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        self.db.query(SessionModel).filter(
            SessionModel.deleted_at < cutoff
        ).delete()
        self.db.commit()
```

#### app/session/session_manager.py (AGGIORNAMENTO)
```python
# Nel __init__ o in una factory function:
from app.session.persistent_store import PersistentSessionStore

class RealtimeSessionManager:
    def __init__(self, db_session):
        self.persistent_store = PersistentSessionStore(db_session)
        self._sessions = {}  # In-memory cache (per performance)
    
    async def resume_session(self, session_id: str) -> Optional[RepairSessionContext]:
        """Carica sessione da DB, pone in memoria."""
        session = self.persistent_store.load_session(session_id)
        if session:
            self._sessions[session_id] = session
        return session
    
    async def save_session(self, session_id: str):
        """Persiste sessione in DB."""
        if session_id in self._sessions:
            self.persistent_store.save_session(
                session_id, 
                self._sessions[session_id]
            )
    
    # Ogni volta che una sessione muta (chat, diagnostica, etc):
    # await session_manager.save_session(session_id)
```

### File da creare:
- `app/models/database.py`
- `app/models/orm_models.py`
- `app/session/persistent_store.py`

### File da aggiornare:
- `app/session/session_manager.py` (integra persistent store)
- `app/main.py` (chiama `init_db()` at startup)
- `requirements.txt` (aggiungi `sqlalchemy>=2.0`)

### Tests da scrivere:
```python
# tests/test_persistent_session.py
import pytest
from app.session.persistent_store import PersistentSessionStore
from app.models.database import SessionLocal
from app.schemas.repair import RepairSessionContext

def test_save_and_load_session():
    db = SessionLocal()
    store = PersistentSessionStore(db)
    
    session_data = RepairSessionContext(
        session_id="test-1",
        device=Device(model="iPhone 13", brand="Apple"),
        context=RepairSessionContext(...)
    )
    
    store.save_session("test-1", session_data)
    loaded = store.load_session("test-1")
    
    assert loaded.session_id == "test-1"
    assert loaded.device.model == "iPhone 13"
    db.close()

def test_session_survives_restart():
    db = SessionLocal()
    store = PersistentSessionStore(db)
    
    # Salva
    session_data = RepairSessionContext(...)
    store.save_session("test-2", session_data)
    db.close()
    
    # Simula restart: nuova connessione DB
    db2 = SessionLocal()
    store2 = PersistentSessionStore(db2)
    loaded = store2.load_session("test-2")
    
    assert loaded is not None
    db2.close()

def test_session_events():
    db = SessionLocal()
    store = PersistentSessionStore(db)
    
    store.add_event("test-1", "CHAT_MESSAGE", {"user": "tech", "text": "ciao"})
    history = store.get_session_history("test-1")
    
    assert len(history) == 1
    assert history[0]["event_type"] == "CHAT_MESSAGE"
```

### No-touch:
- Frontend (nessun cambio)
- PC Agent
- AI Router
- API contracts (deve rimanere backward compatible)

---

## 🎯 PRIORITY 2: SEMANTIC COMMAND PARSER

### Cosa fare:
- [ ] Creare `app/commands/intent_parser_v2.py` con semantic matching
- [ ] Creare `app/commands/intent_models.py` (Pydantic schemas)
- [ ] Registrazione dinamica tool da ToolRegistry
- [ ] Fallback a disambiguation se confidence < 70%
- [ ] Update `app/conversation/command_engine.py` per usare nuovo parser
- [ ] Tests: riconosce 10+ comandi

### Requisiti tecnici:

#### app/commands/intent_models.py
```python
from pydantic import BaseModel
from enum import Enum
from typing import List, Optional

class IntentType(str, Enum):
    OPEN_APPLICATION = "open_application"
    CLOSE_APPLICATION = "close_application"
    RUN_DIAGNOSTIC = "run_diagnostic"
    CLARIFY = "clarify"
    UNKNOWN = "unknown"

class IntentResult(BaseModel):
    intent: IntentType
    tool_id: Optional[str] = None  # es. "windows.3utools.open"
    confidence: float  # 0.0 - 1.0
    options: Optional[List[dict]] = None  # Per CLARIFY: {tool_id, label, confidence}
    reasoning: str  # Spiegazione parsing
```

#### app/commands/intent_parser_v2.py
```python
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict
from app.commands.intent_models import IntentResult, IntentType
from app.tools.registry import ToolRegistry

class SemanticIntentParser:
    """
    Parser rule-based + semantic matching per comandi naturali.
    Usa sentence-transformers per embedding, cosine similarity per matching.
    """
    
    CONFIDENCE_THRESHOLD = 0.70
    CLARIFY_THRESHOLD = 0.55
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.embedder = SentenceTransformer(model_name)
        self.tool_registry = ToolRegistry()
        self.command_templates = self._build_templates()
    
    def _build_templates(self) -> Dict[str, List[str]]:
        """Template per comandi comuni."""
        return {
            "open_application": [
                "aprimi {app}",
                "apri {app}",
                "avvia {app}",
                "lancia {app}",
                "apri il {app}",
                "open {app}",
            ],
            "close_application": [
                "chiudi {app}",
                "chiudi il {app}",
                "close {app}",
            ],
            "run_diagnostic": [
                "fai un test",
                "diagnostica",
                "controlla",
                "run diagnostic",
            ]
        }
    
    def parse(self, user_text: str) -> IntentResult:
        """
        Parse comando naturale → IntentResult.
        
        Logic:
        1. Lowercasing + pulizia
        2. Per ogni tool registrato: calcola embedding similarity
        3. Se top_1 > THRESHOLD → return IntentResult(tool_id, confidence)
        4. Else se top_1 > CLARIFY_THRESHOLD → return IntentResult(CLARIFY, options)
        5. Else → return IntentResult(UNKNOWN)
        """
        user_text_clean = user_text.lower().strip()
        
        # Embedding della richiesta utente
        user_embedding = self.embedder.encode(user_text_clean, convert_to_tensor=True)
        
        # Per ogni tool disponibile: calcola similarity
        scores = {}
        for tool in self.tool_registry.get_all_tools():
            # tool.description es. "Apri 3uTools diagnostico smartphone"
            tool_embedding = self.embedder.encode(tool.description, convert_to_tensor=True)
            similarity = self._cosine_similarity(user_embedding, tool_embedding)
            scores[tool.id] = similarity
        
        # Sort by confidence
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        if not sorted_scores:
            return IntentResult(
                intent=IntentType.UNKNOWN,
                confidence=0.0,
                reasoning="Nessun tool registrato"
            )
        
        top_tool_id, top_confidence = sorted_scores[0]
        
        if top_confidence >= self.CONFIDENCE_THRESHOLD:
            return IntentResult(
                intent=IntentType.OPEN_APPLICATION,
                tool_id=top_tool_id,
                confidence=float(top_confidence),
                reasoning=f"Matched '{top_tool_id}' con confidence {top_confidence:.2f}"
            )
        
        elif top_confidence >= self.CLARIFY_THRESHOLD:
            # Ritorna top 3 per disambiguazione
            options = [
                {
                    "tool_id": tool_id,
                    "label": self.tool_registry.get_tool(tool_id).label,
                    "confidence": float(conf)
                }
                for tool_id, conf in sorted_scores[:3]
            ]
            return IntentResult(
                intent=IntentType.CLARIFY,
                confidence=top_confidence,
                options=options,
                reasoning=f"Ambiguo tra {len(options)} opzioni"
            )
        
        else:
            return IntentResult(
                intent=IntentType.UNKNOWN,
                confidence=float(top_confidence),
                reasoning=f"Confidence troppo bassa: {top_confidence:.2f} < {self.CONFIDENCE_THRESHOLD}"
            )
    
    @staticmethod
    def _cosine_similarity(a, b):
        """Cosine similarity tra due embedding."""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
```

#### app/conversation/command_engine.py (AGGIORNAMENTO)
```python
from app.commands.intent_parser_v2 import SemanticIntentParser
from app.commands.intent_models import IntentType

class ConversationCommandEngine:
    def __init__(self):
        self.intent_parser = SemanticIntentParser()
    
    async def process_user_input(self, user_text: str, session: RepairSessionContext):
        """Process text/voice input → action or conversation."""
        
        intent_result = self.intent_parser.parse(user_text)
        
        if intent_result.intent == IntentType.UNKNOWN:
            # È conversazione, non comando
            return await self.conversation_service.generate_response(user_text, session)
        
        elif intent_result.intent == IntentType.CLARIFY:
            # Chiedi disambiguazione
            options_text = "\n".join(
                f"- {opt['label']} ({opt['confidence']:.0%})"
                for opt in intent_result.options
            )
            return {
                "type": "clarification",
                "message": f"Non sono sicuro. Quale intendi?\n{options_text}",
                "options": intent_result.options
            }
        
        elif intent_result.intent == IntentType.OPEN_APPLICATION:
            # Esegui tool
            return await self.tool_executor.execute_tool(
                intent_result.tool_id,
                session
            )
```

### File da creare:
- `app/commands/intent_models.py`
- `app/commands/intent_parser_v2.py`

### File da aggiornare:
- `app/conversation/command_engine.py` (integra new parser)
- `requirements.txt` (aggiungi `sentence-transformers>=2.2`)

### Tests:
```python
# tests/test_semantic_parser.py
import pytest
from app.commands.intent_parser_v2 import SemanticIntentParser
from app.commands.intent_models import IntentType

@pytest.fixture
def parser():
    return SemanticIntentParser()

def test_parse_open_3utools(parser):
    result = parser.parse("Aprimi 3uTools")
    assert result.intent == IntentType.OPEN_APPLICATION
    assert "3utools" in result.tool_id.lower()
    assert result.confidence > 0.8

def test_parse_open_borneo(parser):
    result = parser.parse("Apri Borneo")
    assert result.intent == IntentType.OPEN_APPLICATION or IntentType.CLARIFY
    if result.intent == IntentType.OPEN_APPLICATION:
        assert "borneo" in result.tool_id.lower()

def test_parse_ambiguous(parser):
    result = parser.parse("Apri il programma")
    assert result.intent == IntentType.CLARIFY
    assert len(result.options) > 0

def test_parse_unknown(parser):
    result = parser.parse("Raccontami una barzelletta")
    assert result.intent == IntentType.UNKNOWN
```

---

## 🎯 PRIORITY 3: AUDIT LOGGING + RBAC

### Cosa fare:
- [ ] Creare `app/security/audit_log.py`
- [ ] Creare `app/security/rbac.py` (Role-based access control)
- [ ] Creare `app/security/models.py` (ORM user + roles)
- [ ] Middleware FastAPI per logging automatico
- [ ] Tests: ogni azione è loggata

### Requisiti tecnici:

#### app/security/models.py
```python
from enum import Enum
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum
from app.models.database import Base
from datetime import datetime

class UserRole(str, Enum):
    TECHNICIAN = "technician"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"

class UserModel(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    role = Column(SQLEnum(UserRole), default=UserRole.TECHNICIAN)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(bool, default=True)

class AuditLogModel(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=True)
    session_id = Column(String, nullable=True)
    action_type = Column(String)  # TOOL_EXECUTE, CHAT_MESSAGE, SESSION_START, etc
    tool_id = Column(String, nullable=True)
    status = Column(String)  # SUCCESS, FAILURE, PENDING
    risk_level = Column(String)  # LOW, MEDIUM, HIGH
    metadata = Column(JSON)  # Input/output aggiuntivo
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

#### app/security/rbac.py
```python
from enum import Enum
from app.security.models import UserRole, UserModel

class ActionRiskLevel(str, Enum):
    LOW = "low"          # Lettura, chat
    MEDIUM = "medium"    # Aprire app
    HIGH = "high"        # Reset device, delete data

class ActionPermission(BaseModel):
    allowed: bool
    requires_confirmation: bool = False
    reason: Optional[str] = None

class RBACManager:
    """Role-based access control."""
    
    PERMISSIONS = {
        UserRole.TECHNICIAN: {
            ActionRiskLevel.LOW: ActionPermission(allowed=True),
            ActionRiskLevel.MEDIUM: ActionPermission(allowed=True),
            ActionRiskLevel.HIGH: ActionPermission(allowed=False, reason="Insufficiente permesso"),
        },
        UserRole.SUPERVISOR: {
            ActionRiskLevel.LOW: ActionPermission(allowed=True),
            ActionRiskLevel.MEDIUM: ActionPermission(allowed=True),
            ActionRiskLevel.HIGH: ActionPermission(allowed=True, requires_confirmation=True),
        },
        UserRole.ADMIN: {
            ActionRiskLevel.LOW: ActionPermission(allowed=True),
            ActionRiskLevel.MEDIUM: ActionPermission(allowed=True),
            ActionRiskLevel.HIGH: ActionPermission(allowed=True),
        },
    }
    
    @staticmethod
    def check_permission(user: UserModel, risk_level: ActionRiskLevel) -> ActionPermission:
        """Verifica se user può eseguire azione."""
        return RBACManager.PERMISSIONS[user.role][risk_level]
```

#### app/security/audit_log.py
```python
from sqlalchemy.orm import Session
from app.security.models import AuditLogModel, ActionRiskLevel
from datetime import datetime
from typing import List, Optional, Dict

class AuditLogger:
    """Centralized audit logging."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_action(
        self,
        user_id: Optional[str],
        action_type: str,
        status: str = "SUCCESS",
        tool_id: Optional[str] = None,
        risk_level: str = "LOW",
        metadata: Optional[Dict] = None,
        session_id: Optional[str] = None,
        error_message: Optional[str] = None,
    ):
        """Log un'azione."""
        log_entry = AuditLogModel(
            user_id=user_id,
            session_id=session_id,
            action_type=action_type,
            tool_id=tool_id,
            status=status,
            risk_level=risk_level,
            metadata=metadata or {},
            error_message=error_message,
        )
        self.db.add(log_entry)
        self.db.commit()
    
    def get_session_audit(self, session_id: str) -> List[Dict]:
        """Storico azioni di una sessione."""
        logs = self.db.query(AuditLogModel).filter(
            AuditLogModel.session_id == session_id
        ).order_by(AuditLogModel.created_at).all()
        
        return [
            {
                "action_type": l.action_type,
                "tool_id": l.tool_id,
                "status": l.status,
                "risk_level": l.risk_level,
                "created_at": l.created_at.isoformat(),
                "metadata": l.metadata,
            }
            for l in logs
        ]
    
    def get_user_audit(self, user_id: str, days: int = 30) -> List[Dict]:
        """Storico azioni di un utente (ultimi N giorni)."""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        logs = self.db.query(AuditLogModel).filter(
            AuditLogModel.user_id == user_id,
            AuditLogModel.created_at >= cutoff
        ).order_by(AuditLogModel.created_at.desc()).all()
        
        return [
            {
                "action_type": l.action_type,
                "session_id": l.session_id,
                "status": l.status,
                "created_at": l.created_at.isoformat(),
            }
            for l in logs
        ]
```

#### app/main.py (MIDDLEWARE)
```python
from fastapi import FastAPI, Request
from app.security.audit_log import AuditLogger
from app.models.database import SessionLocal

app = FastAPI()

@app.middleware("http")
async def audit_logging_middleware(request: Request, call_next):
    """Loga ogni richiesta HTTP."""
    db = SessionLocal()
    logger = AuditLogger(db)
    
    try:
        response = await call_next(request)
        
        # Loga solo endpoint rilevanti
        if request.url.path.startswith("/api/v1"):
            user_id = request.headers.get("X-User-ID", None)
            logger.log_action(
                user_id=user_id,
                action_type=f"{request.method} {request.url.path}",
                status="SUCCESS" if response.status_code < 400 else "FAILURE",
                risk_level="LOW"
            )
        
        return response
    finally:
        db.close()
```

### File da creare:
- `app/security/models.py`
- `app/security/rbac.py`
- `app/security/audit_log.py`

### File da aggiornare:
- `app/main.py` (middleware logging)
- `requirements.txt` (nessuna dipendenza nuova)

### Tests:
```python
# tests/test_audit_log.py
def test_log_action():
    db = SessionLocal()
    logger = AuditLogger(db)
    
    logger.log_action(
        user_id="tech-1",
        action_type="TOOL_EXECUTE",
        tool_id="windows.3utools.open",
        status="SUCCESS",
        risk_level="MEDIUM"
    )
    
    # Verifica log salvato
    audit = logger.get_user_audit("tech-1")
    assert len(audit) == 1
    assert audit[0]["action_type"] == "TOOL_EXECUTE"

def test_rbac_technician_cannot_high_risk():
    from app.security.rbac import RBACManager, ActionRiskLevel
    from app.security.models import UserRole, UserModel
    
    user = UserModel(id="t1", username="tech", role=UserRole.TECHNICIAN)
    perm = RBACManager.check_permission(user, ActionRiskLevel.HIGH)
    
    assert not perm.allowed

def test_rbac_admin_can_everything():
    user = UserModel(id="a1", username="admin", role=UserRole.ADMIN)
    perm = RBACManager.check_permission(user, ActionRiskLevel.HIGH)
    
    assert perm.allowed
```

---

## 🎯 PRIORITY 4: DIAGNOSTIC WORKFLOW

### Cosa fare:
- [ ] Creare `app/diagnostics/workflow_engine.py`
- [ ] Creare `data/diagnostic_trees/` con JSON per device
- [ ] Anti-loop: track test già eseguiti
- [ ] Confidence scoring (Bayesian update)
- [ ] Recommendation engine
- [ ] Tests: workflow non ripete test

### Requisiti tecnici:

#### data/diagnostic_trees/iphone_13.json
```json
{
  "device": "iPhone 13",
  "initial_symptoms": ["display_broken", "battery_drain", "heating", "no_charge"],
  "decision_tree": {
    "symptom": "display_broken",
    "tests": [
      {
        "id": "visual_inspection",
        "label": "Ispezione visiva del display",
        "description": "Controlla graffi, screpolature, scolorimenti",
        "duration_sec": 60,
        "risk_level": "low"
      },
      {
        "id": "test_display_cable",
        "label": "Test connettore display",
        "description": "Apri il device e controlla il cavo display",
        "duration_sec": 300,
        "risk_level": "medium"
      }
    ],
    "diagnosis_flow": {
      "if_both_positive": "display_must_be_replaced",
      "if_only_cable_negative": "cable_replacement_might_fix",
      "confidence_score": 0.95
    }
  }
}
```

#### app/diagnostics/workflow_engine.py
```python
from typing import List, Optional, Dict
from pydantic import BaseModel
from app.schemas.repair import Device
import json

class DiagnosticTest(BaseModel):
    id: str
    label: str
    description: str
    duration_sec: int
    risk_level: str

class DiagnosticRecommendation(BaseModel):
    next_test: Optional[DiagnosticTest] = None
    reasoning: str
    confidence_score: float  # 0.0 - 1.0
    estimated_time_min: int

class DiagnosticWorkflow:
    """
    Orchestrates diagnostic workflow per device.
    Bayesian update: accumula evidenze, aggiorna diagnosi.
    """
    
    def __init__(self, device: Device):
        self.device = device
        self.completed_tests: Dict[str, bool] = {}  # test_id → result (True=pass, False=fail)
        self.hypothesis_confidence: Dict[str, float] = {}  # diagnosis → confidence
        self.tree = self._load_tree(device.model)
    
    def _load_tree(self, device_model: str) -> Dict:
        """Carica decision tree da JSON."""
        # In real: load da data/diagnostic_trees/{device_model}.json
        # Per ora: mock
        return {
            "device": device_model,
            "initial_symptoms": [],
            "decision_tree": {}
        }
    
    def next_step(self, current_symptoms: List[str]) -> DiagnosticRecommendation:
        """
        Suggerisci il prossimo test.
        
        Logic:
        1. Identifica ipotesi plausibili (da sintomi)
        2. Filtra test già eseguiti (no ripetizione)
        3. Suggerisci test con massimo valore informativo
        4. Return recommendation con confidence
        """
        
        # Filtra test non ancora eseguiti
        available_tests = [
            t for t in self._get_tests_for_symptoms(current_symptoms)
            if t["id"] not in self.completed_tests
        ]
        
        if not available_tests:
            return DiagnosticRecommendation(
                reasoning="Tutti i test rilevanti sono stati eseguiti.",
                confidence_score=self._calculate_final_confidence(),
                estimated_time_min=0
            )
        
        # Ordina per valore informativo (info gain)
        # Per ora: ordine default da tree
        best_test = available_tests[0]
        
        return DiagnosticRecommendation(
            next_test=DiagnosticTest(**best_test),
            reasoning=f"Test suggerito: {best_test['label']}",
            confidence_score=0.70,
            estimated_time_min=best_test["duration_sec"] // 60
        )
    
    def record_test_result(self, test_id: str, result: bool):
        """Registra risultato test."""
        self.completed_tests[test_id] = result
        self._update_hypothesis_confidence(test_id, result)
    
    def _update_hypothesis_confidence(self, test_id: str, result: bool):
        """Bayesian update: aggiorna confidenza ipotesi."""
        # Semplice: se test positivo, aumenta confidence della diagnosi correlata
        # In reale: implementare Bayes rule
        for diagnosis in self.hypothesis_confidence:
            if result:
                self.hypothesis_confidence[diagnosis] *= 1.2  # Aumenta
            else:
                self.hypothesis_confidence[diagnosis] *= 0.7  # Diminuisci
        
        # Normalizza a [0, 1]
        max_conf = max(self.hypothesis_confidence.values()) if self.hypothesis_confidence else 1.0
        if max_conf > 0:
            for diag in self.hypothesis_confidence:
                self.hypothesis_confidence[diag] /= max_conf
    
    def _calculate_final_confidence(self) -> float:
        """Confidence media delle ipotesi attuali."""
        if not self.hypothesis_confidence:
            return 0.0
        return sum(self.hypothesis_confidence.values()) / len(self.hypothesis_confidence)
    
    def _get_tests_for_symptoms(self, symptoms: List[str]) -> List[Dict]:
        """Restituisci test pertinenti ai sintomi."""
        # Mock: ordina test per rilevanza
        return self.tree.get("decision_tree", {}).get("tests", [])
```

### File da creare:
- `app/diagnostics/workflow_engine.py`
- `data/diagnostic_trees/iphone_13.json` (almeno uno)

### Tests:
```python
# tests/test_diagnostic_workflow.py
def test_workflow_suggests_first_test():
    device = Device(model="iPhone 13", brand="Apple")
    workflow = DiagnosticWorkflow(device)
    
    rec = workflow.next_step(current_symptoms=["display_broken"])
    assert rec.next_test is not None
    assert rec.next_test.id in ["visual_inspection", "test_display_cable"]

def test_workflow_no_repeat_tests():
    device = Device(model="iPhone 13", brand="Apple")
    workflow = DiagnosticWorkflow(device)
    
    # Esegui primo test
    workflow.record_test_result("visual_inspection", True)
    
    # Prossimo test non deve essere visual_inspection
    rec = workflow.next_step(current_symptoms=["display_broken"])
    assert rec.next_test.id != "visual_inspection"

def test_workflow_confidence_update():
    device = Device(model="iPhone 13", brand="Apple")
    workflow = DiagnosticWorkflow(device)
    
    initial_conf = workflow._calculate_final_confidence()
    workflow.record_test_result("visual_inspection", True)
    updated_conf = workflow._calculate_final_confidence()
    
    # Confidence dovrebbe aumentare se test positivo
    assert updated_conf > initial_conf
```

---

## 🎯 PRIORITY 5: SMART AI ROUTER + FALLBACK

### Cosa fare:
- [ ] Creare `ai/circuit_breaker.py`
- [ ] Creare `ai/prompt_cache.py`
- [ ] Update `ai/router.py` con fallback, cache, circuit breaker
- [ ] Rate limiting per provider cloud
- [ ] Tests: fallback automatico su errore

### Requisiti tecnici:

#### ai/circuit_breaker.py
```python
from enum import Enum
from datetime import datetime, timedelta
from typing import Callable, Any

class CircuitState(str, Enum):
    CLOSED = "closed"      # Normal
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered

class CircuitBreaker:
    """Circuit breaker per AI providers."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout_sec: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = timedelta(seconds=recovery_timeout_sec)
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
    
    def record_failure(self):
        """Registra fallimento."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
    
    def record_success(self):
        """Reset su successo."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def is_available(self) -> bool:
        """Può il circuit accettare richieste?"""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # Prova recovery
            if datetime.utcnow() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        
        # HALF_OPEN: permetti una richiesta di prova
        return True
```

#### ai/prompt_cache.py
```python
from typing import Dict, Optional
from datetime import datetime, timedelta
import hashlib
import json

class PromptCache:
    """Simple in-memory prompt cache con TTL."""
    
    def __init__(self, ttl_sec: int = 3600):
        self.cache: Dict[str, Dict] = {}
        self.ttl = timedelta(seconds=ttl_sec)
    
    def _hash_prompt(self, prompt: str) -> str:
        return hashlib.md5(prompt.encode()).hexdigest()
    
    def get(self, prompt: str) -> Optional[str]:
        """Prova cache hit."""
        key = self._hash_prompt(prompt)
        if key in self.cache:
            entry = self.cache[key]
            if datetime.utcnow() - entry["timestamp"] < self.ttl:
                return entry["response"]
            else:
                del self.cache[key]
        return None
    
    def set(self, prompt: str, response: str):
        """Salva in cache."""
        key = self._hash_prompt(prompt)
        self.cache[key] = {
            "response": response,
            "timestamp": datetime.utcnow()
        }
    
    def clear(self):
        """Pulisci cache."""
        self.cache.clear()
```

#### ai/router.py (AGGIORNAMENTO COMPLETO)
```python
from enum import Enum
from typing import List, Optional
from app.ai.providers import AIProvider, MockProvider
from app.ai.circuit_breaker import CircuitBreaker, CircuitState
from app.ai.prompt_cache import PromptCache
from app.ai.schemas import AIRequest, AIResponse
import asyncio

class FallbackStrategy(str, Enum):
    SEQUENTIAL = "sequential"    # Try provider 1, then 2, then 3
    PARALLEL = "parallel"        # Try all in parallel, fastest wins
    COST_OPTIMIZED = "cost_optimized"  # Cheap first

class SmartAIRouter:
    """
    AI Router con fallback, circuit breaker, cache, rate limiting.
    """
    
    def __init__(self, providers: List[AIProvider] = None):
        self.providers = providers or [MockProvider()]
        self.circuit_breakers = {p.__class__.__name__: CircuitBreaker() for p in self.providers}
        self.cache = PromptCache(ttl_sec=3600)
        self.request_counts = {p.__class__.__name__: 0 for p in self.providers}
        self.rate_limits = {p.__class__.__name__: 1000 for p in self.providers}  # Requests per hour
    
    async def generate(
        self,
        request: AIRequest,
        strategy: FallbackStrategy = FallbackStrategy.SEQUENTIAL,
        use_cache: bool = True
    ) -> AIResponse:
        """
        Generate AI response con fallback e cache.
        
        1. Check cache
        2. Try providers secondo strategy
        3. On failure: next provider
        4. Cache result
        """
        
        # 1. Check cache
        if use_cache:
            cached = self.cache.get(request.prompt)
            if cached:
                return AIResponse(text=cached, provider="cache", latency_ms=0)
        
        # 2. Get available providers
        available = [
            p for p in self.providers
            if self.circuit_breakers[p.__class__.__name__].is_available()
        ]
        
        if not available:
            return AIResponse(
                text="Tutti i provider AI sono temporaneamente non disponibili.",
                provider="fallback",
                error="No providers available"
            )
        
        # 3. Try according to strategy
        if strategy == FallbackStrategy.SEQUENTIAL:
            return await self._try_sequential(request, available)
        elif strategy == FallbackStrategy.PARALLEL:
            return await self._try_parallel(request, available)
        else:  # COST_OPTIMIZED
            return await self._try_cost_optimized(request, available)
    
    async def _try_sequential(self, request: AIRequest, providers: List[AIProvider]) -> AIResponse:
        """Try providers one by one until success."""
        for provider in providers:
            try:
                response = await provider.generate(request)
                self.circuit_breakers[provider.__class__.__name__].record_success()
                
                # Cache
                self.cache.set(request.prompt, response.text)
                return response
            
            except Exception as e:
                self.circuit_breakers[provider.__class__.__name__].record_failure()
                continue
        
        return AIResponse(
            text="Nessun provider ha potuto generare una risposta.",
            provider="fallback",
            error="All providers failed"
        )
    
    async def _try_parallel(self, request: AIRequest, providers: List[AIProvider]) -> AIResponse:
        """Try multiple providers in parallel, return fastest."""
        tasks = [provider.generate(request) for provider in providers]
        done, pending = await asyncio.wait(
            tasks,
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Cancel pending
        for task in pending:
            task.cancel()
        
        result = done.pop().result()
        self.cache.set(request.prompt, result.text)
        return result
    
    async def _try_cost_optimized(self, request: AIRequest, providers: List[AIProvider]) -> AIResponse:
        """Try cheapest provider first."""
        # Sort by estimated cost (mock)
        sorted_providers = sorted(
            providers,
            key=lambda p: getattr(p, 'cost_per_call', 0)
        )
        return await self._try_sequential(request, sorted_providers)
```

### File da creare:
- `ai/circuit_breaker.py`
- `ai/prompt_cache.py`

### File da aggiornare:
- `ai/router.py` (complete rewrite con SmartAIRouter)

### Tests:
```python
# tests/test_smart_router.py
@pytest.mark.asyncio
async def test_sequential_fallback():
    from app.ai.providers import FailingProvider, MockProvider
    
    router = SmartAIRouter([FailingProvider(), MockProvider()])
    request = AIRequest(prompt="test")
    
    response = await router.generate(request, strategy="sequential")
    assert response.text is not None
    assert response.provider == "MockProvider"

@pytest.mark.asyncio
async def test_prompt_cache():
    router = SmartAIRouter([MockProvider()])
    request = AIRequest(prompt="test")
    
    # First call: cache miss
    resp1 = await router.generate(request, use_cache=True)
    
    # Second call: cache hit
    resp2 = await router.generate(request, use_cache=True)
    assert resp2.provider == "cache"

def test_circuit_breaker():
    from ai.circuit_breaker import CircuitBreaker
    
    cb = CircuitBreaker(failure_threshold=3)
    assert cb.is_available()
    
    cb.record_failure()
    cb.record_failure()
    cb.record_failure()
    
    assert not cb.is_available()  # Circuit OPEN
```

---

## 🎯 PRIORITY 6: KNOWLEDGE BASE + RAG

### Cosa fare:
- [ ] Creare `app/knowledge/knowledge_base.py`
- [ ] Creare `app/knowledge/models.py` (ORM)
- [ ] Index repair completate con embedding
- [ ] Search similar cases on chat
- [ ] Augment prompt con RAG context
- [ ] Tests: search trova casi simili

### Requisiti tecnici:

#### app/knowledge/models.py
```python
from sqlalchemy import Column, String, DateTime, Text, Float, JSON
from app.models.database import Base
from datetime import datetime

class KnowledgeEntryModel(Base):
    __tablename__ = "knowledge_base"
    
    id = Column(String, primary_key=True)
    device = Column(String, index=True)  # "iPhone 13"
    brand = Column(String)               # "Apple"
    symptom = Column(String, index=True) # "display broken"
    diagnosis = Column(String)
    solution = Column(String)
    technical_notes = Column(Text)
    # Embedding del symptom (float32 vector)
    embedding_vector = Column(JSON)  # Salva come JSON array
    repair_duration_min = Column(Integer)
    success_rate = Column(Float)     # 0.0 - 1.0
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### app/knowledge/knowledge_base.py
```python
from typing import List, Optional
from sentence_transformers import SentenceTransformer
import numpy as np
from sqlalchemy.orm import Session
from app.knowledge.models import KnowledgeEntryModel
from app.schemas.repair import RepairSessionContext

class KnowledgeBase:
    """RAG-enabled knowledge base con embeddings."""
    
    def __init__(self, db: Session, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.db = db
        self.embedder = SentenceTransformer(model_name)
    
    def index_repair(self, session: RepairSessionContext):
        """
        Indicizza una riparazione completata.
        Estrae: device, symptom, diagnosis, solution.
        Calcola embedding del symptom.
        """
        symptom_text = " ".join(session.symptoms) if session.symptoms else "unknown"
        embedding = self.embedder.encode(symptom_text).tolist()
        
        entry = KnowledgeEntryModel(
            id=session.session_id,
            device=session.device.model,
            brand=session.device.brand,
            symptom=symptom_text,
            diagnosis=session.diagnosis or "",
            solution=session.solution or "",
            technical_notes=session.notes or "",
            embedding_vector=embedding,
            repair_duration_min=session.duration_min,
            success_rate=1.0 if session.status == "completed" else 0.0
        )
        
        self.db.add(entry)
        self.db.commit()
    
    def search_similar(
        self,
        symptom: str,
        device: Optional[str] = None,
        limit: int = 3
    ) -> List[Dict]:
        """
        Cerca riparazioni simili tramite embedding similarity.
        
        1. Embedding del symptom
        2. Query DB: tutti gli entry
        3. Cosine similarity con embedding_vector
        4. Return top_k
        """
        symptom_embedding = self.embedder.encode(symptom).tolist()
        
        # Query DB
        all_entries = self.db.query(KnowledgeEntryModel).all()
        
        if not all_entries:
            return []
        
        # Calcola similarity
        results = []
        for entry in all_entries:
            # Cosine similarity
            similarity = self._cosine_similarity(
                np.array(symptom_embedding),
                np.array(entry.embedding_vector)
            )
            
            # Filter by device se specificato
            if device and entry.device != device:
                similarity *= 0.7  # Penalizza device diverso
            
            results.append({
                "device": entry.device,
                "symptom": entry.symptom,
                "diagnosis": entry.diagnosis,
                "solution": entry.solution,
                "repair_duration_min": entry.repair_duration_min,
                "success_rate": entry.success_rate,
                "similarity": float(similarity)
            })
        
        # Sort e return top_k
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:limit]
    
    @staticmethod
    def _cosine_similarity(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    def get_rag_context(self, symptom: str, device: Optional[str] = None) -> str:
        """Prepara RAG context da passare al prompt AI."""
        similar = self.search_similar(symptom, device, limit=3)
        
        if not similar:
            return ""
        
        context = "Casi simili trovati nel laboratorio:\n"
        for i, case in enumerate(similar, 1):
            context += f"\n{i}. {case['device']} - {case['symptom']}\n"
            context += f"   Diagnosi: {case['diagnosis']}\n"
            context += f"   Soluzione: {case['solution']}\n"
            context += f"   Confidenza: {case['similarity']:.0%}\n"
        
        return context
```

#### app/ai/router.py (AGGIORNAMENTO con RAG)
```python
# Nel metodo generate():
async def generate(self, request: AIRequest, ...) -> AIResponse:
    # ... existing code ...
    
    # Augment prompt with RAG context
    if hasattr(request, 'symptom'):
        kb = KnowledgeBase(db)
        rag_context = kb.get_rag_context(request.symptom)
        augmented_prompt = f"{rag_context}\n\nUtente: {request.prompt}"
        request.prompt = augmented_prompt
    
    # ... continue with providers ...
```

### File da creare:
- `app/knowledge/models.py`
- `app/knowledge/knowledge_base.py`

### Tests:
```python
# tests/test_knowledge_base.py
def test_index_repair():
    db = SessionLocal()
    kb = KnowledgeBase(db)
    
    session = RepairSessionContext(
        session_id="repair-1",
        device=Device(model="iPhone 13", brand="Apple"),
        symptoms=["display broken", "no touch"],
        diagnosis="LCD connector broken",
        solution="Replace display cable",
        status="completed"
    )
    
    kb.index_repair(session)
    
    # Verifica salvato
    entry = db.query(KnowledgeEntryModel).filter(
        KnowledgeEntryModel.id == "repair-1"
    ).first()
    assert entry is not None
    assert "display" in entry.symptom.lower()

def test_search_similar():
    db = SessionLocal()
    kb = KnowledgeBase(db)
    
    # Index due riparazioni
    kb.index_repair(RepairSessionContext(...))
    kb.index_repair(RepairSessionContext(...))
    
    # Search
    results = kb.search_similar("display problem", device="iPhone 13")
    assert len(results) > 0
    assert results[0]["similarity"] > 0.5
```

---

## 🎯 PRIORITY 7: FRONTEND OFFLINE SUPPORT

### Cosa fare:
- [ ] Creare `frontend/public/sw.js` (Service Worker)
- [ ] Update `frontend/src/hooks/useRealtimeClient.ts` con offline queue
- [ ] Update UI con indicator "OFFLINE"
- [ ] IndexedDB per cache risposte
- [ ] Sync logic on reconnect

### Requisiti tecnici:

#### frontend/public/sw.js
```javascript
const CACHE_NAME = 'alpilab-v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/favicon.ico',
  '/src/main.tsx',
];

// Install event
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(urlsToCache);
    })
  );
});

// Activate event
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Fetch event - Network first, fallback to cache
self.addEventListener('fetch', event => {
  event.respondWith(
    fetch(event.request)
      .then(response => {
        // Salva risposta in cache
        const responseClone = response.clone();
        caches.open(CACHE_NAME).then(cache => {
          cache.put(event.request, responseClone);
        });
        return response;
      })
      .catch(() => {
        // Offline: prova cache
        return caches.match(event.request);
      })
  );
});
```

#### frontend/src/hooks/useOfflineQueue.ts
```typescript
import { useCallback, useState, useEffect } from 'react';

export interface QueuedAction {
  id: string;
  type: 'CHAT_MESSAGE' | 'DIAGNOSTIC_UPDATE' | 'TOOL_EXECUTE';
  payload: any;
  timestamp: number;
  status: 'pending' | 'syncing' | 'synced' | 'failed';
}

export function useOfflineQueue() {
  const [queue, setQueue] = useState<QueuedAction[]>([]);
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const addToQueue = useCallback((action: Omit<QueuedAction, 'id' | 'timestamp' | 'status'>) => {
    const newAction: QueuedAction = {
      ...action,
      id: `${Date.now()}-${Math.random()}`,
      timestamp: Date.now(),
      status: 'pending',
    };
    setQueue(prev => [...prev, newAction]);
    return newAction.id;
  }, []);

  const syncQueue = useCallback(async (send: (action: QueuedAction) => Promise<void>) => {
    const pendingActions = queue.filter(a => a.status === 'pending');
    
    for (const action of pendingActions) {
      try {
        setQueue(prev => 
          prev.map(a => a.id === action.id ? {...a, status: 'syncing'} : a)
        );
        
        await send(action);
        
        setQueue(prev => 
          prev.map(a => a.id === action.id ? {...a, status: 'synced'} : a)
        );
      } catch (error) {
        setQueue(prev => 
          prev.map(a => a.id === action.id ? {...a, status: 'failed'} : a)
        );
      }
    }
  }, [queue]);

  useEffect(() => {
    if (isOnline) {
      // Trigger sync quando torna online
      const syncTimer = setTimeout(() => {
        // syncQueue verrà chiamato dal componente che usa questo hook
      }, 1000);
      return () => clearTimeout(syncTimer);
    }
  }, [isOnline]);

  return { queue, isOnline, addToQueue, syncQueue };
}
```

#### frontend/src/components/OfflineIndicator.tsx
```typescript
import React from 'react';
import { useOfflineQueue } from '../hooks/useOfflineQueue';

export function OfflineIndicator() {
  const { isOnline, queue } = useOfflineQueue();
  const pendingCount = queue.filter(a => a.status === 'pending').length;

  if (isOnline && pendingCount === 0) {
    return null;
  }

  return (
    <div className="fixed bottom-4 left-4 bg-yellow-600 text-white px-4 py-2 rounded-lg">
      {!isOnline ? (
        <span>🔴 Offline — Sincronizzazione locale</span>
      ) : pendingCount > 0 ? (
        <span>🔄 Sincronizzazione {pendingCount} azioni...</span>
      ) : (
        <span>✅ Sincronizzato</span>
      )}
    </div>
  );
}
```

### File da creare:
- `frontend/public/sw.js`
- `frontend/src/hooks/useOfflineQueue.ts`
- `frontend/src/components/OfflineIndicator.tsx`

### File da aggiornare:
- `frontend/src/main.tsx` (register service worker)
- `frontend/src/App.tsx` (add OfflineIndicator)

### main.tsx:
```typescript
// Register service worker
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js')
    .then(reg => console.log('SW registered'))
    .catch(err => console.log('SW registration failed', err));
}
```

---

## 🎯 PRIORITY 8: VOICE STT/TTS

### Cosa fare:
- [ ] Update `app/voice/speech_to_text.py` → Whisper o Vosk
- [ ] Update `app/voice/text_to_speech.py` → gTTS o pyttsx3
- [ ] Streaming audio (non wait-for-full)
- [ ] Feedback "Ascoltando..."
- [ ] Tests: STT riconosce testo italiano

### Requisiti tecnici:

#### app/voice/speech_to_text.py (Aggiornamento)
```python
from typing import Optional, AsyncGenerator
import whisper
from pathlib import Path

class WhisperSTT:
    """Speech-to-text usando OpenAI Whisper."""
    
    def __init__(self, model_name: str = "base"):
        self.model = whisper.load_model(model_name)
    
    async def transcribe(self, audio_file: Path, language: str = "it") -> str:
        """Trascrivi audio file (WAV, MP3, etc)."""
        result = self.model.transcribe(
            str(audio_file),
            language=language
        )
        return result["text"]
    
    async def transcribe_stream(self, audio_bytes: bytes) -> str:
        """Trascrivi byte stream."""
        # Salva temporaneamente
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            f.flush()
            result = await self.transcribe(Path(f.name))
        return result
```

#### app/voice/text_to_speech.py (Aggiornamento)
```python
import pyttsx3
from typing import Optional, AsyncGenerator

class LocalTTS:
    """Text-to-speech using pyttsx3 (offline, Italian support)."""
    
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)  # velocità
        self.engine.setProperty('volume', 1.0)
        # Setta lingua italiana
        self.engine.setProperty('language', 'it_IT')
    
    async def speak(self, text: str) -> bytes:
        """Converti testo a audio."""
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            self.engine.save_to_file(text, f.name)
            self.engine.runAndWait()
            
            # Leggi il file wav e ritorna bytes
            with open(f.name, 'rb') as af:
                audio_bytes = af.read()
            return audio_bytes
    
    async def speak_stream(self, text: str) -> AsyncGenerator[bytes, None]:
        """Stream audio chunks."""
        audio_bytes = await self.speak(text)
        # Dividi in chunk
        chunk_size = 4096
        for i in range(0, len(audio_bytes), chunk_size):
            yield audio_bytes[i:i+chunk_size]
```

#### app/conversation/command_engine.py (AGGIORNAMENTO per voice)
```python
class ConversationCommandEngine:
    def __init__(self, stt, tts):
        self.stt = stt  # WhisperSTT
        self.tts = tts  # LocalTTS
    
    async def process_voice_input(self, audio_bytes: bytes, session: RepairSessionContext):
        """Process voice input → text → command/conversation → voice response."""
        
        # 1. STT: audio → text
        user_text = await self.stt.transcribe_stream(audio_bytes)
        
        # 2. Process text (command parsing, conversation, etc)
        response = await self.process_user_input(user_text, session)
        
        # 3. TTS: response → audio
        if isinstance(response, str):
            audio_response = await self.tts.speak(response)
            return {
                "text": response,
                "audio": audio_response
            }
        
        return response
```

### File da aggiornare:
- `app/voice/speech_to_text.py`
- `app/voice/text_to_speech.py`
- `app/conversation/command_engine.py`
- `requirements.txt` (aggiungi `openai-whisper`, `pyttsx3`)

### Tests:
```python
# tests/test_voice.py
@pytest.mark.asyncio
async def test_whisper_italian():
    stt = WhisperSTT(model_name="base")
    # Crea file audio dummy (o usa file di test)
    # (in reale: file WAV con parola italiana)
    result = await stt.transcribe(Path("test_audio_it.wav"), language="it")
    assert isinstance(result, str)
    assert len(result) > 0

@pytest.mark.asyncio
async def test_tts_speaks():
    tts = LocalTTS()
    audio = await tts.speak("Ciao, come stai?")
    assert isinstance(audio, bytes)
    assert len(audio) > 0
```

---

## 📦 REQUIREMENTS.TXT (UPDATED)

Aggiungi questi:

```txt
# Priority 1: Persistent Storage
sqlalchemy>=2.0

# Priority 2: Semantic Parser
sentence-transformers>=2.2

# Priority 5: AI Router (no new deps)

# Priority 6: Knowledge Base (uses sentence-transformers)

# Priority 8: Voice
openai-whisper>=20231117
pyttsx3>=2.90
```
