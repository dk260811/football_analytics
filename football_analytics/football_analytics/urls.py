"""
URL configuration for football_analytics project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
"""from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('football/', include('football_data.urls')), 
]"""

# football_analytics/urls.py
from django.contrib import admin
from django.urls import path, include
from football_data import views  # Import the view if you want to use it directly

urlpatterns = [
    path('admin/', admin.site.urls),
    path('football/', include('football_data.urls')),  # Keep your existing football path
    path('', views.index_view, name='index'),  # Change this to use index_view for the root URL
    
]


# Update git
# git status
# git add .
# git commit -m "Your commit message here"
# git push

# me shkru dikun cka kom bo n projekt deri qetash
# mi marr local krejt t dhanat qe mvyne per regressione niher veq qeto t thjeshtat mandej edhe ato t komplikumet
# mi marr krejt tabelat local mi pas per cdo rast
# mi bo krejt regresionet diqysh online qe me mujt me dizajnu qe njerzt me perdor per qata
# me implementu sene tjera si psh comb calc
# me implementu me update data veq per qit sezon
