"""Validated, declarative backend registration (no network calls during loading)."""

import os
import re
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)


class ConfigurationError(ValueError):
    pass


class UniqueLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str):
            raise ConfigurationError("configuration keys must be strings")
        if key in result:
            raise ConfigurationError(f"duplicate configuration key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping
)


def http_url(value: str) -> str:
    url = urlsplit(value)
    if (
        url.scheme not in {"http", "https"}
        or not url.hostname
        or url.username
        or url.password
        or url.query
        or url.fragment
    ):
        raise ValueError(
            "expected an HTTP(S) URL without credentials, query, or fragment"
        )
    try:
        _ = url.port
    except ValueError:
        raise ValueError("invalid URL port") from None
    if any(part in {".", ".."} for part in url.path.split("/")):
        raise ValueError("URL must not contain dot path segments")
    return value.rstrip("/")


class SettingsModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class S3Settings(SettingsModel):
    endpoint_url: str | None = None
    region: str = "us-east-1"
    access_key_env: str
    secret_key_env: str
    allowed_prefixes: list[str] = Field(min_length=1)

    @field_validator("endpoint_url")
    @classmethod
    def endpoint(cls, value):
        return http_url(value) if value else value

    @field_validator("allowed_prefixes")
    @classmethod
    def prefixes(cls, values):
        for value in values:
            url = urlsplit(value)
            if (
                url.scheme != "s3"
                or not url.netloc
                or not value.endswith("/")
                or url.query
                or url.fragment
            ):
                raise ValueError(
                    "S3 prefixes must be s3://bucket/prefix/ (with trailing slash)"
                )
        return values


class Backend(SettingsModel):
    type: Literal["toil", "wes"] = "toil"
    base_url: str
    connect_timeout: float = Field(default=10, gt=0, le=300)
    read_timeout: float = Field(default=60, gt=0, le=3600)
    keepalive_expiry: float = Field(default=1, ge=0, le=300)
    verify_tls: bool = True
    bearer_token_env: str | None = None
    s3: S3Settings | None = None

    @field_validator("base_url")
    @classmethod
    def url(cls, value):
        return http_url(value)

    @property
    def identity(self):
        return f"{self.type}:{self.base_url}"


class Namespace(SettingsModel):
    backend: str


class Registry(SettingsModel):
    version: Literal[1]
    backends: dict[str, Backend] = Field(min_length=1)
    namespaces: dict[str, Namespace] = Field(min_length=1)
    default_namespace: str | None = None
    max_upload_bytes: int = Field(default=64 * 1024 * 1024, gt=0)

    @model_validator(mode="after")
    def references(self):
        for kind, entries in (
            ("backend", self.backends),
            ("namespace", self.namespaces),
        ):
            for name in entries:
                if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,62}", name):
                    raise ValueError(
                        f"invalid {kind} ID; use 1–63 letters, digits, dots, underscores or hyphens"
                    )
        for name, namespace in self.namespaces.items():
            if namespace.backend not in self.backends:
                raise ValueError(
                    f"namespace {name} references unknown backend {namespace.backend}"
                )
        if (
            self.default_namespace is not None
            and self.default_namespace not in self.namespaces
        ):
            raise ValueError("default_namespace references an unknown namespace")
        return self

    def check_secrets(self):
        for name, backend in self.backends.items():
            refs = [backend.bearer_token_env]
            if backend.s3:
                refs.extend([backend.s3.access_key_env, backend.s3.secret_key_env])
            for ref in refs:
                if ref is not None and not os.environ.get(ref):
                    raise ConfigurationError(
                        f"backend {name}: missing credential environment variable {ref}"
                    )


def load_registry(path: str | Path) -> Registry:
    try:
        config = Registry.model_validate(
            yaml.load(Path(path).read_text(), Loader=UniqueLoader)
        )
        config.check_secrets()
        return config
    except ValidationError as exc:
        # Do not include input values: URLs and unknown fields can contain secrets.
        errors = [
            f"{'.'.join(map(str, e['loc'])) or 'registry'}: {e['msg']}"
            for e in exc.errors()
        ]
        raise ConfigurationError(
            "Invalid backend registry: " + "; ".join(errors)
        ) from None
    except (OSError, yaml.YAMLError):
        raise ConfigurationError(f"Cannot read/parse registry file: {path}") from None
