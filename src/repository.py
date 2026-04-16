import logging
import sqlite3

from src.models import Comment, Post, User

logger = logging.getLogger(__name__)


class Repository:
    def create_tables(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id       INTEGER PRIMARY KEY,
                name     TEXT    NOT NULL,
                username TEXT    NOT NULL,
                email    TEXT    NOT NULL,
                phone    TEXT    NOT NULL DEFAULT '',
                website  TEXT    NOT NULL DEFAULT ''
            )
        """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_addresses (
                user_id  INTEGER PRIMARY KEY,
                street   TEXT    NOT NULL DEFAULT '',
                suite    TEXT    NOT NULL DEFAULT '',
                city     TEXT    NOT NULL DEFAULT '',
                zipcode  TEXT    NOT NULL DEFAULT '',
                geo_lat  TEXT    NOT NULL DEFAULT '',
                geo_lng  TEXT    NOT NULL DEFAULT '',
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_companies (
                user_id       INTEGER PRIMARY KEY,
                name          TEXT    NOT NULL DEFAULT '',
                catch_phrase  TEXT    NOT NULL DEFAULT '',
                bs            TEXT    NOT NULL DEFAULT '',
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS posts (
                id      INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title   TEXT    NOT NULL,
                body    TEXT    NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS comments (
                id      INTEGER PRIMARY KEY,
                post_id INTEGER NOT NULL,
                name    TEXT    NOT NULL,
                email   TEXT    NOT NULL,
                body    TEXT    NOT NULL,
                FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
            )
        """
        )
        logger.info("Схема БД проверена / создана")

    def upsert_users(self, conn: sqlite3.Connection, users: list[User]) -> int:
        sql = """
            INSERT INTO users (id, name, username, email, phone, website)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name    = excluded.name,
                username = excluded.username,
                email   = excluded.email,
                phone   = excluded.phone,
                website = excluded.website
        """
        tuples = [user.to_db_tuple() for user in users]
        conn.executemany(sql, tuples)
        logger.info("Upsert users: %d записей", len(tuples))
        return len(tuples)

    def upsert_user_addresses(self, conn: sqlite3.Connection, users: list[User]) -> int:
        sql = """
            INSERT INTO user_addresses (user_id, street, suite, city, zipcode, geo_lat, geo_lng)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                street  = excluded.street,
                suite   = excluded.suite,
                city    = excluded.city,
                zipcode = excluded.zipcode,
                geo_lat = excluded.geo_lat,
                geo_lng = excluded.geo_lng
        """
        tuples = [user.address.to_db_tuple(user.id) for user in users]
        conn.executemany(sql, tuples)
        logger.debug("Upsert addresses: %d записей", len(tuples))
        return len(tuples)

    def upsert_user_companies(self, conn: sqlite3.Connection, users: list[User]) -> int:
        sql = """
            INSERT INTO user_companies (user_id, name, catch_phrase, bs)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                name         = excluded.name,
                catch_phrase = excluded.catch_phrase,
                bs           = excluded.bs
        """
        tuples = [user.company.to_db_tuple(user.id) for user in users]
        conn.executemany(sql, tuples)
        logger.debug("Upsert companies: %d записей", len(tuples))
        return len(tuples)

    def upsert_posts(self, conn: sqlite3.Connection, posts: list[Post]) -> int:
        sql = """
            INSERT INTO posts (id, user_id, title, body)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                user_id = excluded.user_id,
                title   = excluded.title,
                body    = excluded.body
        """
        tuples = [post.to_db_tuple() for post in posts]
        conn.executemany(sql, tuples)
        logger.info("Upsert posts: %d записей", len(tuples))
        return len(tuples)

    def upsert_comments(self, conn: sqlite3.Connection, comments: list[Comment]) -> int:
        sql = """
            INSERT INTO comments (id, post_id, name, email, body)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                post_id = excluded.post_id,
                name    = excluded.name,
                email   = excluded.email,
                body    = excluded.body
        """
        tuples = [comment.to_db_tuple() for comment in comments]
        conn.executemany(sql, tuples)
        logger.info("Upsert comments: %d записей", len(tuples))
        return len(tuples)
