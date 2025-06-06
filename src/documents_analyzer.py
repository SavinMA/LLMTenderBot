from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Optional

class AnalyzeResult(BaseModel):
    summary: Optional[str] = None # Сводка по всем файлам
    file_errors: Optional[list[str]] = None # Список файлов, которые не удалось обработать

class DocumentsAnalyzer(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def analyze(self, file_paths: list[str]) -> AnalyzeResult:
        pass

