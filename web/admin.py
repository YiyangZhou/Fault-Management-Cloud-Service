from django.contrib import admin
from web.models import *

# Register your models here.

@admin.register(UserInfo)
class UserInfoAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'mobile_phone', 'password', 'image')

@admin.register(PricePolicy)
class PricePolicyAdmin(admin.ModelAdmin):
    list_display = ('category', 'title', 'price', 'project_num', 'project_member', 'project_space', 'per_file_size', 'create_datetime')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('status', 'order', 'user', 'price_policy', 'count', 'price', 'start_datetime', 'end_datetime', 'create_datetime')

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'desc', 'use_space', 'star', 'join_count', 'creator', 'create_datetime', 'bucket', 'region')

@admin.register(ProjectUser)
class ProjectUserAdmin(admin.ModelAdmin):
    list_display = ('project', 'user', 'star', 'create_datetime')

@admin.register(FileRepository)
class FileRepositoryAdmin(admin.ModelAdmin):
    list_display = ('project', 'file_type', 'name', 'key', 'file_size', 'file_path', 'update_user', 'update_datetime')

@admin.register(Wiki)
class WikiAdmin(admin.ModelAdmin):
    list_display = ('project', 'title', 'content', 'depth', 'parent')

@admin.register(Issues)
class IssuesAdmin(admin.ModelAdmin):
    list_display = ('project', 'issues_type', 'module', 'subject', 'desc', 'priority', 'status', 'assign', '关注者', 'start_date', 'end_date', 'mode', 'parent', 'creator', 'create_datetime', 'latest_update_datetime')

    def 关注者(self, obj):
        return [bt.username for bt in obj.attention.all()]
    filter_horizontal = ('attention',)

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('project', 'title')

@admin.register(IssuesType)
class IssuesTypeAdmin(admin.ModelAdmin):
    list_display = ('title', 'project')

@admin.register(IssuesReply)
class IssuesReplyAdmin(admin.ModelAdmin):
    list_display = ('reply_type', 'issues', 'content', 'creator', 'create_datetime')

@admin.register(ProjectInvite)
class ProjectInviteAdmin(admin.ModelAdmin):
    list_display = ('project', 'code', 'count', 'use_count', 'period', 'create_datetime', 'creator')
    
@admin.register(DateAndWeek)
class DateAndWeekAdmin(admin.ModelAdmin):
    list_display = ('project', 'user', 'starttime', 'endtime', 'status')



