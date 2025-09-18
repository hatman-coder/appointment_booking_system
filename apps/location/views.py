import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .services import LocationServices

logger = logging.getLogger(__name__)
from core.enum import UserType


def standardize_response(success: bool, message: str, data=None, status_code=None):
    """
    Standardize API response format
    """
    response_data = {"success": success, "message": message}

    if data is not None:
        if isinstance(data, dict):
            response_data.update(data)
        else:
            response_data["data"] = data

    if status_code is None:
        status_code = status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST

    return Response(response_data, status=status_code)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_all_divisions(request):
    """
    Get all divisions
    GET /api/locations/divisions/

    No authentication required as location data is public
    """
    try:
        result = LocationServices.get_all_divisions()

        if result["success"]:
            return standardize_response(
                True,
                result["message"],
                {
                    "divisions": result["divisions"],
                    "total_count": result["total_count"],
                },
                status_code=status.HTTP_200_OK,
            )
        else:
            return standardize_response(
                False,
                result["message"],
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        logger.error(f"Get divisions API error: {str(e)}")
        return standardize_response(
            False,
            "Failed to retrieve divisions",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def get_districts_by_division(request, division_id):
    """
    Get districts by division ID
    GET /api/locations/divisions/{division_id}/districts/
    """
    try:
        result = LocationServices.get_districts_by_division(division_id)

        if result["success"]:
            return standardize_response(
                True,
                result["message"],
                {
                    "division": result["division"],
                    "districts": result["districts"],
                    "total_count": result["total_count"],
                },
                status_code=status.HTTP_200_OK,
            )
        else:
            return standardize_response(
                False, result["message"], status_code=status.HTTP_404_NOT_FOUND
            )

    except Exception as e:
        logger.error(f"Get districts API error: {str(e)}")
        return standardize_response(
            False,
            "Failed to retrieve districts",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def get_thanas_by_district(request, district_id):
    """
    Get thanas by district ID
    GET /api/locations/districts/{district_id}/thanas/
    """
    try:
        result = LocationServices.get_thanas_by_district(district_id)

        if result["success"]:
            return standardize_response(
                True,
                result["message"],
                {
                    "division": result["division"],
                    "district": result["district"],
                    "thanas": result["thanas"],
                    "total_count": result["total_count"],
                },
                status_code=status.HTTP_200_OK,
            )
        else:
            return standardize_response(
                False, result["message"], status_code=status.HTTP_404_NOT_FOUND
            )

    except Exception as e:
        logger.error(f"Get thanas API error: {str(e)}")
        return standardize_response(
            False,
            "Failed to retrieve thanas",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def get_location_hierarchy(request):
    """
    Get complete location hierarchy for a given location
    GET /api/locations/hierarchy/

    Query parameters:
    - thana_id: Get hierarchy starting from thana
    - district_id: Get hierarchy starting from district
    - division_id: Get hierarchy starting from division
    """
    try:
        thana_id = request.GET.get("thana_id")
        district_id = request.GET.get("district_id")
        division_id = request.GET.get("division_id")

        result = LocationServices.get_location_hierarchy(
            thana_id=thana_id, district_id=district_id, division_id=division_id
        )

        if result["success"]:
            return standardize_response(
                True,
                result["message"],
                {"hierarchy": result["hierarchy"]},
                status_code=status.HTTP_200_OK,
            )
        else:
            return standardize_response(
                False, result["message"], status_code=status.HTTP_400_BAD_REQUEST
            )

    except Exception as e:
        logger.error(f"Get location hierarchy API error: {str(e)}")
        return standardize_response(
            False,
            "Failed to retrieve location hierarchy",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def validate_location_hierarchy(request):
    """
    Validate location hierarchy
    POST /api/locations/validate/

    Expected payload:
    {
        "division_id": 1,
        "district_id": 2,     // optional
        "thana_id": 3         // optional
    }
    """
    try:
        division_id = request.data.get("division_id")
        district_id = request.data.get("district_id")
        thana_id = request.data.get("thana_id")

        if not division_id:
            return standardize_response(
                False,
                "Division ID is required",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        result = LocationServices.validate_location_hierarchy(
            division_id, district_id, thana_id
        )

        if result["success"]:
            return standardize_response(
                True,
                result["message"],
                {"validated_locations": result["validated_locations"]},
                status_code=status.HTTP_200_OK,
            )
        else:
            return standardize_response(
                False, result["message"], status_code=status.HTTP_400_BAD_REQUEST
            )

    except Exception as e:
        logger.error(f"Validate location hierarchy API error: {str(e)}")
        return standardize_response(
            False,
            "Failed to validate location hierarchy",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def search_locations(request):
    """
    Search locations by name
    GET /api/locations/search/

    Query parameters:
    - q: Search query (required, min 2 characters)
    - type: Location type filter ('division', 'district', 'thana', 'all' - default: 'all')
    """
    try:
        query = request.GET.get("q", "").strip()
        location_type = request.GET.get("type", "all").strip().lower()

        if not query:
            return standardize_response(
                False,
                "Search query parameter 'q' is required",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if location_type not in ["all", "division", "district", "thana"]:
            return standardize_response(
                False,
                "Invalid location type. Use 'all', 'division', 'district', or 'thana'",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        result = LocationServices.search_locations(query, location_type)

        if result["success"]:
            return standardize_response(
                True,
                result["message"],
                {
                    "query": result["query"],
                    "results": result["results"],
                    "total_count": result["total_count"],
                },
                status_code=status.HTTP_200_OK,
            )
        else:
            return standardize_response(
                False, result["message"], status_code=status.HTTP_400_BAD_REQUEST
            )

    except Exception as e:
        logger.error(f"Search locations API error: {str(e)}")
        return standardize_response(
            False,
            "Failed to search locations",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def get_location_tree(request):
    """
    Get complete hierarchical location tree
    GET /api/locations/tree/

    Returns the complete hierarchy: divisions -> districts -> thanas
    Useful for frontend dropdowns and complete location display
    """
    try:
        result = LocationServices.get_complete_location_tree()

        if result["success"]:
            return standardize_response(
                True,
                result["message"],
                {
                    "location_tree": result["location_tree"],
                    "total_divisions": result["total_divisions"],
                },
                status_code=status.HTTP_200_OK,
            )
        else:
            return standardize_response(
                False,
                result["message"],
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        logger.error(f"Get location tree API error: {str(e)}")
        return standardize_response(
            False,
            "Failed to retrieve location tree",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_location_statistics(request):
    """
    Get location statistics for admin dashboard
    GET /api/locations/statistics/

    Admin and authenticated users only
    """
    try:
        result = LocationServices.get_location_statistics()

        if result["success"]:
            return standardize_response(
                True,
                result["message"],
                {"statistics": result["statistics"]},
                status_code=status.HTTP_200_OK,
            )
        else:
            return standardize_response(
                False,
                result["message"],
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        logger.error(f"Get location statistics API error: {str(e)}")
        return standardize_response(
            False,
            "Failed to retrieve location statistics",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Admin-only endpoints
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def clear_location_cache(request):
    """
    Clear location cache (Admin only)
    POST /api/locations/admin/clear-cache/

    Useful when location data is updated in the database
    """
    try:
        # Check admin permission
        if request.user.user_type != UserType.ADMIN.value:
            return standardize_response(
                False,
                "Admin privileges required",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        result = LocationServices.clear_location_cache()

        if result["success"]:
            logger.info(f"Location cache cleared by admin: {request.user.email}")
            return standardize_response(
                True, result["message"], status_code=status.HTTP_200_OK
            )
        else:
            return standardize_response(
                False,
                result["message"],
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        logger.error(f"Clear location cache API error: {str(e)}")
        return standardize_response(
            False,
            "Failed to clear location cache",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Convenience endpoints for common use cases
@api_view(["GET"])
@permission_classes([AllowAny])
def get_districts_and_thanas(request, division_id):
    """
    Get districts and their thanas for a division (convenient for forms)
    GET /api/locations/divisions/{division_id}/complete/
    """
    try:
        # Get districts for the division
        districts_result = LocationServices.get_districts_by_division(division_id)

        if not districts_result["success"]:
            return standardize_response(
                False,
                districts_result["message"],
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Get thanas for each district
        districts_with_thanas = []
        for district in districts_result["districts"]:
            thanas_result = LocationServices.get_thanas_by_district(district["id"])

            district_data = {
                "id": district["id"],
                "name": district["name"],
                "thanas": thanas_result["thanas"] if thanas_result["success"] else [],
            }
            districts_with_thanas.append(district_data)

        return standardize_response(
            True,
            f"Complete location data retrieved for {districts_result['division']['name']}",
            {
                "division": districts_result["division"],
                "districts": districts_with_thanas,
                "total_districts": len(districts_with_thanas),
            },
            status_code=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.error(f"Get districts and thanas API error: {str(e)}")
        return standardize_response(
            False,
            "Failed to retrieve complete location data",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def get_location_breadcrumb(request):
    """
    Get location breadcrumb for navigation
    GET /api/locations/breadcrumb/

    Query parameters:
    - thana_id: Get breadcrumb for thana
    - district_id: Get breadcrumb for district
    - division_id: Get breadcrumb for division
    """
    try:
        thana_id = request.GET.get("thana_id")
        district_id = request.GET.get("district_id")
        division_id = request.GET.get("division_id")

        result = LocationServices.get_location_hierarchy(
            thana_id=thana_id, district_id=district_id, division_id=division_id
        )

        if result["success"]:
            # Convert hierarchy to breadcrumb format
            hierarchy = result["hierarchy"]
            breadcrumb = []

            if "division" in hierarchy:
                breadcrumb.append(
                    {
                        "id": hierarchy["division"]["id"],
                        "name": hierarchy["division"]["name"],
                        "type": "division",
                        "level": 1,
                    }
                )

            if "district" in hierarchy:
                breadcrumb.append(
                    {
                        "id": hierarchy["district"]["id"],
                        "name": hierarchy["district"]["name"],
                        "type": "district",
                        "level": 2,
                    }
                )

            if "thana" in hierarchy:
                breadcrumb.append(
                    {
                        "id": hierarchy["thana"]["id"],
                        "name": hierarchy["thana"]["name"],
                        "type": "thana",
                        "level": 3,
                    }
                )

            return standardize_response(
                True,
                "Location breadcrumb retrieved successfully",
                {"breadcrumb": breadcrumb},
                status_code=status.HTTP_200_OK,
            )
        else:
            return standardize_response(
                False, result["message"], status_code=status.HTTP_400_BAD_REQUEST
            )

    except Exception as e:
        logger.error(f"Get location breadcrumb API error: {str(e)}")
        return standardize_response(
            False,
            "Failed to retrieve location breadcrumb",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
