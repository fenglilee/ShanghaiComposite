#!/usr/bin/env python
# -*- coding:utf-8 -*-

from datetime import datetime
from aops.applications.database import db
from aops.applications.exceptions.exception import ValidationError
from sqlalchemy.exc import IntegrityError


class TimeUtilModel:
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime(), nullable=False, default=datetime.now)
    deleted_at = db.Column(db.DateTime(), nullable=True)
    is_deleted = db.Column(db.Boolean(), nullable=False, default=False)

    def update_change(self):
        self.is_deleted = False
        self.updated_at = datetime.now()
        self.deleted_at = None
        db.session.commit()
        return self

    @classmethod
    def soft_delete_by(cls, **kwargs):
        cls.query.filter_by(**kwargs).update({'deleted_at': datetime.now(), 'is_deleted': True})
        return db.session.commit()


class MinModel(db.Model):
    __abstract__ = True

    @classmethod
    def create(cls, **kwargs):
        """Create a new record and save it the database."""
        instance = cls(**kwargs)
        return instance.save()

    @classmethod
    def create_if_not_exist(cls, **kwargs):
        if cls.find(**kwargs):
            return None
        return cls.create(**kwargs)

    def update(self, commit=True, **kwargs):
        """Update specific fields of a record."""
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        # return commit and self.save() or self
        return self.save(commit=commit)

    def save(self, commit=True):
        """Save the record."""
        db.session.add(self)
        if commit:
            try:
                db.session.commit()
            except IntegrityError as e:
                raise ValidationError(e)
            # refresh after commit, otherwise get Nothing.
            db.session.refresh(self)
        return self

    def delete(self, commit=True):
        """Remove the record from the database."""
        db.session.delete(self)
        return commit and db.session.commit()

    @classmethod
    def delete_by(cls, **kwargs):
        cls.query.filter_by(**kwargs).delete()
        return db.session.commit()

    def to_dict(self):
        """ not support column name starts with '_'
        """
        return dict([(k, getattr(self, k)) for k in self.__dict__.keys() if not k.startswith("_")])

    @classmethod
    def take(cls, n, reverse=False):
        return cls.query.order_by((reverse and '-' or '') + 'id').limit(n).all()

    @classmethod
    def first(cls):
        rs = cls.take(1)
        return rs[0] if rs else None

    @classmethod
    def last(cls):
        rs = cls.take(1, False)
        return rs[0] if rs else None

    @classmethod
    def count(cls, **kw):
        if kw:
            return cls.query.filter_by(**kw).count()
        else:
            return cls.query.count()

    @classmethod
    def get_session(cls):
        return db.session

    @classmethod
    def find(cls, **kwargs):
        return cls.query.filter_by(**kwargs).all()
