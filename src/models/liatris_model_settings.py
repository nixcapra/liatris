# SPDX-FileCopyrightText: Copyright © 2023 nixcapra
# SPDX-License-Identifier: MIT

import sqlalchemy as db
from sqlalchemy.ext.declarative import declarative_base

BASE = declarative_base()


class LiatrisSetting(BASE):
    __tablename__ = "LiatrisSettings"

    Key = db.Column("Key", db.String, primary_key=True)
    Value = db.Column("Value", db.String)
