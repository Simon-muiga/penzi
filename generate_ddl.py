from sqlalchemy.schema import CreateTable
from app.database import engine
from app import models

# FORCE LOAD MODELS
_ = models.Base.metadata.tables

for table in models.Base.metadata.sorted_tables:
    print(str(CreateTable(table).compile(engine)))