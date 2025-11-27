from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from typing import List

# MODELOS DE USUARIO
class PersonalInfo(BaseModel):
    name: str
    email: str 
    age: Optional[str] = ""
    gender: Optional[str] = ""
    country: Optional[str] = "MX"
    state: Optional[str] = ""
    phone: Optional[str] = ""
    platformLang: str = "es"

class Preferences(BaseModel):
    notifications: Dict[str, bool] # {'email': True, 'sms': False}

# Modelo Principal para el documento de usuario
class UserProfile(BaseModel):
    id: str
    userId: str # Partition Key
    type: str = "profile" # Siempre fijo
    personalInfo: PersonalInfo
    preferences: Preferences
    topics: Dict[str, Any] # Los temas son dinámicos
    updatedAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    class Config:
        populate_by_name = True

# MODELOS DE CHAT
class ChatMessage(BaseModel):
    role: str # "user" o "ai"
    text: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ChatSession(BaseModel):
    id: str
    userId: str # Partition Key
    type: str = "chat"
    title: str
    createdAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updatedAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    messages: List[ChatMessage] = []

    class Config:
        populate_by_name = True