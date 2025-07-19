from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for, Response
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
from functools import wraps
import os
import json
from datetime import datetime
import subprocess
import uuid
import time

app = Flask(__name__)

# 配置应用的基本URL
app.config['PREFERRED_URL_SCHEME'] = 'https'
app.config['SERVER_NAME'] = 'www.bkspuik.linv.com:5062'

# 获取当前文件所在目录的绝对路径
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# 配置
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static/videos')
app.config['THUMBNAIL_FOLDER'] = os.path.join(BASE_DIR, 'static/thumbnails')
app.config['DATA_FILE'] = os.path.join(BASE_DIR, 'videos.json')
app.config['DEFAULT_THUMBNAILS'] = ['default.jpg', 'default1.jpg', 'default2.jpg']
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'webm', 'mkv'}
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['USERS_FILE'] = os.path.join(BASE_DIR, 'users.json')
app.config['SERVER_NAME'] = "www.liepin.ficlf.com:5062"

# 确保目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['THUMBNAIL_FOLDER'], exist_ok=True)

# 如果用户文件不存在则创建
if not os.path.exists(app.config['USERS_FILE']):
    with open(app.config['USERS_FILE'], 'w') as f:
        json.dump([], f)



# 添加代理支持
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# 存储弹幕
video_danmus = {}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_video_duration(file_path):
    try:
        result = subprocess.check_output(
            ['ffprobe', '-v', 'error', '-show_entries', 
             'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', 
             file_path],
            stderr=subprocess.STDOUT
        )
        total_seconds = float(result)
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)
        return f"{minutes}:{seconds:02d}"
    except:
        return "0:00"

def generate_thumbnail(video_path, thumbnail_path):
    try:
        subprocess.call([
            'ffmpeg', '-i', video_path,
            '-ss', '00:00:01',
            '-vframes', '1',
            thumbnail_path
        ])
        return os.path.exists(thumbnail_path)
    except:
        return False

def scan_videos():
    try:
        with open(app.config['DATA_FILE'], 'r') as f:
            return json.load(f)
    except:
        return []

def load_users():
    try:
        with open(app.config['USERS_FILE'], 'r') as f:
            return json.load(f)
    except:
        return []

def save_users(users):
    with open(app.config['USERS_FILE'], 'w') as f:
        json.dump(users, f, indent=2)

def get_user_following(user_id):
    users = load_users()
    user = next((u for u in users if u['id'] == user_id), None)
    return user.get('following', []) if user else []

def get_user_favorites(user_id):
    users = load_users()
    user = next((u for u in users if u['id'] == user_id), None)
    return user.get('favorites', []) if user else []

# 登录检查装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    videos = scan_videos()
    return render_template('index.html', videos=videos, domain=app.config['SERVER_NAME'])

# 添加搜索路由
@app.route('/search')
def search():
    query = request.args.get('q', '').strip().lower()
    videos = scan_videos()
    
    if query:
        filtered_videos = [
            v for v in videos 
            if query in v['title'].lower() or query in v['filename'].lower()
        ]
    else:
        filtered_videos = videos
    
    return render_template('search.html', videos=filtered_videos, query=query, domain=app.config['SERVER_NAME'])

@app.route('/upload')
@login_required
def upload_page():
    return render_template('upload.html', domain=app.config['SERVER_NAME'])

@app.route('/video/<vid>')
def play_video(vid):
    videos = scan_videos()
    video = next((v for v in videos if v['id'] == vid), None)
    if video:
        video['safe_filename'] = secure_filename(video['filename'])
        video['views'] += 1
        with open(app.config['DATA_FILE'], 'w') as f:
            json.dump(videos, f, indent=2)
        
        # 检查当前用户是否点赞/收藏
        liked = False
        favorited = False
        if 'user_id' in session:
            liked = session['username'] in video.get('liked_by', [])
            favorited = vid in get_user_favorites(session['user_id'])
        
        # 获取作者粉丝数
        author_followers = 0
        users = load_users()
        author_user = next((u for u in users if u['username'] == video.get('author', '')), None)
        if author_user:
            author_followers = author_user.get('followers', 0)
        
    author_avatar = 'default_avatar.jpg'  # 默认值
    if author_user:
        author_avatar = author_user.get('avatar', 'default_avatar.jpg')

        # 获取当前用户关注列表
        current_user_following = []
        if 'user_id' in session:
            current_user_following = get_user_following(session['user_id'])
        
        # 弹幕区域高度百分比 (25%)
        danmu_height = 25
        
        return render_template('video.html', 
                              video=video, 
                              domain=app.config['SERVER_NAME'],
                              liked=liked,
                              favorited=favorited,
                              author_followers=author_followers,
                              current_user_following=current_user_following,
                              comments=video.get('comments', []),
                              danmu_height=danmu_height,
                              author_avatar=author_avatar)
    return "Video not found", 404

@app.route('/update')
def manual_update():
    video_files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) 
                  if f.split('.')[-1] in app.config['ALLOWED_EXTENSIONS']]
    
    try:
        with open(app.config['DATA_FILE'], 'r') as f:
            videos = json.load(f)
    except:
        videos = []
    
    existing_files = {v['filename'] for v in videos}
    
    for filename in video_files:
        if filename not in existing_files:
            vid = filename.split('.')[0]
            safe_filename = secure_filename(filename)
            duration = get_video_duration(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            thumbnail_filename = f"{vid}.jpg"
            thumbnail_path = os.path.join(app.config['THUMBNAIL_FOLDER'], thumbnail_filename)
            if not generate_thumbnail(os.path.join(app.config['UPLOAD_FOLDER'], filename), thumbnail_path):
                idx = len(videos) % len(app.config['DEFAULT_THUMBNAILS'])
                thumbnail_filename = app.config['DEFAULT_THUMBNAILS'][idx]
            
            video_data = {
                "id": vid,
                "title": filename.split('.')[0].replace('_', ' '),
                "filename": safe_filename,
                "upload_date": datetime.now().strftime("%Y-%m-%d"),
                "views": 0,
                "duration": duration,
                "thumbnail": thumbnail_filename,
                "author": "系统",
                "likes": 0,
                "favorites": 0,
                "liked_by": [],
                "favorited_by": [],
                "comments": []
            }
            videos.append(video_data)
    
    with open(app.config['DATA_FILE'], 'w') as f:
        json.dump(videos, f, indent=2)
    
    return "Database updated successfully"

@app.route('/upload_video', methods=['POST'])
@login_required
def upload_video():
    if request.method == 'POST':
        if 'video_file' not in request.files:
            return jsonify({"status": "error", "message": "没有选择文件"}), 400
        
        file = request.files['video_file']
        
        if file.filename == '':
            return jsonify({"status": "error", "message": "没有选择文件"}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            vid = filename.split('.')[0]
            
            counter = 1
            original_filename = filename
            while os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
                name, ext = os.path.splitext(original_filename)
                filename = f"{name}_{counter}{ext}"
                vid = filename.split('.')[0]
                counter += 1
            
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(video_path)
            os.chmod(video_path, 0o644)
            
            duration = get_video_duration(video_path)
            
            thumbnail_filename = f"{vid}.jpg"
            thumbnail_path = os.path.join(app.config['THUMBNAIL_FOLDER'], thumbnail_filename)
            if not generate_thumbnail(video_path, thumbnail_path):
                try:
                    with open(app.config['DATA_FILE'], 'r') as f:
                        videos = json.load(f)
                except:
                    videos = []
                idx = len(videos) % len(app.config['DEFAULT_THUMBNAILS'])
                thumbnail_filename = app.config['DEFAULT_THUMBNAILS'][idx]
            
            title = request.form.get('title', filename.split('.')[0].replace('_', ' '))
            if not title.strip():
                title = filename.split('.')[0].replace('_', ' ')
            
            video_data = {
                "id": vid,
                "title": title,
                "filename": filename,
                "upload_date": datetime.now().strftime("%Y-%m-%d"),
                "views": 0,
                "duration": duration,
                "thumbnail": thumbnail_filename,
                "author": session['username'],
                "likes": 0,
                "favorites": 0,
                "liked_by": [],
                "favorited_by": [],
                "comments": []
            }
            
            try:
                with open(app.config['DATA_FILE'], 'r') as f:
                    videos = json.load(f)
            except:
                videos = []
            
            videos.append(video_data)
            
            with open(app.config['DATA_FILE'], 'w') as f:
                json.dump(videos, f, indent=2)
            
            return jsonify({
                "status": "success", 
                "message": "视频上传成功",
                "video_id": vid
            })
        else:
            return jsonify({
                "status": "error", 
                "message": "不支持的文件类型，仅支持MP4、WebM、MKV"
            }), 400
    
    return jsonify({"status": "error", "message": "无效请求"}), 400

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not password:
            return render_template('register.html', error='用户名和密码不能为空', domain=app.config['SERVER_NAME'])
        
        if password != confirm_password:
            return render_template('register.html', error='两次输入的密码不一致', domain=app.config['SERVER_NAME'])
        
        users = load_users()
        if any(user['username'] == username for user in users):
            return render_template('register.html', error='用户名已存在', domain=app.config['SERVER_NAME'])
        
        new_user = {
            'id': str(uuid.uuid4()),
            'username': username,
            'password': generate_password_hash(password),
            'register_date': datetime.now().strftime("%Y-%m-%d"),
            'followers': 0,
            'following': [],
            'favorites': []
        }
        
        users.append(new_user)
        save_users(users)
        
        session['user_id'] = new_user['id']
        session['username'] = new_user['username']
        return redirect(url_for('index'))
    
    return render_template('register.html', domain=app.config['SERVER_NAME'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        users = load_users()
        user = next((u for u in users if u['username'] == username), None)
        
        if not user or not check_password_hash(user['password'], password):
            return render_template('login.html', error='用户名或密码错误', domain=app.config['SERVER_NAME'])
        
        session['user_id'] = user['id']
        session['username'] = user['username']
        return redirect(url_for('index'))
    
    return render_template('login.html', domain=app.config['SERVER_NAME'])

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow_user(username):
    try:
        users = load_users()
        current_user = next((u for u in users if u['id'] == session['user_id']), None)
        target_user = next((u for u in users if u['username'] == username), None)
        
        if not target_user:
            return jsonify({"status": "error", "message": "用户不存在"}), 404
        
        if username == session['username']:
            return jsonify({"status": "error", "message": "不能关注自己"}), 400
        
        # 确保 following 字段存在
        if 'following' not in current_user:
            current_user['following'] = []
        
        if username in current_user['following']:
            current_user['following'].remove(username)
            target_user['followers'] = max(0, target_user.get('followers', 0) - 1)
            action = "unfollow"
        else:
            current_user['following'].append(username)
            target_user['followers'] = target_user.get('followers', 0) + 1
            action = "follow"
        
        # 更新会话中的关注列表
        session['following'] = current_user['following']
        
        save_users(users)
        return jsonify({
            "status": "success", 
            "action": action, 
            "followers": target_user['followers']
        })
    except Exception as e:
        app.logger.error(f"关注操作失败: {str(e)}")
        return jsonify({"status": "error", "message": "服务器错误"}), 500

@app.route('/video/<vid>/like', methods=['POST'])
@login_required
def like_video(vid):
    videos = scan_videos()
    video = next((v for v in videos if v['id'] == vid), None)
    
    if not video:
        return jsonify({"status": "error", "message": "视频不存在"}), 404
    
    username = session['username']
    
    if username in video['liked_by']:
        # 取消点赞
        video['liked_by'].remove(username)
        video['likes'] -= 1
        action = "unlike"
    else:
        # 点赞
        video['liked_by'].append(username)
        video['likes'] += 1
        action = "like"
    
    with open(app.config['DATA_FILE'], 'w') as f:
        json.dump(videos, f, indent=2)
    
    return jsonify({"status": "success", "action": action, "likes": video['likes']})

@app.route('/video/<vid>/favorite', methods=['POST'])
@login_required
def favorite_video(vid):
    videos = scan_videos()
    video = next((v for v in videos if v['id'] == vid), None)
    
    if not video:
        return jsonify({"status": "error", "message": "视频不存在"}), 404
    
    users = load_users()
    user = next((u for u in users if u['id'] == session['user_id']), None)
    username = session['username']
    
    if vid in user['favorites']:
        # 取消收藏
        user['favorites'].remove(vid)
        if username in video['favorited_by']:
            video['favorited_by'].remove(username)
        video['favorites'] -= 1
        action = "unfavorite"
    else:
        # 收藏
        user['favorites'].append(vid)
        video['favorited_by'].append(username)
        video['favorites'] += 1
        action = "favorite"
    
    save_users(users)
    with open(app.config['DATA_FILE'], 'w') as f:
        json.dump(videos, f, indent=2)
    
    return jsonify({"status": "success", "action": action, "favorites": video['favorites']})

@app.route('/favorites')
@login_required
def favorites_page():
    users = load_users()
    user = next((u for u in users if u['id'] == session['user_id']), None)
    
    if not user:
        return redirect(url_for('login'))
    
    videos = scan_videos()
    favorite_videos = [v for v in videos if v['id'] in user['favorites']]
    
    return render_template('favorites.html', videos=favorite_videos, domain=app.config['SERVER_NAME'])

@app.route('/video/<vid>/danmu', methods=['POST'])
def send_danmu(vid):
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({"status": "error", "message": "弹幕内容不能为空"}), 400
    
    if vid not in video_danmus:
        video_danmus[vid] = []
    
    # 存储弹幕
    danmu = {
        'text': text,
        'time': time.time(),
        'author': session.get('username', '匿名')
    }
    
    video_danmus[vid].append(danmu)
    return jsonify({"status": "success"})

@app.route('/video/<vid>/danmu_stream')
def danmu_stream(vid):
    def event_stream():
        last_id = 0
        while True:
            if vid in video_danmus and len(video_danmus[vid]) > last_id:
                for danmu in video_danmus[vid][last_id:]:
                    yield f"data: {json.dumps(danmu)}\n\n"
                    last_id += 1
            time.sleep(0.5)
    
    return Response(event_stream(), mimetype="text/event-stream")

@app.route('/video/<vid>/comment', methods=['POST'])
@login_required
def post_comment(vid):
    videos = scan_videos()
    video = next((v for v in videos if v['id'] == vid), None)
    
    if not video:
        return jsonify({"status": "error", "message": "视频不存在"}), 404
    
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({"status": "error", "message": "评论内容不能为空"}), 400
    
    # 添加评论
    comment = {
        'id': str(uuid.uuid4()),
        'author': session['username'],
        'text': text,
        'time': datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    
    if 'comments' not in video:
        video['comments'] = []
    
    video['comments'].append(comment)
    
    with open(app.config['DATA_FILE'], 'w') as f:
        json.dump(videos, f, indent=2)
    
    return jsonify({"status": "success", "comment": comment})

@app.route('/user/<username>')
def user_profile(username):
    users = load_users()
    user = next((u for u in users if u['username'] == username), None)
    
    if not user:
        return "用户不存在", 404
    
    videos = scan_videos()
    user_videos = [v for v in videos if v.get('author') == username]
    
    # 获取当前用户关注列表
    current_user_following = []
    if 'user_id' in session:
        current_user_following = get_user_following(session['user_id'])
    
    return render_template('profile.html', 
                          user=user, 
                          videos=user_videos, 
                          domain=app.config['SERVER_NAME'],
                          current_user_following=current_user_following)

def export_static_pages():
    with app.test_client() as client:
        response = client.get('/')
        with open('index_exported.html', 'wb') as f:
            f.write(response.data)

@app.route('/')
def home():
    return render_template('index.html')

export_static_pages()

if __name__ == '__main__':
    # 使用域名对应的SSL证书
    ssl_context = (
        os.path.join(BASE_DIR, 'cert.pem'),
        os.path.join(BASE_DIR, 'key.pem')
    )
    
    # 监听所有接口
    host = '0.0.0.0'
    
    app.run(
        host=host,
        port=5062,
        debug=True,
        ssl_context=ssl_context
    )
