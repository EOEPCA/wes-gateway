"""Durable gateway run IDs and backend bindings; SQLite locally, PostgreSQL in HA."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    Column,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    create_engine,
    select,
    update,
)
from sqlalchemy.exc import IntegrityError

from .config import ConfigurationError

metadata = MetaData()
bindings = Table(
    "backend_bindings",
    metadata,
    Column("id", String(63), primary_key=True),
    Column("identity", Text, nullable=False),
)
runs = Table(
    "gateway_runs",
    metadata,
    Column("seq", Integer, primary_key=True, autoincrement=True),
    Column("id", String(32), unique=True, nullable=False),
    Column("namespace", String(63), nullable=False, index=True),
    Column("backend", String(63), nullable=False),
    Column("upstream_id", Text),
    Column("phase", String(20), nullable=False),
    Column("created_at", String(40), nullable=False),
    UniqueConstraint("backend", "upstream_id"),
)
artifacts = Table(
    "gateway_artifacts",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("run_id", String(32), nullable=False),
    Column("uri", Text, nullable=False),
)


class RunStore:
    def __init__(self, url):
        self.engine = create_engine(url, pool_pre_ping=True)
        metadata.create_all(self.engine)

    def validate_bindings(self, registry):
        with self.engine.connect() as conn:
            for row in conn.execute(select(bindings)).mappings():
                backend = registry.backends.get(row["id"])
                if backend is None or backend.identity != row["identity"]:
                    raise ConfigurationError(
                        f"backend {row['id']} has recorded runs: retain its type/base_url; add a new backend ID instead"
                    )

    def create(self, namespace, backend_id, identity):
        # Bind IDs once. Concurrent inserts can race, so re-read after uniqueness failure.
        try:
            with self.engine.begin() as conn:
                if (
                    conn.execute(
                        select(bindings).where(bindings.c.id == backend_id)
                    ).first()
                    is None
                ):
                    conn.execute(
                        bindings.insert().values(id=backend_id, identity=identity)
                    )
        except IntegrityError:
            pass
        with self.engine.begin() as conn:
            existing = conn.execute(
                select(bindings.c.identity).where(bindings.c.id == backend_id)
            ).scalar_one()
            if existing != identity:
                raise ConfigurationError(f"backend {backend_id} identity changed")
            values = {
                "id": uuid4().hex,
                "namespace": namespace,
                "backend": backend_id,
                "upstream_id": None,
                "phase": "SUBMITTING",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            conn.execute(runs.insert().values(**values))
            return values

    def accepted(self, run_id, upstream_id):
        with self.engine.begin() as conn:
            conn.execute(
                update(runs)
                .where(runs.c.id == run_id)
                .values(upstream_id=upstream_id, phase="ACCEPTED")
            )

    def phase(self, run_id, phase):
        with self.engine.begin() as conn:
            conn.execute(update(runs).where(runs.c.id == run_id).values(phase=phase))

    def get(self, namespace, run_id):
        with self.engine.connect() as conn:
            row = (
                conn.execute(
                    select(runs).where(
                        runs.c.id == run_id, runs.c.namespace == namespace
                    )
                )
                .mappings()
                .first()
            )
            return dict(row) if row else None

    def page(self, namespace, after, size):
        with self.engine.connect() as conn:
            return [
                dict(row)
                for row in conn.execute(
                    select(runs)
                    .where(
                        runs.c.namespace == namespace,
                        runs.c.seq > after,
                        runs.c.phase != "REJECTED",
                    )
                    .order_by(runs.c.seq)
                    .limit(size)
                ).mappings()
            ]

    def unresolved(self):
        with self.engine.connect() as conn:
            return [
                dict(row)
                for row in conn.execute(
                    select(runs).where(
                        runs.c.upstream_id.is_(None), runs.c.phase != "REJECTED"
                    )
                ).mappings()
            ]

    def artifact(self, token, run_id, uri=None):
        if uri is not None:
            try:
                with self.engine.begin() as conn:
                    conn.execute(
                        artifacts.insert().values(id=token, run_id=run_id, uri=uri)
                    )
            except IntegrityError:
                pass
        with self.engine.connect() as conn:
            return conn.execute(
                select(artifacts.c.uri).where(
                    artifacts.c.id == token, artifacts.c.run_id == run_id
                )
            ).scalar_one_or_none()

    def close(self):
        self.engine.dispose()
