from django.contrib import admin
from .models import Division, District, Thana


class DivisionAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "code", "created_at", "updated_at")
    search_fields = ("name", "code")
    ordering = ("name",)


class DistrictAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "code", "division", "created_at", "updated_at")
    list_filter = ("division",)
    search_fields = ("name", "code", "division__name")
    ordering = ("name",)


class ThanaAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "code", "district", "created_at", "updated_at")
    list_filter = ("district__division", "district")
    search_fields = ("name", "code", "district__name", "district__division__name")
    ordering = ("name",)


admin.site.register(Division, DivisionAdmin)
admin.site.register(District, DistrictAdmin)
admin.site.register(Thana, ThanaAdmin)
