from pyrogram.raw.functions.messages import DeleteScheduledMessages

async def edit_scheduled(client, message, text, *args, **kwargs): # Not really possible, we just delete and resend
	if message.reply_to_message:
		kwargs["reply_to_message_id"] = message.reply_to_message.message_id
	peer = await client.resolve_peer(message.chat.id)
	await client.send(DeleteScheduledMessages(peer=peer, id=[message.message_id]))
	return await client.send_message(message.chat.id, message.text.markdown + "\n" + text, *args,
										 schedule_date=message.date, **kwargs)
