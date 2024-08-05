from alembic import command
from alembic.config import Config

from src import DATA_DIR, WORK_DIR
from src.builder.db.crud import get_bots_ids


def run_migrations(database_url: str) -> None:
    alembic_cfg = Config(WORK_DIR / 'bot/db/alembic.ini')
    alembic_cfg.set_main_option('sqlalchemy.url', database_url)
    # command.revision(alembic_cfg, 'update', autogenerate=True)
    command.upgrade(alembic_cfg, 'head')


def main() -> None:
    database_urls = [f'sqlite:///{DATA_DIR.absolute()}/{bot}.db' for bot in get_bots_ids()]

    for url in database_urls:
        run_migrations(url)


if __name__ == '__main__':
    main()
