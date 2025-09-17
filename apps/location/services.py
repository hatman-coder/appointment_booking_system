import logging
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.core.cache import cache

from .models import District, Division, Thana
from .selectors import LocationSelector

logger = logging.getLogger(__name__)


class LocationValidationError(Exception):
    """Custom exception for location validation errors"""

    pass


class LocationServices:
    """Service class for location-related business operations"""

    # Cache configuration
    CACHE_TIMEOUT = 3600 * 24  # 24 hours (location data rarely changes)
    CACHE_PREFIX = "location_"

    @staticmethod
    def get_all_divisions() -> Dict[str, Any]:
        """
        Get all divisions with caching
        """
        try:
            cache_key = f"{LocationServices.CACHE_PREFIX}all_divisions"
            divisions = cache.get(cache_key)

            if divisions is None:
                divisions_queryset = LocationSelector.get_all_divisions()
                divisions = [
                    {
                        "id": division.id,
                        "name": division.name,
                        "name_en": division.name_en,
                        "created_at": division.created_at,
                    }
                    for division in divisions_queryset
                ]
                cache.set(cache_key, divisions, LocationServices.CACHE_TIMEOUT)
                logger.info(f"Cached {len(divisions)} divisions")

            return {
                "success": True,
                "message": "Divisions retrieved successfully",
                "divisions": divisions,
                "total_count": len(divisions),
            }

        except Exception as e:
            logger.error(f"Error retrieving divisions: {str(e)}")
            return {"success": False, "message": "Failed to retrieve divisions"}

    @staticmethod
    def get_districts_by_division(division_id: int) -> Dict[str, Any]:
        """
        Get districts by division ID with caching and validation
        """
        try:
            # Validate division exists
            division = LocationSelector.get_division_by_id(division_id)
            if not division:
                return {"success": False, "message": "Division not found"}

            cache_key = f"{LocationServices.CACHE_PREFIX}districts_{division_id}"
            districts = cache.get(cache_key)

            if districts is None:
                districts_queryset = LocationSelector.get_districts_by_division(
                    division_id
                )
                districts = [
                    {
                        "id": district.id,
                        "name": district.name,
                        "name_en": district.name_en,
                        "division_id": district.division_id,
                        "division_name": district.division.name,
                        "created_at": district.created_at,
                    }
                    for district in districts_queryset
                ]
                cache.set(cache_key, districts, LocationServices.CACHE_TIMEOUT)
                logger.info(
                    f"Cached {len(districts)} districts for division {division_id}"
                )

            return {
                "success": True,
                "message": f"Districts retrieved successfully for {division.name}",
                "division": {
                    "id": division.id,
                    "name": division.name,
                    "name_en": division.name_en,
                },
                "districts": districts,
                "total_count": len(districts),
            }

        except Exception as e:
            logger.error(
                f"Error retrieving districts for division {division_id}: {str(e)}"
            )
            return {"success": False, "message": "Failed to retrieve districts"}

    @staticmethod
    def get_thanas_by_district(district_id: int) -> Dict[str, Any]:
        """
        Get thanas by district ID with caching and validation
        """
        try:
            # Validate district exists
            district = LocationSelector.get_district_by_id(district_id)
            if not district:
                return {"success": False, "message": "District not found"}

            cache_key = f"{LocationServices.CACHE_PREFIX}thanas_{district_id}"
            thanas = cache.get(cache_key)

            if thanas is None:
                thanas_queryset = LocationSelector.get_thanas_by_district(district_id)
                thanas = [
                    {
                        "id": thana.id,
                        "name": thana.name,
                        "name_en": thana.name_en,
                        "district_id": thana.district_id,
                        "district_name": thana.district.name,
                        "division_id": thana.district.division_id,
                        "division_name": thana.district.division.name,
                        "created_at": thana.created_at,
                    }
                    for thana in thanas_queryset
                ]
                cache.set(cache_key, thanas, LocationServices.CACHE_TIMEOUT)
                logger.info(f"Cached {len(thanas)} thanas for district {district_id}")

            return {
                "success": True,
                "message": f"Thanas retrieved successfully for {district.name}",
                "division": {
                    "id": district.division.id,
                    "name": district.division.name,
                    "name_en": district.division.name_en,
                },
                "district": {
                    "id": district.id,
                    "name": district.name,
                    "name_en": district.name_en,
                },
                "thanas": thanas,
                "total_count": len(thanas),
            }

        except Exception as e:
            logger.error(
                f"Error retrieving thanas for district {district_id}: {str(e)}"
            )
            return {"success": False, "message": "Failed to retrieve thanas"}

    @staticmethod
    def get_location_hierarchy(
        thana_id: int = None, district_id: int = None, division_id: int = None
    ) -> Dict[str, Any]:
        """
        Get complete location hierarchy for a given location
        Can start from any level (thana, district, or division)
        """
        try:
            result = {
                "success": True,
                "message": "Location hierarchy retrieved successfully",
                "hierarchy": {},
            }

            if thana_id:
                # Start from thana and get full hierarchy
                thana = LocationSelector.get_thana_by_id(thana_id)
                if not thana:
                    return {"success": False, "message": "Thana not found"}

                result["hierarchy"] = {
                    "division": {
                        "id": thana.district.division.id,
                        "name": thana.district.division.name,
                        "name_en": thana.district.division.name_en,
                    },
                    "district": {
                        "id": thana.district.id,
                        "name": thana.district.name,
                        "name_en": thana.district.name_en,
                    },
                    "thana": {
                        "id": thana.id,
                        "name": thana.name,
                        "name_en": thana.name_en,
                    },
                }

            elif district_id:
                # Start from district
                district = LocationSelector.get_district_by_id(district_id)
                if not district:
                    return {"success": False, "message": "District not found"}

                result["hierarchy"] = {
                    "division": {
                        "id": district.division.id,
                        "name": district.division.name,
                        "name_en": district.division.name_en,
                    },
                    "district": {
                        "id": district.id,
                        "name": district.name,
                        "name_en": district.name_en,
                    },
                }

            elif division_id:
                # Start from division
                division = LocationSelector.get_division_by_id(division_id)
                if not division:
                    return {"success": False, "message": "Division not found"}

                result["hierarchy"] = {
                    "division": {
                        "id": division.id,
                        "name": division.name,
                        "name_en": division.name_en,
                    }
                }
            else:
                return {
                    "success": False,
                    "message": "At least one location ID must be provided",
                }

            return result

        except Exception as e:
            logger.error(f"Error retrieving location hierarchy: {str(e)}")
            return {
                "success": False,
                "message": "Failed to retrieve location hierarchy",
            }

    @staticmethod
    def validate_location_hierarchy(
        division_id: int, district_id: int = None, thana_id: int = None
    ) -> Dict[str, Any]:
        """
        Validate that the provided location hierarchy is correct
        (e.g., district belongs to division, thana belongs to district)
        """
        try:
            # Validate division
            division = LocationSelector.get_division_by_id(division_id)
            if not division:
                return {"success": False, "message": "Invalid division ID"}

            validation_result = {
                "success": True,
                "message": "Location hierarchy is valid",
                "validated_locations": {
                    "division": {"id": division.id, "name": division.name}
                },
            }

            # Validate district if provided
            if district_id:
                district = LocationSelector.get_district_by_id(district_id)
                if not district:
                    return {"success": False, "message": "Invalid district ID"}

                if district.division_id != division_id:
                    return {
                        "success": False,
                        "message": f"District {district.name} does not belong to division {division.name}",
                    }

                validation_result["validated_locations"]["district"] = {
                    "id": district.id,
                    "name": district.name,
                }

                # Validate thana if provided
                if thana_id:
                    thana = LocationSelector.get_thana_by_id(thana_id)
                    if not thana:
                        return {"success": False, "message": "Invalid thana ID"}

                    if thana.district_id != district_id:
                        return {
                            "success": False,
                            "message": f"Thana {thana.name} does not belong to district {district.name}",
                        }

                    validation_result["validated_locations"]["thana"] = {
                        "id": thana.id,
                        "name": thana.name,
                    }

            logger.info(
                f"Location hierarchy validated: Division {division_id}, District {district_id}, Thana {thana_id}"
            )
            return validation_result

        except Exception as e:
            logger.error(f"Error validating location hierarchy: {str(e)}")
            return {
                "success": False,
                "message": "Failed to validate location hierarchy",
            }

    @staticmethod
    def search_locations(query: str, location_type: str = "all") -> Dict[str, Any]:
        """
        Search locations by name across all levels
        """
        try:
            if not query or len(query.strip()) < 2:
                return {
                    "success": False,
                    "message": "Search query must be at least 2 characters long",
                }

            query = query.strip()
            search_results = {"divisions": [], "districts": [], "thanas": []}

            if location_type in ["all", "division"]:
                divisions = LocationSelector.search_divisions(query)
                search_results["divisions"] = [
                    {
                        "id": div.id,
                        "name": div.name,
                        "name_en": div.name_en,
                        "type": "division",
                    }
                    for div in divisions
                ]

            if location_type in ["all", "district"]:
                districts = LocationSelector.search_districts(query)
                search_results["districts"] = [
                    {
                        "id": dist.id,
                        "name": dist.name,
                        "name_en": dist.name_en,
                        "division_name": dist.division.name,
                        "type": "district",
                    }
                    for dist in districts
                ]

            if location_type in ["all", "thana"]:
                thanas = LocationSelector.search_thanas(query)
                search_results["thanas"] = [
                    {
                        "id": thana.id,
                        "name": thana.name,
                        "name_en": thana.name_en,
                        "district_name": thana.district.name,
                        "division_name": thana.district.division.name,
                        "type": "thana",
                    }
                    for thana in thanas
                ]

            # Calculate total results
            total_results = (
                len(search_results["divisions"])
                + len(search_results["districts"])
                + len(search_results["thanas"])
            )

            logger.info(f"Location search for '{query}': {total_results} results found")

            return {
                "success": True,
                "message": f'Found {total_results} locations matching "{query}"',
                "query": query,
                "results": search_results,
                "total_count": total_results,
            }

        except Exception as e:
            logger.error(f"Error searching locations: {str(e)}")
            return {"success": False, "message": "Failed to search locations"}

    @staticmethod
    def get_location_statistics() -> Dict[str, Any]:
        """
        Get location statistics for dashboard/admin use
        """
        try:
            cache_key = f"{LocationServices.CACHE_PREFIX}statistics"
            stats = cache.get(cache_key)

            if stats is None:
                stats = {
                    "total_divisions": LocationSelector.get_divisions_count(),
                    "total_districts": LocationSelector.get_districts_count(),
                    "total_thanas": LocationSelector.get_thanas_count(),
                }

                # Get additional statistics
                division_district_counts = (
                    LocationSelector.get_divisions_with_district_counts()
                )
                district_thana_counts = (
                    LocationSelector.get_districts_with_thana_counts()
                )

                stats.update(
                    {
                        "avg_districts_per_division": round(
                            stats["total_districts"] / max(stats["total_divisions"], 1),
                            2,
                        ),
                        "avg_thanas_per_district": round(
                            stats["total_thanas"] / max(stats["total_districts"], 1), 2
                        ),
                        "top_divisions_by_districts": [
                            {
                                "name": div["division__name"],
                                "district_count": div["district_count"],
                            }
                            for div in division_district_counts[:5]
                        ],
                        "top_districts_by_thanas": [
                            {
                                "name": dist["district__name"],
                                "division_name": dist["district__division__name"],
                                "thana_count": dist["thana_count"],
                            }
                            for dist in district_thana_counts[:5]
                        ],
                    }
                )

                cache.set(cache_key, stats, LocationServices.CACHE_TIMEOUT)
                logger.info("Location statistics cached")

            return {
                "success": True,
                "message": "Location statistics retrieved successfully",
                "statistics": stats,
            }

        except Exception as e:
            logger.error(f"Error retrieving location statistics: {str(e)}")
            return {
                "success": False,
                "message": "Failed to retrieve location statistics",
            }

    @staticmethod
    def get_complete_location_tree() -> Dict[str, Any]:
        """
        Get complete hierarchical location tree (divisions -> districts -> thanas)
        Useful for frontend dropdowns and complete location display
        """
        try:
            cache_key = f"{LocationServices.CACHE_PREFIX}complete_tree"
            location_tree = cache.get(cache_key)

            if location_tree is None:
                divisions = LocationSelector.get_all_divisions()
                location_tree = []

                for division in divisions:
                    division_data = {
                        "id": division.id,
                        "name": division.name,
                        "name_en": division.name_en,
                        "districts": [],
                    }

                    districts = LocationSelector.get_districts_by_division(division.id)
                    for district in districts:
                        district_data = {
                            "id": district.id,
                            "name": district.name,
                            "name_en": district.name_en,
                            "thanas": [],
                        }

                        thanas = LocationSelector.get_thanas_by_district(district.id)
                        district_data["thanas"] = [
                            {
                                "id": thana.id,
                                "name": thana.name,
                                "name_en": thana.name_en,
                            }
                            for thana in thanas
                        ]

                        division_data["districts"].append(district_data)

                    location_tree.append(division_data)

                cache.set(cache_key, location_tree, LocationServices.CACHE_TIMEOUT)
                logger.info(
                    f"Complete location tree cached with {len(location_tree)} divisions"
                )

            return {
                "success": True,
                "message": "Complete location tree retrieved successfully",
                "location_tree": location_tree,
                "total_divisions": len(location_tree),
            }

        except Exception as e:
            logger.error(f"Error retrieving complete location tree: {str(e)}")
            return {"success": False, "message": "Failed to retrieve location tree"}

    @staticmethod
    def clear_location_cache() -> Dict[str, Any]:
        """
        Clear all location-related cache entries
        Useful for admin operations when location data is updated
        """
        try:
            cache_keys = [
                f"{LocationServices.CACHE_PREFIX}all_divisions",
                f"{LocationServices.CACHE_PREFIX}statistics",
                f"{LocationServices.CACHE_PREFIX}complete_tree",
            ]

            # Clear general cache keys
            for key in cache_keys:
                cache.delete(key)

            # Clear division-specific caches (districts)
            divisions = Division.objects.all()
            for division in divisions:
                cache.delete(f"{LocationServices.CACHE_PREFIX}districts_{division.id}")

            # Clear district-specific caches (thanas)
            districts = District.objects.all()
            for district in districts:
                cache.delete(f"{LocationServices.CACHE_PREFIX}thanas_{district.id}")

            logger.info("All location cache cleared")

            return {"success": True, "message": "Location cache cleared successfully"}

        except Exception as e:
            logger.error(f"Error clearing location cache: {str(e)}")
            return {"success": False, "message": "Failed to clear location cache"}

    @staticmethod
    def bulk_validate_locations(location_data: List[Dict[str, int]]) -> Dict[str, Any]:
        """
        Validate multiple location hierarchies at once
        Useful for batch operations and data imports
        """
        try:
            validation_results = []
            valid_count = 0
            invalid_count = 0

            for i, location in enumerate(location_data):
                division_id = location.get("division_id")
                district_id = location.get("district_id")
                thana_id = location.get("thana_id")

                if not division_id:
                    validation_results.append(
                        {"index": i, "valid": False, "error": "Division ID is required"}
                    )
                    invalid_count += 1
                    continue

                validation_result = LocationServices.validate_location_hierarchy(
                    division_id, district_id, thana_id
                )

                if validation_result["success"]:
                    validation_results.append(
                        {
                            "index": i,
                            "valid": True,
                            "validated_locations": validation_result[
                                "validated_locations"
                            ],
                        }
                    )
                    valid_count += 1
                else:
                    validation_results.append(
                        {
                            "index": i,
                            "valid": False,
                            "error": validation_result["message"],
                        }
                    )
                    invalid_count += 1

            logger.info(
                f"Bulk location validation: {valid_count} valid, {invalid_count} invalid out of {len(location_data)}"
            )

            return {
                "success": True,
                "message": f"Bulk validation completed: {valid_count} valid, {invalid_count} invalid",
                "total_processed": len(location_data),
                "valid_count": valid_count,
                "invalid_count": invalid_count,
                "validation_results": validation_results,
            }

        except Exception as e:
            logger.error(f"Error in bulk location validation: {str(e)}")
            return {
                "success": False,
                "message": "Failed to perform bulk location validation",
            }
