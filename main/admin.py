
from django.contrib import admin
from .models import Tag, Project, ProjectImage

# Register your models here.

class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1 # Upload 1 image. 

class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "link") # When viewing the list of projects, we see the title and link. 
    inlines = [ProjectImageInline]
    search_fields = ("title", "description") # Can search based on title and/or description. 
    list_filter = ("tags",) # Need trailing comma so it's treated as a tupple. 

class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

admin.site.register(Tag, TagAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(ProjectImage)