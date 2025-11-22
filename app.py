import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image
import io

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# API Keys (Replace with your actual keys)
TELEGRAM_BOT_TOKEN = "8217382418:AAFA6l0qynU5fyQZv2QLagkF7ZijVOgoxPY"
REMOVE_BG_API_KEY = "cZx8tKGnMu1FVaFGVDdbNDQ6"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
    welcome_text = """
🤖 Welcome to Background Remover Bot!

Send me any image and I'll remove the background for you!

Features:
• Remove background from photos
• Support for PNG, JPG, JPEG formats
• High-quality background removal

Just send me an image and I'll do the magic! ✨
    """
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message when the command /help is issued."""
    help_text = """
📖 How to use this bot:

1. Send any image (PNG, JPG, JPEG)
2. Wait a few seconds while I process it
3. Receive the image with background removed

Commands:
/start - Start the bot
/help - Show this help message

Note: For best results, use images with clear subjects and good contrast.
    """
    await update.message.reply_text(help_text)

async def remove_background(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove background from the received image."""
    try:
        # Send "processing" message
        processing_msg = await update.message.reply_text("🔄 Processing your image... Please wait!")
        
        # Get the photo file
        photo_file = await update.message.photo[-1].get_file()
        
        # Download the photo
        photo_bytes = await photo_file.download_as_bytearray()
        
        # Remove background using remove.bg API
        response = requests.post(
            'https://api.remove.bg/v1.0/removebg',
            files={'image_file': photo_bytes},
            data={'size': 'auto'},
            headers={'X-Api-Key': REMOVE_BG_API_KEY},
        )
        
        if response.status_code == 200:
            # Convert response to image
            processed_image = Image.open(io.BytesIO(response.content))
            
            # Convert to bytes for sending
            output_buffer = io.BytesIO()
            processed_image.save(output_buffer, format='PNG')
            output_buffer.seek(0)
            
            # Send the processed image
            await update.message.reply_photo(
                photo=output_buffer,
                caption="✅ Background removed successfully!"
            )
            
            # Delete processing message
            await processing_msg.delete()
            
        else:
            error_msg = f"❌ Error: {response.status_code} - {response.text}"
            await update.message.reply_text(error_msg)
            await processing_msg.delete()
            
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        error_msg = "❌ Sorry, I couldn't process your image. Please try again with a different image."
        await update.message.reply_text(error_msg)
        try:
            await processing_msg.delete()
        except:
            pass

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle images sent as documents."""
    try:
        document = update.message.document
        
        # Check if it's an image file
        if document.mime_type and document.mime_type.startswith('image/'):
            # Send "processing" message
            processing_msg = await update.message.reply_text("🔄 Processing your image... Please wait!")
            
            # Get the document file
            file = await document.get_file()
            
            # Download the file
            file_bytes = await file.download_as_bytearray()
            
            # Remove background using remove.bg API
            response = requests.post(
                'https://api.remove.bg/v1.0/removebg',
                files={'image_file': file_bytes},
                data={'size': 'auto'},
                headers={'X-Api-Key': REMOVE_BG_API_KEY},
            )
            
            if response.status_code == 200:
                # Convert response to image
                processed_image = Image.open(io.BytesIO(response.content))
                
                # Convert to bytes for sending
                output_buffer = io.BytesIO()
                processed_image.save(output_buffer, format='PNG')
                output_buffer.seek(0)
                
                # Send the processed image
                await update.message.reply_photo(
                    photo=output_buffer,
                    caption="✅ Background removed successfully!"
                )
                
                # Delete processing message
                await processing_msg.delete()
                
            else:
                error_msg = f"❌ Error: {response.status_code} - {response.text}"
                await update.message.reply_text(error_msg)
                await processing_msg.delete()
        else:
            await update.message.reply_text("❌ Please send an image file (PNG, JPG, JPEG)")
            
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        await update.message.reply_text("❌ Sorry, I couldn't process your file. Please try again with an image.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors and handle them gracefully."""
    logger.error(f"Exception while handling an update: {context.error}")
    
    try:
        await update.message.reply_text("❌ An error occurred. Please try again later.")
    except:
        pass

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.PHOTO, remove_background))
    application.add_handler(MessageHandler(filters.Document.IMAGE, handle_document))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start the Bot
    print("🤖 Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()