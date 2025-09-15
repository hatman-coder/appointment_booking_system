from django.shortcuts import render


def render_index_page(request):
    return render(request, 'index/index.html')
