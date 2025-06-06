import ollama
import os
from docling.document_converter import DocumentConverter, ConversionStatus
from documents_analyzer import DocumentsAnalyzer, AnalyzeResult
from config import LLMConfig
from ocr.mistral_ocr import MistralOCR
from prompts import Prompts  
from queries import TenderData
from splitters.semantic_splitter import SemanticSplitter
from loguru import logger
import json

class LocalLLMAnalyzer(DocumentsAnalyzer):
    def __init__(self):
        super().__init__()
        self.llm_config = LLMConfig()
        self.converter = DocumentConverter()

        self.model = self.llm_config.model
        self.host = self.llm_config.host
        self.client = ollama.Client(host=self.host, timeout=60.0)
        self._check_connection()

        self.ocr = MistralOCR()
        self.splitter = SemanticSplitter(750, 0)

    def _check_connection(self) -> bool:
        """Проверка подключения к Ollama."""
        try:
            self.client.list()
            logger.info(f"✅ Успешное подключение к Ollama на {self.host}")
            return True
        except ollama.ResponseError as e:
            error_message = f"❌ Ошибка подключения к Ollama на {self.host}: {e}"
            logger.error(error_message)
            raise Exception(error_message)

    def analyze(self, file_paths: list[str]) -> AnalyzeResult:
        file_errors = []
        summaries: list[dict[str, str]] = []
        
        for file_path in file_paths:
            try:
                summary: TenderData = self._analyze_file(file_path)
                summaries.append({"file_path": file_path, "summary": summary.model_dump_json()})
            except Exception as e:
                file_errors.append(file_path)
        
        if file_errors:
            logger.error(f"❌ Ошибки при обработке файлов: {file_errors}")

        if summaries:
            global_summary = self._summarize_global(summaries)
        else:
            global_summary = None

        return AnalyzeResult(summary=global_summary, file_errors=file_errors)

    def _analyze_file(self, file_path: str) -> TenderData:
        """Обработка документа в зависимости от типа файла"""
        file_extension = os.path.splitext(file_path)[1].lower()
        file_name = os.path.basename(file_path)

        try:
            if file_extension in ['.docx', '.txt']:
                return self._process_with_docling(file_path)
            elif file_extension == '.pdf':
                return self._process_with_mistral(file_path)
            else:
                raise ValueError(f"Неподдерживаемый тип файла: {file_extension}")
        except Exception as e:
            logger.error(f"❌ Ошибка при обработке файла {file_path}: {e}")
            raise e

    def _process_with_docling(self, file_path: str) -> TenderData:
        """Обработка документа с помощью docling"""
        logger.info(f"Processing with docling: {file_path}")
        try:
            result = self.converter.convert(file_path)
            
            if result.status != ConversionStatus.SUCCESS:
                logger.error(f"❌ Ошибка при обработке с docling: {result.status}")
                return ValueError(f"❌ Ошибка при обработке с docling: {result.status}")
            
            markdown_content = result.document.export_to_markdown()
            split_markdown_content = self.splitter.split_text(markdown_content)
            logger.info(f"chunks count: {len(split_markdown_content)}")

            tender_data_schema = TenderData.model_json_schema()
            answers: list[TenderData] = []
            
            for i, content in enumerate(split_markdown_content):
                logger.info(f"Analyzing chunk={i} with LLM. Content length: {len(content)}")
                prompt = Prompts.get_prompt_for_page_analysis_and_format_to_json()
                messages = [
                    {"role": "user", "content": f"{prompt}\n\n'Content': {content}"}
                ]
                try:
                    response = self.client.chat(
                        model=self.model,
                        messages=messages,
                        options={
                            "temperature": 0.0, 
                            "top_p": 0.9
                        },
                        format=tender_data_schema
                    )
                    parsed_data = TenderData.model_validate_json(response.message.content)
                    answers.append(parsed_data)
                    logger.debug(f"RESULT {i}: {response.message.content}")
                except Exception as e:
                    logger.error(f"❌ Ошибка при обращении к Ollama в _process_with_docling (chunk={i}): {e}")

            # Merge answers recursively
            while len(answers) > 1:
                new_answers = []
                for i in range(0, len(answers), 5):
                    batch = answers[i:i+5]
                    
                    # Prepare input for LLM summarization
                    batch_dump_json = [tender_data.model_dump_json() for tender_data in batch]
                    summary_input_json = json.dumps(batch_dump_json)

                    logger.info(f"Merging batch with LLM. Batch size: {len(batch)}")
                    prompt = Prompts.get_prompt_for_summarization(summary_input_json, "JSON")
                    messages = [
                        {"role": "user", "content": prompt}
                    ]
                    try:
                        response = self.client.chat(
                            model=self.model,
                            messages=messages,
                            options={
                                "temperature": 0.0,
                                "top_p": 0.9
                            },
                            format=tender_data_schema
                        )
                        parsed_data = TenderData.model_validate_json(response.message.content)
                        new_answers.append(parsed_data)
                        logger.debug(f"Merged batch result: {response.message.content}")
                    except Exception as e:
                        logger.error(f"❌ Ошибка при обращении к Ollama в _process_with_docling (batch merge): {e}")
                answers = new_answers

            final_tender_data = answers[0] if answers else TenderData()
            
            logger.info(f"Successfully processed with Docling: {file_path}")
            return final_tender_data

        except Exception as e:
            logger.error(f"❌ Ошибка при обработке с Docling: {e}")
            raise e
        
    def _process_with_mistral(self, file_path: str) -> TenderData:
        """Обработка документа с помощью mistral OCR"""
        logger.info(f"Processing with mistral OCR: {file_path}")
        out_model = self.ocr.ocr(file_path)
        pages = out_model.pages
        
        tender_data_schema = TenderData.model_json_schema()
        all_page_data: list[TenderData] = []
        
        for page in pages:
            logger.info(f"Analyzing page with mistral OCR.")
            prompt = Prompts.get_prompt_for_page_analysis_and_format_to_xml(json.dumps(tender_data_schema))
            messages = [
                {"role": "user", "content": f"{prompt}\n\n'Content': {page.markdown}"}
            ]
            try:
                response = self.client.chat(
                    model=self.model,
                    messages=messages,
                    options={
                        "temperature": 0.0, 
                        "top_p": 0.9
                    },
                    format=tender_data_schema,
                    response_format={"type": "json"}
                )
                tender_data = TenderData.model_validate_json(response.message.content)
                all_page_data.append(tender_data)
            except Exception as e:
                logger.error(f"❌ Ошибка при обращении к Ollama в _process_with_mistral (page analysis): {e}")
        
        # Merge all page data into a single TenderData object
        final_tender_data = TenderData()
        for tender_data_chunk in all_page_data:
            for field_name, value in tender_data_chunk.model_dump().items():
                if value and getattr(final_tender_data, field_name) == "":
                    setattr(final_tender_data, field_name, value)
            
        logger.info(f"Successfully processed with mistral OCR: {file_path}")
        return final_tender_data

    def _summarize_global(self, summaries: list[dict[str, str]]) -> str:
        logger.info("Starting global summarization.")

        # Parse and merge all TenderData objects
        final_tender_data = TenderData()
        for item in summaries:
            try:
                current_tender_data = TenderData.model_validate_json(item["summary"])
                for field_name, value in current_tender_data.model_dump().items():
                    if value and getattr(final_tender_data, field_name) == "":
                        setattr(final_tender_data, field_name, value)
            except Exception as e:
                logger.error(f"❌ Ошибка при парсинге TenderData из {item.get('file_path', 'unknown file')}: {e}")
                # Optionally, you might want to skip this item or handle it differently
                continue
        
        summary_input_json = final_tender_data.model_dump_json()

        logger.debug(f"Summary input JSON: {summary_input_json}")
        # First LLM call for global summary
        logger.info("Calling LLM for global summary.")
        summary_result_prompt = Prompts.get_prompt_for_summarization(summary_input_json, "JSON")
        messages_global_summary = [
            {"role": "user", "content": summary_result_prompt}
        ]
        try:
            response_global_summary = self.client.chat(
                model=self.model,
                messages=messages_global_summary,
                options={
                    "temperature": 0.0,
                    "top_p": 0.9
                }
            )
            global_summary_content = response_global_summary.message.content
            logger.info("Global summary generated.")
            logger.debug(f"Global summary content: {global_summary_content}")
        except Exception as e:
            logger.error(f"❌ Ошибка при обращении к Ollama при генерации глобального суммирования: {e}")
            return ""

        # Second LLM call for Telegram style summarization
        logger.info("Calling LLM for Telegram style summarization.")
        telegram_prompt = Prompts.get_prompt_for_telegram_message(global_summary_content, "JSON")
        messages_telegram = [
            {"role": "user", "content": telegram_prompt}
        ]
        try:
            response_telegram = self.client.chat(
                model=self.model,
                messages=messages_telegram,
                options={
                    "temperature": 0.0,
                    "top_p": 0.9
                }
            )
            telegram_summary_content = response_telegram.message.content
            logger.info("Telegram style summary generated.")
        except ollama.ResponseError as e:
            logger.error(f"❌ Ошибка при обращении к Ollama при генерации Telegram-стиля суммирования: {e}")
            return ""

        return telegram_summary_content
        