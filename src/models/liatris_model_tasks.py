# SPDX-FileCopyrightText: Copyright © 2023 nixcapra
# SPDX-License-Identifier: MIT

import sqlalchemy as db
from sqlalchemy.ext.declarative import declarative_base

BASE = declarative_base()


class LiatrisTask(BASE):
    __tablename__ = "LiatrisTasks"

    TaskId = db.Column("TaskId", db.Integer, primary_key=True)
    TaskName = db.Column("TaskName", db.String)
