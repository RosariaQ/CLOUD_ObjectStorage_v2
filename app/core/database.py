# app/core/database.py
import sqlite3
from flask import current_app, g
import click
import os # <--- 이 줄을 추가해주세요!

def get_db():
    if 'db' not in g:
        db_path = current_app.config['DATABASE']
        # 데이터베이스 파일이 저장될 디렉토리가 없으면 생성합니다.
        # 이 로직은 instance 폴더가 자동으로 생성되도록 도와줍니다.
        db_dir = os.path.dirname(db_path)
        if not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir)
                current_app.logger.info(f"Successfully created database directory: {db_dir}")
            except OSError as e:
                current_app.logger.error(f"Error creating database directory {db_dir}: {e}")
                # 디렉토리 생성 실패 시, 여기서 에러를 발생시키거나 다른 처리를 할 수 있습니다.
                # 하지만 connect 시도 시 어차피 파일이 없으면 에러가 발생할 것입니다.

        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    # schema.sql 파일의 경로를 config.py가 있는 프로젝트 루트 기준으로 수정합니다.
    # 현재 database.py는 app/core/ 안에 있으므로, ../../schema.sql 로 접근합니다.
    # 또는 config.py에서 SCHEMA_PATH 같은 설정을 추가하고 current_app.config['SCHEMA_PATH']를 사용할 수 있습니다.
    # 여기서는 상대 경로를 사용합니다.
    schema_path = os.path.join(current_app.root_path, '..', 'schema.sql')
    if not os.path.exists(schema_path):
        # schema.sql 파일이 app 폴더와 같은 레벨에 있다고 가정하고 경로 재조정
        schema_path_alt = os.path.join(os.path.dirname(current_app.root_path), 'schema.sql')
        if os.path.exists(schema_path_alt):
            schema_path = schema_path_alt
        else:
            click.echo(f"Error: schema.sql not found at {schema_path} or {schema_path_alt}. Please check the path.")
            current_app.logger.error(f"schema.sql not found at {schema_path} or {schema_path_alt}")
            return


    try:
        with current_app.open_resource(schema_path, mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
        click.echo('Initialized the database.')
        current_app.logger.info('Database initialized successfully.')
    except Exception as e:
        click.echo(f'Error initializing database: {e}')
        current_app.logger.error(f'Error initializing database: {e}')


@click.command('init-db')
def init_db_command():
    """Clear existing data and create new tables."""
    init_db()

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
