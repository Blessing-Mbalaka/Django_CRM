"""
apps/analytics/api_views.py
Read-only analytics/reporting API endpoint.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError

from functionalities.analytics import services


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_report(request):
    """
    GET /api/analytics/
    Returns full institutional analytics context as JSON.
    """
    context = services.get_reports_context()

    # Serialize health_scores (contains model instances)
    health_scores = [
        {
            'engagement_id':    row['engagement'].pk,
            'engagement_title': row['engagement'].title,
            'days_since_contact': row['days'],
            'score':            row['score'],
            'label':            row['label'],
        }
        for row in (context.get('health_scores') or [])
    ]

    centre_performance = [
        {
            'centre_id':          row['centre'].pk,
            'centre_name':        row['centre'].name,
            'active_engagements': row.get('active_engagements', 0),
            'staff_count':        row.get('staff_count', 0),
            'revenue':            float(row.get('revenue') or 0),
        }
        for row in (context.get('centre_performance') or [])
    ]

    return Response({
        'total_clients':      context.get('total_clients', 0),
        'total_engagements':  context.get('total_engagements', 0),
        'total_revenue':      float(context.get('total_revenue') or 0),
        'unresolved_alerts':  context.get('unresolved_alerts', 0),
        'pipeline_analysis':  {
            'counts':   context.get('pipeline_analysis', {}).get('counts', {}),
            'pipeline': context.get('pipeline_analysis', {}).get('pipeline', {}),
        },
        'centre_performance': centre_performance,
        'health_scores':      health_scores,
        'staff_activity':     list(context.get('staff_activity') or []),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def business_activity(request):
    def optional_id(name):
        value = request.query_params.get(name)
        if not value:
            return None
        try:
            return serializers.IntegerField(min_value=1).run_validation(value)
        except serializers.ValidationError as exc:
            raise serializers.ValidationError({name: exc.detail}) from exc

    try:
        result = services.get_business_activity(
            start_date=request.query_params.get('start_date'),
            end_date=request.query_params.get('end_date'),
            granularity=request.query_params.get('granularity', 'month'),
            source=request.query_params.get('source', 'all'),
            product=optional_id('product'),
            location=optional_id('location'),
            supplier=optional_id('supplier'),
        )
    except DjangoValidationError as exc:
        detail = exc.message_dict if hasattr(exc, 'message_dict') else exc.messages
        raise serializers.ValidationError(detail) from exc
    return Response(result)
