from django.template import Library
from web import models
from django.urls import reverse
register = Library()


@register.inclusion_tag('inclusion/manage_menu_list.html')
def manage_menu_list(request):
    data_list = [
        {'title': '考勤信息', 'url': reverse('facecheck', kwargs={'project_id': request.tracer.project.id})},
        {'title': '打卡', 'url': reverse('facepoint', kwargs={'project_id': request.tracer.project.id})},
        {'title': '人脸录入', 'url': reverse('facein', kwargs={'project_id': request.tracer.project.id})},

    ]
    for item in data_list:
        if request.path_info.startswith(item['url']):
            item['class'] = 'active'
    return {'data_list': data_list}
