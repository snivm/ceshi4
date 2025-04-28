import datetime
import os
import logging
from flask import Blueprint,jsonify, render_template, request, flash, redirect, url_for, session
from .database_models import *
from .exts import db
from ai_model import process_image
import ai_model

blue = Blueprint("ai", __name__)

# 封装数据库操作函数
def save_to_db(obj):
    try:
        db.session.add(obj)
        db.session.commit()
        return True
    except Exception as e:
        logging.error(f"数据库保存失败: {e}")
        db.session.rollback()
        return False

# 初始化管理员账户
def init_admin_account():
    admin_username = "admin"
    admin_password = "123"
    # 同时根据用户名和用户类型查询管理员账户
    admin = User.query.filter_by(username=admin_username, usertype='管理员').first()
    if not admin:
        new_admin = User(username=admin_username, password=admin_password, usertype='管理员')
        if save_to_db(new_admin):
            logging.info("初始管理员账户创建成功")
        else:
            logging.error("初始管理员账户创建失败")


# 注册页
@blue.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('用户名和密码不能为空！')
            return redirect(url_for('ai.register'))
        user = User.query.filter_by(username=username).first()
        if user:
            flash('账号已存在！')
            return redirect(url_for('ai.register'))
        new_user = User(username=username, password=password, usertype='普通用户')
        if save_to_db(new_user):
            flash('注册成功！请登录。')
            return redirect(url_for('ai.login'))
        else:
            flash('注册失败，请稍后重试。')
    return render_template('new_index.html')


# 默认登录页
@blue.route('/')
def login_page():
    return render_template('new_index.html')


# 登录页
@blue.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('用户名和密码不能为空！')
            return redirect(url_for('ai.login'))
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session["username"] = username
            session["usertype"] = user.usertype
            ip_address = request.remote_addr
            record_login_log(username, ip_address)
            return redirect(url_for('ai.index'))
        else:
            flash('账号或密码错误！', 'error')
    return render_template('new_index.html')


# 首页
@blue.route('/index')
def index():
    return render_template('new_default.html')


# 用户页面
@blue.route('/user', methods=['GET', 'POST'])
def user():
    users = User.query.all()
    return render_template('new_user.html', users=users)


# 密码页面
@blue.route('/pwd', methods=['GET', 'POST'])
def pwd():
    if request.method == 'POST':
        username = session.get("username")
        oldpassword = request.form.get('oldpassword')
        newpassword = request.form.get('newpassword')
        if not oldpassword or not newpassword:
            flash('旧密码和新密码不能为空！')
            return redirect(url_for('ai.pwd'))
        user = User.query.filter_by(username=username, password=oldpassword).first()
        if not user:
            flash('旧密码错误！', 'error')
            return redirect(url_for('ai.pwd'))
        user.password = newpassword
        if save_to_db(user):
            flash('密码修改成功！', 'success')
        else:
            flash('密码修改失败，请稍后重试。', 'error')
        return redirect(url_for('ai.pwd'))
    return render_template('new_pwd.html')


# 删除用户
@blue.route('/delete_user/<user_id>', methods=['GET'])
def delete_user_route(user_id):
    user = User.query.filter_by(username=user_id).first()
    if user:
        try:
            db.session.delete(user)
            db.session.commit()
            flash('删除用户成功！', 'success')
        except Exception as e:
            logging.error(f"删除用户失败: {e}")
            db.session.rollback()
            flash('删除用户失败，请稍后重试。', 'error')
    return redirect(url_for('ai.user'))


# 修改用户页面
@blue.route('/user_edit/<user_id>', methods=['GET'])
def user_edit(user_id):
    user = User.query.filter_by(username=user_id).first()
    if user:
        return render_template('user_edit.html', user=user)
    else:
        flash('用户不存在!', 'error')
        return redirect(url_for('ai.user'))

#修改用户页面---保存
@app.route('/user_edit_save', methods=['GET', 'POST'])
def user_edit_save():
    if request.method == 'POST':
        username = request.form['username']
        #password = request.form['password']
        usertype = request.form['usertype']
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 更新用户
                #sql = "UPDATE users SET password = %s,usertype = %s  WHERE username = %s"
                #cursor.execute(sql, (password, usertype,username))
                sql = "UPDATE users SET usertype = %s  WHERE username = %s"
                cursor.execute(sql, ( usertype,username))
            connection.commit()
            flash('用户修改成功！', 'success')
            return redirect(url_for('user'))
        finally:
            connection.close()
    return render_template('user_edit.html')

# 添加用户
@blue.route('/user_add', methods=['GET', 'POST'])
def user_add():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        usertype = request.form.get('usertype')
        if not username or not password or not usertype:
            flash('用户名、密码和用户类型不能为空！')
            return redirect(url_for('ai.user_add'))
        user = User.query.filter_by(username=username).first()
        if user:
            flash('账号已存在！')
            return redirect(url_for('ai.user'))
        new_user = User(username=username, password=password, usertype=usertype)
        if save_to_db(new_user):
            flash('用户添加成功！')
        else:
            flash('用户添加失败，请稍后重试。')
        return redirect(url_for('ai.user'))
    return render_template('new_user.html')


# 记录登录日志
def record_login_log(username, ip_address):
    login_time = datetime.datetime.now()
    log = LoginLog(username=username, ip_address=ip_address, login_time=login_time)
    save_to_db(log)


# 登录日志页面
@blue.route('/login_logs', methods=['GET', 'POST'])
def login_logs():
    logs = LoginLog.query.all()
    return render_template('new_login_logs.html', logs=logs)


# AI拍照
@blue.route('/ai_photo_old', methods=['GET', 'POST'])
def ai_photo_old():
    return render_template('new_ai_photo.html')


@blue.route('/save_photo', methods=['POST'])
def save_photo():
    photo_data = request.form.get('photo')
    if photo_data:
        now = datetime.datetime.now()
        time_str = now.strftime('%H%M%S%f')[:-3]
        photo_data = photo_data.replace('data:image/png;base64,', '')
        import base64
        UPLOAD_FOLDER = 'uploads'
        photo_path = os.path.join(UPLOAD_FOLDER, 'photo_' + time_str + '.png')
        try:
            with open(photo_path, 'wb') as f:
                f.write(base64.b64decode(photo_data))
            record_ai_photo_log(session.get("username"), os.path.basename(photo_path))
            return '照片保存成功'
        except Exception as e:
            logging.error(f"照片保存失败: {e}")
            return '照片保存失败，请稍后重试。'
    return '未收到照片数据'


# 记录AI日志
def record_ai_photo_log(username, fileanme):
    login_time = datetime.datetime.now()
    ai_photo = AIPhoto(userid=username, username=username, fileanme=fileanme, login_time=login_time, result='', con_level=0)
    save_to_db(ai_photo)


# AI拍照日志页面
@blue.route('/ai_photo_logs', methods=['GET', 'POST'])
def ai_photo_logs():
    logs = AIPhoto.query.all()
    return render_template('new_ai_photo_logs.html', logs=logs)


@blue.route('/new_kzmb')
def new_kzmb():
    return render_template('new_kzmb.html')


@blue.route('/new_echarts')
def new_echarts():
    from sqlalchemy import func
    try:
        result = db.session.query(AIPhoto.con_level.label('x_value'), func.count(AIPhoto.con_level).label('y_value')).group_by(AIPhoto.con_level).all()
        scatter_data = [[row.x_value, row.y_value] for row in result]
        logging.info(f"ECharts 数据: {scatter_data}")
        return render_template('new_echarts.html', scatter_data=scatter_data)
    except Exception as e:
        logging.error(f"ECharts 数据查询失败: {e}")
        flash('数据查询失败，请稍后重试。', 'error')
        return render_template('new_echarts.html', scatter_data=[])


# AI
@blue.route('/ai_photo', methods=['GET', 'POST'])
def ai_photo():
    return render_template('new_ai.html')


# AI处理接口
@blue.route('/ai/process', methods=['POST'])
def ai_process():
    if 'image' not in request.files:
        return jsonify({"error": "请选择图片文件"}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "未选择文件"}), 400
    upload_folder = os.path.join('static', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    temp_path = os.path.join(upload_folder, 'temp.png')
    result_temp_path = os.path.join(upload_folder, 'result_temp.png')
    try:
        file.save(temp_path)
        st = ''
        processed_image = process_image(temp_path)
        processed_image.save(result_temp_path)
        if ai_model.g_res is None:
            logging.error("模型未正确初始化，无法进行预测。")
            return jsonify({"error": "模型未正确初始化，无法进行预测。"}), 500
        names = ai_model.g_res.names
        cls = ai_model.g_res.boxes.cls.cpu().numpy()
        conf = ai_model.g_res.boxes.conf.cpu().numpy()
        confidence = 0
        result_class_name = ""
        for i in range(len(cls)):
            class_index = int(cls[i])
            class_name = names[class_index]
            confidence = conf[i]
            result_class_name = result_class_name + get_citrus_disease_info(class_name) + "<br/>"
        record_ai_photo_logx(session.get("username"), "", class_name, confidence)
        return jsonify({
            "result_class_name": result_class_name,
            "result": st + "处理成功",
            "original_image": url_for('static', filename='uploads/temp.png', _external=True),
            "processed_image": url_for('static', filename='uploads/result_temp.png', _external=True)
        })
    except Exception as e:
        logging.error(f"AI 处理失败: {e}")
        return jsonify({"error": f"处理失败：{str(e)}"}), 500


def get_citrus_disease_info(disease_name):
    disease_info = {
        "Brown_Spot": {
            "预防": "加强果园管理，合理修剪，增强树势；及时排水，降低果园湿度；冬季清园，减少病原菌基数。",
            "治疗": "发病初期可选用苯醚甲环唑、戊唑醇等杀菌剂喷雾防治。"
        },
        "Citrus_Black_Spot": {
            "预防": "做好果园卫生，清除病叶、病果；合理施肥，增强树体抗病能力；适时喷药保护，在落花后及幼果期进行药剂防治。",
            "治疗": "可使用代森锰锌、多菌灵等杀菌剂进行喷雾防治。"
        },
        "Citrus_Canker": {
            "预防": "严格执行检疫制度，防止病菌传入；培育无病苗木；加强栽培管理，增施有机肥，避免偏施氮肥。",
            "治疗": "发病时可选用氢氧化铜、春雷霉素等药剂喷雾防治，同时及时剪除病枝、病叶、病果。"
        },
        "Citrus_Greasy_Spot": {
            "预防": "加强栽培管理，增强树势；做好冬季清园工作，减少越冬病菌；合理修剪，改善果园通风透光条件。",
            "治疗": "在春梢和秋梢发病初期，可选用吡唑醚菌酯、肟菌酯等杀菌剂喷雾防治。"
        },
        "Citrus_Scab": {
            "预防": "加强果园管理，合理密植，及时排水；冬季清园，铲除病原菌；在春梢萌芽期和幼果期进行药剂保护。",
            "治疗": "可选用甲基硫菌灵、百菌清等杀菌剂进行喷雾防治。"
        },
        "Greening": {
            "预防": "种植无病苗木；防治柑橘木虱，减少传毒媒介；加强果园管理，增强树势。",
            "治疗": "目前尚无有效的治疗方法，发现病株应及时挖除，集中烧毁，防止扩散。"
        },
        "Healthy": {
            "预防": "保持果园良好的生态环境，合理施肥、灌溉、修剪，做好病虫害监测，及时采取预防措施，维持柑橘树的健康状态。",
            "治疗": "无需治疗，保持预防措施即可。"
        },
        "Leprosis": {
            "预防": "加强检疫，防止病害传入；培育无病苗木；防治传毒昆虫，如蓟马等。",
            "治疗": "目前无特效治疗方法，主要是通过防治传毒昆虫来控制病害传播，同时加强树体营养，增强树势。"
        },
        "Orange_Scab": {
            "预防": "加强果园管理，增强树势；做好冬季清园工作，减少病原菌；在春雨和梅雨季节前进行药剂预防。",
            "治疗": "可选用氟环唑、苯甲·嘧菌酯等杀菌剂进行喷雾防治。"
        },
        "Sooty_Mold": {
            "预防": "防治柑橘蚜虫、蚧壳虫等刺吸式害虫，减少煤烟病的发生源头；加强果园通风透光，降低湿度。",
            "治疗": "及时防治害虫，可使用啶虫脒、噻嗪酮等药剂；同时用清水或弱碱性溶液清洗病叶、病果上的煤烟状物。"
        },
        "Xyloporosis": {
            "预防": "选用无病苗木；轮作换茬，与禾本科作物轮作；增施有机肥，改良土壤。",
            "治疗": "可使用阿维菌素、噻唑膦等药剂进行灌根处理。"
        }
    }
    if disease_name in disease_info:
        info = disease_info[disease_name]
        return f"病虫害名称: {disease_name}\n预防内容: {info['预防']}\n治疗方式: {info['治疗']}"
    else:
        return f"未找到 {disease_name} 的相关信息。"


def record_ai_photo_logx(username, fileanme, class_name, confidence):
    login_time = datetime.datetime.now()
    ai_photo = AIPhoto(userid=username, username=username, fileanme=fileanme, login_time=login_time, result=class_name, con_level=confidence)
    save_to_db(ai_photo)


# AI_VID
@blue.route('/ai_vid', methods=['GET', 'POST'])
def ai_vid():
    return render_template('ai_vid.html')


# AI处理接口
@blue.route('/ai/ai_process_video', methods=['POST'])
def ai_process_video():
    # 验证请求中是否包含视频文件
    if 'video' not in request.files:
        logging.warning("请求中未包含视频文件")
        return jsonify({"error": "请选择视频文件"}), 400
    video = request.files['video']
    # 验证视频文件名是否为空
    if video.filename == '':
        logging.warning("未选择视频文件")
        return jsonify({"error": "未选择视频文件"}), 400
    # 验证文件类型是否为视频
    allowed_extensions = {'mp4', 'avi', 'mov'}
    file_extension = os.path.splitext(video.filename)[1][1:].lower()
    if file_extension not in allowed_extensions:
        logging.warning(f"不支持的文件类型: {file_extension}")
        return jsonify({"error": f"不支持的文件类型，仅支持 {', '.join(allowed_extensions)}"}), 400
    # 生成唯一的文件名
    current_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
    filename, _ = os.path.splitext(video.filename)
    new_filename = f"{filename}_{current_time}.{file_extension}"
    VIDEO_TEMP_FOLDER = os.path.join('vid', 'temp')
    video_path = os.path.join(VIDEO_TEMP_FOLDER, new_filename)
    output_path = os.path.join('static', f"output_video_{current_time}.mp4")
    try:
        # 保存视频文件
        logging.info(f"开始保存视频文件到 {video_path}")
        video.save(video_path)
        logging.info(f"视频文件已保存到 {video_path}")
        # 处理视频
        import video_process_web
        logging.info(f"开始处理视频: {video_path}")
        video_process_web.process_video(video_path, output_path, skip_frames=2)
        logging.info(f"视频处理完成，输出文件: {output_path}")
        # 清理临时文件
        if os.path.exists(video_path):
            os.remove(video_path)
            logging.info(f"临时文件 {video_path} 已删除")
        return jsonify({
            "result": f"处理成功！",
            "confidence": '',
            "label": '',
            "original_image": '',
            "processed_image": '',
        })
    except Exception as e:
        logging.error(f"视频处理失败: {e}")
        # 清理临时文件
        if os.path.exists(video_path):
            os.remove(video_path)
            logging.info(f"临时文件 {video_path} 已删除")
        return jsonify({"error": f"视频处理失败：{str(e)}"}), 500
