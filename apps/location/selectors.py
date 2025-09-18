from typing import List, Optional, Dict, Any
import uuid
from django.db.models import QuerySet, Count
from django.db.models import Q

from .models import District, Division, Thana


class LocationSelector:
    """Selector class for location-related queries"""

    @staticmethod
    def get_all_divisions() -> QuerySet:
        """Get all divisions ordered by name"""
        return Division.objects.all().order_by("name")

    @staticmethod
    def get_division_by_id(division_id: uuid) -> Optional[Division]:
        """Get division by ID"""
        try:
            return Division.objects.get(id=division_id)
        except Division.DoesNotExist:
            return None

    @staticmethod
    def get_division_by_code(code: str) -> Optional[Division]:
        """Get division by code"""
        try:
            return Division.objects.get(code=code)
        except Division.DoesNotExist:
            return None

    @staticmethod
    def get_districts_by_division(division_id: uuid) -> QuerySet:
        """Get all districts under a division"""
        return District.objects.filter(division_id=division_id).order_by("name")

    @staticmethod
    def get_district_by_id(district_id: uuid) -> Optional[District]:
        """Get district by ID with division"""
        try:
            return District.objects.select_related("division").get(id=district_id)
        except District.DoesNotExist:
            return None

    @staticmethod
    def get_thanas_by_district(district_id: uuid) -> QuerySet:
        """Get all thanas under a district"""
        return Thana.objects.filter(district_id=district_id).order_by("name")

    @staticmethod
    def get_thana_by_id(thana_id: uuid) -> Optional[Thana]:
        """Get thana by ID with district and division"""
        try:
            return Thana.objects.select_related("district__division").get(id=thana_id)
        except Thana.DoesNotExist:
            return None

    @staticmethod
    def search_locations(query: str) -> dict:
        """Search across all location types"""
        return {
            "divisions": Division.objects.filter(name__icontains=query),
            "districts": District.objects.filter(name__icontains=query).select_related(
                "division"
            ),
            "thanas": Thana.objects.filter(name__icontains=query).select_related(
                "district__division"
            ),
        }

    # Additional methods needed by LocationServices
    @staticmethod
    def search_divisions(query: str) -> QuerySet:
        """Search divisions by name (both English and local)"""
        return Division.objects.filter(
            Q(name__icontains=query) | Q(name_en__icontains=query)
            if hasattr(Division, "name_en")
            else Q(name__icontains=query)
        ).order_by("name")

    @staticmethod
    def search_districts(query: str) -> QuerySet:
        """Search districts by name (both English and local)"""
        return (
            District.objects.filter(
                Q(name__icontains=query) | Q(name_en__icontains=query)
                if hasattr(District, "name_en")
                else Q(name__icontains=query)
            )
            .select_related("division")
            .order_by("name")
        )

    @staticmethod
    def search_thanas(query: str) -> QuerySet:
        """Search thanas by name (both English and local)"""
        return (
            Thana.objects.filter(
                Q(name__icontains=query) | Q(name_en__icontains=query)
                if hasattr(Thana, "name_en")
                else Q(name__icontains=query)
            )
            .select_related("district__division")
            .order_by("name")
        )

    @staticmethod
    def get_divisions_count() -> int:
        """Get total count of divisions"""
        return Division.objects.count()

    @staticmethod
    def get_districts_count() -> int:
        """Get total count of districts"""
        return District.objects.count()

    @staticmethod
    def get_thanas_count() -> int:
        """Get total count of thanas"""
        return Thana.objects.count()

    @staticmethod
    def get_divisions_with_district_counts() -> List[Dict[str, Any]]:
        """Get divisions with their district counts, ordered by district count descending"""
        return list(
            Division.objects.annotate(district_count=Count("districts"))
            .values("name", "district_count")
            .order_by("-district_count")
        )

    @staticmethod
    def get_districts_with_thana_counts() -> List[Dict[str, Any]]:
        """Get districts with their thana counts, ordered by thana count descending"""
        return list(
            District.objects.annotate(thana_count=Count("thanas"))
            .select_related("division")
            .values("name", "division__name", "thana_count")
            .order_by("-thana_count")
        )

    @staticmethod
    def get_all_districts() -> QuerySet:
        """Get all districts ordered by name"""
        return District.objects.select_related("division").order_by("name")

    @staticmethod
    def get_all_thanas() -> QuerySet:
        """Get all thanas ordered by name"""
        return Thana.objects.select_related("district__division").order_by("name")

    @staticmethod
    def get_district_by_code(code: str) -> Optional[District]:
        """Get district by code"""
        try:
            return District.objects.select_related("division").get(code=code)
        except District.DoesNotExist:
            return None

    @staticmethod
    def get_thana_by_code(code: str) -> Optional[Thana]:
        """Get thana by code"""
        try:
            return Thana.objects.select_related("district__division").get(code=code)
        except Thana.DoesNotExist:
            return None

    @staticmethod
    def get_location_hierarchy(
        thana_id: uuid = None, district_id: uuid = None, division_id: uuid = None
    ) -> Optional[Dict[str, Any]]:
        """Get complete location hierarchy based on provided ID"""
        try:
            if thana_id:
                thana = LocationSelector.get_thana_by_id(thana_id)
                if thana:
                    return {
                        "division": {
                            "id": thana.district.division.id,
                            "name": thana.district.division.name,
                            "name_en": getattr(
                                thana.district.division,
                                "name_en",
                                thana.district.division.name,
                            ),
                        },
                        "district": {
                            "id": thana.district.id,
                            "name": thana.district.name,
                            "name_en": getattr(
                                thana.district, "name_en", thana.district.name
                            ),
                        },
                        "thana": {
                            "id": thana.id,
                            "name": thana.name,
                            "name_en": getattr(thana, "name_en", thana.name),
                        },
                    }
            elif district_id:
                district = LocationSelector.get_district_by_id(district_id)
                if district:
                    return {
                        "division": {
                            "id": district.division.id,
                            "name": district.division.name,
                            "name_en": getattr(
                                district.division, "name_en", district.division.name
                            ),
                        },
                        "district": {
                            "id": district.id,
                            "name": district.name,
                            "name_en": getattr(district, "name_en", district.name),
                        },
                    }
            elif division_id:
                division = LocationSelector.get_division_by_id(division_id)
                if division:
                    return {
                        "division": {
                            "id": division.id,
                            "name": division.name,
                            "name_en": getattr(division, "name_en", division.name),
                        }
                    }
            return None
        except Exception:
            return None

    @staticmethod
    def get_locations_with_pagination(
        location_type: str, page: uuid = 1, limit: uuid = 20
    ) -> Dict[str, Any]:
        """Get locations with pagination"""
        from django.core.paginator import Paginator

        if location_type == "division":
            queryset = LocationSelector.get_all_divisions()
        elif location_type == "district":
            queryset = LocationSelector.get_all_districts()
        elif location_type == "thana":
            queryset = LocationSelector.get_all_thanas()
        else:
            return {"success": False, "message": "Invalid location type"}

        paginator = Paginator(queryset, limit)
        locations_page = paginator.get_page(page)

        locations_data = []
        for location in locations_page:
            location_data = {
                "id": location.id,
                "name": location.name,
                "name_en": getattr(location, "name_en", location.name),
                "code": getattr(location, "code", ""),
            }

            if location_type == "district":
                location_data["division"] = {
                    "id": location.division.id,
                    "name": location.division.name,
                    "name_en": getattr(
                        location.division, "name_en", location.division.name
                    ),
                }
            elif location_type == "thana":
                location_data["district"] = {
                    "id": location.district.id,
                    "name": location.district.name,
                    "name_en": getattr(
                        location.district, "name_en", location.district.name
                    ),
                }
                location_data["division"] = {
                    "id": location.district.division.id,
                    "name": location.district.division.name,
                    "name_en": getattr(
                        location.district.division,
                        "name_en",
                        location.district.division.name,
                    ),
                }

            locations_data.append(location_data)

        return {
            "success": True,
            "locations": locations_data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total_pages": paginator.num_pages,
                "total_count": paginator.count,
                "has_next": locations_page.has_next(),
                "has_previous": locations_page.has_previous(),
            },
        }

    @staticmethod
    def validate_location_hierarchy(
        division_id: uuid = None, district_id: uuid = None, thana_id: uuid = None
    ) -> Dict[str, Any]:
        """Validate that the provided location IDs form a valid hierarchy"""
        try:
            if thana_id:
                thana = LocationSelector.get_thana_by_id(thana_id)
                if not thana:
                    return {"valid": False, "message": "Thana not found"}

                if district_id and thana.district.id != district_id:
                    return {
                        "valid": False,
                        "message": "Thana does not belong to the specified district",
                    }

                if division_id and thana.district.division.id != division_id:
                    return {
                        "valid": False,
                        "message": "Thana does not belong to the specified division",
                    }

                return {
                    "valid": True,
                    "hierarchy": {
                        "division_id": thana.district.division.id,
                        "district_id": thana.district.id,
                        "thana_id": thana.id,
                    },
                }

            elif district_id:
                district = LocationSelector.get_district_by_id(district_id)
                if not district:
                    return {"valid": False, "message": "District not found"}

                if division_id and district.division.id != division_id:
                    return {
                        "valid": False,
                        "message": "District does not belong to the specified division",
                    }

                return {
                    "valid": True,
                    "hierarchy": {
                        "division_id": district.division.id,
                        "district_id": district.id,
                    },
                }

            elif division_id:
                division = LocationSelector.get_division_by_id(division_id)
                if not division:
                    return {"valid": False, "message": "Division not found"}

                return {"valid": True, "hierarchy": {"division_id": division.id}}

            return {"valid": False, "message": "No location IDs provided"}

        except Exception as e:
            return {"valid": False, "message": f"Error validating hierarchy: {str(e)}"}

    @staticmethod
    def get_nearby_locations(
        location_type: str, location_id: uuid, radius_type: str = "same_parent"
    ) -> QuerySet:
        """Get nearby locations based on hierarchy"""
        try:
            if location_type == "thana":
                thana = LocationSelector.get_thana_by_id(location_id)
                if not thana:
                    return Thana.objects.none()

                if radius_type == "same_district":
                    return (
                        Thana.objects.filter(district=thana.district)
                        .exclude(id=location_id)
                        .order_by("name")
                    )
                elif radius_type == "same_division":
                    return (
                        Thana.objects.filter(district__division=thana.district.division)
                        .exclude(id=location_id)
                        .order_by("name")
                    )

            elif location_type == "district":
                district = LocationSelector.get_district_by_id(location_id)
                if not district:
                    return District.objects.none()

                if radius_type == "same_division":
                    return (
                        District.objects.filter(division=district.division)
                        .exclude(id=location_id)
                        .order_by("name")
                    )

            return QuerySet()

        except Exception:
            return QuerySet()
