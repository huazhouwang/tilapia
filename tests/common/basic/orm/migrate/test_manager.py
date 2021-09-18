from functools import partial
from unittest import TestCase
from unittest.mock import Mock, call, patch

from playhouse.migrate import migrate

from common.basic.orm import test_utils
from common.basic.orm.database import db
from common.basic.orm.migrate.manager import migrating
from common.basic.orm.migrate.models import MigrationRecord


@test_utils.cls_test_database(MigrationRecord)
class TestMigrate(TestCase):
    @patch("common.basic.orm.migrate.manager.SqliteMigrator")
    @patch("common.basic.orm.migrate.manager.pkgutil")
    @patch("common.basic.orm.migrate.manager.importlib")
    @patch("common.basic.orm.migrate.manager.settings")
    def test_migrating(self, fake_settings, fake_importlib, fake_pkgutil, fake_sqlite_migrator_creator):
        fake_settings.DB_MODULES = [
            "common.module_a",
            "common.module_b",
        ]

        fake_update_callback = Mock()

        fake_migration_a_dir = Mock(
            __file__=True, __path__="/repo/src/module_a/migrations", __name__="common.module_a.migrations"
        )
        fake_migration_a_01 = Mock(
            __name__="common.module_a.migrations.01_init",
            update=Mock(side_effect=partial(fake_update_callback, test_tag="a_01")),
        )
        fake_migration_a_04 = Mock(
            __name__="common.module_a.migrations.04_update",
            update=Mock(side_effect=partial(fake_update_callback, test_tag="a_04")),
        )

        fake_migration_b_dir = Mock(
            __file__=True, __path__="/repo/src/module_b/migrations", __name__="common.module_b.migrations"
        )
        fake_migration_b_01 = Mock(
            __name__="common.module_b.migrations.01_init_models",
            update=Mock(side_effect=partial(fake_update_callback, test_tag="b_01")),
        )
        fake_migration_b_02 = Mock(
            __name__="common.module_b.migrations.02_update_models",
            update=Mock(side_effect=partial(fake_update_callback, test_tag="b_02")),
        )

        fake_importlib.import_module.side_effect = lambda i: {
            fake_migration_a_dir.__name__: fake_migration_a_dir,
            fake_migration_a_01.__name__: fake_migration_a_01,
            fake_migration_a_04.__name__: fake_migration_a_04,
            fake_migration_b_dir.__name__: fake_migration_b_dir,
            fake_migration_b_01.__name__: fake_migration_b_01,
            fake_migration_b_02.__name__: fake_migration_b_02,
        }.get(i)

        fake_pkgutil.iter_modules.side_effect = lambda i: {
            fake_migration_a_dir.__path__: [
                (1, "01_init", False),
                (2, "_02_deprecated", False),
                (3, "03_meaningless_dir", True),
                (4, "04_update", False),
            ],
            fake_migration_b_dir.__path__: [
                (1, "01_init_models", False),
                (2, "02_update_models", False),
            ],
        }.get(i)

        fake_migrator = Mock()
        fake_sqlite_migrator_creator.return_value = fake_migrator

        self.assertEqual(0, len(MigrationRecord.select()))
        MigrationRecord.create(module="module_a", name="01_init")  # Assuming it was done before

        migrating(db)

        records = list(MigrationRecord.select().order_by(MigrationRecord.id.asc()))
        self.assertEqual(4, len(records))
        self.assertEqual(
            [
                ("module_a", "01_init"),
                ("module_a", "04_update"),
                ("module_b", "01_init_models"),
                ("module_b", "02_update_models"),
            ],
            [(i.module, i.name) for i in records],
        )
        fake_update_callback.assert_has_calls(
            [
                call(db, fake_migrator, migrate, test_tag="a_04"),
                call(db, fake_migrator, migrate, test_tag="b_01"),
                call(db, fake_migrator, migrate, test_tag="b_02"),
            ]
        )
