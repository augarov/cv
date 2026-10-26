"""Website configuration model."""

from typing import Any
from urllib.parse import urljoin, urlparse

from pydantic import BaseModel, ConfigDict, HttpUrl, ValidationInfo, model_validator
from rendercv.schema.models.cv.cv import Cv


class Website(BaseModel):
    """Website-specific metadata not covered by the rendercv schema.

    Only ``url`` is required. The other fields default to values derived from
    ``url`` and from the CV, which is passed in the validation context:
    ``Website.model_validate(data, context={"cv": cv})``.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    url: HttpUrl
    pdf_url: HttpUrl
    source_url: HttpUrl | None = None
    title: str
    author: str
    app_name: str
    keywords: str | None = None
    locale: str | None = None
    pdf_filename: str | None = None

    @model_validator(mode="before")
    @classmethod
    def fill_defaults(cls, data: Any, info: ValidationInfo) -> Any:
        """Normalize ``url`` and fill the fields left out of the file."""
        if not isinstance(data, dict):
            return data
        data = dict(data)

        url = data.get("url")
        if isinstance(url, str) and urlparse(url).netloc:
            if not url.endswith("/"):
                url += "/"
            data["url"] = url
            data.setdefault("pdf_url", urljoin(url, "cv.pdf"))

        cv = (info.context or {}).get("cv")
        if isinstance(cv, Cv) and cv.name:
            title = f"{cv.name} – {cv.headline}" if cv.headline else cv.name
            data.setdefault("title", title)
            data.setdefault("author", cv.name)
            data.setdefault("app_name", cv.name)

        return data
