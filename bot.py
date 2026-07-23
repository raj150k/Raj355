import re, os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from config import config
from downloader import detect_platform, download_media, get_file_size as dl_size, clean_up as dl_clean
from converter import convert_media, get_file_size as conv_size, clean_up as conv_clean

def menu():
    kb = []
    plist = list(config.PLATFORMS.items())
    for i in range(0, len(plist), 3):
        row = [InlineKeyboardButton(f"{v}", callback_data=f"p:{k}") for k, v in plist[i:i+3]]
        kb.append(row)
    clist = list(config.CONVERSIONS.items())
    for i in range(0, len(clist), 2):
        row = [InlineKeyboardButton(f"{v}", callback_data=f"c:{k}") for k, v in clist[i:i+2]]
        kb.append(row)
    kb.append([InlineKeyboardButton("Help", callback_data="help"), InlineKeyboardButton("About", callback_data="about")])
    return InlineKeyboardMarkup(kb)

async def start(upd: Update, ctx: ContextTypes.DEFAULT_TYPE):
    name = upd.effective_user.first_name or "User"
    txt = (
        f"All Link Download Bot\n\n"
        f"Welcome {name}!\n"
        f"Owner: @{config.OWNER_USERNAME}\n\n"
        f"How to Use:\n"
        f"Send any link (TikTok, Reddit, Dailymotion, etc.)\n"
        f"I will download it for you!\n\n"
        f"Also supports media conversion (MP4 to MP3, GIF, etc.)\n\n"
        f"Send a link or choose an option:"
    )
    await upd.message.reply_text(txt, reply_markup=menu())

async def help_cmd(upd: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await upd.message.reply_text("Send a link to download. Send a media file to convert. Tap buttons below.", reply_markup=menu())

async def about_cmd(upd: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await upd.message.reply_text(f"All Link Download Bot v2.0\nDeveloper: @{config.OWNER_USERNAME}", reply_markup=menu())

async def handle_msg(upd: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if upd.message and upd.message.text:
        url = upd.message.text.strip()
        if not re.match(r"https?://", url, re.I):
            await upd.message.reply_text("Please send a valid link.", reply_markup=menu())
            return
        plat = detect_platform(url) or "link"
        msg = await upd.message.reply_text(f"Downloading from {plat}...")
        fp, err = await download_media(url)
        if err:
            await msg.edit_text(f"{err}\nTry again.", reply_markup=menu())
            return
        sz = await dl_size(fp)
        if sz > config.MAX_FILE_SIZE:
            await msg.edit_text("File too large (>45MB).", reply_markup=menu())
            dl_clean(fp)
            return
        await msg.edit_text("Uploading...")
        try:
            with open(fp, "rb") as f:
                await upd.message.reply_document(f, caption=f"Downloaded from {plat}")
            await msg.delete()
        except Exception as e:
            await msg.edit_text(f"Upload error: {str(e)[:100]}")
        finally:
            dl_clean(fp)
    elif upd.message and (upd.message.document or upd.message.video):
        f = upd.message.document or upd.message.video
        ctx.user_data["media_id"] = f.file_id
        await upd.message.reply_text("Media saved! Now choose conversion:", reply_markup=menu())
    else:
        await upd.message.reply_text("Send a link or media file.", reply_markup=menu())

async def callback(upd: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = upd.callback_query
    await q.answer()
    d = q.data
    if d == "help":
        await q.edit_message_text("Send a link = download. Send media = convert.", reply_markup=menu())
    elif d == "about":
        await q.edit_message_text(f"All Link Download Bot\nOwner: @{config.OWNER_USERNAME}", reply_markup=menu())
    elif d.startswith("p:"):
        plat = d[2:]
        await q.edit_message_text(f"{plat.title()}\n\nSend a link from {plat.title()} and I'll download it.", reply_markup=menu())
    elif d.startswith("c:"):
        key = d[2:]
        label = config.CONVERSIONS.get(key, key)
        mid = ctx.user_data.get("media_id")
        if not mid:
            await q.edit_message_text(f"Send a media file first, then tap {label}.", reply_markup=menu())
            return
        target = key.split("_to_")[-1] if "_to_" in key else key
        # download file
        fo = await ctx.bot.get_file(mid)
        inp = os.path.join(config.CONVERTED_DIR, f"inp_{mid[:8]}.mp4")
        await fo.download_to_drive(inp)
        await q.edit_message_text(f"Converting to {target}...")
        out, err = await convert_media(inp, target, conv_key=key)
        clean_up(inp)
        if err:
            await q.edit_message_text(f"{err}", reply_markup=menu())
            return
        sz = await conv_size(out)
        if sz > config.MAX_FILE_SIZE:
            await q.edit_message_text("Converted file too large.", reply_markup=menu())
            clean_up(out)
            return
        try:
            with open(out, "rb") as f:
                await q.message.reply_document(f, caption=f"Converted to {target}")
            await q.edit_message_text("Done! Choose another:", reply_markup=menu())
        except Exception as e:
            await q.edit_message_text(f"Error: {str(e)[:100]}")
        finally:
            clean_up(out)

def build_app():
    app = Application.builder().token(config.BOT_TOKEN).concurrent_updates(True).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("about", about_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.ALL, handle_msg))
    app.add_handler(CallbackQueryHandler(callback))
    return app
