from django.db import models
from rest_framework import serializers
from .tenancy import current_company_id


class CompanyModelSerializer(serializers.ModelSerializer):
    def run_validation(self, data=serializers.empty):
        attrs = super().run_validation(data)
        model = self.Meta.model
        if not any(f.name == 'company' for f in model._meta.fields):
            return attrs
        company_id = current_company_id() or getattr(self.instance, 'company_id', None)
        if not company_id:
            return attrs
        for constraint in model._meta.constraints:
            if not isinstance(constraint, models.UniqueConstraint) or not constraint.fields:
                continue
            values = {}
            for name in constraint.fields:
                value = company_id if name == 'company' else attrs.get(name, getattr(self.instance, name, None))
                if value is None:
                    break
                values['company_id' if name == 'company' else name] = value
            else:
                qs = model.objects.filter(**values)
                if self.instance:
                    qs = qs.exclude(pk=self.instance.pk)
                if qs.exists():
                    field = next((f for f in constraint.fields if f != 'company'), 'non_field_errors')
                    raise serializers.ValidationError({field: 'This value already exists in your company.'})
        return attrs
