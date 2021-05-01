from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from utils import encrypt, information
from utils.tencent.cos import delete_bucket
from web import models
import datetime


def setting(request, project_id):
    # 获取当前项目创建人的id
    now_project = models.Project.objects.filter(id=request.tracer.project.id).first()
    create = now_project.creator_id
    return render(request, 'setting.html', {'create': create})


@csrf_exempt
def managedel(request, project_id):
    """ 删除模块 """
    ret = request.POST.getlist('modelname')[0]
    exist = models.Module.objects.filter(project_id=request.tracer.project.id, title=ret).first()
    if exist:
        models.Module.objects.filter(project_id=request.tracer.project.id, title=ret).delete()
        return JsonResponse({'status': True})
    return JsonResponse({'status': False, 'error': ''})


@csrf_exempt
def managepro(request, project_id):
    if request.method == 'GET':
        # 获取当前项目创建人的id
        now_project = models.Project.objects.filter(id=request.tracer.project.id).first()
        create = now_project.creator_id
        # 从数据库获取模块
        model = models.Module.objects.filter(project_id=request.tracer.project.id)
        model_list = []
        for item in model:
            model_list.append(item.title)
        return render(request, 'setting_managepro.html', {'create': create, 'model_list': model_list})

    # print(request.POST.getlist('modelid')[0])
    # 如果相等报错
    exist = models.Module.objects.filter(title=request.POST.getlist('modelid')[0], project_id=project_id).first()
    if exist:
        return render(request, 'setting_managepro.html')
    # 把新增加模块存入数据库
    models.Module.objects.create(title=request.POST.getlist('modelid')[0], project_id=project_id)
    return JsonResponse({'status': True})


def mysetting(request, project_id):
    """个人资料的展示"""
    if request.method == 'GET':
        # 获取当前项目创建人的id
        now_project = models.Project.objects.filter(id=request.tracer.project.id).first()
        create = now_project.creator_id
        # 获取用户信息
        user_obj = models.UserInfo.objects.filter(id=request.tracer.user.id).first()
        # 获取用户的vip等级
        vip_id = models.Transaction.objects.filter(user=request.tracer.user.id, status=2,).order_by('-id').first().price_policy_id
        # 获取用户人脸照片路径
        face_path = models.UserInfo.objects.filter(id=request.tracer.user.id).first().image


        # 获取用户vip等级剩余天数
        leave_time = 0
        if vip_id != 1:
            end_time = models.Transaction.objects.filter(user=request.tracer.user.id, status=2, ).order_by('-id').first().end_datetime
            now_time = datetime.datetime.now()
            leave_time = end_time - now_time

            return render(request, 'setting_mysetting.html', {'user_obj': user_obj, 'vip_id': vip_id, 'leave_time': leave_time.days, 'create': create, 'face_path': face_path})
        return render(request, 'setting_mysetting.html', {'user_obj': user_obj, 'vip_id': vip_id, 'create': create, 'face_path': face_path})


def changepwd(request, project_id):
    """修改个人密码"""
    # 获取当前项目创建人的id
    now_project = models.Project.objects.filter(id=request.tracer.project.id).first()
    create = now_project.creator_id
    if request.method == 'GET':
        return render(request, 'setting_changepwd.html', {'create': create})

    key_value = request.POST.get('key_value')
    if len(key_value) < 8:
        return render(request, 'setting_changepwd.html', {'error': '密码长度不能小于8个字符', 'create': create})
    if len(key_value) > 64:
        return render(request, 'setting_changepwd.html', {'error': '密码长度不能大于64个字符', 'create': create})
    old_pwd = models.UserInfo.objects.filter(id=request.tracer.user.id).first().password
    if old_pwd == encrypt.md5(key_value):
        return render(request, 'setting_changepwd.html', {'error': '新密码不能与原密码相同', 'create': create})
    models.UserInfo.objects.filter(id=request.tracer.user.id).update(password=encrypt.md5(key_value))
    request.session.delete()
    return redirect('login')


def delete(request, project_id):
    """ 删除项目 """
    # 获取当前项目创建人的id
    now_project = models.Project.objects.filter(id=request.tracer.project.id).first()
    create = now_project.creator_id
    if request.method == 'GET':
        return render(request, 'setting_delete.html', {'create': create})
    project_name = request.POST.get('project_name')
    if not project_name or project_name != request.tracer.project.name:
        return render(request, 'setting_delete.html', {'error': '项目名错误', 'create': create})
    # 项目名写对了进行删除(只有创建者可以删除)
    if request.tracer.user != request.tracer.project.creator:
        return render(request, 'setting_delete.html', {'error': '只有项目创建者可以删除', 'create': create})
    # 1.删除桶:删除桶中文件，删除桶中所有碎片,删除桶
    # 2.删除项目
    delete_bucket(request.tracer.project.bucket, request.tracer.project.region)
    models.Project.objects.filter(id=request.tracer.project.id).delete()
    return redirect('project_list')


def signin(request, project_id):
    """ 更改签到时间 """
    now_project = models.Project.objects.filter(id=request.tracer.project.id).first()
    create = now_project.creator_id
    if request.method == 'GET':
        morning_time1 = models.Project.objects.filter(id=project_id).first().morning_start
        morning_time2 = models.Project.objects.filter(id=project_id).first().morning_end
        after_time1 = models.Project.objects.filter(id=project_id).first().arft_start
        after_time2 = models.Project.objects.filter(id=project_id).first().arft_end
        return render(request, 'setting_signin.html', {'create': create, 'morning1': morning_time1, 'morning2': morning_time2, 'arfter1': after_time1, 'arfter2': after_time2})
    mor1 = request.POST.get('mor1')
    mor2 = request.POST.get('mor2')
    arf1 = request.POST.get('arf1')
    arf2 = request.POST.get('arf2')

    # information.morning[0] = int(mor1)
    # information.morning[1] = int(mor2)
    # information.after[0] = int(arf1)
    # information.after[1] = int(arf2)
    models.Project.objects.filter(id=project_id).update(morning_start=mor1, morning_end=mor2, arft_start=arf1, arft_end=arf2)
    return render(request, 'setting_signin.html', {'create': create, 'morning1': mor1, 'morning2': mor2, 'arfter1': arf1, 'arfter2': arf2})
