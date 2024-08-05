from alembic import command
from alembic.config import Config

from src.builder.db.crud import get_bots_ids


def run_migrations(database_url: str) -> None:
    alembic_cfg = Config('./feedbackbot/bot/db/alembic.ini')
    alembic_cfg.set_main_option('sqlalchemy.url', database_url)
    command.upgrade(alembic_cfg, 'head')


def main() -> None:
    database_urls = [f'sqlite:///feedbackbot/data/{bot}.db' for bot in get_bots_ids()]

    for url in database_urls:
        run_migrations(url)


if __name__ == '__main__':
    main()
