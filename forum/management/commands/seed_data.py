"""
建立示範資料：python manage.py seed_data
- 已有資料時不會重複建立（可加 --reset 清空重建）
- 會建立前台測試帳號 testuser / Test1234!
- 若有設定環境變數 DJANGO_SUPERUSER_USERNAME / DJANGO_SUPERUSER_PASSWORD，會同時建立後台管理員
"""
import os
import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from forum.models import Board, BrowseHistory, Category, Comment, Favorite, Post

CATEGORIES = [
    ("綜合", "general", "#6b5bd6"), ("科技", "tech", "#2f6fe0"), ("財經", "finance", "#0f8a6a"),
    ("生活", "life", "#d9772b"), ("娛樂", "fun", "#d64b8a"), ("運動", "sports", "#1f9d55"),
    ("遊戲", "game", "#8a4fd6"),
]

BOARDS = [
    ("Gossiping", "八卦板", "綜合", "什麼都能聊的綜合討論區，時事、問卦、生活大小事。"),
    ("Tech_Job", "科技工作板", "科技", "科技業求職、面試心得、薪資福利與職涯討論。"),
    ("Soft_Job", "軟體工作板", "科技", "軟體工程師的職涯、技術選型與工作甘苦談。"),
    ("MobileComm", "手機通訊板", "科技", "手機選購、資費方案、通訊相關討論。"),
    ("PC_Shopping", "電腦選購板", "科技", "組電腦、筆電選購、零組件價格與開箱。"),
    ("Stock", "股票板", "財經", "台股、美股與投資觀念討論，理性交流。"),
    ("home-sale", "房屋買賣板", "財經", "買房、賣房、房貸與看屋經驗分享。"),
    ("Lifeismoney", "省錢板", "生活", "優惠情報、信用卡回饋、各種省錢小技巧。"),
    ("Food", "美食板", "生活", "各地餐廳食記、料理心得與美食推薦。"),
    ("car", "汽車板", "生活", "買車、養車、用車經驗與新車資訊。"),
    ("C_Chat", "希洽板", "娛樂", "動畫、漫畫、輕小說與 ACG 閒聊。"),
    ("movie", "電影板", "娛樂", "電影心得、上映資訊與影評討論（請注意防雷）。"),
    ("Baseball", "棒球板", "運動", "職棒、國際賽與各級棒球討論。"),
    ("basketballTW", "台灣籃球板", "運動", "國內職籃、大專籃球與籃球話題。"),
    ("LoL", "英雄聯盟板", "遊戲", "英雄聯盟賽事、版本改動與遊戲心得。"),
]

AUTHORS = ["namant", "photolover", "coder_99", "user123", "ic_engineer", "foodie_tw",
           "stock_newbie", "anime_fan", "bullpen7", "night_owl", "saver_king", "carguy88"]

IMG = "https://picsum.photos/seed/{}/800/450"

# (看板, 前綴, 標題, 內文, 封面圖 seed 或 None, 幾天前)
POSTS = [
    ("Tech_Job", "討論", "2026 科技業年終與分紅預測",
     "今年大家狀況如何？聽說有些部門外商已經開始調薪，也有人說分紅會比去年少。\n\n想請大家分享一下自己公司的狀況（不用講公司名，講產業就好），讓還在觀望的人有個參考。", "office", 1),
    ("Tech_Job", "心得", "研發替代役面試心得分享（半導體）",
     "上週去了兩間半導體廠的研發替代役面試，整理一些心得給學弟妹參考。\n\n1. 一面主要問碩論內容，要能用五分鐘講清楚研究動機。\n2. 二面有主管問專業題，記得複習電路與製程基礎。\n3. 最後 HR 會問可以接受的輪班制度。\n\n整體氣氛不錯，準備充分就不用太緊張。", "interview", 2),
    ("Tech_Job", "請益", "科技業新鮮人求職與面試準備請教",
     "明年要畢業了，想投數位 IC 設計相關職缺。想請問前輩們：\n\n- 履歷要放多少專題經驗？\n- 面試常考哪些題目？\n- 白板題需要練到什麼程度？\n\n先謝謝大家回覆！", None, 3),
    ("Tech_Job", "問題", "數位 IC 設計面試沒收到感謝信，還有機會嗎？",
     "兩週前面試完到現在都沒消息，也沒收到感謝函。想問這種狀況通常是還在比較，還是其實已經沒機會了？", None, 5),
    ("Tech_Job", "情報", "外商半導體公司開出大量新鮮人職缺",
     "看到幾間外商陸續在徵製程與設備工程師，起薪比去年高一些。有興趣的可以注意各公司官網，面試流程大約三到四週。", "factory", 8),
    ("Soft_Job", "心得", "三年資歷軟體工程師轉職面試分享",
     "最近轉職成功，總共面了六間公司，分享一下面試流程與心得：\n\n大部分公司是 線上測驗 → 技術面試 → 主管面試 → HR。技術面試會考資料結構與系統設計，建議把常見題型練熟。\n\n最重要的是準備好說明自己做過的專案，面試官很愛追問細節。", "laptop", 1),
    ("Soft_Job", "討論", "前端框架 2026 年還值得學什麼？",
     "身邊同事有人說還是要先把基礎 JavaScript 打好，也有人說直接學框架上手比較快。大家覺得新人應該怎麼安排學習順序？", None, 4),
    ("Soft_Job", "請益", "Django 後端專案部署到雲端要注意什麼？",
     "第一次把 Django 專案部署到雲端，想問環境變數、靜態檔案、資料庫連線這幾個部分大家都怎麼處理？有推薦的免費方案嗎？", None, 6),
    ("MobileComm", "選購", "萬元以下拍照手機推薦（附實測）",
     "幫家人挑手機，預算一萬以內，最在意拍照與電池。實際借了幾台來比較，整理如下：\n\n夜拍：差距最明顯，中階機種進步很多。\n電池：大部分都能撐一天以上。\n\n實測照片：\nhttps://picsum.photos/seed/phonecam/800/500.jpg\n\n大家有其他推薦也歡迎補充！", "phone", 2),
    ("MobileComm", "問題", "4G 吃到飽方案續約該怎麼談比較划算？",
     "合約快到期了，想問大家續約時都怎麼跟電信談？直接打客服還是去門市比較容易拿到優惠？", None, 9),
    ("PC_Shopping", "討論", "顯卡太貴了，現在組電腦該等還是該買？",
     "預算三萬五想組一台可以玩 3A 遊戲的電腦，但顯卡價格一直下不來。大家覺得現在入手合理嗎？還是再等等？", "pc", 3),
    ("PC_Shopping", "心得", "第一次自己組電腦就上手的心得",
     "一直以為組電腦很難，實際做了才發現只要照說明書一步一步來就好。最難的是理線，花了快一個小時。附上成品照！", "pcbuild", 12),
    ("Stock", "討論", "新手存股第一年的心得與檢討",
     "去年開始每月定期定額，一年下來最大的收穫是學會不要每天看盤。也分享幾個踩過的坑：追高、聽明牌、沒設停損。\n\n純心得分享，不構成任何投資建議。", "stock", 1),
    ("Stock", "請益", "ETF 與個股該怎麼分配比例？",
     "剛出社會，每月可以投入一萬元。想請問大家都怎麼分配 ETF 與個股的比例？會不會太保守？", None, 4),
    ("Stock", "新聞", "央行利率決策出爐，市場反應平淡",
     "本次會議維持利率不變，市場普遍已經預期，盤面反應不大。後續觀察重點在物價走勢。", None, 10),
    ("home-sale", "心得", "首購族看了 30 間房子後的心得",
     "花了半年看房，整理幾個建議：\n1. 先算好每月能負擔的房貸。\n2. 白天晚上都要去看一次。\n3. 屋況檢查要找專業的人。\n\n最後終於找到喜歡的，分享給還在看的人。", "house", 7),
    ("Lifeismoney", "情報", "本月超商咖啡優惠整理",
     "整理了這個月幾家超商的咖啡優惠，第二杯半價和寄杯方案都有，自己算一下哪個最划算。", "coffee", 0),
    ("Lifeismoney", "分享", "信用卡回饋怎麼搭配最省錢？",
     "分享我自己的搭配：日常消費用一張高回饋卡，網購用另一張，加油再用專門的卡。重點是不要為了回饋多花錢。", None, 3),
    ("Lifeismoney", "問題", "大家都用什麼記帳 App？",
     "想開始記帳省錢，但試了幾個 App 都撐不過一週。有沒有推薦簡單好用的？", None, 6),
    ("Food", "心得", "台中巷弄裡的平價早午餐",
     "週末在巷子裡發現一間小店，份量很足，價格也很親民。推薦他們的厚片吐司和手沖咖啡！", "brunch", 2),
    ("Food", "分享", "在家做一鍋番茄燉牛肉",
     "天氣變冷就想吃燉菜，分享做法：牛肋條先煎香，再加番茄、洋蔥、紅蘿蔔燉兩小時。\n\n成品：\nhttps://picsum.photos/seed/stew/800/500.jpg", "stew", 5),
    ("car", "請益", "第一台車該買新車還是中古車？",
     "預算六十萬，通勤用，偶爾出遊。家人建議買中古車，自己比較想要新車的保固。大家怎麼看？", "car", 4),
    ("C_Chat", "閒聊", "這季動畫大家追了哪些？",
     "這季好看的動畫好多，時間都不夠用了。大家覺得哪部最推？我目前最喜歡奇幻冒險那部。", "anime", 0),
    ("C_Chat", "討論", "動畫改編原作，大家能接受改多少？",
     "最近看了幾部改編作品，有的刪減很多但節奏變好，有的幾乎照搬原作。大家覺得忠於原作比較重要，還是好看比較重要？", None, 3),
    ("C_Chat", "心得", "第一次參加同人展的心得",
     "第一次去同人展，人潮比想像中多很多！建議大家帶現金、穿好走的鞋，熱門攤位一開場就要先衝。", "expo", 11),
    ("movie", "心得", "這部科幻片的配樂真的太加分（無雷）",
     "整體劇情普通，但配樂和音效真的值得進影廳看一次。推薦選音響好一點的廳。", "cinema", 2),
    ("movie", "討論", "大家都怎麼選電影院座位？",
     "我習慣坐中間偏後，朋友說要坐前面才有沉浸感。好奇大家的習慣？", None, 8),
    ("Baseball", "討論", "季後賽首戰大家看了嗎？",
     "比賽延長到十一局才結束，兩隊牛棚都很拚。最後那個守備真的是本季最佳！", "baseball", 1),
    ("basketballTW", "閒聊", "主場氣氛真的越來越好",
     "這季去現場看了好幾場，應援和場館體驗都比以前進步很多，推薦大家帶朋友去看一次。", "basketball", 4),
    ("LoL", "討論", "新版本改動後，哪些角色變強了？",
     "改版後打了幾場，感覺坦克角色明顯變硬。大家覺得目前版本最強勢的是哪些？", "game", 2),
    ("Gossiping", "問卦", "有沒有大家下班後都在做什麼的卦？",
     "最近下班後只想躺著滑手機，覺得有點浪費時間。大家下班後都怎麼安排？運動？追劇？學新東西？", None, 0),
    ("Gossiping", "問卦", "有沒有颱風假到底怎麼決定的八卦？",
     "每次颱風來都在等宣布，想知道各縣市到底是根據什麼標準決定的？", None, 1),
    ("Gossiping", "新聞", "多地明起轉涼，民眾注意保暖",
     "氣象單位表示鋒面通過後各地氣溫下降，早晚溫差大，外出記得多帶件外套。", None, 2),
    ("Gossiping", "問卦", "有沒有新手第一次用 PTT 都看不懂的八卦？",
     "朋友第一次用 PTT，看到一堆英文板名和推文符號完全看不懂。大家當初是怎麼學會的？", None, 3),
]

PUSH = ["推推", "推分享", "感謝整理", "很實用", "收藏了", "說得好", "這篇推", "真的", "同意", "長知識了", "好文推", "有幫助"]
BOO = ["不太認同", "這個有待商榷", "想太多了吧", "跟我經驗不一樣"]
ARROW = ["補充一下我的經驗", "看情況吧", "可以再觀察", "我也想知道", "等後續", "+1"]


class Command(BaseCommand):
    help = "建立示範資料（看板、文章、推文、測試帳號）"

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="清除論壇資料後重建")

    @transaction.atomic
    def handle(self, *args, **opts):
        self._ensure_superuser()
        self._ensure_testuser()

        if opts["reset"]:
            Post.objects.all().delete()
            Board.objects.all().delete()
            Category.objects.all().delete()
        if Board.objects.exists():
            self.stdout.write(self.style.WARNING("已有看板資料，略過建立（要重建請加 --reset）"))
            return

        rng = random.Random(14)
        now = timezone.now()

        cats = {}
        for i, (name, slug, color) in enumerate(CATEGORIES):
            cats[name] = Category.objects.create(name=name, slug=slug, color=color, icon=name[0], order=i)
        boards = {}
        for name, zh, cat, desc in BOARDS:
            boards[name] = Board.objects.create(name=name, zh_name=zh, category=cats[cat], description=desc)

        authors = []
        for name in AUTHORS:
            u, created = User.objects.get_or_create(username=name)
            if created:
                u.set_unusable_password()
                u.save()
            authors.append(u)

        for board, prefix, title, content, img, days in POSTS:
            created = now - timedelta(days=days, hours=rng.randint(0, 20), minutes=rng.randint(0, 59))
            post = Post.objects.create(
                board=boards[board], author=rng.choice(authors), prefix=prefix, title=title,
                content=content, image_url=IMG.format(img) if img else "",
                created_at=created, views=rng.randint(80, 4000),
            )
            n = rng.randint(3, 28)
            comments = []
            for k in range(n):
                kind = rng.choices(["push", "boo", "arrow"], weights=[70, 10, 20])[0]
                text = rng.choice({"push": PUSH, "boo": BOO, "arrow": ARROW}[kind])
                comments.append(Comment(
                    post=post, author=rng.choice(authors), kind=kind, content=text,
                    created_at=created + timedelta(minutes=5 + k * rng.randint(3, 40)),
                ))
            Comment.objects.bulk_create(comments)

        tester = User.objects.get(username="testuser")
        for name in ["Tech_Job", "Stock", "C_Chat", "Lifeismoney"]:
            Favorite.objects.get_or_create(user=tester, board=boards[name])
        for p in Post.objects.filter(board__name__in=["Tech_Job", "Stock"])[:4]:
            BrowseHistory.objects.get_or_create(user=tester, post=p)

        self.stdout.write(self.style.SUCCESS(
            f"完成：{Category.objects.count()} 分類、{Board.objects.count()} 看板、"
            f"{Post.objects.count()} 文章、{Comment.objects.count()} 推文"))

    def _ensure_testuser(self):
        u, created = User.objects.get_or_create(username="testuser", defaults={"email": "testuser@example.com"})
        if created:
            u.set_password("Test1234!")
            u.save()
            self.stdout.write("建立前台測試帳號 testuser / Test1234!")

    def _ensure_superuser(self):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        if not (username and password):
            return
        u, created = User.objects.get_or_create(username=username, defaults={
            "email": os.environ.get("DJANGO_SUPERUSER_EMAIL", ""), "is_staff": True, "is_superuser": True})
        if created:
            u.set_password(password)
            u.save()
            self.stdout.write(f"建立後台管理員 {username}")
