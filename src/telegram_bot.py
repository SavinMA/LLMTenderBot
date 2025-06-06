import os
import sys
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from collections import defaultdict
import asyncio
from pydantic import BaseModel, Field
import tempfile
import pathlib
from config import BotConfig
from local_LLM_analyzer import LocalLLMAnalyzer
from loguru import logger

# Load environment variables from .env file
load_dotenv()

# Configure Loguru
logger.add("logs/bot.log", rotation="500 MB", compression="zip", level="INFO")
logger.add("logs/bot_debug.log", level="DEBUG")

class DocumentInfo(BaseModel):
    file_id: str
    file_name: str
    chat_id: int

class UserSession(BaseModel):
    # Key: media_group_id, Value: List of DocumentInfo
    media_group_documents: defaultdict[str, list[DocumentInfo]] = Field(default_factory=lambda: defaultdict(list))
    # Key: media_group_id, Value: asyncio.Task
    # Note: asyncio.Task cannot be directly serialized by Pydantic. 
    # We'll manage this outside of direct Pydantic validation if strict serialization is needed.
    media_group_timers: dict[str, any] = Field(default_factory=dict)

class TelegramBot:
    def __init__(self):
        self.config = BotConfig()
        self.user_sessions: defaultdict[int, UserSession] = defaultdict(UserSession)
        self.analyzer = LocalLLMAnalyzer()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Отправляет приветственное сообщение при вызове команды /start."""
        await update.message.reply_text("Привет! Отправьте мне документы для суммаризации.")

    async def summarize_files(self, file_info_list: list[DocumentInfo], context: ContextTypes.DEFAULT_TYPE) -> str:
        """Заглушка для суммаризации нескольких документов. Будет заменена на реальную суммаризацию."""
        downloaded_file_paths = []
        for doc_info in file_info_list:
            try:
                file_object = await context.bot.get_file(doc_info.file_id)
                with tempfile.TemporaryDirectory(delete=False) as tmpdir:
                    temp_file_path = pathlib.Path(tmpdir) / doc_info.file_name
                    await file_object.download_to_drive(custom_path=temp_file_path)
                    logger.info(f"Downloaded file {doc_info.file_name} to {temp_file_path}")
                    downloaded_file_paths.append(str(temp_file_path))
            except Exception as e:
                logger.error(f"Error downloading file {doc_info.file_name} (ID: {doc_info.file_id}): {e}")
                # Если файл не скачался, добавляем его в список ошибок и продолжаем
                pass 
        
        if downloaded_file_paths:
            analyze_result = self.analyzer.analyze(downloaded_file_paths)
            if analyze_result.file_errors:
                if analyze_result.summary:
                    error_files_str = ", ".join(analyze_result.file_errors)
                    return f"Частичная суммаризация. Ошибки при обработке файлов: {error_files_str}.\n\n{analyze_result.summary}"
                else:
                    error_files_str = ", ".join(analyze_result.file_errors)
                    return f"Ошибки при обработке файлов: {error_files_str}."
            else:
                return analyze_result.summary
        else:
            return "Не удалось скачать ни один файл для суммаризации."

    async def process_media_group(self, context: ContextTypes.DEFAULT_TYPE, user_id: int, media_group_id: str, chat_id: int) -> None:
        """Обрабатывает медиа-группу после получения всех документов для конкретного пользователя."""
        logger.info(f"Processing media group: {media_group_id} for user: {user_id}")
        user_session = self.user_sessions[user_id]
        files_to_summarize = user_session.media_group_documents.pop(media_group_id, [])
        
        if files_to_summarize:
            summary = await self.summarize_files(files_to_summarize, context)
            await context.bot.send_message(chat_id=chat_id, text=f"Готово!\n\n{summary}", parse_mode="MarkdownV2")
        
        # Clear the timer for this media group for this user
        if media_group_id in user_session.media_group_timers:
            user_session.media_group_timers.pop(media_group_id).cancel()

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает входящие сообщения, проверяя наличие документов для суммаризации."""
        if not update.effective_user or not update.effective_user.id:
            logger.warning("Could not get user ID from update.")
            await update.message.reply_text("Не удалось определить вашего пользователя. Пожалуйста, попробуйте еще раз.")
            return

        user_id = update.effective_user.id
        user_session = self.user_sessions[user_id]

        if update.message.document:
            file_id = update.message.document.file_id
            file_name = update.message.document.file_name
            chat_id = update.message.chat_id

            doc_info = DocumentInfo(file_id=file_id, file_name=file_name, chat_id=chat_id)

            if update.message.media_group_id:
                media_group_id = update.message.media_group_id
                logger.info(f"Получен документ в медиа-группе: {file_name} (ID: {file_id}), Группа: {media_group_id}, Пользователь: {user_id}")
                user_session.media_group_documents[media_group_id].append(doc_info)

                # Cancel any existing timer for this media group for this user
                if media_group_id in user_session.media_group_timers:
                    user_session.media_group_timers.pop(media_group_id).cancel()
                
                # Start a new timer to process the media group after a short delay
                # This delay allows all parts of the media group to arrive
                user_session.media_group_timers[media_group_id] = asyncio.create_task(
                    asyncio.sleep(1.5) # Adjust delay as needed
                )
                user_session.media_group_timers[media_group_id].add_done_callback(
                    lambda t: asyncio.create_task(self.process_media_group(context, user_id, media_group_id, chat_id))
                )

            else:
                # Single document, process immediately
                logger.info(f"Получен одиночный документ: {file_name} (ID: {file_id}), Пользователь: {user_id}")
                await update.message.reply_text(f"Обрабатываю ваш документ: {file_name}...")
                summary = await self.summarize_files([doc_info], context)
                await update.message.reply_text(f"Краткое содержание для {file_name}:\n\n{summary}")
        else:
            await update.message.reply_text("Я обрабатываю только документы. Пожалуйста, отправьте мне файл!")

    def run_bot(self) -> None:
        """Запускает бота."""
        try:
            bot_config = self.config
        except Exception as e:
            logger.error(f"Ошибка при загрузке конфигурации бота: {e}")
            logger.error("Убедитесь, что переменная окружения BOT_TOKEN установлена в файле .env")
            return

        application = Application.builder().token(bot_config.bot_token).build()

        # Register handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(MessageHandler(filters.Document.ALL | (filters.TEXT & ~filters.COMMAND), self.handle_message))

        # Run the bot until the user presses Ctrl-C
        logger.info("Бот запущен. Нажмите Ctrl-C, чтобы остановить.")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

def main():
    """Главная точка входа для запуска бота."""
    TelegramBot().run_bot()

if __name__ == "__main__":
    main() 