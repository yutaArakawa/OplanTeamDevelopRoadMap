from django.shortcuts import render


def escape(request):
    return render(request, 'prison/escape.html')
