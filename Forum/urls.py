from django.urls import path
from Forum import views

app_name = 'Forum'
urlpatterns = [
    path('', views.home, name='home'),
    path('new_topic/', views.new_topic, name='new_topic'),
    path('topics/<int:pk>/', views.topic_posts, name='topic_posts'),
    path('topics/<int:pk>/reply/', views.reply_topic, name='reply'),
    path('post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('topic/<int:topic_id>/delete/', views.delete_topic, name='delete_topic'),
    path('post/<int:post_id>/hide/', views.hide_post, name='hide_post'),  # 隐藏帖子
    path('post/<int:post_id>/unhide/', views.unhide_post, name='unhide_post'),  # 取消隐藏帖子
    path('topic/<int:topic_id>/hide/', views.hide_topic, name='hide_topic'),  # 隐藏主题
    path('topic/<int:topic_id>/unhide/', views.unhide_topic, name='unhide_topic'),  # 取消隐藏主题
]