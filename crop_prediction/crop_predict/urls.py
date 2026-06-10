from django.urls import path
from .views import (
    admin_delete_prediction,
    home,
    index,
    predict,
    signup,
    login,
    about,
    contact,
    logout_view,
    result,
    user_history_view,
    user_delete_prediction,
    profile_view,
    change_password_view,
    admin_login_view,
    admin_dashboard_view,
    admin_users_view,
    admin_user_delete,
    admin_view_predictions,
    admin_logout,
)

urlpatterns = [
    path('', home, name='home'),
    path('form/', index, name='form'),
    path('predict/', predict, name='predict'),
    path('signup/', signup, name='signup'),
    path('login/', login, name='login'),
    path('about/', about, name='about'),
    path('contact/', contact, name='contact'),
    path('logout/', logout_view, name='logout'),
    path('history/', user_history_view, name='history'),
    path('history/delete/<int:id>/', user_delete_prediction, name='user_delete_prediction'),
    path('result/', result, name='result'),
    path('profile/', profile_view, name='profile'),
    path('change-password/', change_password_view, name='change_password'),
    path('admin-login/', admin_login_view, name='admin_login'),
    path('admin-dashboard/', admin_dashboard_view, name='admin_dashboard'),
    path('admin-view-users/', admin_users_view, name='admin_view_users'),
    path('admin-view-users/delete/<int:id>/', admin_user_delete, name='admin_delete_user'),
    path('admin_view_predictions/', admin_view_predictions, name='admin_view_predictions'),
    path('admin-view-predictions/delete/<int:id>/', admin_delete_prediction, name='admin_delete_prediction'),
    path('admin-logout/', admin_logout , name='admin_logout')



]
