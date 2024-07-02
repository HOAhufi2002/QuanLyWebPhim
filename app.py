import os
import gzip
import json
import pyodbc
import hashlib
from flask import Flask, request, render_template, redirect, url_for, session, flash, send_file

# Khởi tạo ứng dụng Flask
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Khóa bí mật cần thiết cho quản lý phiên (session management)

# Cấu hình kết nối cơ sở dữ liệu
conn_str = 'DRIVER={SQL Server};SERVER=minhhoa;DATABASE=dbmovie;Trusted_Connection=yes;'
conn = pyodbc.connect(conn_str)  # Kết nối tới cơ sở dữ liệu
cursor = conn.cursor()  # Tạo một con trỏ cơ sở dữ liệu để thực hiện các truy vấn

# Đảm bảo rằng các thư mục tồn tại
if not os.path.exists('video_files'):
    os.makedirs('video_files')  # Tạo thư mục lưu trữ video nếu chưa tồn tại

if not os.path.exists('static/thumbnails'):
    os.makedirs('static/thumbnails')  # Tạo thư mục lưu trữ thumbnail nếu chưa tồn tại

# Trang chủ hiển thị danh sách video
@app.route('/')
def index():
    cursor.execute("SELECT id, title, description, thumbnail FROM videos")  # Thực hiện truy vấn để lấy danh sách video
    videos = cursor.fetchall()  # Lấy tất cả các bản ghi từ truy vấn
    return render_template('index.html', videos=videos)  # Trả về template trang chủ với danh sách video

# Đăng ký người dùng
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':  # Kiểm tra xem phương thức yêu cầu có phải là POST không
        username = request.form['username']  # Lấy tên người dùng từ form đăng ký
        password = request.form['password']  # Lấy mật khẩu từ form đăng ký
        hashed_password = hashlib.sha256(password.encode()).hexdigest()  # Băm mật khẩu
        
        # Thực hiện truy vấn để thêm người dùng mới vào cơ sở dữ liệu
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, hashed_password, 'user'))
        conn.commit()  # Xác nhận thay đổi trong cơ sở dữ liệu
        
        flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')  # Hiển thị thông báo đăng ký thành công
        return redirect(url_for('login'))  # Chuyển hướng tới trang đăng nhập
    return render_template('register.html')  # Trả về template trang đăng ký

# Tìm kiếm phim
@app.route('/search')
def search():
    query = request.args.get('q', '')  # Lấy chuỗi tìm kiếm từ URL
    cursor.execute("SELECT id, title, description, thumbnail FROM videos WHERE title LIKE ?", ('%' + query + '%',))  # Thực hiện truy vấn tìm kiếm video theo tiêu đề
    videos = cursor.fetchall()  # Lấy tất cả các bản ghi từ truy vấn
    return render_template('search_results.html', videos=videos, query=query)  # Trả về template trang kết quả tìm kiếm với danh sách video tìm được

# Đăng nhập người dùng
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':  # Kiểm tra xem phương thức yêu cầu có phải là POST không
        username = request.form['username']  # Lấy tên người dùng từ form đăng nhập
        password = request.form['password']  # Lấy mật khẩu từ form đăng nhập
        hashed_password = hashlib.sha256(password.encode()).hexdigest()  # Băm mật khẩu
        
        # Thực hiện truy vấn kiểm tra thông tin đăng nhập
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_password))
        user = cursor.fetchone()  # Lấy bản ghi người dùng từ truy vấn
        
        if user:  # Kiểm tra xem có bản ghi người dùng không
            session['user_id'] = user[0]  # Lưu ID người dùng vào session
            session['username'] = user[1]  # Lưu tên người dùng vào session
            session['role'] = user[3]  # Giả sử role là cột thứ tư trong bảng users
            flash('Đăng nhập thành công!', 'success')  # Hiển thị thông báo đăng nhập thành công
            return redirect(url_for('index'))  # Chuyển hướng tới trang chủ
        else:
            flash('Thông tin đăng nhập không hợp lệ', 'danger')  # Hiển thị thông báo đăng nhập thất bại nếu thông tin không hợp lệ
    
    return render_template('login.html')  # Trả về template trang đăng nhập

# Xóa video
@app.route('/delete/<int:video_id>', methods=['POST'])
def delete_video(video_id):
    if 'user_id' not in session or session.get('role') != 'admin':  # Kiểm tra xem người dùng có trong session và có vai trò là admin không
        flash('Bạn không có quyền thực hiện hành động này', 'danger')  # Hiển thị thông báo không có quyền nếu không phải là admin
        return redirect(url_for('index'))  # Chuyển hướng tới trang chủ
    
    # Lấy thông tin video để xóa file
    cursor.execute("SELECT video_data, thumbnail FROM videos WHERE id=?", (video_id,))
    video = cursor.fetchone()  # Lấy bản ghi video từ truy vấn
    if video:
        # Xóa file video và thumbnail
        if os.path.exists(video[0]):
            os.remove(video[0])
        if os.path.exists(video[1]):
            os.remove(video[1])
        
        # Xóa bản ghi video khỏi cơ sở dữ liệu
        cursor.execute("DELETE FROM videos WHERE id=?", (video_id,))
        conn.commit()  # Xác nhận thay đổi trong cơ sở dữ liệu
        flash('Xóa video thành công', 'success')  # Hiển thị thông báo xóa video thành công
    else:
        flash('Không tìm thấy video', 'danger')  # Hiển thị thông báo không tìm thấy video nếu không có bản ghi
    
    return redirect(url_for('index'))  # Chuyển hướng tới trang chủ

# Đăng xuất người dùng
@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Xóa ID người dùng khỏi session
    session.pop('username', None)  # Xóa tên người dùng khỏi session
    session.pop('role', None)  # Xóa vai trò người dùng khỏi session
    return redirect(url_for('index'))  # Chuyển hướng tới trang chủ

# Trang tải lên video
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' not in session:  # Kiểm tra xem người dùng có trong session không
        return redirect(url_for('login'))  # Nếu không có trong session, chuyển hướng tới trang đăng nhập
    
    if request.method == 'POST':  # Kiểm tra xem phương thức yêu cầu có phải là POST không
        title = request.form['title']  # Lấy tiêu đề video từ form tải lên
        description = request.form['description']  # Lấy mô tả video từ form tải lên
        thumbnail = request.files['thumbnail']  # Lấy file thumbnail từ form tải lên
        video = request.files['video']  # Lấy file video từ form tải lên

        # Lưu thumbnail
        thumbnail_path = os.path.join('static/thumbnails/', thumbnail.filename)  # Tạo đường dẫn để lưu file thumbnail
        thumbnail.save(thumbnail_path)  # Lưu file thumbnail vào đường dẫn đã tạo

        # Nén video và lưu dưới dạng file gzip
        gz_file_path = os.path.join('video_files', f"{title}.gz")  # Tạo đường dẫn để lưu file nén video
        with gzip.open(gz_file_path, 'wb') as gz_file:
            gz_file.write(video.read())  # Nén và ghi dữ liệu video vào file gzip

        video_info = {
            'title': title,
            'description': description,
            'thumbnail': thumbnail_path,
            'video_data': gz_file_path
        }

        file_path = os.path.join('video_files', f"{title}.json")  # Tạo đường dẫn để lưu file JSON chứa thông tin video
        with open(file_path, 'w') as f:
            json.dump(video_info, f)  # Ghi thông tin video vào file JSON

        # Lưu thông tin file JSON vào cơ sở dữ liệu
        cursor.execute("INSERT INTO videos (title, description, thumbnail, video_data) VALUES (?, ?, ?, ?)",
                       (title, description, thumbnail_path, file_path))
        conn.commit()  # Xác nhận thay đổi trong cơ sở dữ liệu

        return redirect(url_for('index'))  # Chuyển hướng tới trang chủ

    return render_template('upload.html')  # Trả về template trang tải lên video

# Trang xem video
@app.route('/video/<int:video_id>')
def view_video(video_id):
    cursor.execute("SELECT title, description, video_data FROM videos WHERE id=?", (video_id,))
    video = cursor.fetchone()  # Lấy bản ghi video từ truy vấn
    if video:
        with open(video[2], 'r') as f:
            video_info = json.load(f)  # Đọc thông tin video từ file JSON
        
        gz_file_path = video_info['video_data']  # Đường dẫn file nén video

        # Giải nén video
        with gzip.open(gz_file_path, 'rb') as gz_file:
            video_data = gz_file.read()  # Đọc và giải nén dữ liệu video

        # Lưu tạm thời file video để gửi tới trình duyệt
        temp_video_path = os.path.join('video_files', f"temp_{video_id}.mp4")  # Tạo đường dẫn để lưu file video tạm thời
        with open(temp_video_path, 'wb') as temp_video_file:
            temp_video_file.write(video_data)  # Ghi dữ liệu video đã giải nén vào file tạm thời

        return render_template('view_video.html', title=video_info['title'], description=video_info['description'], video_path=url_for('stream_video', video_id=video_id))
    return "Không tìm thấy video", 404  # Trả về thông báo lỗi nếu không tìm thấy video

# Điểm cuối để stream video
@app.route('/stream/<int:video_id>')
def stream_video(video_id):
    temp_video_path = os.path.join('video_files', f"temp_{video_id}.mp4")  # Đường dẫn file video tạm thời
    return send_file(temp_video_path, as_attachment=False)  # Gửi file video tạm thời tới trình duyệt

# Quản lý người dùng
@app.route('/manage_users')
def manage_users():
    if 'user_id' not in session or session.get('role') != 'admin':  # Kiểm tra xem người dùng có trong session và có vai trò là admin không
        flash('Bạn không có quyền truy cập trang này', 'danger')  # Hiển thị thông báo không có quyền nếu không phải là admin
        return redirect(url_for('index'))  # Chuyển hướng tới trang chủ

    cursor.execute("SELECT id, username, role FROM users")  # Thực hiện truy vấn để lấy danh sách người dùng
    users = cursor.fetchall()  # Lấy tất cả các bản ghi từ truy vấn
    return render_template('manage_users.html', users=users)  # Trả về template trang quản lý người dùng với danh sách người dùng

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if 'user_id' not in session or session.get('role') != 'admin':  # Kiểm tra xem người dùng có trong session và có vai trò là admin không
        flash('Bạn không có quyền truy cập trang này', 'danger')  # Hiển thị thông báo không có quyền nếu không phải là admin
        return redirect(url_for('index'))  # Chuyển hướng tới trang chủ

    if request.method == 'POST':  # Kiểm tra xem phương thức yêu cầu có phải là POST không
        username = request.form['username']  # Lấy tên người dùng từ form chỉnh sửa
        password = request.form['password']  # Lấy mật khẩu từ form chỉnh sửa
        role = request.form['role']  # Lấy vai trò từ form chỉnh sửa

        if password:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()  # Băm mật khẩu nếu có thay đổi
            cursor.execute("UPDATE users SET username=?, password=?, role=? WHERE id=?", (username, hashed_password, role, user_id))
        else:
            cursor.execute("UPDATE users SET username=?, role=? WHERE id=?", (username, role, user_id))

        conn.commit()  # Xác nhận thay đổi trong cơ sở dữ liệu
        flash('Cập nhật người dùng thành công', 'success')  # Hiển thị thông báo cập nhật thành công
        return redirect(url_for('manage_users'))  # Chuyển hướng tới trang quản lý người dùng

    cursor.execute("SELECT id, username, role FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()  # Lấy bản ghi người dùng từ truy vấn
    return render_template('edit_user.html', user=user)  # Trả về template trang chỉnh sửa người dùng

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'user_id' not in session or session.get('role') != 'admin':  # Kiểm tra xem người dùng có trong session và có vai trò là admin không
        flash('Bạn không có quyền truy cập trang này', 'danger')  # Hiển thị thông báo không có quyền nếu không phải là admin
        return redirect(url_for('index'))  # Chuyển hướng tới trang chủ

    cursor.execute("DELETE FROM users WHERE id=?", (user_id,))  # Thực hiện truy vấn để xóa người dùng khỏi cơ sở dữ liệu
    conn.commit()  # Xác nhận thay đổi trong cơ sở dữ liệu
    flash('Xóa người dùng thành công', 'success')  # Hiển thị thông báo xóa người dùng thành công
    return redirect(url_for('manage_users'))  # Chuyển hướng tới trang quản lý người dùng

if __name__ == '__main__':
    app.run(debug=True)  # Khởi chạy ứng dụng Flask trong chế độ debug
