"""
URL configuration for JobRecruitment project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin

from django.urls import path, include, re_path
from django.views.static import serve
from django.conf import settings

from UserAuth import views
from django.conf.urls.static import static

urlpatterns = [
    path("", include('Forum.urls')),
    # path("", views.index),
    path("admin/", admin.site.urls),
    path("auth/", include("UserAuth.urls")),
    path("info/", include("UserInfo.urls")),
    path("position/", include("PublishPosition.urls")),
    path("mdeditor/", include("mdeditor.urls")),
    path("application/", include("Application.urls")),
    path("message/", include("UserMessage.urls")),
    # path("privatemessage/", include("PrivateMessage.urls")),  # 为 PrivateMessage 设定新的路径
    path('conversation/', include('PrivateMessage.urls')),
    re_path(r'media/(?P<path>.*)', serve,
            {'document_root': settings.MEDIA_ROOT}),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
