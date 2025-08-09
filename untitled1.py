import os
import logging
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from pytube import YouTube
from io import BytesIO

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token from BotFather
TOKEN = "8493867699:AAH7wiNu3qyzcsvLhEAqX4RoP7ElG5ZY9Ec"

def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    update.message.reply_text(
        'Hi! Send me a text file containing YouTube links (one per line) '
        'and I will download them as MP3 files for you.'
    )

def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text(
        'Send me a text file with YouTube links (one per line) to get MP3 files. '
        'You can also send individual YouTube links directly.'
    )

def download_audio(url: str) -> BytesIO:
    """Download YouTube audio and return as BytesIO object."""
    try:
        yt = YouTube(url)
        audio_stream = yt.streams.filter(only_audio=True).first()
        
        if not audio_stream:
            raise Exception("No audio stream found")
            
        buffer = BytesIO()
        audio_stream.stream_to_buffer(buffer)
        buffer.seek(0)
        return buffer, yt.title
    except Exception as e:
        logger.error(f"Error downloading {url}: {e}")
        raise

def handle_text_file(update: Update, context: CallbackContext) -> None:
    """Handle the received text file with YouTube links."""
    if not update.message.document:
        return
        
    if not update.message.document.mime_type == 'text/plain':
        update.message.reply_text("Please send a text file (.txt)")
        return
    
    # Download the file
    file = context.bot.get_file(update.message.document.file_id)
    file_path = f"temp_{update.message.message_id}.txt"
    file.download(file_path)
    
    # Read links from file
    with open(file_path, 'r') as f:
        links = [line.strip() for line in f.readlines() if line.strip()]
    
    # Clean up
    os.remove(file_path)
    
    if not links:
        update.message.reply_text("No valid links found in the file.")
        return
    
    update.message.reply_text(f"Found {len(links)} links. Starting download...")
    
    # Process each link
    for i, url in enumerate(links, 1):
        try:
            update.message.reply_text(f"Processing {i}/{len(links)}: {url}")
            audio_buffer, title = download_audio(url)
            
            # Send the audio file
            context.bot.send_audio(
                chat_id=update.effective_chat.id,
                audio=InputFile(audio_buffer, filename=f"{title}.mp3"),
                title=title
            )
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
            update.message.reply_text(f"Failed to process {url}: {str(e)}")

def handle_text_message(update: Update, context: CallbackContext) -> None:
    """Handle text messages that might contain YouTube links."""
    text = update.message.text
    if "youtube.com" in text or "youtu.be" in text:
        try:
            update.message.reply_text("Downloading audio...")
            audio_buffer, title = download_audio(text)
            
            context.bot.send_audio(
                chat_id=update.effective_chat.id,
                audio=InputFile(audio_buffer, filename=f"{title}.mp3"),
                title=title
            )
        except Exception as e:
            logger.error(f"Error processing {text}: {e}")
            update.message.reply_text(f"Failed to process the link: {str(e)}")
    else:
        update.message.reply_text("Please send a YouTube link or a text file with YouTube links.")

def main() -> None:
    """Start the bot."""
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(MessageHandler(Filters.document, handle_text_file))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
