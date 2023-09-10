# SPDX-FileCopyrightText: Copyright © 2023 nixcapra
# SPDX-License-Identifier: MIT

import os
import sqlalchemy as db
import sqlalchemy_utils as dbu
from sqlalchemy.orm import sessionmaker
from re import search as research

from models.liatris_model_settings import LiatrisSetting
from models.liatris_model_tasks import LiatrisTask
from models.liatris_model_items import LiatrisItem
from models.liatris_model_itemnotes import LiatrisItemNote

DB_DIR = "/home/" + os.getlogin() + "/.liatris"
DB_FILE = DB_DIR + "/liatrisdb"


# Initializes the database
def init_db():
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)

    engine = db.create_engine("sqlite:///" + DB_FILE)
    if not dbu.database_exists(engine.url):
        dbu.create_database(engine.url)

    meta = db.MetaData()

    liatris_settings = db.Table(
        "LiatrisSettings", meta,
        db.Column("Key", db.String, primary_key=True),
        db.Column("Value", db.String)
    )

    liatris_tasks = db.Table(
        "LiatrisTasks", meta,
        db.Column("TaskId", db.Integer, primary_key=True),
        db.Column("TaskName", db.String)
    )

    liatris_items = db.Table(
        "LiatrisItems", meta,
        db.Column("ItemId", db.Integer, primary_key=True),
        db.Column("TaskId", db.Integer),
        db.Column("ItemIsDone", db.Boolean),
        db.Column("ItemTitle", db.String),
        db.Column("ItemDate", db.DateTime)
    )

    liatris_item_notes = db.Table(
        "LiatrisItemNotes", meta,
        db.Column("NoteId", db.Integer, primary_key=True),
        db.Column("ItemId", db.Integer, unique=True),
        db.Column("NoteContent", db.Text)
    )

    meta.create_all(engine)
    return engine


ENGINE = init_db()
SESSION = sessionmaker(bind=ENGINE)
__SESSION__ = SESSION()


# A class containing a Task with its associated items
class LiatrisTaskItem:
    TASK = None
    ITEMS = None

    def __init__(self, task, items):
        if isinstance(task, LiatrisTask) and isinstance(items, list):
            self.TASK = task
            self.ITEMS = items


class LiatrisSQLCore:
    # Adds one object entry to the database
    # Takes a object instance.
    def insert(obj):
        try:
            __SESSION__.add(obj, _warn=False)
            __SESSION__.commit()
        except db.exc.SQLAlchemyError:
            __SESSION__.rollback()
            return False
        return True

    # Adds many object entries to the database
    def insert_many(object_list):
        try:
            __SESSION__.add_all(object_list)
            __SESSION__.commit()
        except db.exc.SQLAlchemyError:
            __SESSION__.rollback()
            return False
        return True

    # Settings specific database functions
    class Settings:

        # Retrieves a settings by the provided key from the database
        def get_setting_by_key(key):
            setting = None
            try:
                setting = __SESSION__.query(LiatrisSetting).filter(LiatrisSetting.Key == key).first()
            except db.exc.SQLAlchemyError:
                return False
            if setting is None:
                return False
            return setting

        # Updates a settings object in the database
        def update_setting(setting):
            try:
                stmt = db.update(LiatrisSetting).where(LiatrisSetting.Key == setting.Key).values(Value=setting.Value). \
                    execution_options(synchronize_session="fetch")
                __SESSION__.execute(stmt)
                __SESSION__.commit()
            except:
                __SESSION__.rollback()
                return False
            return True

    class Tasks:
        # Deletes a task and all associated items of that task from the database
        def delete_task(task_id):
            try:
                __SESSION__.query(LiatrisTask).filter(LiatrisTask.TaskId == task_id).delete()
                # Remove all associated tasks from LiatrisItems and LiatrisItemNotes
                as_items = __SESSION__.query(LiatrisItem).filter(LiatrisItem.TaskId == task_id).all()
                item_ids = []
                for item in as_items:
                    item_ids.append(item.ItemId)

                __SESSION__.query(LiatrisItemNote).filter(LiatrisItemNote.ItemId in item_ids).delete()
                __SESSION__.query(LiatrisItem).filter(LiatrisItem.TaskId == task_id).delete()
                __SESSION__.commit()
            except db.exc.SQLAlchemyError:
                __SESSION__.rollback()
                return False
            return True

        @staticmethod
        def get_all_tasks():
            task = None
            try:
                task = __SESSION__.query(LiatrisTask)
            except db.exc.SQLAlchemyError:
                return False
            if task is None:
                return False
            return task.all()

        # Updates a task in the database with a new name
        def update_task(task):
            try:
                stmt = db.update(LiatrisTask).where(LiatrisTask.TaskId == task.TaskId).values(TaskName=task.TaskName) \
                    .execution_options(synchronize_session="fetch")
                __SESSION__.execute(stmt)
                __SESSION__.commit()
            except:
                __SESSION__.rollback()
                return False
            return True

        # Produces a list of all tasks with their associated items
        @staticmethod
        def produce_all_task_items():
            task_items = []
            try:
                tasks = __SESSION__.query(LiatrisTask).all()

                for task in tasks:
                    as_items = __SESSION__.query(LiatrisItem).filter(LiatrisItem.TaskId == task.TaskId).all()

                    task_item = LiatrisTaskItem(task, as_items)
                    task_items.append(task_item)
            except db.exc.SQLAlchemyError:
                return False
            return task_items

        # Produces a list of a specific task, identified by id with its associated items
        def produce_task_item_by_task_id(task_id):
            task_item = None
            try:
                task = __SESSION__.query(LiatrisTask).filter(LiatrisTask.TaskId == task_id).first()
                if task is None:
                    return False

                as_items = __SESSION__.query(LiatrisItem).filter(LiatrisItem.TaskId == task.TaskId).all()

                task_item = LiatrisTaskItem(task, as_items)
            except db.exc.SQLAlchemyError:
                return False
            if task_item is None:
                return False
            return task_item

        # Searches all tasks by their title
        def search_tasks(search_key):
            tasks = []
            search_key = str(search_key).lower()
            try:
                all_tasks = __SESSION__.query(LiatrisTask).all()

                for task in all_tasks:
                    if task.TaskName is not None and task.TaskId is not None:
                        if research(search_key, str(task.TaskName.lower())) is not None:
                            tasks.append(task)

            except db.exc.SQLAlchemyError:
                return False
            return tasks

        # This function searches items by name and date with the search key and joins back to the task to create
        # TaskItem objects
        def search_task_items(search_key):
            task_items = []
            search_key = str(search_key).lower()
            search_key = search_key.split(" ")
            try:
                tasks = __SESSION__.query(LiatrisTask).all()

                for task in tasks:
                    as_items = __SESSION__.query(LiatrisItem).filter(LiatrisItem.TaskId == task.TaskId).all()

                    filtered_items = []

                    for key in search_key:
                        for item in as_items:
                            if (research(key, str(item.ItemTitle).lower()) is not None or
                                    research(key, str(item.ItemDate).split(" ")[0]) is not None):
                                filtered_items.append(item)

                    seen = set()
                    filtered_items = [x for x in filtered_items if x not in seen and not seen.add(x)]

                    if len(filtered_items) != 0:
                        task_item = LiatrisTaskItem(task, filtered_items)
                        task_items.append(task_item)
            except db.exc.SQLAlchemyError:
                return False
            return task_items

    class Items:
        # Allows you to update items in the database (use this to mark items as completed)
        def update_item(item):
            try:
                stmt = db.update(LiatrisItem).where(LiatrisItem.ItemId == item.ItemId) \
                    .values(TaskId=item.TaskId, ItemIsDone=item.ItemIsDone, \
                            ItemTitle=item.ItemTitle, ItemDate=item.ItemDate) \
                    .execution_options(synchronize_session="fetch")
                __SESSION__.execute(stmt)
                __SESSION__.commit()
            except:
                __SESSION__.rollback()
                return False
            return True

        # Retrieves an item from the database by its itemid
        def get_item_by_id(item_id):
            item = None
            try:
                item = __SESSION__.query(LiatrisItem).filter(LiatrisItem.ItemId == item_id)
            except db.exc.SQLAlchemyError:
                return False
            if item is None:
                return False
            return item.first()

        # Deletes an item from the database
        def delete_item(item_id):
            try:
                # Remove both the item and the item note from the database
                __SESSION__.query(LiatrisItemNote).filter(LiatrisItemNote.ItemId == item_id).delete()
                __SESSION__.query(LiatrisItem).filter(LiatrisItem.ItemId == item_id).delete()
                __SESSION__.commit()
            except db.exc.SQLAlchemyError:
                __SESSION__.rollback()
                return False
            return True

    class ItemNotes:
        # This updates an item notes content entry in the database we do not allow moving item notes around different
        # items
        def update_item_note(item_note):
            try:
                stmt = db.update(LiatrisItemNote).where(LiatrisItemNote.NoteId == item_note.NoteId) \
                    .values(NoteContent=item_note.NoteContent) \
                    .execution_options(synchronize_session="fetch")
                __SESSION__.execute(stmt)
                __SESSION__.commit()
            except:
                __SESSION__.rollback()
                return False
            return True

        # Gets an item note entry based on the id of its item
        def get_item_note_by_item_id(item_id):
            item_note = None
            try:
                item_note = __SESSION__.query(LiatrisItemNote).filter(LiatrisItemNote.ItemId == item_id).first()
            except db.exc.SQLAlchemyError:
                return False
            if item_note is None:
                return False
            return item_note
