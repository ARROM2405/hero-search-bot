from typing import TypeVar

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import Field

field_type = TypeVar("field_type", bound=Field)


def create_base_serializer_with_field(
    field_name: str,
    field: type(field_type),
):
    class BaseSerializer(serializers.Serializer):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields[field_name] = field()

    return BaseSerializer


class TelegramUserSerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["id"] = serializers.IntegerField()

    is_bot = serializers.BooleanField()
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    username = serializers.CharField(max_length=100, required=False, allow_blank=True)


WithFromFieldSerializerBase = create_base_serializer_with_field(
    "from",
    TelegramUserSerializer,
)

WithIdFieldSerializerBase = create_base_serializer_with_field(
    "id",
    serializers.IntegerField,
)


class NewChatMemberDetailsSerializer(serializers.Serializer):
    status = serializers.CharField(max_length=25)


class NewChatMemberSerializer(serializers.Serializer):
    status = serializers.CharField()


class ChatSerializer(WithIdFieldSerializerBase):
    type = serializers.CharField(max_length=25)


class ChatMemberSerializer(WithFromFieldSerializerBase):
    new_chat_member = NewChatMemberSerializer()
    chat = ChatSerializer()


class EntitiesSerializer(serializers.Serializer):
    type = serializers.CharField(max_length=25)


class MessageSerializer(WithFromFieldSerializerBase):
    text = serializers.CharField(required=False)
    entities = EntitiesSerializer(
        many=True,
        required=False,
        allow_null=True,
    )


class RepliedMessageSerializer(serializers.Serializer):
    chat = ChatSerializer()
    message_id = serializers.IntegerField()
    reply_markup = serializers.JSONField()


class CallBackQuerySerializer(WithFromFieldSerializerBase):
    data = serializers.CharField(max_length=256)
    message = RepliedMessageSerializer()


class TelegramBotSerializer(serializers.Serializer):
    message = MessageSerializer(required=False)
    my_chat_member = ChatMemberSerializer(required=False)
    callback_query = CallBackQuerySerializer(required=False)

    def validate(self, attrs):
        message = attrs.get("message")
        my_chat_member = attrs.get("my_chat_member")
        callback_query = attrs.get("callback_query")
        if not any(
            [
                message,
                my_chat_member,
                callback_query,
            ]
        ):
            raise ValidationError(
                "message or my_chat_member or callback_query value has to be provided."
            )
        return super().validate(attrs)
