"""Instâncias de extensões Flask compartilhadas entre os módulos da aplicação."""
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

db = SQLAlchemy()
csrf = CSRFProtect()
