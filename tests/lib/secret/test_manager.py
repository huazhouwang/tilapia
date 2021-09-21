from unittest import TestCase
from unittest.mock import call, patch

from tilapia.lib.basic import cipher
from tilapia.lib.basic.orm import test_utils
from tilapia.lib.secret import daos as secret_daos
from tilapia.lib.secret import manager as secret_manager
from tilapia.lib.secret import utils
from tilapia.lib.secret.data import CurveEnum, PubKeyType, SecretKeyType
from tilapia.lib.secret.models import PubKeyModel, SecretKeyModel


@test_utils.cls_test_database(PubKeyModel, SecretKeyModel)
class TestSecretManager(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.message = b"Hello OneKey"
        cls.mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        cls.passphrase = "OneKey"
        cls.master_seed = bytes.fromhex(
            "ac7728a67cf7fe4a237668db29f7d93243da5cecd3e7cb790dc393e31fdfaadf8ced5e17bb53be83823faae50eb4fc4a8d67486fa04851238accc29005734692"
        )

        cls.account_level_path = "m/44'/60'/0'"
        cls.account_level_xpub = "xpub6CEGaxz3GGxefcUFP4mYo6f8BmAUywBSfYbLd8Z851RntgRrp2vhYaiddPFJR9a6TV2Fsz2PY3PbGHNMgnNTKQVPssfcaieBHnT8Leh47VR"
        cls.account_level_xprv = "xprv9yEvBTT9RuQMT8PnH3EYRxiPdjKzaUTbJKfjpk9WWftp1t6iGVcSznQ9n7Y6aLTjGf2P1pD3QDfugmjgVRw1d8t1MmZeaqArnKCUTMfovLR"
        cls.account_level_signature = (
            "19f8ab7d24d019bdf1443719447516961d4918cb441ef083e3531ad74f364b5303c070d6a0175751afb93fb32f21f666e652f89262139b5f474b34d9305d8ece",
            0,
        )

        cls.address_level_path = f"{cls.account_level_path}/0/0"
        cls.address_level_prvkey = "77f22e0d920c7b59df81a629dc75c27513b5360a45d55f3253454f5d3cb23bab"
        cls.address_level_pubkey = "02deb60902c06bfed8d78e33337be995d0b3efc28fbc61b6f88cb5cfb27dc4efd1"
        cls.address_level_signature = (
            "e1b1ed07c97cc6204cb9b5a5f446d4757bf3abc6bf48f886c7a96c303552575b41cc543b07ca36c6987121a9628ddd1d76ab603e7821b5f5ca83f063aba6bbf7",
            1,
        )

    def test_import_pubkey(self):
        pubkey_model = secret_manager.import_pubkey(CurveEnum.SECP256K1, bytes.fromhex(self.address_level_pubkey))

        models = list(PubKeyModel.select())
        self.assertEqual(1, len(models))

        first_model: PubKeyModel = models[0]
        self.assertEqual(pubkey_model.id, first_model.id)
        self.assertEqual(CurveEnum.SECP256K1, first_model.curve)
        self.assertEqual(PubKeyType.PUBKEY, first_model.pubkey_type)
        self.assertEqual(self.address_level_pubkey, first_model.pubkey)
        self.assertIsNone(first_model.path)
        self.assertIsNone(first_model.parent_pubkey_id)
        self.assertIsNone(first_model.secret_key_id)

    def test_import_xpub(self):
        xpub_model = secret_manager.import_xpub(CurveEnum.SECP256K1, self.account_level_xpub, self.account_level_path)

        models = list(PubKeyModel.select())
        self.assertEqual(1, len(models))

        first_model: PubKeyModel = models[0]
        self.assertEqual(xpub_model.id, first_model.id)
        self.assertEqual(CurveEnum.SECP256K1, first_model.curve)
        self.assertEqual(PubKeyType.XPUB, first_model.pubkey_type)
        self.assertEqual(self.account_level_xpub, first_model.pubkey)
        self.assertEqual(self.account_level_path, first_model.path)
        self.assertIsNone(first_model.parent_pubkey_id)
        self.assertIsNone(first_model.secret_key_id)

    def test_import_xpub_and_sub_pubkey(self):
        xpub_model = secret_manager.import_xpub(CurveEnum.SECP256K1, self.account_level_xpub, self.account_level_path)
        pubkey_model = secret_manager.import_pubkey(
            CurveEnum.SECP256K1,
            bytes.fromhex(self.address_level_pubkey),
            self.address_level_path,
            parent_pubkey_id=xpub_model.id,
        )

        models = list(PubKeyModel.select())
        self.assertEqual(2, len(models))
        self.assertEqual(xpub_model, models[0])
        self.assertEqual(pubkey_model, models[1])

    @patch("tilapia.lib.secret.manager.encrypt")
    def test_import_prvkey(self, fake_encrypt):
        fake_encrypt.encrypt_data.side_effect = lambda p, d: f"Encrypted<{p},{d}>"

        pubkey_model, secret_key_model = secret_manager.import_prvkey(
            "hello",
            CurveEnum.SECP256K1,
            bytes.fromhex(self.address_level_prvkey),
        )

        fake_encrypt.encrypt_data.assert_called_once_with("hello", self.address_level_prvkey)
        fake_encrypt.decrypt_data.assert_not_called()

        secret_key_models = list(SecretKeyModel.select())
        self.assertEqual(1, len(secret_key_models))

        first_secret_key_model: SecretKeyModel = secret_key_models[0]
        self.assertEqual(secret_key_model.id, first_secret_key_model.id)
        self.assertEqual(SecretKeyType.PRVKEY, first_secret_key_model.secret_key_type)
        self.assertEqual(f"Encrypted<hello,{self.address_level_prvkey}>", first_secret_key_model.encrypted_secret_key)

        pubkey_models = list(PubKeyModel.select())
        self.assertEqual(1, len(pubkey_models))

        first_pubkey_model: PubKeyModel = pubkey_models[0]
        self.assertEqual(pubkey_model.id, first_pubkey_model.id)
        self.assertEqual(secret_key_model.id, first_pubkey_model.secret_key_id)
        self.assertEqual(PubKeyType.PUBKEY, first_pubkey_model.pubkey_type)
        self.assertEqual(self.address_level_pubkey, first_pubkey_model.pubkey)
        self.assertEqual(CurveEnum.SECP256K1, first_pubkey_model.curve)
        self.assertIsNone(first_pubkey_model.path)
        self.assertIsNone(first_pubkey_model.parent_pubkey_id)

    @patch("tilapia.lib.secret.manager.encrypt")
    def test_import_xprv(self, fake_encrypt):
        fake_encrypt.encrypt_data.side_effect = lambda p, d: f"Encrypted<{p},{d}>"

        pubkey_model, secret_key_model = secret_manager.import_xprv(
            "hello",
            CurveEnum.SECP256K1,
            self.account_level_xprv,
            path=self.account_level_path,
        )

        fake_encrypt.encrypt_data.assert_called_once_with("hello", self.account_level_xprv)
        fake_encrypt.decrypt_data.assert_not_called()

        secret_key_models = list(SecretKeyModel.select())
        self.assertEqual(1, len(secret_key_models))

        first_secret_key_model: SecretKeyModel = secret_key_models[0]
        self.assertEqual(secret_key_model.id, first_secret_key_model.id)
        self.assertEqual(SecretKeyType.XPRV, first_secret_key_model.secret_key_type)
        self.assertEqual(f"Encrypted<hello,{self.account_level_xprv}>", first_secret_key_model.encrypted_secret_key)

        pubkey_models = list(PubKeyModel.select())
        self.assertEqual(1, len(pubkey_models))

        first_pubkey_model: PubKeyModel = pubkey_models[0]
        self.assertEqual(pubkey_model.id, first_pubkey_model.id)
        self.assertEqual(secret_key_model.id, first_pubkey_model.secret_key_id)
        self.assertEqual(PubKeyType.XPUB, first_pubkey_model.pubkey_type)
        self.assertEqual(self.account_level_xpub, first_pubkey_model.pubkey)
        self.assertEqual(CurveEnum.SECP256K1, first_pubkey_model.curve)
        self.assertEqual(self.account_level_path, first_pubkey_model.path)
        self.assertIsNone(first_pubkey_model.parent_pubkey_id)

    @patch("tilapia.lib.secret.manager.encrypt")
    def test_import_master_seed(self, fake_encrypt):
        fake_encrypt.encrypt_data.side_effect = lambda p, d: f"Encrypted<{p},{d}>"

        secret_key_model = secret_manager.import_mnemonic("hello", self.mnemonic, self.passphrase)

        fake_encrypt.encrypt_data.assert_has_calls(
            [
                call("hello", self.master_seed.hex()),
                call("hello", f"{self.mnemonic}|{self.passphrase}"),
            ]
        )
        fake_encrypt.decrypt_data.assert_not_called()

        secret_key_models = list(SecretKeyModel.select())
        self.assertEqual(1, len(secret_key_models))

        first_secret_key_model: SecretKeyModel = secret_key_models[0]
        self.assertEqual(secret_key_model.id, first_secret_key_model.id)
        self.assertEqual(SecretKeyType.SEED, first_secret_key_model.secret_key_type)
        self.assertEqual(f"Encrypted<hello,{self.master_seed.hex()}>", first_secret_key_model.encrypted_secret_key)
        self.assertEqual(
            f"Encrypted<hello,{self.mnemonic}|{self.passphrase}>",
            first_secret_key_model.encrypted_message,
        )

    @patch("tilapia.lib.secret.manager.encrypt")
    def test_export_mnemonic(self, fake_encrypt):
        fake_encrypt.encrypt_data.side_effect = lambda p, d: d
        fake_encrypt.decrypt_data.side_effect = lambda p, d: d

        secret_key_model = secret_manager.import_mnemonic("hello", self.mnemonic, self.passphrase)

        fake_encrypt.encrypt_data.assert_has_calls(
            [
                call("hello", self.master_seed.hex()),
                call("hello", f"{self.mnemonic}|{self.passphrase}"),
            ]
        )
        fake_encrypt.decrypt_data.assert_not_called()
        fake_encrypt.encrypt_data.reset_mock()

        mnemonic, passphrase = secret_manager.export_mnemonic("hello", secret_key_model.id)
        fake_encrypt.encrypt_data.assert_not_called()
        fake_encrypt.decrypt_data.assert_has_calls(
            [
                call("hello", f"{self.mnemonic}|{self.passphrase}"),
                call("hello", self.master_seed.hex()),
            ]
        )
        self.assertEqual(self.mnemonic, mnemonic)
        self.assertEqual(self.passphrase, passphrase)

    @patch("tilapia.lib.secret.manager.encrypt")
    def test_derive_by_secret_key(self, fake_encrypt):
        fake_encrypt.encrypt_data.side_effect = lambda p, d: d
        fake_encrypt.decrypt_data.side_effect = lambda p, d: d

        secret_key_model = secret_manager.import_mnemonic("hello", self.mnemonic, self.passphrase)

        fake_encrypt.encrypt_data.assert_has_calls(
            [
                call("hello", self.master_seed.hex()),
                call("hello", f"{self.mnemonic}|{self.passphrase}"),
            ]
        )
        fake_encrypt.decrypt_data.assert_not_called()
        fake_encrypt.encrypt_data.reset_mock()

        pubkey_model = secret_manager.derive_by_secret_key(
            "hello", CurveEnum.SECP256K1, secret_key_model.id, self.account_level_path
        )  # Only create new object, without saving to the database

        fake_encrypt.encrypt_data.assert_not_called()
        fake_encrypt.decrypt_data.assert_called_once_with("hello", secret_key_model.encrypted_secret_key)

        self.assertEqual(0, len(PubKeyModel.select()))
        self.assertIsNone(pubkey_model.id)
        self.assertEqual(secret_key_model.id, pubkey_model.secret_key_id)
        self.assertEqual(PubKeyType.XPUB, pubkey_model.pubkey_type)
        self.assertEqual(self.account_level_xpub, pubkey_model.pubkey)
        self.assertEqual(CurveEnum.SECP256K1, pubkey_model.curve)
        self.assertEqual(self.account_level_path, pubkey_model.path)
        self.assertIsNone(pubkey_model.parent_pubkey_id)

    @patch("tilapia.lib.secret.manager.encrypt")
    def test_derive_by_xpub(self, fake_encrypt):
        fake_encrypt.encrypt_data.side_effect = lambda p, d: d

        secret_key_model = secret_manager.import_mnemonic("hello", self.mnemonic, self.passphrase)

        fake_encrypt.encrypt_data.assert_has_calls(
            [
                call("hello", self.master_seed.hex()),
                call("hello", f"{self.mnemonic}|{self.passphrase}"),
            ]
        )
        fake_encrypt.decrypt_data.assert_not_called()
        fake_encrypt.encrypt_data.reset_mock()

        xpub_model = secret_manager.import_xpub(
            CurveEnum.SECP256K1, self.account_level_xpub, self.account_level_path, secret_key_id=secret_key_model.id
        )
        fake_encrypt.encrypt_data.assert_not_called()
        fake_encrypt.decrypt_data.assert_not_called()

        sub_path = utils.diff_bip32_paths(self.account_level_path, self.address_level_path)
        self.assertEqual("m/0/0", sub_path)

        pubkey_model = secret_manager.derive_by_xpub(
            xpub_model.id, sub_path, target_pubkey_type=PubKeyType.PUBKEY
        )  # Only create new object, without saving to the database
        fake_encrypt.encrypt_data.assert_not_called()
        fake_encrypt.decrypt_data.assert_not_called()

        self.assertEqual(1, len(PubKeyModel.select()))
        self.assertIsNone(pubkey_model.id)
        self.assertEqual(secret_key_model.id, pubkey_model.secret_key_id)
        self.assertEqual(PubKeyType.PUBKEY, pubkey_model.pubkey_type)
        self.assertEqual(self.address_level_pubkey, pubkey_model.pubkey)
        self.assertEqual(CurveEnum.SECP256K1, pubkey_model.curve)
        self.assertEqual(self.address_level_path, pubkey_model.path)
        self.assertEqual(xpub_model.id, pubkey_model.parent_pubkey_id)

    @patch("tilapia.lib.secret.manager.encrypt")
    def test_get_verifier(self, fake_encrypt):
        xpub_model = secret_manager.import_xpub(CurveEnum.SECP256K1, self.account_level_xpub, self.account_level_path)
        pubkey_model = secret_manager.import_pubkey(
            CurveEnum.SECP256K1,
            bytes.fromhex(self.address_level_pubkey),
            self.address_level_path,
            parent_pubkey_id=xpub_model.id,
        )
        fake_encrypt.encrypt_data.assert_not_called()
        fake_encrypt.decrypt_data.assert_not_called()

        self.assertTrue(
            secret_manager.get_verifier(xpub_model.id).verify(
                self.message, bytes.fromhex(self.account_level_signature[0])
            )
        )
        self.assertTrue(
            secret_manager.get_verifier(pubkey_model.id).verify(
                self.message, bytes.fromhex(self.address_level_signature[0])
            )
        )
        fake_encrypt.encrypt_data.assert_not_called()
        fake_encrypt.decrypt_data.assert_not_called()

    @patch("tilapia.lib.secret.manager.encrypt")
    def test_get_signer(self, fake_encrypt):
        fake_encrypt.encrypt_data.side_effect = lambda p, d: d
        fake_encrypt.decrypt_data.side_effect = lambda p, d: d

        # 1. import mnemonic
        secret_key_model = secret_manager.import_mnemonic("hello", self.mnemonic, self.passphrase)

        fake_encrypt.encrypt_data.assert_has_calls(
            [
                call("hello", self.master_seed.hex()),
                call("hello", f"{self.mnemonic}|{self.passphrase}"),
            ]
        )
        fake_encrypt.decrypt_data.assert_not_called()
        fake_encrypt.encrypt_data.reset_mock()

        # 2. derive account level xpub from master seed
        temp_account_level_xpub = secret_manager.derive_by_secret_key(
            "hello", CurveEnum.SECP256K1, secret_key_model.id, self.account_level_path
        )
        imported_account_level_xpub = secret_manager.import_xpub(
            temp_account_level_xpub.curve,
            temp_account_level_xpub.pubkey,
            path=temp_account_level_xpub.path,
            parent_pubkey_id=temp_account_level_xpub.parent_pubkey_id,
            secret_key_id=temp_account_level_xpub.secret_key_id,
        )

        fake_encrypt.encrypt_data.assert_not_called()
        fake_encrypt.decrypt_data.assert_called_once_with(
            "hello", secret_key_model.encrypted_secret_key
        )  # Only expose the seed when generating xpub
        fake_encrypt.decrypt_data.reset_mock()

        # 3. derive address level pubkey from account level xpub
        temp_address_level_pubkey = secret_manager.derive_by_xpub(
            imported_account_level_xpub.id,
            utils.diff_bip32_paths(self.account_level_path, self.address_level_path),
            PubKeyType.PUBKEY,
        )
        imported_address_level_pubkey = secret_manager.import_pubkey(
            temp_address_level_pubkey.curve,
            bytes.fromhex(temp_address_level_pubkey.pubkey),
            temp_address_level_pubkey.path,
            temp_address_level_pubkey.parent_pubkey_id,
            temp_address_level_pubkey.secret_key_id,
        )

        fake_encrypt.encrypt_data.assert_not_called()
        fake_encrypt.decrypt_data.assert_not_called()

        signer = secret_manager.get_signer("hello", imported_address_level_pubkey.id)
        fake_encrypt.encrypt_data.assert_not_called()
        fake_encrypt.decrypt_data.assert_called_once_with("hello", secret_key_model.encrypted_secret_key)

        self.assertEqual(
            (bytes.fromhex(self.address_level_signature[0]), self.address_level_signature[1]),
            signer.sign(self.message),
        )

    def test_update_secret_key_password(self):
        # 1. import mnemonic
        secret_key_model = secret_manager.import_mnemonic("hello", self.mnemonic, self.passphrase)

        # 2. raise if password illegal
        with self.assertRaises(cipher.InvalidPassword):
            secret_manager.update_secret_key_password(secret_key_model.id, "HELLO", "bye")

        # 3. change password successfully
        secret_manager.update_secret_key_password(secret_key_model.id, "hello", "bye")

        # 4. it can be called multiple times, as long as the new password is correct
        secret_manager.update_secret_key_password(secret_key_model.id, "hello", "bye")
        secret_manager.update_secret_key_password(secret_key_model.id, "hello2", "bye")

    def test_cascade_delete_related_models_by_pubkey_ids(self):
        # 1. create secret key a
        secret_key_model_a = secret_manager.import_mnemonic("hello", self.mnemonic, self.passphrase)
        pubkeys_from_a = []

        # 2. create a bunch of public keys by secret key a
        for i in range(10):
            pubkey_model = secret_manager.derive_by_secret_key(
                "hello",
                CurveEnum.SECP256K1,
                secret_key_model_a.id,
                f"m/44'/0'/0'/0/{i}",
                target_pubkey_type=PubKeyType.PUBKEY,
            )
            pubkey_model = secret_manager.import_pubkey(
                pubkey_model.curve,
                bytes.fromhex(pubkey_model.pubkey),
                pubkey_model.path,
                secret_key_id=pubkey_model.secret_key_id,
            )

            pubkeys_from_a.append(pubkey_model)

        # 3. create secret key b
        secret_key_model_b = secret_manager.import_mnemonic("hello", self.mnemonic, self.passphrase + "1")
        pubkeys_from_b = []

        # 4. create a bunch of public keys by secret key b
        for i in range(10):
            pubkey_model = secret_manager.derive_by_secret_key(
                "hello",
                CurveEnum.SECP256K1,
                secret_key_model_b.id,
                f"m/44'/0'/0'/0/{i}",
                target_pubkey_type=PubKeyType.PUBKEY,
            )
            pubkey_model = secret_manager.import_pubkey(
                pubkey_model.curve,
                bytes.fromhex(pubkey_model.pubkey),
                pubkey_model.path,
                secret_key_id=pubkey_model.secret_key_id,
            )

            pubkeys_from_b.append(pubkey_model)

        # 5. verify existing first
        self.assertEqual(pubkeys_from_a, secret_daos.query_pubkey_models_by_secret_ids([secret_key_model_a.id]))
        self.assertEqual(pubkeys_from_b, secret_daos.query_pubkey_models_by_secret_ids([secret_key_model_b.id]))

        # 6. delete all public keys belonging to secret key a
        secret_manager.cascade_delete_related_models_by_pubkey_ids([i.id for i in pubkeys_from_a])
        self.assertEqual(0, len(secret_daos.query_pubkey_models_by_secret_ids([secret_key_model_a.id])))
        with self.assertRaises(SecretKeyModel.DoesNotExist):
            secret_daos.get_secret_key_model_by_id(secret_key_model_a.id)

        # 7. delete all public keys belonging to secret key b except for the first one
        secret_manager.cascade_delete_related_models_by_pubkey_ids([i.id for i in pubkeys_from_b[1:]])
        self.assertEqual(pubkeys_from_b[:1], secret_daos.query_pubkey_models_by_secret_ids([secret_key_model_b.id]))
        self.assertEqual(secret_key_model_b, secret_daos.get_secret_key_model_by_id(secret_key_model_b.id))

        # 8. only one pubkey and secret key existing
        self.assertEqual(pubkeys_from_b[:1], list(PubKeyModel.select()))
        self.assertEqual([secret_key_model_b], list(SecretKeyModel.select()))

        # 9. delete the last pubkey, then nothing anymore
        secret_manager.cascade_delete_related_models_by_pubkey_ids([pubkeys_from_b[0].id])
        self.assertEqual(0, len(PubKeyModel.select()))
        self.assertEqual(0, len(SecretKeyModel.select()))
