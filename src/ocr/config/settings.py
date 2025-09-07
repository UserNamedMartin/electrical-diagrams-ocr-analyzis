from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, Field, field_validator
from pathlib import Path

class Settings(BaseSettings):
    model: str
    api_key: SecretStr
    pdf_path: Path
    temperature: float = Field(1.0, ge=0.0, le=2.0)
    dpi: int = Field(400, gt=0)
    batch_size: int = Field(3, ge=1)
    output_dir: Path = Path("runs/")

    model_config = SettingsConfigDict(
        env_file=".env"
    )

    @field_validator("pdf_path")
    @classmethod
    def validate_pdf_path(cls, pdf_path: Path) -> Path:
        if not pdf_path.exists(): 
            raise ValueError(f"PDF path does not exist: {pdf_path}")
        if not pdf_path.is_file():
            raise ValueError(f"PDF path is not a file: {pdf_path}")
        if pdf_path.suffix.lower() != ".pdf":
            raise ValueError(f"Expected .pdf file, not {pdf_path.suffix}")
        return pdf_path
    
    @field_validator("output_dir")
    @classmethod
    def validate_output_dir(csl, output_dir: Path) -> Path:
        if not output_dir.exists():
            raise ValueError(f"Output directory does not exist: {output_dir}")
        if not output_dir.is_dir():
            raise ValueError(f"Output directory is not a directory: {output_dir}")
        return output_dir
