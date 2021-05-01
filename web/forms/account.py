import random
from django import forms
from web import models
from django.conf import settings
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from utils.tencent.sms import send_sms_single
from django_redis import get_redis_connection
from utils import encrypt
from web.forms.bootstrap import BootStrapForm


class RegisterModelForm(BootStrapForm, forms.ModelForm):
    password = forms.CharField(
        label='密码',
        min_length=8,
        max_length=64,
        error_messages={
            'min_length': '密码长度不能小于8个字符',
            'max_length': '密码长度不能大于64个字符',
        },
        widget=forms.PasswordInput())
    # 如果我在orm创建数据库表单时候再生成一个确认密码那么存储了密码和确认密码一样的就多余了
    confirm_password = forms.CharField(
        label='重复密码',
        error_messages={
            'min_length': '重复密码长度不能小于8个字符',
            'max_length': '重复密码长度不能大于64个字符',
        },
        widget=forms.PasswordInput())

    mobile_phone = forms.CharField(
        label='手机号',
        validators=[RegexValidator(r'^(1[3|4|5|6|7|8|9])\d{9}$', '手机号格式错误'), ])

    # 新增一个验证码字段
    code = forms.CharField(
        label='手机验证码',
        widget=forms.TextInput())

    class Meta:
        model = models.UserInfo
        fields = ['username', 'email', 'password', 'confirm_password', 'mobile_phone', 'code']

    def clean_username(self):
        username = self.cleaned_data['username']
        exists = models.UserInfo.objects.filter(username=username).exists()
        if exists:
            raise ValidationError('用户名已存在')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        exists = models.UserInfo.objects.filter(email=email).exists()
        if exists:
            raise ValidationError('邮箱已存在')
        return email

    def clean_password(self):
        """这个钩子函数用于加密原密码，直接返回加密后的密码"""
        pwd = self.cleaned_data['password']
        # 加密 & 返回
        return encrypt.md5(pwd)

    def clean_confirm_password(self):
        # 这里拿到的是上面钩子函数返回回来已经加密了的密码
        pwd = self.cleaned_data.get('password')
        # 因为django取数据按顺序来，上面的password加密了所有为了比较这里的确认密码也要加密
        confirm_pwd = encrypt.md5(self.cleaned_data['confirm_password'])
        if pwd != confirm_pwd:
            raise ValidationError('两次密码不一致')
        return confirm_pwd

    def clean_mobile_phone(self):
        mobile_phone = self.cleaned_data['mobile_phone']
        exists = models.UserInfo.objects.filter(mobile_phone=mobile_phone).exists()
        if exists:
            raise ValidationError('手机号已注册')
        return mobile_phone

    def clean_code(self):
        code = self.cleaned_data['code']
        mobile_phone = self.cleaned_data.get('mobile_phone')
        if not mobile_phone:
            return code
        # 去redis里面获取存入的手机号:验证码键值对进行校验
        conn = get_redis_connection()
        redis_code = conn.get(mobile_phone)
        if not redis_code:
            raise ValidationError('验证码失效或未发送,请重新发')
        # 查到的验证码是个bytes类型需要转换一下
        redis_str_code = redis_code.decode('utf-8')
        if code.strip() != redis_str_code:
            raise ValidationError('验证码错误,请重新输入')
        return code


class SendSmsForm(forms.Form):
    mobile_phone = forms.CharField(label='手机号', validators=[RegexValidator(r'^(1[3|4|5|6|7|8|9])\d{9}$', '手机号格式错误'), ])

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean_mobile_phone(self):
        """ 手机号校验是否注册过的钩子函数 """
        mobile_phone = self.cleaned_data['mobile_phone']
        # 判断短信模板是否有问题
        tpl = self.request.GET.get('tpl')
        template_id = settings.TENCENT_SMS_TEMPLATE.get(tpl)
        if not template_id:
            raise ValidationError('模板错误')

        exists = models.UserInfo.objects.filter(mobile_phone=mobile_phone).exists()

        if tpl == 'login':
            if not exists:
                raise ValidationError('手机号不存在')
        else:
            # 校验数据库中是否已经存在这个手机号
            if exists:
                raise ValidationError('手机号已存在')

        # 发短信
        code = random.randrange(1000, 9999)
        sms = send_sms_single(mobile_phone, template_id, [code, ])
        if sms['result'] != 0:
            raise ValidationError('短信发送失败, {}'.format(sms['errmsg']))

        # 验证码写入redis（django-redis）
        conn = get_redis_connection()
        # 设置超时时间60秒
        conn.set(mobile_phone, code, ex=60)
        return mobile_phone


class LoginSmsForm(BootStrapForm, forms.Form):
    mobile_phone = forms.CharField(label='手机号', validators=[RegexValidator(r'^(1[3|4|5|6|7|8|9])\d{9}$', '手机号格式错误'), ])
    code = forms.CharField(
        label='手机验证码',
        widget=forms.TextInput())

    def clean_mobile_phone(self):
        mobile_phone = self.cleaned_data['mobile_phone']
        exists = models.UserInfo.objects.filter(mobile_phone=mobile_phone).exists()
        if not exists:
            raise ValidationError('手机号不存在')
        return mobile_phone

    def clean_code(self):
        code = self.cleaned_data['code']
        # 因为在上面验证通过后返回的moblie_phone是一个object对象所以下面去redis里面拿的时候需要点
        mobile_phone = self.cleaned_data.get('mobile_phone')
        # 手机号不存在则验证码无需判断
        if not mobile_phone:
            return code

        # 去redis里面获取存入的手机号:验证码键值对进行校验
        conn = get_redis_connection()
        redis_code = conn.get(mobile_phone)
        if not redis_code:
            raise ValidationError('验证码失效或未发送,请重新发')
        # 查到的验证码是个bytes类型需要转换一下
        redis_str_code = redis_code.decode('utf-8')
        if code.strip() != redis_str_code:
            raise ValidationError('验证码错误,请重新输入')
        return code


class LoginForm(BootStrapForm, forms.Form):
    username = forms.CharField(label='邮箱或手机号')
    password = forms.CharField(label='密码', widget=forms.PasswordInput(render_value=True))
    code = forms.CharField(label='图片验证码')

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean_password(self):
        """这个钩子函数用于加密原密码，直接返回加密后的密码"""
        pwd = self.cleaned_data['password']
        # 加密 & 返回
        return encrypt.md5(pwd)

    def clean_code(self):
        """ 钩子校验图片验证码 """
        # 读取用户输入的验证码
        code = self.cleaned_data['code']
        # 去session中获取自己的验证码
        session_code = self.request.session.get('image_code')
        if not session_code:
            raise ValidationError('验证码已过期,请重新获取')
        # 用户输入验证码是小写的也是支持的
        if code.strip().upper() != session_code.strip().upper():
            raise ValidationError('验证码输入错误')
        return code


