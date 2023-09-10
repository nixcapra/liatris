# SPDX-FileCopyrightText: Copyright © 2023 nixcapra
# SPDX-License-Identifier: MIT

import sqlalchemy as db
from sqlalchemy.ext.declarative import declarative_base

BASE = declarative_base()


class LiatrisItemNote(BASE):
    __tablename__ = "LiatrisItemNotes"

    NoteId = db.Column("NoteId", db.Integer, primary_key=True)
    ItemId = db.Column("ItemId", db.Integer, unique=True)
    NoteContent = db.Column("NoteContent", db.Text)
