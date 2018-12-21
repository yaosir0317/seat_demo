from django.contrib import auth
from django.shortcuts import render, redirect, HttpResponse

# Create your views here.

from .models import *
import datetime
import json
from django.http import JsonResponse


# 预定信息api
def index(request):
    # 当前访问日期:年/月/日
    current_date = datetime.datetime.now().date()
    # 获取前端需展示预定信息的日期,无则为当天访问日期
    book_date = request.GET.get("book_date", current_date)
    # 会议室所允许预定的时间段列表
    time_choices = Book.time_choices
    # 会议室列表
    room_list = Room.objects.all()
    # 获取已经被预定的会议室信息列表,[{'room_id': , 'time_id': , 'user__username': ''},{...}]
    books = list(
        Book.objects.filter(
            date=book_date).values(
            "room_id",
            "time_id",
            "user__username"))
    books = json.dumps(books)

    return render(request, 'index.html', locals())


# 修改预定信息
def book(request):
    """
    {'post_data': ['{
        "DEL":{"3":["6"]},
        "ADD":{"1":["8","10"],"2":["7"],"3":["3","9"]}
        }'],
     'choose_date': ['2018 - 12 - 21']}
    """
    response = {'status': True, 'msg': None, 'data': None}
    try:
        # 预定日期
        choice_date = request.POST.get('choose_date')
        # 增加和删除的预定信息
        post_data = json.loads(request.POST.get('post_data'))

        # 增加预定
        book_obj_list = []
        for room_id, time_list in post_data['ADD'].items():
            for time_id in time_list:
                obj = Book(
                    room_id=room_id,
                    time_id=time_id,
                    user_id=request.user.pk,
                    date=choice_date)
                book_obj_list.append(obj)
        # 批量创建,不用每次save都访问数据库,可以减少数据库压力
        Book.objects.bulk_create(book_obj_list)

        # 删除会议室预定信息
        from django.db.models import Q
        # 实例化Q对象
        remove_booking = Q()
        for room_id, time_id_list in post_data['DEL'].items():
            for time_id in time_id_list:
                temp = Q()
                temp.connector = 'AND'
                # 构建同时满足下面四条件的Q对象
                temp.children.append(('user_id', request.user.pk,))
                temp.children.append(('date', choice_date))
                temp.children.append(('room_id', room_id,))
                temp.children.append(('time_id', time_id,))
                # 合并条件进行查询,关系为或,合并的每个Q对象都是我们的要删除的预定信息,他们之间不存在查询关系
                remove_booking.add(temp, 'OR')
        if remove_booking:
            Book.objects.filter(remove_booking).delete()

    except Exception as e:

        response['status'] = False
        response['msg'] = str(e)

    return JsonResponse(response)


def login(request):

    if request.method == "POST":
        user = request.POST.get("user")
        pwd = request.POST.get("pwd")
        user = auth.authenticate(username=user, password=pwd)
        if user:
            auth.login(request, user)
            return redirect("/index/")

    return render(request, "login.html")
