"""initial_migration

Revision ID: 001_initial_migration
Revises: 
Create Date: 2026-06-02 00:00:00

Tables créées :
- users
- user_skills
- mentorships
- mentoring_sessions
- mentor_messages
- projects
- project_members
- project_applications
- clubs
- club_members
- events
- event_registrations
- certifications
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "001_initial_migration"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ─── users ────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("role", sa.Enum("student", "mentor", "club_admin", "admin", name="userrole"), nullable=False, server_default="student"),
        sa.Column("year_level", sa.Enum("B1", "B2", "B3", "M1", "M2", name="yearlevel"), nullable=True),
        sa.Column("specialty", sa.String(200), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_available", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("hours_per_week", sa.Integer(), nullable=False, server_default=sa.text("10")),
        sa.Column("linkedin_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ─── user_skills ──────────────────────────────────────────────────────────
    op.create_table(
        "user_skills",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("category", sa.Enum(
            "Développement", "Data & IA", "Design", "Business",
            "Langues", "Soft Skills", "Autre", name="skillcategory"
        ), nullable=False),
        sa.Column("level", sa.Enum(
            "débutant", "intermédiaire", "avancé", "expert", name="skilllevel"
        ), nullable=False),
        sa.Column("is_validated", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("validated_by", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["validated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_skills_user_id", "user_skills", ["user_id"])

    # ─── mentorships ──────────────────────────────────────────────────────────
    op.create_table(
        "mentorships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("mentor_id", sa.Integer(), nullable=False),
        sa.Column("mentee_id", sa.Integer(), nullable=False),
        sa.Column("match_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("goals", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("mentee_rating", sa.Float(), nullable=True),
        sa.Column("mentee_feedback", sa.Text(), nullable=True),
        sa.Column("rated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["mentor_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["mentee_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mentorships_mentor_id", "mentorships", ["mentor_id"])
    op.create_index("ix_mentorships_mentee_id", "mentorships", ["mentee_id"])

    # ─── mentoring_sessions ───────────────────────────────────────────────────
    op.create_table(
        "mentoring_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("mentorship_id", sa.Integer(), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_min", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("location", sa.String(200), nullable=True),
        sa.Column("topic", sa.String(300), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="scheduled"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("mentor_rating", sa.Float(), nullable=True),
        sa.Column("mentee_rating", sa.Float(), nullable=True),
        sa.Column("mentor_feedback", sa.Text(), nullable=True),
        sa.Column("mentee_feedback", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["mentorship_id"], ["mentorships.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mentoring_sessions_mentorship_id", "mentoring_sessions", ["mentorship_id"])

    # ─── mentor_messages ──────────────────────────────────────────────────────
    op.create_table(
        "mentor_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("mentorship_id", sa.Integer(), nullable=False),
        sa.Column("sender_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["mentorship_id"], ["mentorships.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mentor_messages_mentorship_id", "mentor_messages", ["mentorship_id"])

    # ─── projects ─────────────────────────────────────────────────────────────
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("type", sa.Enum(
            "tech", "data", "design", "business", "recherche", "open_innovation",
            name="projecttype"
        ), nullable=False),
        sa.Column("status", sa.Enum(
            "brouillon", "ouvert", "en cours", "terminé", "annulé",
            name="projectstatus"
        ), nullable=False, server_default="ouvert"),
        sa.Column("required_skills", sa.JSON(), nullable=False),
        sa.Column("max_members", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("required_hours_per_week", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("supervisor_id", sa.Integer(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("embedding", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["supervisor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # ─── project_members ──────────────────────────────────────────────────────
    op.create_table(
        "project_members",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(100), nullable=False, server_default="membre"),
        sa.Column("status", sa.String(50), nullable=False, server_default="accepted"),
        sa.Column("joined_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_project_members_project_id", "project_members", ["project_id"])
    op.create_index("ix_project_members_user_id", "project_members", ["user_id"])

    # ─── project_applications ─────────────────────────────────────────────────
    op.create_table(
        "project_applications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("applicant_id", sa.Integer(), nullable=False),
        sa.Column("match_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["applicant_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_project_applications_project_id", "project_applications", ["project_id"])
    op.create_index("ix_project_applications_applicant_id", "project_applications", ["applicant_id"])

    # ─── clubs ────────────────────────────────────────────────────────────────
    op.create_table(
        "clubs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("icon", sa.String(10), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("admin_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["admin_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # ─── club_members ─────────────────────────────────────────────────────────
    op.create_table(
        "club_members",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("club_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, server_default="membre"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("joined_at", sa.DateTime(), nullable=False),
        sa.Column("left_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["club_id"], ["clubs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_club_members_club_id", "club_members", ["club_id"])
    op.create_index("ix_club_members_user_id", "club_members", ["user_id"])

    # ─── events ───────────────────────────────────────────────────────────────
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("emoji", sa.String(10), nullable=True),
        sa.Column("event_date", sa.DateTime(), nullable=False),
        sa.Column("location", sa.String(300), nullable=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("club_id", sa.Integer(), nullable=True),
        sa.Column("organizer_id", sa.Integer(), nullable=False),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_cancelled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("skill_tags", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["club_id"], ["clubs.id"]),
        sa.ForeignKeyConstraint(["organizer_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # ─── event_registrations ──────────────────────────────────────────────────
    op.create_table(
        "event_registrations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="confirmed"),
        sa.Column("registered_at", sa.DateTime(), nullable=False),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        sa.Column("feedback_rating", sa.Float(), nullable=True),
        sa.Column("feedback_text", sa.Text(), nullable=True),
        sa.Column("feedback_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_event_registrations_event_id", "event_registrations", ["event_id"])
    op.create_index("ix_event_registrations_user_id", "event_registrations", ["user_id"])

    # ─── certifications ───────────────────────────────────────────────────────
    op.create_table(
        "certifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("issuer", sa.String(100), nullable=True),
        sa.Column("issue_date", sa.DateTime(), nullable=True),
        sa.Column("expiry_date", sa.DateTime(), nullable=True),
        sa.Column("credential_id", sa.String(100), nullable=True),
        sa.Column("credential_url", sa.String(500), nullable=True),
        sa.Column("file_path", sa.String(500), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_certifications_id", "certifications", ["id"])


def downgrade() -> None:
    """Supprime toutes les tables dans l'ordre inverse (respecte les FK)."""
    op.drop_table("certifications")
    op.drop_table("event_registrations")
    op.drop_table("events")
    op.drop_table("club_members")
    op.drop_table("clubs")
    op.drop_table("project_applications")
    op.drop_table("project_members")
    op.drop_table("projects")
    op.drop_table("mentor_messages")
    op.drop_table("mentoring_sessions")
    op.drop_table("mentorships")
    op.drop_table("user_skills")
    op.drop_table("users")

    # Supprimer les types Enum (PostgreSQL uniquement)
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TYPE IF EXISTS yearlevel")
    op.execute("DROP TYPE IF EXISTS skilllevel")
    op.execute("DROP TYPE IF EXISTS skillcategory")
    op.execute("DROP TYPE IF EXISTS projecttype")
    op.execute("DROP TYPE IF EXISTS projectstatus")