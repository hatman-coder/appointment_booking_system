from drf_spectacular.utils import OpenApiParameter


def set_query_params(api_type=None, field_data=None):
    data = []
    if not field_data:
        field_data = []

    for field in field_data:
        data.append(OpenApiParameter(
            name=field.get('name', ''),
            type={'type': field.get('type', 'str')},
            location=OpenApiParameter.QUERY,
            required=field.get('required', False),
            style='form',
            explode=False,
            description=field.get("description", ""),
            enum=field.get("enum", None),
        ))

    return data
