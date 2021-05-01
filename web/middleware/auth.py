from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from web import models
import datetime


class Tracer(object):

    def __init__(self):
        self.user = None
        self.price_policy = None
        self.project = None


class AuthMiddleware(MiddlewareMixin):

    def process_request(self, request):
        """ 如果用户已登录，则request中赋值 """

        request.tracer = Tracer()

        user_id = request.session.get('user_id', 0)
        user_object = models.UserInfo.objects.filter(id=user_id).first()
        request.tracer.user = user_object

        # 白名单: 没有登录都可以访问的url
        """
        1.获取当前用户访问的url
        2.检测URL是否在当前白名单中，如果如果在则可以继续向后访问，如果未登录则返回到登录界面
        """
        item = request.path_info
        if request.path_info in settings.WHITE_REGEX_URL_LIST or item.startswith("/admin/"):
            return
        # 检测用户是否登录，如果已经登录继续往后走，未登录则返回登录界面
        if not request.tracer.user:
            return redirect('login')

        # 登录成功之后，访问后台管理时候：获取当前用户所拥有的额度
        # 方式一：免费额度在交易记录中存储
        # 获取当前用户ID最大(最新)的记录
        # _object = models.Transaction.objects.filter(user=user_object, status=2).order_by('-id').first()
        _object = models.Transaction.objects.filter(user=user_object, status=2).order_by('-price').first()
        # 判断是否已过期
        current_datetime = datetime.datetime.now()
        if _object.end_datetime and _object.end_datetime < current_datetime:
            # 过期设置成免费版
            _object = models.Transaction.objects.filter(user=user_object, status=2, price_policy__category=1).first()
        request.tracer.price_policy = _object.price_policy

    def process_view(self, request, view, args, kwargs):
        # 先判断url是否是以manage开头，如果是则判断项目id是否是我的
        if not request.path_info.startswith('/manage/'):
            return

        project_id = kwargs.get('project_id')
        # 判断是否是我创建的
        project_object = models.Project.objects.filter(creator=request.tracer.user, id=project_id).first()
        if project_object:
            # 是我创建的项目，我就让他通过
            request.tracer.project = project_object
            return
        # 是否是我参与的项目
        project_user_object = models.ProjectUser.objects.filter(user=request.tracer.user, project_id=project_id).first()
        if project_user_object:
            # 是我参与的项目
            request.tracer.project = project_user_object.project
            return

        return redirect('project_list')
