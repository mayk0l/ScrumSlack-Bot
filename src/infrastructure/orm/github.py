"""Módulo ORM."""
from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import ARRAY, Date, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database import Base

from src.domain.models import (
    PullRequest as PullRequestDomain,
    Issue as IssueDomain,
)

class PullRequestORM(Base):
    """Modelo ORM para pull requests."""

    __tablename__ = "pull_requests"
    __table_args__ = (
        UniqueConstraint("team_id", "repository", "pr_number"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    repository: Mapped[str] = mapped_column(String(255), nullable=False)
    pr_number: Mapped[int] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    author: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    merged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewers: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    lead_time_hours: Mapped[float | None] = mapped_column(nullable=True)

    team: Mapped["TeamORM"] = relationship(back_populates="pull_requests")

    def to_domain(self) -> PullRequestDomain:
        return PullRequestDomain(
            id=self.id,
            team_id=self.team_id,
            repository=self.repository,
            pr_number=self.pr_number,
            title=self.title,
            author=self.author,
            state=self.state,
            created_at=self.created_at,
            updated_at=self.updated_at,
            merged_at=self.merged_at,
            reviewers=list(self.reviewers or []),
            lead_time_hours=self.lead_time_hours,
        )

    @classmethod
    def from_domain(cls, pr: PullRequestDomain) -> "PullRequestORM":
        return cls(
            id=pr.id,
            team_id=pr.team_id,
            repository=pr.repository,
            pr_number=pr.pr_number,
            title=pr.title,
            author=pr.author,
            state=pr.state,
            created_at=pr.created_at,
            updated_at=pr.updated_at,
            merged_at=pr.merged_at,
            reviewers=list(pr.reviewers or []),
            lead_time_hours=pr.lead_time_hours,
        )



class IssueORM(Base):
    """Modelo ORM para issues de GitHub."""

    __tablename__ = "issues"
    __table_args__ = (
        UniqueConstraint("team_id", "repository", "issue_number"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    repository: Mapped[str] = mapped_column(String(255), nullable=False)
    issue_number: Mapped[int] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    state: Mapped[str] = mapped_column(String(20), nullable=False)
    labels: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    assignee: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    team: Mapped["TeamORM"] = relationship(back_populates="issues")

    def to_domain(self) -> IssueDomain:
        return IssueDomain(
            id=self.id,
            team_id=self.team_id,
            repository=self.repository,
            issue_number=self.issue_number,
            title=self.title,
            state=self.state,
            labels=list(self.labels or []),
            assignee=self.assignee,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, issue: IssueDomain) -> "IssueORM":
        return cls(
            id=issue.id,
            team_id=issue.team_id,
            repository=issue.repository,
            issue_number=issue.issue_number,
            title=issue.title,
            state=issue.state,
            labels=list(issue.labels or []),
            assignee=issue.assignee,
            created_at=issue.created_at,
            updated_at=issue.updated_at,
        )
