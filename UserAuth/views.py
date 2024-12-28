from io import BytesIO
import re

from django.shortcuts import render, HttpResponse, redirect
from django.http import JsonResponse
import base64
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from UserAuth.utils.Forms import RegisterForm, LoginForm, ResetPasswordForm

from UserAuth import models

from UserAuth.utils.generateCode import check_code, send_sms_code
from UserAuth.utils.validators import is_valid_email

from UserAuth.utils.encrypt import rsa_decrypt_password, from_url_safe_base64


def register(request):
    if request.method == 'GET':
        form = RegisterForm(request=request)
        context = {
            'form': form,
            'nid': 1  # represent registration
        }
        return render(request, 'UserAuth/UserAuth.html', context=context)

    # if method is post
    form = RegisterForm(data=request.POST, request=request)
    print("form is valid ? ", form.is_valid())
    if not form.is_valid():
        print("Form errors:", form.errors)
        context = {
            'form': form,
            'nid': 1
        }
        return render(request, 'UserAuth/UserAuth.html', context=context)

    # store userinfo
    form.instance.identity = 1  # default: User
    try:
        form.instance.password = rsa_decrypt_password(form.instance.password).decode('latin1')
    except:
        raise ValidationError("哈希值转字符串失败，请联系管理员")
    form.save()

    # generate cookie
    obj = models.User.objects.filter(username=form.cleaned_data["username"]).first()
    request.session["UserInfo"] = {
        'id': obj.id,
        'username': obj.username,
        'identity': obj.identity
    }
    request.session.set_expiry(60 * 60 * 24 * 7)  # 7天免登录
    return redirect("/")

def login(request):
    if request.method == 'GET':
        form = LoginForm(request=request)
        context = {
            'form': form,
            'nid': 2
        }
        return render(request, 'UserAuth/UserAuth.html', context=context)

    # if method is POST
    form = LoginForm(data=request.POST, request=request)
    if not form.is_valid():
        context = {
            'form': form,
            'nid': 2
        }
        return render(request, 'UserAuth/UserAuth.html', context=context)

    row_obj = models.User.objects.filter(username=form.cleaned_data['username']).first()
    request.session["UserInfo"] = {
        'id': row_obj.id,
        'username': row_obj.username,
        'identity': row_obj.identity
    }
    request.session.modified = True  # 强制保存会话
    request.session.set_expiry(60 * 60 * 24 * 7)  # 7天免登录
    return redirect(reverse('Forum:home'))


def reset_password(request):
    if request.method == 'GET':
        form = ResetPasswordForm(request=request)
        context = {
            'form': form,
            'nid': 2
        }
        return render(request, 'UserAuth/forget_password.html', context=context)

    # else POST method
    form = ResetPasswordForm(data=request.POST, request=request)
    if not form.is_valid():
        context = {
            'form': form,
        }
        return render(request, 'UserAuth/forget_password.html', context=context)

    username_or_mobile = form.cleaned_data['username_or_mobile']
    # 判断输入的是手机号还是用户名
    pattern = r'\d{11}'
    if re.search(pattern=pattern, string=username_or_mobile):  # 是手机号
        query_set = models.User.objects.filter(mobile_phone=username_or_mobile)
    else:
        query_set = models.User.objects.filter(username=username_or_mobile)

    if not query_set:
        return render(request, "UserAuth/alert_page.html", {'msg': '错误的用户信息'})

    new_password = form.cleaned_data['password']

    new_password_hash = rsa_decrypt_password(new_password)
    # 这里new_password_hash是bytes类型，需要转成str存储
    try:
        str_decoded_password_hash = new_password_hash.decode('latin1')
    except:
        raise ValidationError("哈希值转字符串失败，请联系管理员")
    # print("new password:", new_password)
    # print("new password hash:", new_password_hash)
    # 重置密码
    query_set.update(password=str_decoded_password_hash)  # 更新数据库中的密码
    return render(request, "UserAuth/alert_page.html", context={'msg': "您的密码已被重置！", 'success': True})



def change_identity(request):
    """更改登录身份"""
    user_query_set = models.User.objects.filter(id=request.session.get("UserInfo").get("id"))
    if not user_query_set:
        return render(request, "UserAuth/alert_page.html", {'msg': '错误的用户信息', 'return_path': '/info/info/'})
    user_obj = user_query_set.first()

    if user_obj.identity == 2:
        # 目前是HR身份
        user_query_set.update(identity=1)  # 切换回用户身份
        return redirect("/info/account/")

    # 目前不是HR身份
    if not user_obj.hr_allowed == 3:
        # 如果不具备HR资格
        if user_obj.hr_allowed == 1:
            return render(request, "UserAuth/alert_page.html",
                      {'msg': '您尚不具备HR身份，请联系管理员获取', 'return_path': '/info/info/'})
        else:
            return render(request, "UserAuth/alert_page.html",
                          {'msg': '您的申请已提交，请等待审核通过', 'return_path': '/info/info/', 'success': True})

    user_query_set.update(identity=2)

    return redirect("/info/account/")


def generate_verification_code(request):
    """产生图片验证码"""
    stream = BytesIO()
    img, code = check_code()
    # img 储存到内存流中
    img.save(stream, 'png')
    request.session["login_verification_code"] = code
    request.session.set_expiry(120)  # 验证码120秒有效期
    return HttpResponse(stream.getvalue())


@csrf_exempt
def register_email(request):
    """注册时发送邮箱验证码"""
    if request.method == 'GET':
        data = {
            'state': False,
            'msg': 'Invalid request method'
        }
        return JsonResponse(data)

    email = request.POST.get('email_address')
    if not is_valid_email(email):
        data = {
            'state': False,
            'msg': 'Invalid Email format'
        }
        return JsonResponse(data)
    else:
        # 发送邮件
        state, code = send_sms_code(target_email=email)
        request.session['register_verification_code'] = code
        request.session.set_expiry(2 * 60)
        data = {
            'state': True,
            'msg': 'Send Email successfully'
        }
        return JsonResponse(data)


@csrf_exempt
def reset_password_email(request):
    """重置密码的邮箱验证码"""
    if not request.method == 'POST':
        data = {
            'state': False,
            'msg': 'Unsupported method'
        }
        return JsonResponse(data)

    username_or_mobile = request.POST.get('username_or_mobile')
    # 判断输入的是手机号还是用户名
    pattern = r'\d{11}'
    if re.search(pattern=pattern, string=username_or_mobile):
        # 是手机号
        query_set = models.User.objects.filter(mobile_phone=username_or_mobile)
    else:
        query_set = models.User.objects.filter(username=username_or_mobile)

    # 判空
    if not query_set:
        data = {
            'state': False,
            'msg': '不存在的用户名或手机号'
        }
        return JsonResponse(data)

    # 非空
    email = query_set.first().email
    # print(email)
    state_code, code = send_sms_code(target_email=email)
    if not state_code:  # 发送失败
        data = {
            'state': False,
            'msg': '邮件发送失败，请稍后重试'
        }
        return JsonResponse(data)

    # 发送成功, state_code == 0
    request.session['reset_password_verification_code'] = code  # 将重置验证码写入session
    request.session.set_expiry(2 * 60)
    # 返回信息
    return_msg = '验证码已发送至{}'.format(email)
    data = {
        'state': True,
        'msg': return_msg
    }
    return JsonResponse(data)


def index(request):
    userinfo = request.session.get("UserInfo")
    context = {
        'username': userinfo
    }
    return render(request, 'UserAuth/index.html', context=context)


def logout(request):
    request.session.clear()
    return redirect("/")


def check_login_state(request):
    user_info = request.session.get("UserInfo")
    if not user_info:
        return HttpResponse("您尚未登录")

    return HttpResponse("Welcome User: " + user_info["username"])

def get_public_key(request):
    public_key_path = os.path.join(settings.BASE_DIR, 'public_key.pem')
    with open(public_key_path, 'r') as file:
        public_key = file.read()
    return HttpResponse(public_key, content_type="text/plain")