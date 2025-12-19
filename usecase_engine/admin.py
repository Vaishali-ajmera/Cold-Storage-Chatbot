from django.contrib import admin
from usecase_engine.models import UserInput

class UserInputAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'user_choice', 'created_at')
    list_filter = ('user_choice', 'created_at')


admin.site.register(UserInput, UserInputAdmin)

