"""Company boundaries shared by requests, ORM queries, jobs and model writes."""
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models


_company_id = ContextVar('company_id', default=None)


def current_company_id():
    return _company_id.get()


def default_company_id():
    # Reserved by the initial data migration; model construction must not query
    # the database (Django also instantiates User during pre-migration checks).
    return 1


def owned_company_id():
    return current_company_id() or default_company_id()


@contextmanager
def company_context(company):
    token = _company_id.set(getattr(company, 'pk', company))
    try:
        yield
    finally:
        _company_id.reset(token)


def company_job(func):
    """Legacy jobs operate on the original company; company_command selects another."""
    @wraps(func)
    def wrapped(*args, **kwargs):
        with company_context(owned_company_id()):
            return func(*args, **kwargs)
    return wrapped


def validate_company_links(model, company_id, values):
    for field in model._meta.concrete_fields:
        if not field.is_relation or field.name == 'company':
            continue
        related_model = field.remote_field.model
        if not any(f.name == 'company' for f in related_model._meta.fields):
            continue
        value = values.get(field.attname, values.get(field.name))
        if value is None:
            continue
        value = getattr(value, 'pk', value)
        if not related_model._base_manager.filter(pk=value, company_id=company_id).exists():
            raise ValidationError({field.name: 'Choose a record belonging to this company.'})


class CompanyQuerySet(models.QuerySet):
    def _clone(self):
        clone = super()._clone()
        clone._scoped_company_id = getattr(self, '_scoped_company_id', None)
        return clone

    def _apply_company(self):
        company_id = current_company_id()
        if company_id and getattr(self, '_scoped_company_id', None) != company_id:
            self.query.add_q(models.Q(company_id=company_id))
            self._scoped_company_id = company_id
        return self

    def _chain(self):
        # Class-level view querysets and copied form fields are scoped when cloned.
        return super()._chain()._apply_company()

    def _fetch_all(self):
        self._apply_company()
        return super()._fetch_all()

    def count(self):
        return super(CompanyQuerySet, self._apply_company()).count()

    def exists(self):
        return super(CompanyQuerySet, self._apply_company()).exists()

    def iterator(self, *args, **kwargs):
        self._apply_company()
        return super().iterator(*args, **kwargs)

    def aggregate(self, *args, **kwargs):
        self._apply_company()
        return super().aggregate(*args, **kwargs)

    def update(self, **kwargs):
        self._apply_company()
        if 'company' in kwargs or 'company_id' in kwargs:
            raise ValidationError('Company ownership cannot be changed by a bulk update.')
        if current_company_id():
            validate_company_links(self.model, current_company_id(), kwargs)
        return super().update(**kwargs)

    def delete(self):
        self._apply_company()
        return super().delete()

    def bulk_create(self, objs, **kwargs):
        objs = list(objs)
        for obj in objs:
            obj.validate_company()
        return super().bulk_create(objs, **kwargs)

    def bulk_update(self, objs, fields, **kwargs):
        objs = list(objs)
        if 'company' in fields or 'company_id' in fields:
            raise ValidationError('Company ownership cannot be changed by a bulk update.')
        for obj in objs:
            obj.validate_company()
        return super().bulk_update(objs, fields, **kwargs)


class CompanyManager(models.Manager.from_queryset(CompanyQuerySet)):
    def get_queryset(self):
        return super().get_queryset()._apply_company()


def validate_company_m2m(sender, instance, action, model, pk_set, **kwargs):
    if action != 'pre_add' or not pk_set:
        return
    company_id = getattr(instance, 'company_id', None)
    if company_id and any(f.name == 'company' for f in model._meta.fields):
        if model._base_manager.filter(pk__in=pk_set).exclude(company_id=company_id).exists():
            raise ValidationError('Related records must belong to the same company.')


def require_company_admin(user):
    if not user.is_authenticated or user.role not in ('admin', 'dean'):
        raise PermissionDenied('Company administrator access is required.')
