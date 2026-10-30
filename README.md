# 批踢踢 Redesign：第 14 組 WEB 期中專題

以作業一的 PTT Bad UI 分析為基礎，用 **Django + Neon PostgreSQL** 實作重新設計的論壇網站，並部署到 **Render**。

---

## 一、網站功能對照表（寫報告時可直接引用）

| 頁面 | 網址 | 對應 Bad UI 問題／作業一分鏡 |
|---|---|---|
| 首頁（登入前） | `/` | 問題 1：四大入口，包括搜尋框、熱門看板、熱門文章、登入註冊（畫面 1-1、2-1） |
| 首頁（登入後＝個人儀表板） | `/` | Persona C：我的收藏、看板動態、最近瀏覽（畫面 3-1） |
| 分類看板 | `/boards/` | 問題 2：分類標籤，看板名稱旁附中文說明，可篩選與排序 |
| 看板文章列表 | `/bbs/Tech_Job/` | 問題 3：麵包屑導航。另有最新／熱門切換、板內搜尋、前綴篩選，以及 FAB 發文按鈕（畫面 1-2、3-2） |
| 文章內文 | `/post/1/` | 問題 4、5、6：卡片式推文區、推文輸入框、FAB，圖片與 YouTube 自動嵌入（畫面 1-3、3-3） |
| 搜尋結果 | `/search/?q=面試` | Persona B：可依時間、看板、分類篩選，可依相關度、最新、熱門排序，關鍵字會標示出來（畫面 2-2） |
| 我的收藏 | `/me/` | 收藏管理、最近瀏覽、我的文章（需登入） |
| 註冊／登入／發文 | `/signup/`、`/accounts/login/`、`/post/new/` | 會員功能 |
| Django 後台 | `/admin/` | 管理會員、權限、分類、看板、文章、推文、收藏、瀏覽紀錄 |

### 登入前和登入後的差異（老師會測）

| 功能 | 未登入 | 已登入 |
|---|---|---|
| 首頁 | 新手導覽，有搜尋框、熱門看板和熱門文章 | 個人儀表板，有收藏看板、看板動態和最近瀏覽 |
| 左側欄 | 顯示「登入解鎖更多功能」 | 顯示「我的最愛」看板清單 |
| 推文 | 看得到推文，但要推文會被導向登入頁 | 可以推、噓、→ |
| 收藏看板／發文 | 按鈕顯示為「登入以收藏／發文」 | 可以收藏，也有右下角 FAB 可以發文 |
| 我的收藏 `/me/` | 會導向登入頁 | 可以管理收藏、看瀏覽紀錄 |

### 資料表（Neon PostgreSQL）

`auth_user`（會員）、`Category`（看板分類）、`Board`（看板）、`Post`（文章）、`Comment`（推文）、`Favorite`（收藏看板）、`BrowseHistory`（瀏覽紀錄）

---

## 二、部署步驟（約 30 分鐘）

### Step 1：建立 Neon 資料庫

1. 到 https://neon.tech 用 GitHub 或 Google 帳號註冊。
2. 按 **Create project**：
   - Project name：`ptt-redesign`
   - Region：選 **AWS Asia Pacific (Singapore)**，離台灣最近。
3. 建好之後按 **Connect**，複製 **Connection string**。它長這樣：
   ```
   postgresql://neondb_owner:xxxxxxxx@ep-xxxx-xxxx.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
   ```
   先把它存在記事本，Step 3 會用到。**不要貼到 GitHub 或報告上。**

### Step 2：把程式碼放上 GitHub

**方法 A：用網頁上傳（最簡單）**

1. 到 GitHub 按 **New repository**。名稱可以取 `ptt-redesign`，選 **Public**，再按 Create。
2. 在新 repo 頁面點 **uploading an existing file**。
3. 把解壓縮後的 `ptt_redesign` 資料夾**裡面的所有檔案和資料夾**拖進去。注意是拖裡面的東西，不是拖整個外層資料夾。
4. 按 **Commit changes**。
5. 確認 repo 首頁直接看得到 `manage.py`、`build.sh`、`requirements.txt`。

**方法 B：用 git 指令**

```bash
cd ptt_redesign
git init
git add .
git commit -m "PTT Redesign 期中專題"
git branch -M main
git remote add origin https://github.com/你的帳號/ptt-redesign.git
git push -u origin main
```

### Step 3：部署到 Render

1. 到 https://render.com 用 GitHub 帳號登入。
2. 按 **New ＋ → Web Service**，選剛剛的 `ptt-redesign` repo。
3. 依下表填寫：

   | 欄位 | 填入 |
   |---|---|
   | Name | `ptt-redesign-g14`（會變成網址的一部分） |
   | Region | Singapore |
   | Branch | `main` |
   | Language／Runtime | **Python 3** |
   | Build Command | `bash build.sh` |
   | Start Command | `gunicorn config.wsgi:application` |
   | Instance Type | **Free** |

4. 往下找到 **Environment Variables**，加入以下 5 個變數：

   | Key | Value |
   |---|---|
   | `DATABASE_URL` | Step 1 複製的 Neon 連線字串 |
   | `SECRET_KEY` | 隨便打一串 50 字以上的英數亂碼 |
   | `DEBUG` | `False` |
   | `DJANGO_SUPERUSER_USERNAME` | `admin` |
   | `DJANGO_SUPERUSER_PASSWORD` | 自訂後台密碼，例如 `Ptt14Admin!2026` |

5. 按 **Deploy Web Service**，等 3～5 分鐘。Log 出現 `完成：7 分類、15 看板、34 文章…` 和 `Your service is live` 就是成功了。
6. 網址會是 `https://ptt-redesign-g14.onrender.com`，後台在網址後面加 `/admin/`。

> `build.sh` 每次部署都會自動執行 migrate（建立資料表）和 seed_data（匯入示範資料與帳號），**不需要用 Shell**。示範資料只會在第一次匯入，之後重新部署不會重複建立。

### Step 4：確認 Neon 有資料

回到 Neon，點左邊的 **Tables**。看得到 `forum_post`、`forum_board`、`auth_user` 等資料表而且裡面有資料，就代表前台和後台用的是同一個 Neon 資料庫。報告可以截這個畫面。

---

## 三、測試帳號（寫進報告給老師）

| 用途 | 網址 | 帳號 | 密碼 |
|---|---|---|---|
| 前台會員 | `https://你的網址.onrender.com/accounts/login/` | `testuser` | `Test1234!` |
| Django 後台 | `https://你的網址.onrender.com/admin/` | `admin` | 你在 Render 設的 `DJANGO_SUPERUSER_PASSWORD` |

---

## 四、常見問題

| 狀況 | 解法 |
|---|---|
| 網頁第一次打開要等 30～60 秒 | Render 免費方案閒置 15 分鐘會休眠，屬於正常現象。**Demo 和繳交前先自己開一次網站**把它叫醒 |
| `DisallowedHost` | 到 Render 的 Environment 新增 `ALLOWED_HOSTS`，值填你的網域 |
| `CSRF verification failed` | 確認網址是 `https://…onrender.com`。如果用自訂網域，請加進 `ALLOWED_HOSTS` |
| Build 失敗，訊息有 `could not connect` | 檢查 `DATABASE_URL` 有沒有完整貼上、結尾是否有 `?sslmode=require` |
| 後台登不進去 | 確認環境變數名稱拼字正確。改完之後到 **Manual Deploy → Deploy latest commit** 重新部署 |
| 想把示範資料清空重建 | 把 Build Command 暫時改成 `bash build.sh && python manage.py seed_data --reset`，部署一次之後再改回來 |

---

## 五、本機執行（選用）

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
python manage.py createsuperuser
python manage.py runserver
```

打開 http://127.0.0.1:8000 就能看到網站。沒有設定 `DATABASE_URL` 時，會自動改用本機的 SQLite。

---

## 六、專案結構

```
ptt_redesign/
├─ config/settings.py      設定（Neon、Render、靜態檔）
├─ forum/
│  ├─ models.py            資料表
│  ├─ views.py             各頁面邏輯（搜尋篩選、登入前後差異）
│  ├─ admin.py             Django 後台設定
│  ├─ templatetags/        圖片／YouTube 自動嵌入、關鍵字標示
│  └─ management/commands/seed_data.py   示範資料
├─ templates/              HTML 頁面
├─ static/css/style.css    樣式（RWD）
├─ static/js/main.js       互動（收藏不換頁、手機選單、密碼顯示）
├─ build.sh                Render 建置指令
└─ requirements.txt
```
