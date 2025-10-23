from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator

class OAuthClient(models.Model):
    client_id = fields.CharField(max_length=255, pk=True)
    client_secret = fields.CharField(max_length=255)
    client_name = fields.CharField(max_length=255)
    client_uri = fields.CharField(max_length=255, null=True)
    redirect_uris = fields.JSONField()
    grant_types = fields.JSONField()
    response_types = fields.JSONField()
    scope = fields.CharField(max_length=255)
    client_id_issued_at = fields.IntField()
    client_secret_expires_at = fields.IntField()
    created_at = fields.FloatField()

    class PydanticMeta:
        pass

class OAuthCode(models.Model):
    code = fields.CharField(max_length=255, pk=True)
    client = fields.ForeignKeyField("models.OAuthClient", related_name="codes")
    redirect_uri = fields.CharField(max_length=255)
    scope = fields.CharField(max_length=255)
    user_info = fields.JSONField(null=True)
    code_challenge = fields.CharField(max_length=255, null=True)
    code_challenge_method = fields.CharField(max_length=255, null=True)
    created_at = fields.FloatField()
    expires_at = fields.FloatField()

    class PydanticMeta:
        pass

OAuthClient_Pydantic = pydantic_model_creator(OAuthClient)
OAuthCode_Pydantic = pydantic_model_creator(OAuthCode)