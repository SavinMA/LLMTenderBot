from mistralai import Mistral
from mistralai.extra import response_format_from_pydantic_model
from mistralai.models import OCRResponse
from typing import Any, Dict, Optional
import base64
from pydantic import BaseModel, Field, create_model
import json
from enum import Enum
from config import MistralOCRConfig

class ImageType(str, Enum):
    GRAPH = "graph"
    TEXT = "text"
    TABLE = "table"
    IMAGE = "image"

class Image(BaseModel):
    image_type: ImageType = Field(..., description="Тип изображения. Должен быть одним из 'graph', 'text', 'table' или 'image'.")
    description: str = Field(..., description="Описание изображения.")

class QueryAnswer(BaseModel):
    query: str = Field(default="", description="Question")
    answer: Optional[str] = Field(default=None, description="Answer to the question")

class Document(BaseModel):
    title: str = Field(default="", description="Title of the document")
    summary: str = Field(default="", description="Summary of the document")
    questions: list[QueryAnswer] = Field(default_factory=list, description="List of questions and answers")

class OutPageModel(BaseModel):
    page_number: int = Field(default=0, description="Page number")
    markdown: str = Field(default="", description="Markdown text")

class OutModel(BaseModel):
    document: Any = Field(default=None, description="Document or dynamic question answers")
    pages: list[OutPageModel] = Field(default_factory=list, description="List of pages")

class MistralOCR:
    def __init__(self):
        self.config = MistralOCRConfig()
        self.mistral = Mistral(api_key=self.config.api_key)

    def _encode_pdf(self, pdf_path):
        """Encode the pdf to base64."""
        try:
            with open(pdf_path, "rb") as pdf_file:
                return base64.b64encode(pdf_file.read()).decode('utf-8')
        except FileNotFoundError:
            print(f"Error: The file {pdf_path} was not found.")
            return None
        except Exception as e:  # Added general exception handling
            print(f"Error: {e}")
            return None

    def _replace_images_in_markdown_annotated(self, markdown_str: str, images_dict: dict) -> str:
        """
        Replace image placeholders in markdown with base64-encoded images and their annotation.

        Args:
            markdown_str: Markdown text containing image placeholders
            images_dict: Dictionary mapping image IDs to base64 strings

        Returns:
            Markdown text with images replaced by base64 data and their annotation
        """
        for img_name, data in images_dict.items():
            markdown_str = markdown_str.replace(
                f"![{img_name}]({img_name})", f"![{img_name}]({data['image']})\n\n**{data['annotation']}**"
            )
        return markdown_str

    def _get_combined_markdown_annotated(self, ocr_response: OCRResponse) -> list[OutPageModel]:
        """
        Combine OCR text, annotation and images into a single markdown document.

        Args:
            ocr_response: Response from OCR processing containing text and images

        Returns:
            Combined markdown string with embedded images and their annotation
        """

        markdowns: list[OutPageModel] = []
        # Extract images from page
        for page in ocr_response.pages:
            image_data = {}
            for img in page.images:
                image_data[img.id] = {"image":img.image_base64, "annotation": img.image_annotation}
            # Replace image placeholders with actual images
            markdowns.append(OutPageModel(page_number=page.index, markdown=self._replace_images_in_markdown_annotated(page.markdown, image_data)))

        return markdowns

    def ocr(self, file_path: str, questions_to_ask: Optional[list[str]] = None) -> OutModel:
        """
        Обрабатывает PDF и возвращает текст, опционально отвечая на заданные вопросы.
        """
        base64_pdf = self._encode_pdf(file_path)
        if base64_pdf is None:
            return OutModel(document=None, pages=[])

        include_images = True

        document_annotation_model: type[BaseModel]
        returned_document_data: Any = None

        if questions_to_ask:
            fields = {}
            for i, question_text in enumerate(questions_to_ask):
                field_name = f"question_{i+1}_answer"
                fields[field_name] = (Optional[str], Field(None, description=f"Answer the following question: {question_text}"))
            
            document_annotation_model = create_model("DynamicQuestionAnswers", **fields)
        else:
            document_annotation_model = Document

        ocr_response = self.mistral.ocr.process(
            model="mistral-ocr-latest",
            pages=list(range(min(8, 1000))),
            document={
                "type": "document_url",
                "document_url": f"data:application/pdf;base64,{base64_pdf}"
            },
            bbox_annotation_format=response_format_from_pydantic_model(Image),
            document_annotation_format=response_format_from_pydantic_model(document_annotation_model),
            include_image_base64=include_images
        )
        
        if ocr_response.document_annotation:
            json_doc = json.loads(ocr_response.document_annotation)
            if questions_to_ask:
                returned_document_data = json_doc
            else:
                returned_document_data = Document(**json_doc)

        pages = self._get_combined_markdown_annotated(ocr_response)

        return OutModel(document=returned_document_data, pages=pages)