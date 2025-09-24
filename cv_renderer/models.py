"""
Pydantic models for CV data validation.

This module defines validation models for different field types and the complete CV data structure.
"""

from typing import Dict, List, Optional, Union, Any
from pydantic import (
    BaseModel,
    EmailStr,
    HttpUrl,
    Field,
    field_validator,
    BeforeValidator,
    model_validator,
)
from typing_extensions import Annotated
import re
import mistune


def strip_str(v: str) -> str:
    """Strip whitespace from string values."""
    if isinstance(v, str):
        return v.strip()
    return v


# Type alias for string fields that need stripping and validation
StrippedStr = Annotated[str, BeforeValidator(strip_str)]


class MarkdownText(BaseModel):
    """Model for markdown text with AST validation."""

    text: StrippedStr = Field(..., min_length=1, description="Raw markdown text")
    ast: List[Dict[str, Any]] = Field(
        default_factory=list, description="Parsed AST representation"
    )

    def __init__(self, **data):
        """Initialize MarkdownText with AST parsing."""
        # If only text is provided, parse it into AST
        if "text" in data and "ast" not in data:
            text = data["text"]
            if isinstance(text, str) and text.strip():
                # Create markdown parser with AST renderer
                markdown_parser = mistune.create_markdown(renderer="ast")
                data["ast"] = markdown_parser(text.strip())
            else:
                data["ast"] = []

        super().__init__(**data)

    @field_validator("ast")
    @classmethod
    def validate_supported_markup(cls, v: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate that AST only contains supported markdown markup."""
        if not v:
            return v

        # Define supported token types based on what our renderers can handle
        supported_token_types = {
            "paragraph",
            "text",
            "strong",
            "linebreak",
            "softbreak",
        }

        def check_tokens(tokens: List[Dict[str, Any]], path: str = "root") -> None:
            """Recursively check all tokens for unsupported types."""
            for i, token in enumerate(tokens):
                if not isinstance(token, dict):
                    continue

                token_type = token.get("type")
                if token_type and token_type not in supported_token_types:
                    raise ValueError(
                        f"Unsupported markdown markup '{token_type}' found at {path}[{i}]. "
                        f"Supported markup: {', '.join(sorted(supported_token_types))}"
                    )

                # Recursively check children
                if "children" in token and isinstance(token["children"], list):
                    check_tokens(token["children"], f"{path}[{i}].children")

        check_tokens(v)
        return v

    @model_validator(mode="before")
    @classmethod
    def convert_string_to_markdown_text(cls, data):
        """Convert string inputs to MarkdownText objects automatically."""
        if isinstance(data, str):
            # Convert string input to expected dictionary format
            text = data.strip()
            if text:
                # Create markdown parser with AST renderer
                markdown_parser = mistune.create_markdown(renderer="ast")
                ast = markdown_parser(text)
                return {"text": text, "ast": ast}
            else:
                return {"text": text, "ast": []}
        return data


class Name(BaseModel):
    """Model for person's name."""

    first: StrippedStr = Field(..., min_length=1, max_length=50)
    last: StrippedStr = Field(..., min_length=1, max_length=50)


class Link(BaseModel):
    """Model for a URL link with optional display name."""

    url: HttpUrl = Field(..., description="Full URL starting with http:// or https://")
    display_name: Optional[str] = Field(None, description="Display name for the link")

    def __init__(self, **data):
        """Initialize Link with auto-generated display_name if not provided."""
        super().__init__(**data)
        if self.display_name is None:
            url_str = str(self.url)
            # Remove https:// or http:// prefix
            if url_str.startswith("https://"):
                self.display_name = url_str[8:]  # Remove 'https://'
            elif url_str.startswith("http://"):
                self.display_name = url_str[7:]  # Remove 'http://'
            else:
                self.display_name = url_str


class Contact(BaseModel):
    """Model for contact information."""

    email: EmailStr
    linkedin: Optional[Link] = Field(None, description="LinkedIn profile URL")
    telegram: Optional[Link] = Field(None, description="Telegram profile URL")
    github: Optional[Link] = Field(None, description="GitHub profile URL")


class Personal(BaseModel):
    """Model for personal information."""

    name: Name
    title: StrippedStr = Field(..., min_length=1, max_length=50)
    summary: MarkdownText = Field(
        ..., description="Personal summary with markdown support"
    )
    location: StrippedStr = Field(..., min_length=1, max_length=50)
    contact: Contact


class Language(BaseModel):
    """Model for language proficiency."""

    language: StrippedStr = Field(..., min_length=1, max_length=50)
    level: StrippedStr = Field(..., min_length=1, max_length=50)


class GPA(BaseModel):
    """Model for GPA information."""

    cumulative: StrippedStr = Field(..., min_length=1, max_length=20)
    major: StrippedStr = Field(..., min_length=1, max_length=20)


class Education(BaseModel):
    """Model for education entry."""

    institution: StrippedStr = Field(..., min_length=1, max_length=50)
    degree: StrippedStr = Field(..., min_length=1, max_length=50)
    period: StrippedStr = Field(..., min_length=1, max_length=200)
    location: StrippedStr = Field(..., min_length=1, max_length=50)
    specialization: StrippedStr = Field(..., min_length=1, max_length=50)
    focus: StrippedStr = Field(..., min_length=1, max_length=50)
    gpa: GPA


class Experience(BaseModel):
    """Model for work experience entry."""

    company: StrippedStr = Field(..., min_length=1, max_length=50)
    position: StrippedStr = Field(..., min_length=1, max_length=50)
    period: StrippedStr = Field(..., min_length=1, max_length=50)
    location: StrippedStr = Field(..., min_length=1, max_length=50)
    description: MarkdownText = Field(
        ..., description="Job description with markdown support"
    )
    achievements: List[MarkdownText] = Field(
        ..., min_length=1, description="List of achievements with markdown support"
    )
    stack: StrippedStr = Field(..., min_length=1, max_length=200)

    @field_validator("achievements")
    @classmethod
    def validate_achievements(cls, v: List[MarkdownText]) -> List[MarkdownText]:
        """Validate achievements list."""
        if not v:
            raise ValueError("Achievements list cannot be empty")
        return v


class Metadata(BaseModel):
    """Model for PDF metadata."""

    pdf_title: StrippedStr = Field(..., min_length=1, max_length=50)
    pdf_author: StrippedStr = Field(..., min_length=1, max_length=50)
    pdf_subject: StrippedStr = Field(..., min_length=1, max_length=50)
    pdf_keywords: StrippedStr = Field(..., min_length=1, max_length=100)
    pdf_filename: StrippedStr = Field(..., min_length=1, max_length=50)
    url: HttpUrl = Field(..., description="Full URL starting with http:// or https://")
    app_name: StrippedStr = Field(..., min_length=1, max_length=20)


class SkillCategory(BaseModel):
    """Model for a skill category with its associated skills."""

    category: StrippedStr = Field(..., min_length=1, max_length=50)
    skills: List[StrippedStr] = Field(..., min_length=1)

    @field_validator("skills")
    @classmethod
    def validate_skills(cls, v: List[str]) -> List[str]:
        """Validate skills list."""
        if not v:
            raise ValueError("Skills list cannot be empty")

        # Additional validation to ensure no empty skills after stripping
        for skill in v:
            if not skill:  # This will catch empty strings after stripping
                raise ValueError("Individual skill cannot be empty")

        return v


class CVData(BaseModel):
    """Root model for complete CV data validation."""

    personal: Personal
    skills: List[SkillCategory] = Field(..., min_length=1)
    languages: List[Language] = Field(..., min_length=1)
    education: List[Education] = Field(..., min_length=1)
    experience: List[Experience] = Field(..., min_length=1)
    metadata: Metadata
