import time
import math
from django.http import HttpResponse
from django.shortcuts import render, redirect
import json
from web import models
import datetime
from django_redis import get_redis_connection
from utils.encrypt import uid
from django.conf import settings
from utils.alipay import AliPay
from django.db.models import Q


def function(request):
    return render(request, 'function.html')


def enterprise(request):
    return render(request, 'enterprise.html')


def help(request):
    return render(request, 'help.html')


def index(request):
    return render(request, 'index.html')


def price(request):
    """ 套餐 """
    # 获取套餐
    policy_list = models.PricePolicy.objects.filter(category=2)
    return render(request, 'price.html', {'policy_list': policy_list})


def payment(request, policy_id):
    """ 支付页面 """
    # 1.价格策略policy_id
    policy_object = models.PricePolicy.objects.filter(id=policy_id, category=2).first()
    if not policy_object:
        return redirect('price')
    # 2.获取要购买的数量
    number = request.GET.get('number', '')
    if not number or not number.isdecimal():
        return redirect('price')
    number = int(number)
    if number < 1:
        return redirect('price')

    ##########
    # 删除上一个过期记录
    old_obj = models.Transaction.objects.filter(user=request.tracer.user, status=2).order_by('-price').first()
    current_datetime = datetime.datetime.now()
    if old_obj.end_datetime and old_obj.end_datetime < current_datetime:
        old_obj.delet()

    # 3.计算原价
    origin_price = number * policy_object.price
    # 4.之前购买的套餐抵扣(之前买过)
    balance = 0
    new_time_add = 0
    _object = None
    if request.tracer.price_policy.category == 2:
        # 找到之前的订单:总支付的费用,剩余天数,计算抵扣的钱
        _object = models.Transaction.objects.filter(user=request.tracer.user, status=2).order_by('-price').first()
        total_timedalta = _object.end_datetime - _object.start_datetime
        balance_timedalta = _object.end_datetime - datetime.datetime.now()
        policy_tp = models.PricePolicy.objects.filter(id=_object.price_policy_id).first()
        # if math.ceil(total_timedalta.days) == math.ceil(balance_timedalta.days):
        if math.ceil(policy_tp.price / total_timedalta.days * balance_timedalta.days) == policy_tp.price:
            balance = 0
        else:
            balance = policy_tp.price / total_timedalta.days * balance_timedalta.days
        # 如果抵扣的钱多于现在购买的套餐判断它是不是升级如果不是升级跳转回购买页面
        if (int(_object.price_policy_id) > int(policy_id)):
            return redirect('price')
        # 如果是升级,且之前金额更大vip20% svip35%
        if (int(balance) > int(origin_price)) and (int(_object.price_policy_id) < int(policy_id)):

            # 之前为vip
            if _object.price_policy_id == 2:
                balance = policy_object.price
            # 之前为svip
            if _object.price_policy_id == 3:
                balance = policy_object.price

    context = {
        'policy_id': policy_object.id,
        'number': number,
        'origin_price': origin_price,
        'balance': round(balance, 2),
        'total_price': origin_price - round(balance, 2),
        'new_time_add': new_time_add,
    }
    conn = get_redis_connection()
    key = 'payment_{}'.format(request.tracer.user.mobile_phone)
    conn.set(key, json.dumps(context), ex=60 * 30)

    context['policy_object'] = policy_object
    context['Transaction'] = _object
    return render(request, 'payment.html', context)


"""
def pay(request):

    conn = get_redis_connection()
    key = 'payment_{}'.format(request.tracer.user.mobile_phone)

    context_string = conn.get(key)
    if not context_string:
        return redirect('price')

    context = json.loads(context_string.decode('utf-8'))
    # 1.数据库生成待支付订单,支付完把订单状态更新为已支付，开始和结束时间需要计算
    order_id = uid(request.tracer.user.mobile_phone)
    total_price = context['total_price']
    models.Transaction.objects.create(
        status=1,
        order=order_id,
        user=request.tracer.user,
        price_policy_id=context['policy_id'],
        count=context['number'],
        price=total_price,
    )

    # 2.跳转到支付宝
    # 构造字典
    params = {
        'app_id': "2016102400754054",
        'method': 'alipay.trade.page.pay',
        'format': 'JSON',
        'return_url': "http://127.0.0.1:8001/pay/notify/",
        'notify_url': "http://127.0.0.1:8001/pay/notify/",
        'charset': 'utf-8',
        'sign_type': 'RSA2',
        'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'version': '1.0',
        'biz_content': json.dumps({
            'out_trade_no': order_id,
            'product_code': 'FAST_INSTANT_TRADE_PAY',
            'total_amount': total_price,
            'subject': "tracer payment"
        }, separators=(',', ':'))
    }

    # 获取待签名的字符串
    unsigned_string = "&".join(["{0}={1}".format(k, params[k]) for k in sorted(params)])

    # 签名 SHA256WithRSA(对应sign_type为RSA2)
    from Crypto.PublicKey import RSA
    from Crypto.Signature import PKCS1_v1_5
    from Crypto.Hash import SHA256
    from base64 import decodebytes, encodebytes

    # SHA256WithRSA + 应用私钥 对待签名的字符串 进行签名
    private_key = RSA.importKey(open("files/应用私钥2048.txt").read())
    signer = PKCS1_v1_5.new(private_key)
    signature = signer.sign(SHA256.new(unsigned_string.encode('utf-8')))

    # 对签名之后的执行进行base64 编码，转换为字符串
    sign_string = encodebytes(signature).decode("utf8").replace('\n', '')

    # 把生成的签名赋值给sign参数，拼接到请求参数中。

    from urllib.parse import quote_plus
    result = "&".join(["{0}={1}".format(k, quote_plus(params[k])) for k in sorted(params)])
    result = result + "&sign=" + quote_plus(sign_string)

    gateway = "https://openapi.alipaydev.com/gateway.do"
    ali_pay_url = "{}?{}".format(gateway, result)

    return redirect(ali_pay_url)
"""


def pay(request):
    conn = get_redis_connection()
    key = 'payment_{}'.format(request.tracer.user.mobile_phone)
    context_string = conn.get(key)
    if not context_string:
        return redirect('price')
    context = json.loads(context_string.decode('utf-8'))

    # 1. 数据库中生成交易记录（待支付）
    #     等支付成功之后，我们需要把订单的状态更新为已支付、开始&结束时间
    order_id = uid(request.tracer.user.mobile_phone)
    total_price = context['total_price']

    models.Transaction.objects.create(
        status=1,
        order=order_id,
        user=request.tracer.user,
        price_policy_id=context['policy_id'],
        count=context['number'],
        price=total_price
    )

    # 生成支付链接

    ali_pay = AliPay(
        appid=settings.ALI_APPID,
        app_notify_url=settings.ALI_NOTIFY_URL,
        return_url=settings.ALI_RETURN_URL,
        app_private_key_path=settings.ALI_PRI_KEY_PATH,
        alipay_public_key_path=settings.ALI_PUB_KEY_PATH
    )
    query_params = ali_pay.direct_pay(
        subject="trace rpayment",  # 商品简单描述
        out_trade_no=order_id,  # 商户订单号
        total_amount=total_price
    )
    pay_url = "{}?{}".format(settings.ALI_GATEWAY, query_params)
    return redirect(pay_url)


def pay_notify(request):
    """ 支付成功之后触发的URL """
    ali_pay = AliPay(
        appid=settings.ALI_APPID,
        app_notify_url=settings.ALI_NOTIFY_URL,
        return_url=settings.ALI_RETURN_URL,
        app_private_key_path=settings.ALI_PRI_KEY_PATH,
        alipay_public_key_path=settings.ALI_PUB_KEY_PATH
    )

    if request.method == 'GET':
        # 只做跳转，判断是否支付成功了，不做订单的状态更新。
        # 支付吧会讲订单号返回：获取订单ID，然后根据订单ID做状态更新 + 认证。
        # 支付宝公钥对支付给我返回的数据request.GET 进行检查，通过则表示这是支付宝返还的接口。
        params = request.GET.dict()
        sign = params.pop('sign', None)
        status = ali_pay.verify(params, sign)
        if status:
            current_datetime = datetime.datetime.now()
            out_trade_no = params['out_trade_no']
            _object = models.Transaction.objects.filter(order=out_trade_no).first()
            # 如果抵扣了钱那么总时长不加并且删除之前的vip
            policy_obj = models.PricePolicy.objects.filter(id=_object.price_policy_id).first()
            if _object.price != _object.count * policy_obj.price:
                models.Transaction.objects.filter(user=request.tracer.user, status=2, price_policy_id__gt=1).delete()
            else:
                # 如果没有抵钱
                old_obj = models.Transaction.objects.filter(user=request.tracer.user, status=2,
                                                            price_policy_id__gt=1).first()
                if old_obj:
                    leave_time = old_obj.end_datetime - current_datetime

                    # 转换成时间戳

                    timestamp = leave_time.total_seconds()
                    if old_obj.price_policy_id == 2:
                        timestamp1 = timestamp * 0.2

                    if old_obj.price_policy_id == 3:
                        timestamp1 = timestamp * 0.35

                    models.Transaction.objects.filter(user=request.tracer.user, status=2,
                                                      price_policy_id__gt=1).delete()
                    _object.status = 2
                    _object.start_datetime = current_datetime
                    _object.end_datetime = current_datetime + datetime.timedelta(
                        days=365 * _object.count) + datetime.timedelta(days=timestamp1 // (60 * 60 * 24))
                    _object.save()
                    return redirect('index')
            _object.status = 2
            _object.start_datetime = current_datetime
            _object.end_datetime = current_datetime + datetime.timedelta(days=365 * _object.count)
            _object.save()
            return redirect('index')

        return HttpResponse('支付失败')
    else:
        from urllib.parse import parse_qs
        body_str = request.body.decode('utf-8')
        post_data = parse_qs(body_str)
        post_dict = {}
        for k, v in post_data.items():
            post_dict[k] = v[0]

        sign = post_dict.pop('sign', None)
        status = ali_pay.verify(post_dict, sign)
        if status:
            current_datetime = datetime.datetime.now()
            out_trade_no = post_dict['out_trade_no']
            _object = models.Transaction.objects.filter(order=out_trade_no).first()

            _object.status = 2
            _object.start_datetime = current_datetime
            _object.end_datetime = current_datetime + datetime.timedelta(days=365 * _object.count)
            _object.save()
            return HttpResponse('success')

        return HttpResponse('error')
