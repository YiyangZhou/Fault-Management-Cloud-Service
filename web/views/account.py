"""
用户账户相关的功能：注册,短信,登录,注销
"""
import uuid
import datetime
from web import models
from django.db.models import Q
from django.shortcuts import render, HttpResponse, redirect
from django.http import JsonResponse
from web.forms.account import RegisterModelForm, SendSmsForm, LoginSmsForm, LoginForm
from io import BytesIO
from utils.image_code import check_code


def register(request):
    """ 注册 """
    if request.method == 'GET':
        form = RegisterModelForm()
        return render(request, 'register.html', {'form': form})
    form = RegisterModelForm(data=request.POST)
    if form.is_valid():
        # 验证通过后,写入数据库（用户密码需要加密）
        instance = form.save()  # 通过save存入数据库它会自动剔除比如重复密码，验证码这种数据库中没用的字段，而models点手动添加比较繁琐
        # 创建交易记录
        policy_object = models.PricePolicy.objects.filter(category=1, title='个人免费版').first()
        models.Transaction.objects.create(
            status=2,
            order=str(uuid.uuid4()),
            user=instance,
            price_policy=policy_object,
            count=0,
            price=0,
            start_datetime=datetime.datetime.now()
        )
        return JsonResponse({'status': True, 'data': '/login/'})
    return JsonResponse({'status': False, 'error': form.errors})


def send_sms(request):
    """ 发送短信 """
    form = SendSmsForm(request, data=request.GET)
    # 只校验手机号：不能为空，格式是否正确
    if form.is_valid():
        return JsonResponse({'status': True})
    return JsonResponse({'status': False, 'error': form.errors})


def login_sms(request):
    """ 短信登录 """
    if request.method == 'GET':
        form = LoginSmsForm()
        return render(request, 'login_sms.html', {'form': form})
    form = LoginSmsForm(request.POST)
    if form.is_valid():
        # 用户输入正确，登录成功
        mobile_phone = form.cleaned_data['mobile_phone']
        # 将用户名放入session
        user_object = models.UserInfo.objects.filter(mobile_phone=mobile_phone).first()
        request.session['user_id'] = user_object.id
        request.session.set_expiry(60 * 60 * 24 * 14)
        return JsonResponse({'status': True, 'data': '/index/'})
    return JsonResponse({'status': False, 'error': form.errors})


def login(request):
    """ 用户名和密码登录 """
    if request.method == 'GET':
        form = LoginForm(request)
        return render(request, 'login.html', {'form': form})
    form = LoginForm(request, data=request.POST)
    if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        # user_object = models.UserInfo.objects.filter(username=username, password=password).first()
        # （手机=手机 and 密码=密码） or （邮箱=邮箱 and 密码=密码）

        user_object = models.UserInfo.objects.filter(Q(email=username) | Q(mobile_phone=username)).filter(
            password=password).first()

        if user_object:
            # 登录成功
            request.session['user_id'] = user_object.id
            request.session.set_expiry(60*60*24*14)

            # 用户名密码是正确的
            return redirect('index')
        form.add_error('username', '用户名或密码错误')
    return render(request, 'login.html', {'form': form})


def image_code(request):
    """ 生成图片验证码 """

    image_object, code = check_code()
    request.session['image_code'] = code
    request.session.set_expiry(60)  # 主动修改session的过期时间为60s

    stream = BytesIO()
    image_object.save(stream, 'png')
    return HttpResponse(stream.getvalue())


def logout(request):
    request.session.flush()
    return redirect('index')
