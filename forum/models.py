from django.conf import settings
from django.db import models
from django.db.models import Count, Q
from django.urls import reverse
from django.utils import timezone


class Category(models.Model):
    """看板分類標籤（科技、娛樂、生活…）— 對應 Bad UI 問題 2"""
    name = models.CharField("分類名稱", max_length=20, unique=True)
    slug = models.SlugField("代稱", max_length=30, unique=True)
    icon = models.CharField("圖示文字", max_length=4, default="#")
    color = models.CharField("標籤顏色", max_length=7, default="#3B6FE0")
    order = models.PositiveIntegerField("排序", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "看板分類"
        verbose_name_plural = "看板分類"

    def __str__(self):
        return self.name


class Board(models.Model):
    """看板：英文名稱 + 強制中文說明"""
    name = models.CharField("看板英文名稱", max_length=30, unique=True)
    zh_name = models.CharField("中文名稱", max_length=30)
    description = models.CharField("看板說明", max_length=200, blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="boards", verbose_name="分類")
    is_active = models.BooleanField("開放中", default=True)
    created_at = models.DateTimeField("建立時間", auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "看板"
        verbose_name_plural = "看板"

    def __str__(self):
        return f"{self.name}（{self.zh_name}）"

    def get_absolute_url(self):
        return reverse("board_detail", args=[self.name])


class PostQuerySet(models.QuerySet):
    def with_stats(self):
        return self.annotate(
            push_total=Count("comments", filter=Q(comments__kind="push"), distinct=True),
            boo_total=Count("comments", filter=Q(comments__kind="boo"), distinct=True),
            comment_total=Count("comments", distinct=True),
        ).annotate(score=models.F("push_total") - models.F("boo_total"))


class Post(models.Model):
    PREFIX_CHOICES = [
        ("討論", "討論"), ("問卦", "問卦"), ("請益", "請益"), ("心得", "心得"),
        ("分享", "分享"), ("新聞", "新聞"), ("情報", "情報"), ("閒聊", "閒聊"),
        ("問題", "問題"), ("選購", "選購"),
    ]
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="posts", verbose_name="看板")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts", verbose_name="作者")
    prefix = models.CharField("分類前綴", max_length=4, choices=PREFIX_CHOICES, default="討論")
    title = models.CharField("標題", max_length=80)
    content = models.TextField("內文", help_text="貼上圖片網址或 YouTube 連結會自動顯示預覽")
    image_url = models.URLField("封面圖片網址", blank=True)
    views = models.PositiveIntegerField("瀏覽數", default=0)
    created_at = models.DateTimeField("發文時間", default=timezone.now)

    objects = PostQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "文章"
        verbose_name_plural = "文章"

    def __str__(self):
        return f"[{self.prefix}] {self.title}"

    def get_absolute_url(self):
        return reverse("post_detail", args=[self.pk])


class Comment(models.Model):
    """推文：推 / 噓 / →"""
    KIND_CHOICES = [("push", "推"), ("boo", "噓"), ("arrow", "→")]
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments", verbose_name="文章")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments", verbose_name="推文者")
    kind = models.CharField("類型", max_length=5, choices=KIND_CHOICES, default="push")
    content = models.CharField("推文內容", max_length=100)
    created_at = models.DateTimeField("推文時間", default=timezone.now)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "推文"
        verbose_name_plural = "推文"

    def __str__(self):
        return f"{self.get_kind_display()} {self.author}: {self.content[:20]}"


class Favorite(models.Model):
    """我的收藏看板 — 對應 Persona C"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites", verbose_name="會員")
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="favorited_by", verbose_name="看板")
    created_at = models.DateTimeField("收藏時間", auto_now_add=True)

    class Meta:
        unique_together = ("user", "board")
        ordering = ["created_at"]
        verbose_name = "收藏看板"
        verbose_name_plural = "收藏看板"

    def __str__(self):
        return f"{self.user} ♥ {self.board.name}"


class BrowseHistory(models.Model):
    """最近瀏覽紀錄"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="history", verbose_name="會員")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="+", verbose_name="文章")
    viewed_at = models.DateTimeField("瀏覽時間", default=timezone.now)

    class Meta:
        unique_together = ("user", "post")
        ordering = ["-viewed_at"]
        verbose_name = "瀏覽紀錄"
        verbose_name_plural = "瀏覽紀錄"

    def __str__(self):
        return f"{self.user} → {self.post.title}"
