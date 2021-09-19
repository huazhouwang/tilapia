from unittest import TestCase
from unittest.mock import Mock, patch

from wallet.lib.basic.orm import test_utils
from wallet.lib.provider import data as provider_data
from wallet.lib.utxo import daos, data, manager, models


@test_utils.cls_test_database(models.UTXO, models.WhoSpent)
class TestUTXOManager(TestCase):
    def test_choose_utxos(self):
        daos.bulk_create_utxos(
            [
                daos.new_utxo("btc", "btc", "address1", "txid1", 0, data.UTXOStatus.SPENDABLE, 100),
                daos.new_utxo("btc", "btc", "address1", "txid1", 1, data.UTXOStatus.SPENDABLE, 1000),
                daos.new_utxo("btc", "btc", "address1", "txid2", 0, data.UTXOStatus.SPENDABLE, 200),
                daos.new_utxo("btc", "btc", "address2", "txid2", 2, data.UTXOStatus.SPENDABLE, 2000),
                daos.new_utxo("btc", "btc", "address2", "txid2", 3, data.UTXOStatus.SPENDABLE, 5000),
            ]
        )
        self.assertEqual(5, models.UTXO.select().count())

        utxos = list(models.UTXO.select())

        self.assertEqual([utxos[0]], manager.choose_utxos("btc", ["address1"], 100))
        self.assertEqual([], manager.choose_utxos("btc", ["address1"], 100, min_value=100))
        self.assertEqual([utxos[2]], manager.choose_utxos("btc", ["address1"], 101, min_value=100))
        self.assertEqual([utxos[1], utxos[2]], manager.choose_utxos("btc", ["address1"], 1200))
        self.assertEqual([utxos[1], utxos[2], utxos[0]], manager.choose_utxos("btc", ["address1"], 1400))

        self.assertEqual([utxos[3]], manager.choose_utxos("btc", ["address1", "address2"], 2000))
        utxos[3].status = data.UTXOStatus.CHOSEN
        utxos[3].save()
        self.assertEqual([utxos[4]], manager.choose_utxos("btc", ["address1", "address2"], 2000))

        utxos[4].status = data.UTXOStatus.SPENT
        utxos[4].save()
        self.assertEqual([utxos[1], utxos[2], utxos[0]], manager.choose_utxos("btc", ["address1", "address2"], 2000))

    @patch("wallet.lib.utxo.manager.provider_manager.search_utxos_by_address")
    @patch("wallet.lib.utxo.manager.coin_manager.get_chain_info")
    def test_refresh_utxos_by_address(self, fake_get_chain_info, fake_search_utxos_by_address):
        daos.bulk_create_utxos(
            [
                daos.new_utxo("btc", "btc", "address1", "txid1", 0, data.UTXOStatus.SPENDABLE, 1000),
                daos.new_utxo("btc", "btc", "address1", "txid1", 1, data.UTXOStatus.SPENT, 1500),
                daos.new_utxo("btc", "btc", "address1", "txid2", 0, data.UTXOStatus.CHOSEN, 1000),
                daos.new_utxo("btc", "btc", "address2", "txid2", 2, data.UTXOStatus.SPENDABLE, 2000),
                daos.new_utxo("btc", "btc", "address2", "txid2", 3, data.UTXOStatus.CHOSEN, 5000),
            ]
        )
        self.assertEqual(5, models.UTXO.select().count())

        fake_get_chain_info.return_value = Mock(dust_threshold=546)

        with self.subTest("Search utxos by address1"):
            fake_search_utxos_by_address.return_value = [
                provider_data.UTXO(txid="txid1", vout=1, value=1500),
                provider_data.UTXO(txid="txid2", vout=0, value=1000),
                provider_data.UTXO(txid="txid2", vout=1, value=545),  # Lower than dust_threshold
                provider_data.UTXO(txid="txid2", vout=4, value=546),
            ]
            self.assertEqual(3, manager.refresh_utxos_by_address("btc", "address1"))
            fake_get_chain_info.assert_called_once_with("btc")
            fake_search_utxos_by_address.assert_called_once_with("btc", "address1")

            self.assertEqual(6, models.UTXO.select().count())
            self.assertEqual(
                [
                    (1, data.UTXOStatus.SPENT),
                    (2, data.UTXOStatus.SPENDABLE),
                    (3, data.UTXOStatus.CHOSEN),
                    (4, data.UTXOStatus.SPENDABLE),
                    (5, data.UTXOStatus.CHOSEN),
                    (6, data.UTXOStatus.SPENDABLE),
                ],
                [(i.id, i.status) for i in models.UTXO.select()],
            )

        with self.subTest("Call throttled"):
            fake_get_chain_info.reset_mock()
            fake_search_utxos_by_address.reset_mock()
            self.assertEqual(0, manager.refresh_utxos_by_address("btc", "address1"))
            fake_get_chain_info.assert_not_called()
            fake_search_utxos_by_address.assert_not_called()

        with self.subTest("Search utxos by address2"):
            fake_search_utxos_by_address.return_value = [
                provider_data.UTXO(txid="txid2", vout=2, value=2000),
                provider_data.UTXO(txid="txid2", vout=3, value=5000),
                provider_data.UTXO(txid="txid3", vout=1, value=1000),
            ]
            self.assertEqual(1, manager.refresh_utxos_by_address("btc", "address2"))
            fake_get_chain_info.assert_called_once_with("btc")
            fake_search_utxos_by_address.assert_called_once_with("btc", "address2")

            self.assertEqual(7, models.UTXO.select().count())
            self.assertEqual(
                [
                    (1, data.UTXOStatus.SPENT),
                    (2, data.UTXOStatus.SPENDABLE),
                    (3, data.UTXOStatus.CHOSEN),
                    (4, data.UTXOStatus.SPENDABLE),
                    (5, data.UTXOStatus.CHOSEN),
                    (6, data.UTXOStatus.SPENDABLE),
                    (7, data.UTXOStatus.SPENDABLE),
                ],
                [(i.id, i.status) for i in models.UTXO.select()],
            )

    def test_query_utxo_ids_by_txid_vout_tuples(self):
        daos.bulk_create_utxos(
            [
                daos.new_utxo("btc", "btc", "address1", "txid1", 0, data.UTXOStatus.SPENDABLE, 100),
                daos.new_utxo("btc", "btc", "address1", "txid1", 1, data.UTXOStatus.SPENDABLE, 100),
                daos.new_utxo("btc", "btc", "address1", "txid2", 0, data.UTXOStatus.SPENDABLE, 100),
                daos.new_utxo("btc", "btc", "address2", "txid2", 2, data.UTXOStatus.SPENDABLE, 100),
                daos.new_utxo("btc", "btc", "address2", "txid2", 3, data.UTXOStatus.SPENDABLE, 100),
            ]
        )
        self.assertEqual(5, models.UTXO.select().count())

        self.assertEqual([1], manager.query_utxo_ids_by_txid_vout_tuples("btc", [("txid1", 0), ("txid2", 1)]))
        self.assertEqual([1, 4], manager.query_utxo_ids_by_txid_vout_tuples("btc", [("txid1", 0), ("txid2", 2)]))
        self.assertEqual(
            [1, 2, 3, 4, 5],
            manager.query_utxo_ids_by_txid_vout_tuples(
                "btc", [("txid1", 0), ("txid1", 1), ("txid2", 0), ("txid2", 2), ("txid2", 3)]
            ),
        )

    def test_get_utxos_chosen_by_txid(self):
        daos.bulk_create_utxos(
            [
                daos.new_utxo("btc", "btc", "address1", "txid1", 0, data.UTXOStatus.CHOSEN, 100),
                daos.new_utxo("btc", "btc", "address1", "txid1", 1, data.UTXOStatus.CHOSEN, 100),
                daos.new_utxo("btc", "btc", "address1", "txid2", 0, data.UTXOStatus.CHOSEN, 100),
                daos.new_utxo("btc", "btc", "address2", "txid2", 2, data.UTXOStatus.CHOSEN, 100),
                daos.new_utxo("btc", "btc", "address2", "txid2", 3, data.UTXOStatus.CHOSEN, 100),
            ]
        )
        daos.bulk_create_who_spent(
            [
                daos.new_who_spent("btc", "txid2", 1),
                daos.new_who_spent("btc", "txid3", 2),
                daos.new_who_spent("btc", "txid3", 3),
                daos.new_who_spent("btc", "txid3", 4),
                daos.new_who_spent("btc", "txid3", 5),
            ]
        )
        self.assertEqual(5, models.UTXO.select().count())
        self.assertEqual(5, models.WhoSpent.select().count())

        self.assertEqual([models.UTXO.get_by_id(1)], manager.get_utxos_chosen_by_txid("btc", "txid2"))
        self.assertEqual(
            list(models.UTXO.select().where(models.UTXO.id.in_((2, 3, 4, 5)))),
            manager.get_utxos_chosen_by_txid("btc", "txid3"),
        )

    def test_mark_utxos_chosen_by_txid(self):
        daos.bulk_create_utxos(
            [
                daos.new_utxo("btc", "btc", "address1", "txid1", 0, data.UTXOStatus.SPENDABLE, 100),
                daos.new_utxo("btc", "btc", "address1", "txid1", 1, data.UTXOStatus.SPENDABLE, 100),
                daos.new_utxo("btc", "btc", "address1", "txid2", 0, data.UTXOStatus.SPENDABLE, 100),
                daos.new_utxo("btc", "btc", "address2", "txid2", 2, data.UTXOStatus.SPENDABLE, 100),
                daos.new_utxo("btc", "btc", "address2", "txid2", 3, data.UTXOStatus.SPENDABLE, 100),
            ]
        )

        self.assertEqual(5, models.UTXO.select().count())
        self.assertEqual(0, models.WhoSpent.select().count())

        with self.subTest("Choose by txid2"):
            manager.mark_utxos_chosen_by_txid("btc", "txid2", [1])
            self.assertEqual(5, models.UTXO.select().count())
            self.assertEqual(1, models.WhoSpent.select().count())

            who_spent = models.WhoSpent.get_by_id(1)
            self.assertEqual(("btc", "txid2", 1), (who_spent.chain_code, who_spent.txid, who_spent.utxo_id))
            utxo = models.UTXO.get_by_id(1)
            self.assertEqual(data.UTXOStatus.CHOSEN, utxo.status)

        with self.subTest("Choose by txid3"):
            manager.mark_utxos_chosen_by_txid("btc", "txid3", [2, 3, 4, 5])
            self.assertEqual(5, models.UTXO.select().count())
            self.assertEqual(5, models.UTXO.select().where(models.UTXO.status == data.UTXOStatus.CHOSEN).count())
            self.assertEqual(5, models.WhoSpent.select().count())

            who_spents = models.WhoSpent.select().where(models.WhoSpent.id.in_((2, 3, 4, 5)))
            self.assertEqual(
                [("btc", "txid3", 2), ("btc", "txid3", 3), ("btc", "txid3", 4), ("btc", "txid3", 5)],
                [(i.chain_code, i.txid, i.utxo_id) for i in who_spents],
            )
            utxos = models.UTXO.select().where(models.UTXO.id.in_((2, 3, 4, 5)))
            self.assertEqual([data.UTXOStatus.CHOSEN] * 4, [i.status for i in utxos])

        with self.subTest("UNIQUE Constraint"):
            with self.assertRaisesRegex(
                Exception, "UNIQUE constraint failed: whospent.chain_code, whospent.txid, whospent.utxo_id"
            ):
                manager.mark_utxos_chosen_by_txid("btc", "txid2", [1])

    def test_mark_utxos_spent_by_txid(self):
        daos.bulk_create_utxos(
            [
                daos.new_utxo("btc", "btc", "address1", "txid1", 0, data.UTXOStatus.CHOSEN, 100),
                daos.new_utxo("btc", "btc", "address1", "txid1", 1, data.UTXOStatus.CHOSEN, 100),
                daos.new_utxo("btc", "btc", "address1", "txid2", 0, data.UTXOStatus.CHOSEN, 100),
                daos.new_utxo("btc", "btc", "address2", "txid2", 2, data.UTXOStatus.CHOSEN, 100),
                daos.new_utxo("btc", "btc", "address2", "txid2", 3, data.UTXOStatus.CHOSEN, 100),
            ]
        )
        daos.bulk_create_who_spent(
            [
                daos.new_who_spent("btc", "txid2", 1),
                daos.new_who_spent("btc", "txid3", 2),
                daos.new_who_spent("btc", "txid3", 3),
                daos.new_who_spent("btc", "txid3", 4),
                daos.new_who_spent("btc", "txid3", 5),
            ]
        )

        self.assertEqual(5, models.UTXO.select().count())
        self.assertEqual(5, models.WhoSpent.select().count())

        with self.subTest("Confirmed txid2"):
            manager.mark_utxos_spent_by_txid("btc", "txid2")
            utxo = models.UTXO.get_by_id(1)
            self.assertEqual(data.UTXOStatus.SPENT, utxo.status)
            self.assertEqual(1, models.UTXO.select().where(models.UTXO.status == data.UTXOStatus.SPENT).count())

        with self.subTest("Confirmed txid3"):
            manager.mark_utxos_spent_by_txid("btc", "txid3")
            self.assertEqual(5, models.UTXO.select().where(models.UTXO.status == data.UTXOStatus.SPENT).count())

    def test_delete_utxos_by_addresses(self):
        daos.bulk_create_utxos(
            [
                daos.new_utxo("btc", "btc", "address1", "txid1", 0, data.UTXOStatus.SPENT, 100),
                daos.new_utxo("btc", "btc", "address1", "txid1", 1, data.UTXOStatus.SPENDABLE, 100),
                daos.new_utxo("btc", "btc", "address1", "txid2", 0, data.UTXOStatus.SPENDABLE, 100),
                daos.new_utxo("btc", "btc", "address2", "txid2", 2, data.UTXOStatus.SPENDABLE, 100),
                daos.new_utxo("btc", "btc", "address2", "txid2", 3, data.UTXOStatus.CHOSEN, 100),
            ]
        )
        daos.bulk_create_who_spent([daos.new_who_spent("btc", "txid2", 1)])

        self.assertEqual(5, models.UTXO.select().count())
        self.assertEqual(1, models.WhoSpent.select().count())

        with self.subTest("Delete address3 - Nothing happened"):
            manager.delete_utxos_by_addresses("btc", ["address3"])
            self.assertEqual(5, models.UTXO.select().count())
            self.assertEqual(1, models.WhoSpent.select().count())

        with self.subTest("Delete address1"):
            manager.delete_utxos_by_addresses("btc", ["address1"])
            self.assertEqual(2, models.UTXO.select().count())
            self.assertEqual(0, models.UTXO.select().where(models.UTXO.address == "address1").count())
            self.assertEqual(0, models.WhoSpent.select().count())

        with self.subTest("Delete address2"):
            manager.delete_utxos_by_addresses("btc", ["address2"])
            self.assertEqual(0, models.UTXO.select().count())
            self.assertEqual(0, models.WhoSpent.select().count())
