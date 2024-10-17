# PRIVATE

BOT_KICKED_FROM_THE_PRIVATE_CHAT = {
    "my_chat_member": {
        "chat": {
            "first_name": "SomeFName",
            "last_name": "SomeLName",
            "id": 111111111,
            "type": "private",
            "username": "SomeUserName",
        },
        "date": 1715027895,
        "from": {
            "first_name": "SomeFName",
            "last_name": "SomeLName",
            "id": 111111111,
            "is_bot": False,
            "language_code": "uk",
            "username": "SomeUserName",
        },
        "new_chat_member": {
            "status": "kicked",
            "until_date": 0,
            "user": {
                "first_name": "BotFName",
                "id": 222222222,
                "is_bot": True,
                "username": "BotUserName",
            },
        },
        "old_chat_member": {
            "status": "member",
            "user": {
                "first_name": "BotFName",
                "id": 222222222,
                "is_bot": True,
                "username": "BotUserName",
            },
        },
    },
    "update_id": 333333333,
}

BOT_ADDED_TO_THE_PRIVATE_CHAT = {
    "my_chat_member": {
        "chat": {
            "first_name": "SomeFName",
            "id": 111111111,
            "last_name": "SomeLName",
            "username": "SomeUserName",
            "type": "private",
        },
        "date": 1714984431,
        "from": {
            "first_name": "SomeFName",
            "id": 111111111,
            "is_bot": False,
            "language_code": "uk",
            "last_name": "SomeLName",
            "username": "SomeUserName",
        },
        "new_chat_member": {
            "status": "member",
            "user": {
                "first_name": "BotFName",
                "id": 222222222,
                "is_bot": True,
                "username": "BotUserName",
            },
        },
        "old_chat_member": {
            "status": "kicked",
            "until_date": 0,
            "user": {
                "first_name": "BotFName",
                "id": 222222222,
                "is_bot": True,
                "username": "BotUserName",
            },
        },
    },
    "update_id": 333333333,
}


COMMAND_AS_MESSAGE_IN_PRIVATE_CHAT = {
    "message": {
        "chat": {
            "first_name": "SomeFName",
            "id": 111111111,
            "last_name": "SomeLName",
            "type": "private",
            "username": "SomeUserName",
        },
        "date": 1715028863,
        "entities": [{"length": 6, "offset": 0, "type": "bot_command"}],
        "from": {
            "first_name": "SomeFName",
            "id": 111111111,
            "is_bot": False,
            "language_code": "uk",
            "last_name": "SomeLName",
            "username": "SomeUserName",
        },
        "message_id": 222,
        "text": "/start",
    },
    "update_id": 333333333,
}


COMMAND_AS_CALLBACK_IN_PRIVATE_CHAT = {
    "callback_query": {
        "chat_instance": "1111111111111111111",
        "data": "/some_command",
        "from": {
            "first_name": "SomeFName",
            "id": 111111111,
            "is_bot": False,
            "language_code": "uk",
            "last_name": "SomeLName",
            "username": "SomeUserName",
        },
        "id": "222222222222222222",
        "message": {
            "chat": {
                "first_name": "SomeFName",
                "id": 111111111,
                "type": "private",
                "last_name": "SomeLName",
                "username": "SomeUserName",
            },
            "date": 1715028863,
            "from": {
                "first_name": "BotFName",
                "id": 222222222,
                "is_bot": True,
                "username": "BotUserName",
            },
            "message_id": 333,
            "reply_markup": {
                "inline_keyboard": [
                    [
                        {
                            "callback_data": "/some_command",
                            "text": "text_on_the_button",
                        }
                    ]
                ]
            },
            "text": "text_of_the_message_replied_to",
        },
    },
    "update_id": 444444444,
}

MESSAGE_IN_PRIVATE_CHAT = {
    "message": {
        "chat": {
            "first_name": "SomeFName",
            "id": 111111111,
            "last_name": "SomeLName",
            "username": "SomeUserName",
            "type": "private",
        },
        "date": 1714984521,
        "from": {
            "first_name": "SomeFName",
            "id": 111111111,
            "is_bot": False,
            "language_code": "uk",
            "last_name": "SomeLName",
            "username": "SomeUserName",
        },
        "message_id": 222,
        "text": "1234567890",
    },
    "update_id": 333333333,
}

MESSAGE_EDITED = {
    "edited_message": {
        "chat": {
            "first_name": "SomeFName",
            "id": 111111111,
            "last_name": "SomeLName",
            "username": "SomeUserName",
            "type": "private",
        },
        "date": 1720960475,
        "edit_date": 1720960484,
        "from": {
            "first_name": "SomeFName",
            "id": 111111111,
            "is_bot": False,
            "language_code": "uk",
            "last_name": "SomeLName",
            "username": "SomeUserName",
        },
        "message_id": 222,
        "text": "SomeText",
    },
    "update_id": 508043956,
}

# GROUP

BOT_ADDED_TO_THE_GROUP = {
    "my_chat_member": {
        "chat": {
            "all_members_are_administrators": True,
            "id": -111111111,
            "title": "SomeTitle",
            "type": "group",
        },
        "date": 1715079281,
        "from": {
            "first_name": "SomeFName",
            "id": 222222222,
            "is_bot": False,
            "language_code": "uk",
            "last_name": "SomeLName",
            "username": "SomeUseName",
        },
        "new_chat_member": {
            "status": "member",
            "user": {
                "first_name": "BotFName",
                "id": 3333333333,
                "is_bot": True,
                "username": "BotUserName",
            },
        },
        "old_chat_member": {
            "status": "left",
            "user": {
                "first_name": "BotFName",
                "id": 3333333333,
                "is_bot": True,
                "username": "BotUserName",
            },
        },
    },
    "update_id": 444444444,
}

BOT_KICKED_FROM_THE_GROUP_1 = {
    "message": {
        "chat": {
            "all_members_are_administrators": True,
            "id": -1111111111,
            "title": "SomeTitle",
            "type": "group",
        },
        "date": 1715029869,
        "from": {
            "first_name": "SomeFName",
            "id": 222222222,
            "is_bot": False,
            "language_code": "uk",
            "last_name": "SomeLName",
            "username": "SomeUseName",
        },
        "left_chat_member": {
            "first_name": "BotFName",
            "id": 3333333333,
            "is_bot": True,
            "username": "BotUserName",
        },
        "left_chat_participant": {
            "first_name": "BotFName",
            "id": 3333333333,
            "is_bot": True,
            "username": "BotUserName",
        },
        "message_id": 444,
    },
    "update_id": 555555555,
}

BOT_KICKED_FROM_THE_GROUP_2 = {
    "my_chat_member": {
        "chat": {
            "all_members_are_administrators": True,
            "id": -1111111111,
            "title": "SomeTitle",
            "type": "group",
        },
        "date": 1715029869,
        "from": {
            "first_name": "SomeFName",
            "id": 222222222,
            "is_bot": False,
            "language_code": "uk",
            "last_name": "SomeLName",
            "username": "SomeUseName",
        },
        "new_chat_member": {
            "status": "left",
            "user": {
                "first_name": "BotFName",
                "id": 3333333333,
                "is_bot": True,
                "username": "BotUserName",
            },
        },
        "old_chat_member": {
            "status": "member",
            "user": {
                "first_name": "BotFName",
                "id": 3333333333,
                "is_bot": True,
                "username": "BotUserName",
            },
        },
    },
    "update_id": 444444444,
}

COMMAND_AS_MESSAGE_IN_GROUP_CHAT = {
    "message": {
        "chat": {
            "all_members_are_administrators": True,
            "id": -111111111,
            "title": "SomeTitle",
            "type": "group",
        },
        "date": 1714984387,
        "entities": [{"length": 6, "offset": 0, "type": "bot_command"}],
        "from": {
            "first_name": "SomeFName",
            "id": 222222222,
            "is_bot": False,
            "last_name": "SomeLName",
            "language_code": "uk",
            "username": "SomeUsername",
        },
        "message_id": 333,
        "text": "/start",
    },
    "update_id": 444444444,
}

COMMAND_AS_CALLBACK_IN_GROUP = {}

MESSAGE_IN_GROUP = {}

# CHANNEL

BOT_SET_AS_ADMIN_IN_CHANNEL = {
    "my_chat_member": {
        "chat": {"id": -1111111111111, "title": "SomeTitle", "type": "channel"},
        "date": 1715079522,
        "from": {
            "first_name": "SomeFName",
            "id": 222222222,
            "is_bot": False,
            "language_code": "uk",
            "last_name": "SomeLName",
            "username": "SomeUseName",
        },
        "new_chat_member": {
            "can_be_edited": False,
            "can_change_info": True,
            "can_delete_messages": True,
            "can_delete_stories": True,
            "can_edit_messages": True,
            "can_edit_stories": True,
            "can_invite_users": True,
            "can_manage_chat": True,
            "can_manage_video_chats": True,
            "can_manage_voice_chats": True,
            "can_post_messages": True,
            "can_post_stories": True,
            "can_promote_members": False,
            "can_restrict_members": True,
            "is_anonymous": False,
            "status": "administrator",
            "user": {
                "first_name": "BotFName",
                "id": 3333333333,
                "is_bot": True,
                "username": "BotUserName",
            },
        },
        "old_chat_member": {
            "status": "left",
            "user": {
                "first_name": "BotFName",
                "id": 3333333333,
                "is_bot": True,
                "username": "BotUserName",
            },
        },
    },
    "update_id": 508043906,
}
