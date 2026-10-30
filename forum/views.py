from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Case, Count, F, IntegerField, Q, Value, When
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import CommentForm, PostForm, SignUpForm
from .models import Board, BrowseHistory, Category, Favorite, Post

HOME = ("首頁", "/")


def home(request):
    """首頁：登入前＝新手導覽；登入後＝個人儀表板"""
    hot_boards = (
        Board.objects.filter(is_active=True)
        .select_related("category")
        .annotate(post_n=Count("posts", distinct=True), heat=Count("posts__comments", distinct=True))
        .order_by("-heat")[:6]
    )
    week_ago = timezone.now() - timedelta(days=7)
    hot_posts = (
        Post.objects.with_stats().select_related("board", "author")
        .filter(created_at__gte=week_ago).order_by("-score", "-created_at")[:8]
    )
    if len(hot_posts) < 4:  # 資料少時退回全部時間
        hot_posts = Post.objects.with_stats().select_related("board", "author").order_by("-score")[:8]

    ctx = {"hot_boards": hot_boards, "hot_posts": hot_posts,
           "hot_keywords": ["面試", "年終", "手機", "省錢", "動畫"]}

    if request.user.is_authenticated:
        fav_ids = list(request.user.favorites.values_list("board_id", flat=True))
        ctx["feed"] = (
            Post.objects.with_stats().select_related("board", "author")
            .filter(board_id__in=fav_ids).order_by("-created_at")[:10]
        )
        ctx["recent"] = request.user.history.select_related("post__board")[:6]
        return render(request, "forum/dashboard.html", ctx)
    return render(request, "forum/home.html", ctx)


def board_list(request):
    """分類看板：分類標籤 + 看板中文說明 + 看板名稱篩選"""
    cat_slug = request.GET.get("cat", "")
    q = request.GET.get("q", "").strip()
    boards = (
        Board.objects.filter(is_active=True).select_related("category")
        .annotate(post_n=Count("posts", distinct=True), heat=Count("posts__comments", distinct=True))
    )
    current = None
    if cat_slug:
        current = get_object_or_404(Category, slug=cat_slug)
        boards = boards.filter(category=current)
    if q:
        boards = boards.filter(Q(name__icontains=q) | Q(zh_name__icontains=q) | Q(description__icontains=q))
    sort = request.GET.get("sort", "hot")
    boards = boards.order_by("name") if sort == "name" else boards.order_by("-heat")

    fav_ids = set()
    if request.user.is_authenticated:
        fav_ids = set(request.user.favorites.values_list("board_id", flat=True))

    crumbs = [HOME, ("分類看板", "/boards/")]
    if current:
        crumbs.append((current.name, None))
    return render(request, "forum/board_list.html", {
        "boards": boards, "current": current, "q": q, "sort": sort,
        "fav_ids": fav_ids, "crumbs": crumbs,
    })


def board_detail(request, name):
    """看板文章列表：最新 / 熱門 切換、板內搜尋、前綴篩選"""
    board = get_object_or_404(Board.objects.select_related("category"), name=name)
    tab = request.GET.get("tab", "latest")
    q = request.GET.get("q", "").strip()
    prefix = request.GET.get("prefix", "")

    posts = Post.objects.with_stats().select_related("author").filter(board=board)
    if q:
        posts = posts.filter(Q(title__icontains=q) | Q(content__icontains=q))
    if prefix:
        posts = posts.filter(prefix=prefix)
    posts = posts.order_by("-score", "-created_at") if tab == "hot" else posts.order_by("-created_at")

    page = Paginator(posts, 10).get_page(request.GET.get("page"))
    is_fav = request.user.is_authenticated and Favorite.objects.filter(user=request.user, board=board).exists()
    prefixes = board.posts.values_list("prefix", flat=True).distinct()

    return render(request, "forum/board_detail.html", {
        "board": board, "page": page, "tab": tab, "q": q, "prefix": prefix,
        "prefixes": sorted(set(prefixes)), "is_fav": is_fav,
        "crumbs": [HOME, (board.category.name, f"/boards/?cat={board.category.slug}"), (f"{board.name}（{board.zh_name}）", None)],
    })


def post_detail(request, pk):
    post = get_object_or_404(Post.objects.with_stats().select_related("board__category", "author"), pk=pk)

    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.info(request, "登入後才能推文喔！")
            return redirect(f"/accounts/login/?next={post.get_absolute_url()}")
        form = CommentForm(request.POST)
        if form.is_valid():
            c = form.save(commit=False)
            c.post, c.author = post, request.user
            c.save()
            messages.success(request, "推文成功！")
            return redirect(f"{post.get_absolute_url()}#comments")
    else:
        form = CommentForm()

    Post.objects.filter(pk=pk).update(views=F("views") + 1)
    if request.user.is_authenticated:
        BrowseHistory.objects.update_or_create(user=request.user, post=post, defaults={"viewed_at": timezone.now()})

    related = (Post.objects.filter(board=post.board).exclude(pk=pk).order_by("-created_at")[:5])
    is_fav = request.user.is_authenticated and Favorite.objects.filter(user=request.user, board=post.board).exists()
    return render(request, "forum/post_detail.html", {
        "post": post, "comments": post.comments.select_related("author"),
        "form": form, "related": related, "is_fav": is_fav,
        "crumbs": [HOME, (post.board.category.name, f"/boards/?cat={post.board.category.slug}"),
                   (post.board.name, post.board.get_absolute_url()), (post.title, None)],
    })


def search(request):
    """全站搜尋 + 條件篩選（時間範圍 / 看板 / 分類前綴 / 排序）"""
    q = request.GET.get("q", "").strip()
    period = request.GET.get("period", "all")
    board_name = request.GET.get("board", "")
    prefix = request.GET.get("prefix", "")
    sort = request.GET.get("sort", "relevance")

    posts = Post.objects.with_stats().select_related("board", "author")
    matched_boards = Board.objects.none()
    if q:
        posts = posts.filter(
            Q(title__icontains=q) | Q(content__icontains=q) | Q(author__username__icontains=q)
            | Q(board__name__icontains=q) | Q(board__zh_name__icontains=q)
        ).annotate(rel=Case(When(title__icontains=q, then=Value(3)),
                            When(board__zh_name__icontains=q, then=Value(2)),
                            default=Value(1), output_field=IntegerField()))
        matched_boards = Board.objects.filter(Q(name__icontains=q) | Q(zh_name__icontains=q) | Q(description__icontains=q))[:6]
    else:
        posts = posts.annotate(rel=Value(1, output_field=IntegerField()))

    days = {"week": 7, "month": 30, "year": 365}.get(period)
    if days:
        posts = posts.filter(created_at__gte=timezone.now() - timedelta(days=days))
    if board_name:
        posts = posts.filter(board__name=board_name)
    if prefix:
        posts = posts.filter(prefix=prefix)

    order = {"latest": ["-created_at"], "hot": ["-score", "-created_at"]}.get(sort, ["-rel", "-score", "-created_at"])
    posts = posts.order_by(*order)
    page = Paginator(posts, 10).get_page(request.GET.get("page"))

    return render(request, "forum/search.html", {
        "q": q, "period": period, "board_name": board_name, "prefix": prefix, "sort": sort,
        "page": page, "total": page.paginator.count, "matched_boards": matched_boards,
        "all_boards": Board.objects.filter(is_active=True).order_by("name"),
        "prefix_choices": Post.PREFIX_CHOICES,
        "crumbs": [HOME, ("搜尋結果", None)],
    })


@login_required
@require_POST
def toggle_favorite(request, name):
    board = get_object_or_404(Board, name=name)
    fav, created = Favorite.objects.get_or_create(user=request.user, board=board)
    if not created:
        fav.delete()
    if request.headers.get("x-requested-with") == "fetch":
        return JsonResponse({"favorited": created, "board": board.name})
    messages.success(request, f"已{'加入' if created else '移除'}收藏：{board.name}")
    return redirect(request.POST.get("next") or board.get_absolute_url())


@login_required
def post_create(request):
    initial = {}
    if request.GET.get("board"):
        initial["board"] = Board.objects.filter(name=request.GET["board"]).first()
    form = PostForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        messages.success(request, "發文成功！")
        return redirect(post.get_absolute_url())
    return render(request, "forum/post_form.html", {"form": form, "crumbs": [HOME, ("發表文章", None)]})


@login_required
def my_favorites(request):
    favs = request.user.favorites.select_related("board__category").annotate(post_n=Count("board__posts"))
    recent = request.user.history.select_related("post__board")[:20]
    my_posts = Post.objects.with_stats().filter(author=request.user).select_related("board")[:20]
    return render(request, "forum/my_favorites.html", {
        "favs": favs, "recent": recent, "my_posts": my_posts,
        "crumbs": [HOME, ("我的收藏", None)],
    })


def signup(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"註冊成功，歡迎 {user.username}！先去收藏幾個常看的看板吧。")
        return redirect("board_list")
    return render(request, "registration/signup.html", {"form": form})
