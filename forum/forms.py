from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Board, Comment, Post


class SignUpForm(UserCreationForm):
    email = forms.EmailField(label="Email", required=False)

    class Meta:
        model = User
        fields = ("username", "email")
        labels = {"username": "帳號"}
        help_texts = {"username": "英文、數字或 @/./+/-/_，150 字以內"}


class PostForm(forms.ModelForm):
    board = forms.ModelChoiceField(queryset=Board.objects.filter(is_active=True), label="看板")

    class Meta:
        model = Post
        fields = ("board", "prefix", "title", "content", "image_url")
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "請輸入標題"}),
            "content": forms.Textarea(attrs={"rows": 10, "placeholder": "內文…貼上圖片網址（.jpg/.png）或 YouTube 連結會自動顯示預覽"}),
            "image_url": forms.URLInput(attrs={"placeholder": "https://…（選填，顯示於列表縮圖）"}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("kind", "content")
        labels = {"kind": "", "content": ""}
        widgets = {
            "kind": forms.Select(attrs={"class": "kind-select"}),
            "content": forms.TextInput(attrs={"placeholder": "我要推文…（最多 100 字）", "maxlength": 100}),
        }
