import os
from documents_analyzer import DocumentsAnalyzer, AnalyzeResult
from config import MistralConfig
from ocr.mistral_ocr import MistralOCR
from prompts import Prompts
from queries import TenderData
from loguru import logger
import json
from mistralai import Mistral
from mistralai.models import File

class MistralAnalyzer(DocumentsAnalyzer):
    def __init__(self):
        super().__init__()
        self.llm_config = MistralConfig()

        self.model = self.llm_config.model
        self.client = Mistral(api_key=self.llm_config.api_key, timeout_ms=60000)
        self._check_api_key()

        self.ocr = MistralOCR()

    def _check_api_key(self) -> bool:
        """Проверка наличия API ключа Mistral."""
        if not self.llm_config.api_key:
            error_message = "❌ API ключ Mistral не найден. Установите переменную окружения MISTRAL_API_KEY."
            logger.error(error_message)
            raise Exception(error_message)
        logger.info("✅ API ключ Mistral найден.")
        return True

    def analyze(self, file_paths: list[str]) -> AnalyzeResult:
        file_errors = []
        summaries: list[TenderData] = []
        
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            try:
                summary: TenderData = self._analyze_file(file_path)
                summaries.append(summary)
            except Exception as e:
                file_errors.append(file_name)
        
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

        try:
            if file_extension in ['.docx', '.txt', '.pdf', '.doc']:
                return self._process_with_upload_file_and_chat(file_path)
            else:
                raise ValueError(f"Неподдерживаемый тип файла: {file_extension}")
        except Exception as e:
            logger.error(f"❌ Ошибка при обработке файла {file_path}: {e}")
            raise e
        
    def _process_with_upload_file_and_chat(self, file_path: str) -> TenderData:
        """Загрузка файла в Mistral и получение ответа от чата"""
        logger.info(f"Processing with upload file and chat: {file_path}")
        file_id = None
        try:
            file_name = os.path.basename(file_path)

            with open(file_path, 'rb') as file:
                file_content = file.read()

            response = self.client.files.upload(
                file=File(
                    file_name=file_name,
                    content=file_content
                ),
                purpose="ocr"
            )
            file_id = response.id
            logger.debug(response)

            signed_url = self.client.files.get_signed_url(file_id=file_id)
            logger.debug(signed_url)

            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Ответь на вопросы по документу"
                        },
                        {
                            "type": "document_url",
                            "document_url": signed_url.url
                        }
                    ]
                }
            ]

            response = self.client.chat.parse(
                model=self.model,
                messages=messages,
                temperature=0.0,
                response_format=TenderData
            )
            logger.debug(response)
            return response.choices[0].message.parsed
        except Exception as e:
            logger.error(f"❌ Ошибка при обращении к Mistral API в _process_with_upload_file_and_chat: {e}")
            raise e
        finally:    
            if file_id:
                self.client.files.delete(file_id=file_id)

    def _summarize_global(self, summaries: list[TenderData]) -> str:
        logger.info("Starting global summarization.")

        # Parse and merge all TenderData objects
        if len(summaries) > 1:
            jsons = [tender_data.model_dump_json() for tender_data in summaries]
            summary_input_json = json.dumps(jsons)
        
            logger.debug(f"Summary input JSON: {summary_input_json}")
            # First LLM call for global summary
            logger.info("Calling LLM for global summary.")
            summary_result_prompt = Prompts.get_prompt_for_summarization(summary_input_json, "JSON")
            messages_global_summary = [
                {"role": "user", "content": summary_result_prompt}
            ]
            try:
                response_global_summary = self.client.chat.parse(
                    model=self.model,
                    messages=messages_global_summary,
                    temperature=0.0,
                    response_format=TenderData
                )
                global_summary_content = response_global_summary.choices[0].message.parsed
                logger.info("Global summary generated.")
                logger.debug(f"Global summary content: {global_summary_content}")
            except Exception as e:
                logger.error(f"❌ Ошибка при обращении к Mistral API при генерации глобального суммирования: {e}")
                return ""
        else:
            global_summary_content = summaries[0]

        telegram_markdown_content = self._create_telegram_message(global_summary_content)
        
        return telegram_markdown_content
    
    def _create_telegram_message(self, global_summary_content: TenderData) -> str:
        """Создание Telegram сообщения"""
        message_parts = []

        if global_summary_content.procurement_name:
            message_parts.append(f"📦 *Наименование закупки*: {global_summary_content.procurement_name}")
        if global_summary_content.customer_info_company_name:
            message_parts.append(f"🏢 *Заказчик*: {global_summary_content.customer_info_company_name}")
        if global_summary_content.notice_number:
            message_parts.append(f"📄 *Номер извещения*: {global_summary_content.notice_number}")
        if global_summary_content.publication_and_submission_deadline:
            message_parts.append(f"🗓️ *Срок подачи заявок*: {global_summary_content.publication_and_submission_deadline}")
        if global_summary_content.lots:
            lots_info = []
            for i, lot in enumerate(global_summary_content.lots):
                lot_details = []
                if lot.name:
                    lot_details.append(f"Наименование: {lot.name}")
                if lot.initial_max_price:
                    lot_details.append(f"Начальная максимальная цена: {lot.initial_max_price}")
                if lot.currency:
                    lot_details.append(f"Валюта: {lot.currency}")
                if lot.quantity:
                    lot_details.append(f"Количество: {lot.quantity}")
                if lot_details:
                    lots_info.append(f"Лот {i+1}:
  - " + "\n  - ".join(lot_details))
            if lots_info:
                message_parts.append(f"🏷️ *Информация о лотах*:
" + "\n".join(lots_info))
        if global_summary_content.delivery_department:
            message_parts.append(f"🚚 *Подразделение поставки*: {global_summary_content.delivery_department}")
        if global_summary_content.initial_max_price_with_vat:
            message_parts.append(f"💰 *Начальная максимальная цена (с НДС)*: {global_summary_content.initial_max_price_with_vat}")
        if global_summary_content.contact_persons:
            contact_persons_info = []
            for person in global_summary_content.contact_persons:
                person_details = []
                if person.full_name:
                    person_details.append(f"ФИО: {person.full_name}")
                if person.phone_number:
                    person_details.append(f"📞 Телефон: {person.phone_number}")
                if person.email:
                    person_details.append(f"📧 Email: {person.email}")
                if person.position:
                    person_details.append(f"💼 Должность: {person.position}")
                if person_details:
                    contact_persons_info.append("  - " + "\n    - ".join(person_details))
            if contact_persons_info:
                message_parts.append(f"👤 *Контактные лица*:
" + "\n".join(contact_persons_info))
        if global_summary_content.application_security:
            message_parts.append(f"🔐 *Обеспечение заявки*: {global_summary_content.application_security}")
        if global_summary_content.re_bidding_date:
            message_parts.append(f"🔄 *Дата переторжки*: {global_summary_content.re_bidding_date}")
        if global_summary_content.etp_platform:
            message_parts.append(f"🌐 *ЭТП*: {global_summary_content.etp_platform}")
        if global_summary_content.application_review_deadline:
            message_parts.append(f"📅 *Срок рассмотрения заявок*: {global_summary_content.application_review_deadline}")
        if global_summary_content.results_summary_date:
            message_parts.append(f"📊 *Дата подведения итогов*: {global_summary_content.results_summary_date}")
        if global_summary_content.contract_security:
            message_parts.append(f"📜 *Обеспечение договора*: {global_summary_content.contract_security}")
        if global_summary_content.participation_price:
            message_parts.append(f"💲 *Цена участия*: {global_summary_content.participation_price}")
        if global_summary_content.warranty_requirements:
            message_parts.append(f"🛠️ *Гарантийные требования*: {global_summary_content.warranty_requirements}")
        if global_summary_content.required_delivery_period:
            message_parts.append(f"⏱️ *Срок поставки*: {global_summary_content.required_delivery_period}")
        if global_summary_content.payment_terms:
            message_parts.append(f"💳 *Условия оплаты*: {global_summary_content.payment_terms}")
        if global_summary_content.delivery_documents_names:
            message_parts.append(f"📄 *Документы для поставки*: {global_summary_content.delivery_documents_names}")
        if global_summary_content.delivery_method:
            message_parts.append(f"📦 *Метод доставки*: {global_summary_content.delivery_method}")
        if global_summary_content.product_dimensions:
            message_parts.append(f"📏 *Размеры товара*: {global_summary_content.product_dimensions}")
        if global_summary_content.product_purpose:
            message_parts.append(f"🎯 *Назначение товара*: {global_summary_content.product_purpose}")
        if global_summary_content.contract_term:
            message_parts.append(f"🗓️ *Срок действия договора*: {global_summary_content.contract_term}")
        if global_summary_content.delivery_address:
            message_parts.append(f"📍 *Адрес доставки*: {global_summary_content.delivery_address}")
        
        telegram_markdown_content = "\n\n".join(message_parts)
        return telegram_markdown_content
        
        
        