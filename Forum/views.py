from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage

from UserAuth.models import User
from .models import Topic, Post
from .forms import NewTopicForm, PostForm

from ContentReview.llm_check import check


import re
import os
import logging

logger = logging.getLogger(__name__)

def get_matching_files(request):
    pattern = re.compile(str(request.session['UserInfo'].get("id")) + r'.*')
    file_names = os.listdir(settings.PROFILE_ROOT)
    matching_files = []
    for file_name in file_names:
        if pattern.match(file_name):
            matching_files.append(file_name)
    # 没有上传就用默认的
    if not matching_files:
        matching_files.append('default.jpeg')
    return matching_files[0]


# Create your views here.
def home(request):
    user = User.objects.get(id=request.session['UserInfo'].get('id'))
    
    if user.identity in [2, 3]:  # HR 和管理员可以看到所有主题
        topics = Topic.objects.order_by('last_updated')
    else:  # 普通用户只能看到未隐藏的主题
        topics = Topic.objects.filter(is_hidden=False).order_by('last_updated')

    topics_per_page = 20
    paginator = Paginator(topics, topics_per_page)
    page_number = request.GET.get('page')

    try:
        current_page = paginator.get_page(page_number)
    except EmptyPage:
        current_page = paginator.page(paginator.num_pages)

    context = {
        'matching_files': get_matching_files(request),
        'topics': current_page,
        'page_size': topics_per_page,
    }
    return render(request, 'Forum/home.html', context)



def new_topic(request):
    if request.method == 'POST':
        form = NewTopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.starter = User.objects.get(pk=request.session['UserInfo'].get('id'))

            # 内容审核逻辑
            user_message = form.cleaned_data.get('message')
            is_violating = check(user_message)  # 调用内容审核函数

            # 设置主题的隐藏状态
            topic.is_hidden = is_violating  # 如果内容违规，将主题设置为隐藏
            topic.save()

            # 创建第一条帖子
            post = Post.objects.create(
                message=user_message,
                topic=topic,
                created_by=topic.starter,
                is_hidden=is_violating  # 帖子和主题的隐藏状态一致
            )

            return redirect('Forum:topic_posts', pk=topic.pk)

    else:
        form = NewTopicForm()

    context = {
        'form': form,
        'matching_files': get_matching_files(request),
    }
    return render(request, 'Forum/new_topic.html', context)




def topic_posts(request, pk):
    user = User.objects.get(id=request.session['UserInfo'].get('id'))
    topic = get_object_or_404(Topic, pk=pk)

    # 如果主题被隐藏，普通用户不能访问
    if topic.is_hidden and user.identity not in [2, 3]:
        return HttpResponse("您无权查看此主题。", status=403)

    # 管理员和 HR 可以看到所有帖子，普通用户只能看到未隐藏的帖子
    if user.identity in [2, 3]:
        posts = topic.posts.all()
    else:
        posts = topic.posts.filter(is_hidden=False)

    topic.views += 1
    topic.save()

    context = {
        'topic': topic,
        'posts': posts,
        'matching_files': get_matching_files(request),
    }

    return render(request, 'Forum/topic_posts.html', context)


def reply_topic(request, pk):
    topic = get_object_or_404(Topic, pk=pk)
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            user_message = form.cleaned_data.get('message')

            # 内容审核逻辑
            is_violating = check(user_message)  # 调用内容审核函数

            # 创建回复
            post = form.save(commit=False)
            post.topic = topic
            post.created_by = User.objects.get(pk=request.session['UserInfo'].get('id'))
            post.is_hidden = is_violating  # 根据审核结果设置隐藏状态
            post.save()

            return redirect('Forum:topic_posts', pk=pk)
    else:
        form = PostForm()
    return render(request, 'Forum/reply_topic.html', {'topic': topic, 'form': form})

def delete_post(request, post_id):
    """
    删除单个帖子，仅管理员用户可以操作。
    """
    user = User.objects.get(id=request.session['UserInfo'].get('id'))
    if user.identity != 3: 
        return HttpResponse("您没有权限删除帖子。", status=403)
    post = get_object_or_404(Post, id=post_id)
    post.delete()

    return redirect('Forum:topic_posts', pk=post.topic.pk)

def delete_topic(request, topic_id):
    """
    删除整个主题及其相关的所有帖子，仅管理员用户可以操作。
    """
    user = User.objects.get(id=request.session['UserInfo'].get('id'))
    if user.identity != 3:
        return HttpResponse("您没有权限删除主题。", status=403)
    topic = get_object_or_404(Topic, id=topic_id)
    topic.delete()

    return redirect('Forum:home')

def hide_post(request, post_id):
    """
    隐藏帖子，仅限管理员用户操作。
    """
    user = User.objects.get(id=request.session['UserInfo'].get('id'))
    if user.identity != 3:  
        return HttpResponse("您没有权限隐藏帖子。", status=403)
    post = get_object_or_404(Post, id=post_id)
    post.is_hidden = True
    post.save()
    return redirect('Forum:topic_posts', pk=post.topic.pk)

def unhide_post(request, post_id):
    """
    取消隐藏帖子，仅限管理员用户操作。
    """
    user = User.objects.get(id=request.session['UserInfo'].get('id'))
    if user.identity != 3: 
        return HttpResponse("您没有权限取消隐藏帖子。", status=403)
    post = get_object_or_404(Post, id=post_id)
    post.is_hidden = False
    post.save()
    return redirect('Forum:topic_posts', pk=post.topic.pk)

def hide_topic(request, topic_id):
    """
    隐藏主题，仅限管理员用户操作。
    """
    user = User.objects.get(id=request.session['UserInfo'].get('id'))
    if user.identity != 3:  
        return HttpResponse("您没有权限隐藏主题。", status=403)
    topic = get_object_or_404(Topic, id=topic_id)
    topic.is_hidden = True
    topic.save()
    return redirect('Forum:home')

def unhide_topic(request, topic_id):
    """
    取消隐藏主题，仅限管理员用户操作。
    """
    user = User.objects.get(id=request.session['UserInfo'].get('id'))
    if user.identity != 3:  
        return HttpResponse("您没有权限取消隐藏主题。", status=403)
    topic = get_object_or_404(Topic, id=topic_id)
    topic.is_hidden = False
    topic.save()
    return redirect('Forum:home')


def check_and_log(message):
    is_violating = check(message)
    if is_violating:
        logger.warning(f"Post flagged as violating: {message}")
    return is_violating