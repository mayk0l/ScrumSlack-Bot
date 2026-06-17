import os
import re

source_file = "src/infrastructure/orm_models.py"
dest_dir = "src/infrastructure/orm"

os.makedirs(dest_dir, exist_ok=True)

with open(source_file, "r", encoding="utf-8") as f:
    content = f.read()

# Base imports that all files might need
base_imports = """\"\"\"Módulo ORM.\"\"\"
from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import ARRAY, Date, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database import Base
"""

# Extract models
models = {
    "team.py": ["TeamORM", "TeamDomain"],
    "member.py": ["MemberORM", "MemberDomain", "MemberRole"],
    "sprint.py": ["SprintORM", "SprintDomain", "SprintStatus"],
    "standup.py": ["StandupSessionORM", "StandupSessionDomain", "SessionStatus", "StandupResponseORM", "StandupResponseDomain"],
    "github.py": ["PullRequestORM", "PullRequestDomain", "IssueORM", "IssueDomain"],
    "risk.py": ["RiskORM", "RiskDomain", "RiskType", "Severity"],
    "metric.py": ["MetricSnapshotORM", "MetricSnapshotDomain"]
}

import_pattern = re.compile(r"from src\.domain\.models import \((.*?)\)", re.DOTALL)
domain_imports = import_pattern.search(content).group(1)

for filename, classes in models.items():
    file_content = base_imports + "\n"
    
    # Add domain imports
    needed_imports = []
    for cls_name in classes:
        if "Domain" in cls_name or cls_name in ["MemberRole", "SprintStatus", "SessionStatus", "RiskType", "Severity"]:
            # find original import
            for line in domain_imports.split("\n"):
                if cls_name in line:
                    needed_imports.append(line.strip())
                    break
    
    if needed_imports:
        file_content += "from src.domain.models import (\n"
        for imp in needed_imports:
            file_content += f"    {imp}\n"
        file_content += ")\n\n"

    # Extract class definitions
    for cls_name in classes:
        if "ORM" not in cls_name:
            continue
        
        # Regex to find class definition
        class_regex = re.compile(f"class {cls_name}\\(Base\\):(.*?)(?=\\nclass |\\Z)", re.DOTALL)
        match = class_regex.search(content)
        if match:
            class_body = match.group(1)
            # Fix Mapped[Type] to Mapped["Type"] for relationships to avoid circular imports
            class_body = re.sub(r"Mapped\[(TeamORM|MemberORM|SprintORM|StandupSessionORM|StandupResponseORM|PullRequestORM|IssueORM|RiskORM|MetricSnapshotORM)( \| None)?\]", r'Mapped["\1"\2]', class_body)
            
            file_content += f"class {cls_name}(Base):{class_body}\n\n"
    
    with open(os.path.join(dest_dir, filename), "w", encoding="utf-8") as f:
        f.write(file_content.strip() + "\n")

# Create __init__.py
init_content = '"""Paquete ORM."""\n\n'
all_classes = []
for filename, classes in models.items():
    orm_classes = [c for c in classes if "ORM" in c]
    init_content += f"from .{filename[:-3]} import {', '.join(orm_classes)}\n"
    all_classes.extend(orm_classes)

init_content += f"\n__all__ = [\n"
for c in all_classes:
    init_content += f'    "{c}",\n'
init_content += "]\n"

with open(os.path.join(dest_dir, "__init__.py"), "w", encoding="utf-8") as f:
    f.write(init_content)

# Update original orm_models.py as a facade
facade_content = '"""Módulo: orm_models.\n\nFacade para mantener compatibilidad hacia atrás.\n"""\n\n'
facade_content += "from src.infrastructure.orm import *\n"

with open(source_file, "w", encoding="utf-8") as f:
    f.write(facade_content)

print("Split completed successfully.")
