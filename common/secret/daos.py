from typing import List

from common.secret.data import CurveEnum, PubKeyType, SecretKeyType
from common.secret.models import PubKeyModel, SecretKeyModel


def new_pubkey_model(
    curve: CurveEnum,
    pubkey_type: PubKeyType,
    pubkey: str,
    path: str = None,
    parent_pubkey_id: int = None,
    secret_key_id: int = None,
) -> PubKeyModel:
    return PubKeyModel(
        curve=curve,
        pubkey_type=pubkey_type,
        pubkey=pubkey,
        path=path,
        parent_pubkey_id=parent_pubkey_id,
        secret_key_id=secret_key_id,
    )


def create_pubkey_model(
    curve: CurveEnum,
    pubkey_type: PubKeyType,
    pubkey: str,
    path: str = None,
    parent_pubkey_id: int = None,
    secret_key_id: int = None,
) -> PubKeyModel:
    return PubKeyModel.create(
        curve=curve,
        pubkey_type=pubkey_type,
        pubkey=pubkey,
        path=path,
        parent_pubkey_id=parent_pubkey_id,
        secret_key_id=secret_key_id,
    )


def get_pubkey_model_by_id(pubkey_id: int) -> PubKeyModel:
    return PubKeyModel.get_by_id(pubkey_id)


def query_pubkey_models_by_ids(pubkey_ids: List[int]) -> List[PubKeyModel]:
    models = PubKeyModel.select().where(PubKeyModel.id.in_(pubkey_ids))
    return list(models)


def create_secret_key_model(
    secret_key_type: SecretKeyType,
    encrypted_secret_key: str,
    encrypted_message: str = None,
) -> SecretKeyModel:
    return SecretKeyModel.create(
        secret_key_type=secret_key_type,
        encrypted_secret_key=encrypted_secret_key,
        encrypted_message=encrypted_message,
    )


def get_secret_key_model_by_id(secret_key_id: int) -> SecretKeyModel:
    return SecretKeyModel.get_by_id(secret_key_id)


def update_secret_key_encrypted_data(secret_key_id: int, encrypted_secret_key: str, encrypted_message: str):
    SecretKeyModel.update(encrypted_secret_key=encrypted_secret_key, encrypted_message=encrypted_message).where(
        SecretKeyModel.id == secret_key_id
    ).execute()


def query_pubkey_models_by_secret_ids(secret_key_ids: List[int]) -> List[PubKeyModel]:
    models = PubKeyModel.select().where(PubKeyModel.secret_key_id.in_(secret_key_ids))
    return list(models)


def delete_pubkey_by_ids(pubkey_ids: List[int]):
    PubKeyModel.delete().where(PubKeyModel.id.in_(pubkey_ids)).execute()


def delete_secret_key_by_ids(secret_key_ids: List[int]):
    SecretKeyModel.delete().where(SecretKeyModel.id.in_(secret_key_ids)).execute()
