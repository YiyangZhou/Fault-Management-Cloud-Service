from django.shortcuts import render, HttpResponse
from django.db.models import Count, Q
from django.http import JsonResponse
from utils import get_time
from web import models
from django.shortcuts import render, redirect, HttpResponse
import os
import datetime
from utils import information, encrypt
from utils.face import Face
import xlwt
from django.db.models import Count
from io import BytesIO
import base64


def facecheck(request, project_id):
    """ BUG云智能打卡后台 """
    year = datetime.datetime.now().year
    attendance = list()
    time_list = models.DateAndWeek.objects.filter(project_id=project_id, starttime__year=year).values("id",
                                                                                                      "project__name",
                                                                                                      "user__username",
                                                                                                      "status",
                                                                                                      "starttime",
                                                                                                      "endtime")
    week_list = [0] * 7
    for i in range(7):
        time = get_time.getdate(i)
        # 获取当前星期几
        today = datetime.datetime.now().weekday() + 1
        attendance_count = models.DateAndWeek.objects.filter(project_id=project_id, starttime__contains=time).count()
        all_person = models.ProjectUser.objects.filter(project_id=project_id).count() + 1
        if (today - i) >= 0:
            week_list[today - i - 1] = int(attendance_count / all_person * 100)
        # attendance.append(int(attendance_count / all_person * 100))
    item = {}

    try:
        for item_obj in time_list:
            # datetime转化时间成字符串
            if item_obj['starttime']:
                starttime = datetime.datetime.strftime(item_obj['starttime'], '%Y-%m-%d %H:%M:%S')
            else:
                starttime = ""
            if item_obj['endtime']:
                endtime = datetime.datetime.strftime(item_obj['endtime'], '%Y-%m-%d %H:%M:%S')
            else:
                endtime = ""
            if item_obj['user__username'] in item.keys():
                item[item_obj['user__username']].append(
                    [starttime, endtime, item_obj['status'], item_obj['user__username']])
            else:
                item[item_obj['user__username']] = [
                    [starttime, endtime, item_obj['status'], item_obj['user__username']]]
    except:
        pass
    return render(request, 'face_check.html', {"item": item, "attendance": week_list})


def export(request, project_id):
    """
    导出xlsx文件
    """
    start = request.POST.get("start")
    end = request.POST.get("end")
    project_id = project_id
    excel_list = models.DateAndWeek.objects.filter(project_id=project_id, starttime__range=(start, end)).values(
        "user__username", "project__name", "starttime", "endtime", "status")

    # 设置HTTPResponse的类型
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment;filename=content.xls'
    # 创建一个文件对象
    wb = xlwt.Workbook(encoding='utf8')
    # 创建一个sheet对象
    sheet = wb.add_sheet('order-sheet')
    # 设置文件头的样式,这个不是必须的可以根据自己的需求进行更改
    style_heading = xlwt.easyxf("""
                font:
                    name Arial,
                    colour_index white,
                    bold on,
                    height 0xA0;
                align:
                    wrap off,
                    vert center,
                    horiz center;
                pattern:
                    pattern solid,
                    fore-colour 0x19;
                borders:
                    left THIN,
                    right THIN,
                    top THIN,
                    bottom THIN;
                """)

    # 写入文件标题
    sheet.write(0, 0, '用户名', style_heading)
    sheet.write(0, 1, '项目名', style_heading)
    sheet.write(0, 2, '签到时间', style_heading)
    sheet.write(0, 3, '签退时间', style_heading)
    sheet.write(0, 4, '状态', style_heading)
    # 写入数据
    data_row = 1
    # 这个是查询条件,可以根据自己的实际需求做调整.
    for i in excel_list:
        if i['starttime']:
            start_time = i['starttime'].strftime('%Y-%m-%d %H:%M:%S')
        else:
            start_time = None
        if i['endtime']:
            end_time = i['endtime'].strftime('%Y-%m-%d %H:%M:%S')
        else:
            end_time = None
        sheet.write(data_row, 0, i['user__username'])
        sheet.write(data_row, 1, i['project__name'])
        sheet.write(data_row, 2, start_time)
        sheet.write(data_row, 3, end_time)
        sheet.write(data_row, 4, i['status'])
        data_row = data_row + 1
    # 写出到IO
    output = BytesIO()
    wb.save(output)
    # 重新定位到开始
    output.seek(0)
    response.write(output.getvalue())
    return response


def facepoint(request, project_id):
    """ 打卡 """
    if request.method == "GET":
        return render(request, "face_point.html")
    images = request.POST.get("img")
    if not images:
        return JsonResponse(information.play_error)
    img = base64.b64decode(images.split(',')[1])
    img_path = os.path.join("faces", "images", "test.png")
    with open(img_path, 'wb') as m:
        m.write(img)
        m.close()
    # 普通模式========= 挺慢
    # score, job = Face.score(img_path)
    # ============== 数据库形式 ===============
    import time
    images_list = models.UserInfo.objects.filter(~Q(image_content=None), id=request.tracer.user.id).values(
        "image_content", "id")
    face_data = Face.face_detection(img_path)
    score = 1
    for item in images_list:
        try:
            score = Face.compare(face_data, eval(item['image_content']))

            if score < 0.4:
                user = item['id']
                break
        except:
            pass
        # return JsonResponse(information.play_error)
    # =========================================
    if score < 0.4:
        time = datetime.datetime.now()
        # 早上时间打卡
        if models.Project.objects.filter(id=project_id).first().morning_start < time.hour < models.Project.objects.filter(id=project_id).first().morning_end:
            is_get = models.DateAndWeek.objects.filter(user_id=user, starttime__year=time.year,
                                                       starttime__month=time.month, starttime__day=time.day,
                                                       project_id=request.tracer.project.id)
            if is_get:
                return JsonResponse(information.play_exits)
            if models.Project.objects.filter(id=project_id).first().morning_start + 1 <= time.hour < models.Project.objects.filter(id=project_id).first().morning_end:
                models.DateAndWeek.objects.create(user_id=user, project_id=request.tracer.project.id, starttime=time,
                                                  status="已迟到")
                return JsonResponse(information.play_late)
            else:
                models.DateAndWeek.objects.create(user_id=user, project_id=request.tracer.project.id, starttime=time,
                                                  status="已签到")
                return JsonResponse(information.play_success)
        # 下午时间打卡
        elif models.Project.objects.filter(id=project_id).first().arft_start < time.hour < models.Project.objects.filter(id=project_id).first().arft_end:
            models.DateAndWeek.objects.filter(user_id=user, starttime__year=time.year,
                                              starttime__month=time.month, starttime__day=time.day).update(endtime=time)
            return JsonResponse(information.play_back)
        else:
            return JsonResponse(information.play_error)

    return JsonResponse(information.play_error)


def facein(request, project_id):
    """ 录入人脸数据 """
    if request.method == "GET":
        return render(request, "face_in.html")

    pwd = encrypt.uid(request.tracer.user.id)
    images = request.POST.get("img")

    img = base64.b64decode(images.split(',')[1])
    if not images:
        return JsonResponse(information.play_error)
    is_image = models.UserInfo.objects.filter(id=request.tracer.user.id).values("image", "image_content").first()
    if is_image['image']:
        face_path = models.UserInfo.objects.filter(id=request.tracer.user.id).values("image").first().get('image')[6:]
        de_img1 = os.path.join("faces", face_path)
        de_img2 = os.path.join("web\\static\\faces", face_path)
        os.remove(de_img1)
        os.remove(de_img2)
        img_path1 = os.path.join("faces", pwd + '.png')
        img_path2 = os.path.join("web\\static\\faces", pwd + '.png')
        with open(img_path1, 'wb') as f:
            f.write(img)
            f.close()
        with open(img_path2, 'wb') as f:
            f.write(img)
            f.close()
        content = Face.face_detection(img_path1)
        models.UserInfo.objects.filter(id=request.tracer.user.id).update(image=img_path1, image_content=list(content))
        return JsonResponse(information.re_image)
    img_path1 = os.path.join("faces", pwd + '.png')
    img_path2 = os.path.join("web\\static\\faces", pwd + '.png')
    with open(img_path1, 'wb') as f:
        f.write(img)
        f.close()
    with open(img_path2, 'wb') as f:
        f.write(img)
        f.close()
    content = Face.face_detection(img_path1)
    models.UserInfo.objects.filter(id=request.tracer.user.id).update(image=img_path1, image_content=list(content))
    return JsonResponse(information.record_success)
