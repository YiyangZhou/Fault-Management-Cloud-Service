from django.shortcuts import render, HttpResponse, redirect
from django.http import JsonResponse
from web.forms.project import ProjectModelForm
from web import models
from utils.tencent.cos import creat_bucket
import time


def project_list(request):
    """ 项目列表 """
    if request.method == 'GET':
        # GET请求查看项目列表
        """
        1. 从数据库中获取两部分数据
            我创建的所有项目：已星标、未星标
            我参与的所有项目：已星标、未星标
        2. 提取已星标
            列表 = 循环 [我创建的所有项目] + [我参与的所有项目] 把已星标的数据提取
        
        得到三个列表：星标、创建、参与
        """
        project_dict = {'star': [], 'my': [], 'join': []}

        my_project_list = models.Project.objects.filter(creator=request.tracer.user)
        for row in my_project_list:
            if row.star:
                project_dict['star'].append({'value': row, 'type': 'my'})
            else:
                project_dict['my'].append(row)

        join_project_list = models.ProjectUser.objects.filter(user=request.tracer.user)
        for item in join_project_list:
            if item.star:
                # 上面表和下面表查询出来是不同的对象
                project_dict['star'].append({'value': item.project, 'type': 'join'})
            else:
                project_dict['join'].append(item.project)

        form = ProjectModelForm(request)
        return render(request, 'project_list.html', {'form': form, 'project_dict': project_dict})

    # POST,ajax添加项目
    form = ProjectModelForm(request, data=request.POST)
    if form.is_valid():
        # 为项目创建一个桶
        bucket = "{}-{}-1304183991".format(request.tracer.user.mobile_phone, str(int(time.time())))
        region = 'ap-nanjing'
        creat_bucket(bucket, region)
        # 把桶和区域写入到数据库
        form.instance.bucket = bucket
        form.instance.region = region
        # 验证通过:项目名，颜色，描述 + 还要加上一个creator谁创建的
        form.instance.creator = request.tracer.user
        # 创建项目
        instance = form.save()
        # 初始化项目问题类型
        # issues_type_object_list = []
        # for item in models.IssuesType.PROJECT_INIT_LIST:
        #     issues_type_object_list.append(models.IssuesType(project=instance, title=item))
        # models.IssuesType.objects.bulk_create(issues_type_object_list)
        return JsonResponse({'status': True})
    return JsonResponse({'status': False, 'error': form.errors})


def project_star(request, project_type, project_id):
    """ 星标项目 """
    if project_type == 'my':
        models.Project.objects.filter(id=project_id, creator=request.tracer.user).update(star=True)
        return redirect('project_list')
    if project_type == 'join':
        models.ProjectUser.objects.filter(project_id=project_id, user=request.tracer.user).update(star=True)
        return redirect('project_list')
    return HttpResponse('请求错误')


def project_unstar(request, project_type, project_id):
    """ 取消星标 """
    if project_type == 'my':
        models.Project.objects.filter(id=project_id, creator=request.tracer.user).update(star=False)
        return redirect('project_list')
    if project_type == 'join':
        models.ProjectUser.objects.filter(project_id=project_id, user=request.tracer.user).update(star=False)
        return redirect('project_list')
    return HttpResponse('请求错误')
