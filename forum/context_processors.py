from django.db.models import Count

from .models import Board, Category


def sidebar(request):
    """每一頁左側導覽列需要的資料"""
    hot_boards = (
        Board.objects.filter(is_active=True)
        .annotate(n=Count("posts__comments"))
        .order_by("-n")[:6]
    )
    favorites = []
    if request.user.is_authenticated:
        favorites = [f.board for f in request.user.favorites.select_related("board")]
    return {
        "nav_categories": Category.objects.all(),
        "nav_hot_boards": hot_boards,
        "nav_favorites": favorites,
    }
