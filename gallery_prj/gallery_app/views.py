from django.shortcuts import render

# Create your views here.


def home(request):
    return render(request, 'home.html')


def photo_detail(request, photo_id):
    photo_id = int(photo_id)

    prev_photo_id = photo_id - 1 if photo_id > 1 else 1
    next_photo_id = photo_id + 1 if photo_id < 9 else 9

    context = {
        'photo_id': photo_id,
        'prev_photo_id': prev_photo_id,
        'next_photo_id': next_photo_id,
    }

    return render(request, 'photo_detail.html', context)