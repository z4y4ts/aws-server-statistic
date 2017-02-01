from django.conf.urls import url
from . import views

app_name = 'ownservers'

urlpatterns = [
    url(r'^$', views.HomePage.as_view(), name='homepage'),
    url(r'^(?P<person>\w+)/(?P<server>[-\w\+%_&]+)/$', views.ServersInformation.as_view(), name='server'),
]