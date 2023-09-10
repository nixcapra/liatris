# SPDX-FileCopyrightText: Copyright © 2023 nixcapra
# SPDX-License-Identifier: MIT

import sqlalchemy as db
from sqlalchemy.ext.declarative import declarative_base

BASE = declarative_base()


class LiatrisItem(BASE):
    __tablename__ = "LiatrisItems"

    ItemId = db.Column("ItemId", db.Integer, primary_key=True)
    TaskId = db.Column("TaskId", db.Integer)
    ItemIsDone = db.Column("ItemIsDone", db.Boolean)
    ItemTitle = db.Column("ItemTitle", db.String)
    ItemDate = db.Column("ItemDate", db.DateTime)
