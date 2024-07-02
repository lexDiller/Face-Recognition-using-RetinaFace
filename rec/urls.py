from django.urls import include, path
from rest_framework import routers
from .views import index, get_time_report, get_time_report_range
#get_weekly_time_report
router = routers.SimpleRouter()

urlpatterns = [
    path('', include(router.urls)),
    path('cal', index, name='index'),
    path('report/<date>/', get_time_report, name='get_time_report'),
    path('report-range/<start_date>/<end_date>/', get_time_report_range, name='get_time_report_range')
]