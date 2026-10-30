from django.contrib import admin

from .models import Board, BrowseHistory, Category, Comment, Favorite, Post


class BoardInline(admin.TabularInline):
    model = Board
    extra = 0
    fields = ("name", "zh_name", "is_active")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "icon", "color", "order", "board_count")
    list_editable = ("order",)
    prepopulated_fields = {"slug": ("name",)}
    inlines = [BoardInline]

    @admin.display(description="看板數")
    def board_count(self, obj):
        return obj.boards.count()


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ("name", "zh_name", "category", "post_count", "is_active", "created_at")
    list_filter = ("category", "is_active")
    search_fields = ("name", "zh_name", "description")
    list_editable = ("is_active",)

    @admin.display(description="文章數")
    def post_count(self, obj):
        return obj.posts.count()


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    fields = ("kind", "author", "content", "created_at")
    raw_id_fields = ("author",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "prefix", "board", "author", "views", "comment_count", "created_at")
    list_filter = ("board__category", "board", "prefix", "created_at")
    search_fields = ("title", "content", "author__username")
    date_hierarchy = "created_at"
    raw_id_fields = ("author",)
    inlines = [CommentInline]

    @admin.display(description="推文數")
    def comment_count(self, obj):
        return obj.comments.count()


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("kind", "content", "author", "post", "created_at")
    list_filter = ("kind", "post__board")
    search_fields = ("content", "author__username", "post__title")
    raw_id_fields = ("author", "post")


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "board", "created_at")
    list_filter = ("board",)
    search_fields = ("user__username", "board__name")


@admin.register(BrowseHistory)
class BrowseHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "post", "viewed_at")
    search_fields = ("user__username", "post__title")
    raw_id_fields = ("post",)
