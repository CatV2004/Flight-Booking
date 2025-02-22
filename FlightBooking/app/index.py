from datetime import datetime, timedelta

from app.Customer.customer_dao import get_customer_email_by_order_id, get_order_details_by_order_id
from app.dao import load_comments, is_username_exists, auth_user, add_or_get_user_from_google, get_user_by_id, \
    validate_profile_data, update_user_profile, check_current_password, update_password, load_airline, load_flight, \
    load_flight_click_search, load_chair, load_airport, load_area, add_user, save_comment, huy_ve, load_discount, \
    them_khach_hang, load_id, them_nguoi_dung, load_customer, them_don_hang, them_thanh_toan, dem_so_luong_hanh_ly, \
    them_hanh_ly, them_ve, them_chi_tiet_ve, update_state_chari, load_id_plane, cac_tuyen_bay, them_chuyen_bay, \
    them_lich_bay, them_san_bay_tg, take_info_ve
from app import app, login, google, db, mail, Message, generate_email_content
from flask_login import login_user, login_required, logout_user, current_user
from app.models import TaiKhoan, VaiTro, SanBay, MayBay, KhachHang
from app.Customer.customer_index import customer_bp
from enum import Enum
from babel.numbers import format_number
from flask import render_template, request, redirect, jsonify, url_for, session, flash, json
import random
import re

# Đăng ký Blueprint cho module Customer
app.register_blueprint(customer_bp, url_prefix='/customer')


#ham tao ma tu dong
def tao_ma_tu_dong(ma):
    number = random.randint(0,9999)
    formatted_number = f"{number:05d}"
    return f"{ma}{formatted_number}"

@app.route("/", methods=["GET", "POST"])
def index():
    # Kiểm tra nếu session có dữ liệu chuyến bay, và nếu đúng là trang chủ thì xóa đi
    if 'outbound_flight' in session or 'return_flight' in session or 'passengers' in session:
        session.pop('outbound_flight', None)  # Xóa chuyến bay đi
        session.pop('return_flight', None)  # Xóa chuyến bay về
        session.pop('passengers', None)  # Xóa danh sách hành khách

        print("Toàn bộ dữ lệu đã được reset")
    comments = load_comments()
    return render_template('index.html', comments=comments)

@app.route("/api/comments", methods=['POST'])
def add_comment():
    data = request.get_json()

    if not data or 'content' not in data or not data['content'].strip():
        return jsonify({"error": "Nội dung bình luận không hợp lệ"}), 400

    try:
        # Lưu bình luận vào database
        new_comment = save_comment(content=data['content'].strip())

        # Lấy thông tin khách hàng (nếu có)
        khach_hang = KhachHang.query.get(new_comment.khach_hang) if new_comment.khach_hang else None
        # Trả về JSON để cập nhật giao diện
        return jsonify({
            "content": new_comment.noi_dung,
            "thoi_gian": new_comment.thoi_gian.isoformat(),
            "fname": khach_hang.fname if khach_hang else None,
            "lname": khach_hang.lname if khach_hang else None,
        }), 201

    except Exception as e:
        app.logger.error(f"Lỗi khi thêm bình luận: {e}")
        return jsonify({"error": "Đã xảy ra lỗi từ phía server"}), 500


@app.route("/register", methods=['get', 'post'])
def register_view():
    next_url = request.args.get('next')
    err_msg = ''
    if request.method.__eq__('POST'):
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm')

        if is_username_exists(username):
            err_msg = 'Tài khoản này đã được tạo. Vui lòng tạo tài khoản khác.'
        elif not password.__eq__(confirm):
            err_msg = 'Mật khẩu không khớp!'
        else:
            data = {
                'first_name': first_name,
                'last_name': last_name,
                'username': username,
                'password': password,
                'email': email
            }
            add_user(**data)

            return redirect('/login')

    return render_template('register.html', err_msg=err_msg, next=next_url)


@app.route('/admin_login', methods=['post'])
def admin_login():
    username = request.form.get('username')
    password = request.form.get('password')

    user = auth_user(username=username, password=password, role=VaiTro.ADMIN)
    if user:
        login_user(user=user)
        return redirect('/admin')

    return f"Login failed for user: {username}", 401

# @app.before_request
# def check_admin_access():
#     if request.endpoint and '/admin' in request.endpoint:
#         if not current_user.is_authenticated or current_user.tai_khoan.vai_tro != VaiTro.ADMIN:
#             flash("Bạn không có quyền truy cập vào trang quản trị.", "danger")
#             return redirect(url_for('index'))

@app.route("/login", methods=['get', 'post'])
def login_view():
    next_url = request.args.get('next')
    err_msg = ''
    if request.method.__eq__('POST'):
        username = request.form.get('username')
        password = request.form.get('password')

        # Sử dụng hàm auth_user để xác thực
        user = auth_user(username, password)
        if user:
            login_user(user=user)
            print(user.vai_tro)
            if user.vai_tro == VaiTro.USER:

                # return redirect('/')
                # Nếu có next_url thì chuyển hướng về đó, nếu không thì về trang chủ
                # Kiểm tra nếu next_url hợp lệ
                if not next_url:
                    next_url = url_for('index')
                return redirect(next_url)


            elif user.vai_tro == VaiTro.EMPLOYEE:
                return redirect('/page/sellticket')
            elif user.vai_tro == VaiTro.ADMIN:
                return redirect('/admin')
            else:
                # Mặc định nếu có vai trò khác chưa xử lý
                flash("Tài khoản không có quyền truy cập.", "danger")
                return redirect(url_for('index'))
        else:
            # Kiểm tra nếu tài khoản tồn tại
            if is_username_exists(username):
                err_msg = 'Mật khẩu không đúng. Vui lòng thử lại.'
            else:
                err_msg = 'Tài khoản không tồn tại.'

    return render_template('login.html', err_msg=err_msg)


# Gọi đăng nhập Google
@app.route('/login/google')
def login_google():
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route('/login/google/callback')
def google_callback():
    try:
        # Lấy token từ Google
        token = google.authorize_access_token()

        # Lấy thông tin người dùng từ Google

        user_info = google.get('userinfo').json()

        # Trích xuất thông tin cần thiết
        email = user_info.get('email')
        name = user_info.get('name', email)  # Nếu 'name' không có, dùng email làm mặc định

        # first_name hoặc last_name tách từ name
        name_parts = name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        # Thêm hoặc lấy người dùng từ cơ sở dữ liệu
        user = add_or_get_user_from_google(
            first_name=first_name,
            last_name=last_name,
            username=email,
            email=email
        )

        if user:
            login_user(user=user)  # Đăng nhập người dùng
            return redirect('/')  # Chuyển hướng về trang chủ
        else:
            raise Exception("Người dùng không hợp lệ hoặc không được tạo thành công.")
    except Exception as e:
        print(f"Lỗi khi xử lý đăng nhập Google: {e}")
        return redirect('/login')


@app.route('/logout')
def logout_process():
    logout_user()
    return redirect('/')

@login.user_loader
def load_user(user_id):
    return get_user_by_id(user_id)

# Gọi page profile
@app.route('/profile')
def profile():
    return render_template('profile.html')  # Chỉ định template `profile.html`


@app.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    # Lấy dữ liệu từ form
    form_data = {
        'lname': request.form.get('lname'),
        'fname': request.form.get('fname'),
        'ngay_sinh': request.form.get('ngay_sinh'),
        'dia_chi': request.form.get('dia_chi'),
        'so_CCCD': request.form.get('so_CCCD'),
        'so_dien_thoai': request.form.get('so_dien_thoai'),
        'email': request.form.get('email')
    }

    # Xác thực dữ liệu
    valid, error_message = validate_profile_data(form_data)
    if not valid:
        flash(error_message, 'danger')
        return redirect(url_for('profile'))

    try:
        # Chuyển ngày sinh về kiểu `datetime.date`
        ngay_sinh_date = datetime.strptime(form_data['ngay_sinh'], '%d/%m/%Y').date() if form_data[
            'ngay_sinh'] else None

        # Gọi DAO để cập nhật thông tin
        success = update_user_profile(
            user_id=current_user.id,
            fname=form_data['fname'],
            lname=form_data['lname'],
            ngay_sinh=ngay_sinh_date,
            dia_chi=form_data['dia_chi'],
            so_CCCD=form_data['so_CCCD'],
            so_dien_thoai=form_data['so_dien_thoai'],
            email=form_data['email']
        )

        if success:
            flash("Cập nhật thông tin thành công!", "success")
        else:
            flash("Cập nhật thất bại. Người dùng không tồn tại.", "danger")
    except Exception as e:
        flash(f"Có lỗi xảy ra: {e}", "danger")

    return redirect(url_for('profile'))


@app.route('/update-password', methods=['POST'])
@login_required
def update_password_route():
    # Lấy thông tin từ form
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    # Kiểm tra mật khẩu hiện tại
    if not check_current_password(current_user, current_password):
        flash("Mật khẩu hiện tại không đúng.", "danger")
        return redirect(url_for('profile'))  # Redirect về trang profile sau khi lỗi

    # Kiểm tra mật khẩu mới và xác nhận mật khẩu mới
    if new_password != confirm_password:
        flash("Mật khẩu mới và xác nhận mật khẩu không khớp.", "danger")
        return redirect(url_for('profile'))  # Redirect về trang profile nếu có lỗi

    # Kiểm tra độ dài mật khẩu mới (ví dụ tối thiểu 6 ký tự)
    if len(new_password) < 6:
        flash("Mật khẩu mới phải có ít nhất 6 ký tự.", "danger")
        return redirect(url_for('profile'))  # Redirect về trang profile nếu có lỗi

    # Cập nhật mật khẩu mới trong cơ sở dữ liệu
    try:
        update_password(current_user, new_password)
        flash("Cập nhật mật khẩu thành công!", "success")
    except Exception as e:
        flash(f"Có lỗi xảy ra: {e}", "danger")

    return redirect(url_for('profile'))  # Redirect về trang profile sau khi thành công


#Tạo API để lấy danh sách sân bay dưới dạng JSON
@app.route('/api/sanbay', methods=['GET'])
def api_san_bay():
    try:
        danh_sach_san_bay = SanBay.query.all()
        if not danh_sach_san_bay:
            print("No airports found in database.")
            return jsonify({"error": "No data found"}), 404

        data = [
            {
                "ma_san_bay": sb.ma_san_bay,
                "ten_san_bay": sb.ten_san_bay,
                "dia_diem": sb.dia_diem
            }
            for sb in danh_sach_san_bay
        ]
        return jsonify(data)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500


#Ham luu du lieu chuyen bay tam thoi
def save_data_flight_temp(flight, name):
    info_flight = session.get(name)
    cleaned_data = flight.replace("datetime.datetime", "datetime")
    flight_update = eval(cleaned_data)  # chuyen chuoi thanh tuple
    if not info_flight:
        info_flight= {}
    info_flight.update({
        "hang_bay": flight_update[0],
        "noi_di": flight_update[1],
        "noi_den": flight_update[2],
        "ngay_di": flight_update[3],
        "ngay_ve": flight_update[4],
        "gia_tien": flight_update[5],
        "so_luong_diem_dung": flight_update[6],
        "ma_chuyen_bay": flight_update[7]
    })
    return info_flight

@app.route('/page/chooseticket', methods=['get','post'])
def choose_ticket():
    app.config["CHOOSE_TICKET_RETURN"] = False
    airlines = load_airline()
    flights = load_flight(session['info']['noi_di'], session['info']['noi_den'], session['info']['ngay_di'], session['info']['so_luong_hanh_khach'][0], app.config["TICKET_CATEGORY"][session['info']['hang_ve']])
    if request.method == "POST":
        flight = request.form.get('flight')
        info_flight_one = save_data_flight_temp(flight, 'info_flight_one')
        session['info_flight_one'] = info_flight_one
        if session['info']['loai_ve'] == "Khứ Hồi":
            return redirect('/page/chooseticketreturn')
        return redirect('/page/booktickets')
    return render_template('Employees/choose_ticket.html', airlines=airlines, flights=flights)



@app.route('/api/searchflights', methods=['get','post'])
def searchflights():
    so_diem_dung = thoi_gian_bay = hang_bay = ''
    if request.method == 'POST':
        so_diem_dung = request.json.get('so_diem_dung')
        thoi_gian_bay = request.json.get('thoi_gian_bay')
        hang_bay = request.json.get('hang_bay')

    flight = session.get('flight')
    if not flight:
        flight = {}
    flight.update({
        "so_diem_dung": so_diem_dung,
        "thoi_gian_bay": thoi_gian_bay,
        "hang_bay": hang_bay
    })
    session["flight"] = flight

    temp_time_flight = 12 if thoi_gian_bay == "Chuyến Bay Sáng" else 6 # Bien de tinh thoi gian

    temp_number_stop = 4 if so_diem_dung == "Số điểm dừng" else app.config["NUMBER_STOP"][so_diem_dung]

    noi_di = session['info']['noi_di'] if app.config["CHOOSE_TICKET_RETURN"] == False else session['info']['noi_den']
    noi_den = session['info']['noi_den'] if app.config["CHOOSE_TICKET_RETURN"] == False else session['info']['noi_di']
    ngay_bay = session['info']['ngay_di'] if app.config["CHOOSE_TICKET_RETURN"] == False else session['info']['ngay_ve']

    flights1 = load_flight_click_search(noi_di, noi_den, ngay_bay,
                                            temp_number_stop, 35 if thoi_gian_bay == "Thời gian bay" else app.config["TIME_FLIGHT"][thoi_gian_bay],
                                            hang_bay, temp_time_flight,app.config["TICKET_CATEGORY"][session['info']['hang_ve']],
                                            session['info']['so_luong_hanh_khach'][0])
    flights = [dict(flight._mapping) for flight in flights1] # mapping là thuôcj tính của đôi tượng row của sqlalchema cho phép chuyển row thành dic
    list_time_flight = []
    list_date_flight = []
    for i in range(0, len(flights)):
        time ={
            "thoi_gian_di": flights[i]['thoi_gian_di'].strftime('%H:%M'),
            'thoi_gian_den': flights[i]['thoi_gian_den'].strftime('%H:%M')
        }
        date = {
            "thoi_gian_di": repr(flights[i]['thoi_gian_di']), # chuyen doi tuong thanh chuoi
            'thoi_gian_den': repr(flights[i]['thoi_gian_den'])
        }
        list_date_flight.append(date)
        list_time_flight.append(time)
    return jsonify({'flights_data': flights, 'list_time_flight': list_time_flight, 'list_date_flight':list_date_flight})

@app.route('/page/chooseticketreturn', methods=['get','post'])
def choose_ticket_return():
    app.config["CHOOSE_TICKET_RETURN"] = True
    airlines = load_airline()
    flights = load_flight(session['info']['noi_den'], session['info']['noi_di'], session['info']['ngay_ve'],
                              session['info']['so_luong_hanh_khach'][0],
                              app.config["TICKET_CATEGORY"][session['info']['hang_ve']])

    if request.method == "POST":
        flight = request.form.get('flight')
        info_flight_two = save_data_flight_temp(flight, 'info_flight_two')
        session['info_flight_two'] = info_flight_two
        return redirect('/page/booktickets')

    return render_template('Employees/choose_ticket_return.html', airlines=airlines, flights=flights)

#ham tao ma tu dong
def tao_ma_tu_dong(ma):
    number = random.randint(0,9999)
    formatted_number = f"{number:05d}"
    return f"{ma}{formatted_number}"

# Lay thong tin cac ve
@app.route('/page/booktickets', methods=['GET', 'POST'])
def book_tickets():
    time_now = datetime.today()
    chairs_first_turn = load_chair(session['info_flight_one']['ma_chuyen_bay'],
                                       app.config["TICKET_CATEGORY"][session['info']['hang_ve']])
    print(chairs_first_turn)
    charis_return = load_chair(session['info_flight_two']['ma_chuyen_bay'],
                                   app.config["TICKET_CATEGORY"][session['info']['hang_ve']]) if session['info']['loai_ve'] == 'Khứ Hồi' else []
    if request.method == "POST":
        if request.content_type == 'application/json':
            tickets = request.get_json()
            for i in range(0, len(tickets)):
                if i == 0 and load_user(tickets[str(i)]['cccd']) is None:
                    user = load_id()
                    them_khach_hang(tickets[str(i)]['fname'], tickets[str(i)]['lname'], tickets[str(i)]['email'],
                                        tickets[str(i)]['phone'], tickets[str(i)]['birthday'], tickets[str(i)]['cccd'])
                elif load_user(tickets[str(i)]['cccd']) is None:
                    them_nguoi_dung(tickets[str(i)]['fname'], tickets[str(i)]['lname'], tickets[str(i)]['email'],
                                        tickets[str(i)]['phone'], tickets[str(i)]['birthday'], tickets[str(i)]['cccd'])
            user = load_customer(tickets[str(0)]['cccd'])
            ma_DH = tao_ma_tu_dong("DH")

            print(ma_DH)
            madh = session.get('ma_DH')
            if not madh:
                madh = {}
            madh.update({
                "ma_DH": ma_DH
            })
            them_don_hang(user[0], current_user.id, int(session['info']['so_luong_hanh_khach'][0]),
                              tickets[str(0)]['id_discount'], tickets[str(0)]['tong'], ma_DH)
            them_thanh_toan(tickets[str(0)]['cccd'], tickets[str(0)]['pay-method'], tickets[str(0)]['tong_tien'], ma_DH)
            for i in range(0, len(tickets)):
                ma_ve = tao_ma_tu_dong("VE")
                so_luong_hanh_ly = dem_so_luong_hanh_ly()
                if tickets[str(i)]['baggage'] != '0':
                    ma_HL = tao_ma_tu_dong("HL")
                    them_hanh_ly(float(tickets[str(i)]['baggage']), ma_HL)
                them_ve(tickets[str(i)]['cccd'],ma_ve,"KHUHOI" if session['info']['loai_ve']=="Khứ Hồi" else "MOTCHIEU",
                            tickets[str(i)]['ticket_price'], ma_DH)
                them_chi_tiet_ve(session['info_flight_one']['ma_chuyen_bay'], ma_ve,tickets[str(i)]['seat_go'],
                                     session['info_flight_one']['gia_tien'], so_luong_hanh_ly,
                                     app.config["TICKET_CATEGORY"][session['info']['hang_ve']], tickets[str(i)]['baggage'], ma_HL)
                update_state_chari(tickets[str(i)]['seat_go'], chairs_first_turn[0].so_hieu_mb)
                if session['info']['loai_ve']=="Khứ Hồi":
                    them_chi_tiet_ve(session['info_flight_two']['ma_chuyen_bay'],ma_ve,tickets[str(i)]['seat_return'],
                                         session['info_flight_two']['gia_tien'], so_luong_hanh_ly,
                                         app.config["TICKET_CATEGORY"][session['info']['hang_ve']], tickets[str(i)]['baggage'], ma_HL)
                    update_state_chari(tickets[str(i)]['seat_return'], charis_return[0].so_hieu_mb)
            return jsonify({"redirect": "1" if tickets[str(0)]['pay-method'] == 'Tiền mặt' else "0"})
    return render_template('Employees/book_tickets.html',time_now=time_now.strftime('%Y-%m-%d'),
                           quantity = int(session['info']['so_luong_hanh_khach'][0]),
                           chairs_first_turn=chairs_first_turn, charis_return = charis_return, )



@app.route('/api/updateTotalPay', methods=['POST', 'GET'])
def updateTotalPay():
    ma_KM = request.json.get('ma_KM')
    ty_le_giam = load_discount(ma_KM)
    return jsonify({'ty_le_giam': ty_le_giam[0].ty_le_giam if len(ty_le_giam) != 0 else 0})


#LKay thong tin ve muon xoa
@app.route('/api/takeinfo', methods=['POST', 'GET'])
def take_info():
    if request.method == 'POST':  # Sử dụng chữ hoa
        info = request.get_json()
        ma_ve = info['ma_ve'].replace(" ","")
        info_ticket = take_info_ve(ma_ve)
        data = {
            "khong_thay": 0
        }
        if info_ticket is None:

            data["khong_thay"] = 1

            return jsonify({"data_none" : data})
        info_ticket_json = {
            key: (value.name if isinstance(value, Enum) else value)
            for key, value in info_ticket._mapping.items()
        }
        info_ticket_json['loai_ve'] = 'Khứ Hồi' if info_ticket_json['loai_ve'] == "KHUHOI" else 'Một Chiều'
        info_ticket_json['hang_ve'] = 'Phổ Thông' if info_ticket_json['hang_ve'] == "PHOTHONG" else 'Thương Gia'
        nd = info_ticket_json['thoi_gian_di'].strftime('%d/%m/%Y')
        ngay_di = {
            "thoi_gian_di": nd
        }
        print(info_ticket_json)
        return jsonify({"info_ticket_json": info_ticket_json, "ngay_di": ngay_di, "data_none" : data})
    return jsonify({"info": 1})


@app.route('/api/cancel', methods=['POST', 'GET'])
def cancel():
    data = {
        "du_lieu": 1
    }
    if request.method == 'POST':
        ma_ve = request.get_json()
        huy_ve(ma_ve['ma_ve'])


    return jsonify({"data":data})
#Hủy vé
@app.route('/page/cancelticket', methods=['get'])
def cancel_tickets():

    return render_template('Employees/cancel_tickets.html')


#Đổi vé
@app.route('/page/changeticket', methods=['get'])
def change_tickets():

    return render_template('Employees/change_ticket.html')

#Ham kiem tra gio phut giay co dung dinh dang hay khong
def check_time_format(s):
    pattern = r'^(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d$'
    return bool(re.match(pattern, s))

def kiem_tra_thoi_gian_dung(thoi_gian_dung, thoi_gian_tiep_tuc ):
    hieu = thoi_gian_tiep_tuc - thoi_gian_dung
    phut = hieu.total_seconds() / 60  # Chuyển đổi tổng số giây thành phút
    if phut > 30 or phut < 20:
        return False
    return True
# Lập lịch
@app.route('/page/schedule', methods=['get', 'post'])
def schedule_flight():
    time_now = datetime.now() + timedelta(days=1)
    airports = load_airport()
    planes = load_id_plane()
    flight_route = cac_tuyen_bay()
    print(datetime.now())
    err = ""
    if request.method.__eq__('POST'):
        tuyen_bay = request.form.get('tuyen-bay')
        ngay_di = request.form.get('ngay-di')
        ngay_den = request.form.get('ngay-den')
        thoi_gian_di = request.form.get('thoi-gian-di')
        thoi_gian_den = request.form.get('thoi-gian-den')
        san_bay_tg_1 = request.form.get('san-bay-tg-1')
        ngay_dung_1 = request.form.get('ngay-dung-1')
        thoi_gian_dung_1 = request.form.get("thoi-gian-dung-1")
        thoi_gian_tt_1 = request.form.get("thoi-gian-tt-1")
        ghi_chu_1 = request.form.get('ghi-chu-1')
        san_bay_tg_2 = request.form.get('san-bay-tg-2')
        ngay_dung_2 = request.form.get('ngay-dung-2')
        thoi_gian_dung_2 = request.form.get("thoi-gian-dung-2")
        thoi_gian_tt_2 = request.form.get("thoi-gian-tt-2")
        ghi_chu_2 = request.form.get('ghi-chu-2')
        ma_may_bay = request.form.get('ma-may-bay')
        so_tien_hang_trieu = request.form.get('so-tien-hang-trieu')
        so_tien_hang_tram = request.form.get('so-tien-hang-tram')
        so_tien_hang_chuc = request.form.get('so-tien-hang-chuc')

        #Kiem tra du lieu co trong hay khoong dung dinh dang hay khong
        if (thoi_gian_di == '' or thoi_gian_den == '' or ngay_di == '' or ngay_den == '' or
                check_time_format(thoi_gian_di) is False or check_time_format(thoi_gian_den) is False or
                (ngay_dung_1 != "" and (thoi_gian_dung_1 == "" or thoi_gian_tt_1 ==""
                                        or check_time_format(thoi_gian_dung_1) is False or check_time_format(thoi_gian_tt_1) is False)) or
                (ngay_dung_2 != "" and (thoi_gian_dung_2 == "" or thoi_gian_tt_2 ==""
                                        or check_time_format(thoi_gian_dung_2) is False or check_time_format(thoi_gian_tt_2) is False)) or
                (so_tien_hang_trieu == '0' and so_tien_hang_tram == '0' and so_tien_hang_chuc=='0')):
            print("hello1")
            err = "Dữ liệu không hợp lệ."
            return render_template('Employees/schedule.html', airports=airports, time_now=time_now.strftime('%Y-%m-%d'),
                                   planes=planes, flight_route=flight_route, err=err)
        else:
            thoi_gian_bay_di = datetime.strptime(f"{ngay_di} {thoi_gian_di}", "%Y-%m-%d %H:%M:%S")
            thoi_gian_bay_den = datetime.strptime(f"{ngay_den} {thoi_gian_den}", "%Y-%m-%d %H:%M:%S")

        if thoi_gian_bay_den < thoi_gian_bay_di:
            return render_template('Employees/schedule.html', airports=airports,
                                   time_now=time_now.strftime('%Y-%m-%d'),
                                   planes=planes, flight_route=flight_route, err=err)

        #Kiem tra neu co ssan bay trung gian 1 thi thoi gian nghi khi tru di 30p co be hon thoi gian bat dau bay hay khong
        if ngay_dung_1 != "" and thoi_gian_dung_1!="" and thoi_gian_tt_1!="":
            thoi_gian_dung_chan1 = datetime.strptime(f"{ngay_dung_1} {thoi_gian_dung_1}", "%Y-%m-%d %H:%M:%S")
            thoi_gian_tiep_tuc1 = datetime.strptime(f"{ngay_dung_1} {thoi_gian_tt_1}", "%Y-%m-%d %H:%M:%S")
            if (thoi_gian_dung_chan1 - timedelta(minutes=30) <= thoi_gian_bay_di or
                    thoi_gian_tiep_tuc1 + timedelta(minutes=30) > thoi_gian_bay_den or
                    kiem_tra_thoi_gian_dung(thoi_gian_dung_chan1, thoi_gian_tiep_tuc1) is False):
                err = "Dữ liệu không hợp lệ."
                print("hello2")
                return render_template('Employees/schedule.html', airports=airports,
                                       time_now=time_now.strftime('%Y-%m-%d'),
                                       planes=planes, flight_route=flight_route, err=err)

        #Kiem tra neu co ssan bay trung gian 2 thi thoi gian nghi khi tru di 30p co be hon thoi gian bat dau bay hay khong
        if ngay_dung_2 != "" and thoi_gian_dung_2!="" and thoi_gian_tt_2!="":
            thoi_gian_dung_chan2 = datetime.strptime(f"{ngay_dung_2} {thoi_gian_dung_2}", "%Y-%m-%d %H:%M:%S")
            thoi_gian_tiep_tuc2 = datetime.strptime(f"{ngay_dung_2} {thoi_gian_tt_2}", "%Y-%m-%d %H:%M:%S")
            if (thoi_gian_dung_chan2 - timedelta(minutes=30) <= thoi_gian_bay_di or
                    thoi_gian_tiep_tuc2 + timedelta(minutes=30) > thoi_gian_bay_den or
                    thoi_gian_dung_chan2 < thoi_gian_dung_chan1 or
                    san_bay_tg_1 == san_bay_tg_2 or
                    kiem_tra_thoi_gian_dung(thoi_gian_dung_chan2, thoi_gian_tiep_tuc2) is False):
                err = "Dữ liệu không hợp lệ."
                print("hello3")
                return render_template('Employees/schedule.html', airports=airports,
                                       time_now=time_now.strftime('%Y-%m-%d'),
                                       planes=planes, flight_route=flight_route, err=err)

        number = random.randint(0, 99999)
        # Tao ma lich
        sml = "ML"
        formatted_number = f"{number:05d}"
        ma_lich = f"{sml}{formatted_number}"
        # Tao ma chuyen bay
        scb = 'CB'
        ma_chuyen_bay = f"{scb}{formatted_number}"
        gia_chuyen_bay = int(so_tien_hang_trieu) * 1000000 + int(so_tien_hang_tram) * 100000 + int(so_tien_hang_chuc) * 10000
        # Them lich bay va chuyen bay
        them_lich_bay(ma_lich)
        them_chuyen_bay(ma_may_bay, tuyen_bay[0:6], thoi_gian_bay_di, thoi_gian_bay_den, ma_lich, ma_chuyen_bay,
                            gia_chuyen_bay)

        #Thêm sân bay trung gian thứ nhất
        if ngay_dung_1 != "" and thoi_gian_dung_1 != "" and thoi_gian_tt_1 != "":
            print("hi1")
            them_san_bay_tg(san_bay_tg_1, tuyen_bay[0:6], ma_chuyen_bay, thoi_gian_dung_chan1, thoi_gian_tiep_tuc1,1,
                                ghi_chu_1)

        #Thêm sân bay trung gian thứ 2
        if ngay_dung_2 != "" and thoi_gian_dung_2 != "" and thoi_gian_tt_2 != "":
            print("hi1")
            them_san_bay_tg(san_bay_tg_2, tuyen_bay[0:6], ma_chuyen_bay, thoi_gian_dung_chan2, thoi_gian_tiep_tuc2,2,
                                ghi_chu_2)
        return redirect(url_for('schedule_flight')) # Chuyen huong lai chính hàm

    return render_template('Employees/schedule.html', airports=airports, time_now=time_now.strftime('%Y-%m-%d'), planes=planes, flight_route=flight_route, err=err)


#Xuất vé
@app.route('/page/printticket', methods=['get'])
def print_ticket():

    return render_template('Employees/print_ticket.html')


#Bán vé
@app.route('/page/sellticket', methods=['get', 'post'])
def sell_ticket():
    time_now = datetime.today()
    airports = load_airport()
    areas = load_area()
    err_msg = ''
    if request.method == 'POST':
        fromInput = request.form.get('fromInput')
        toInput = request.form.get('toInput')
        if fromInput != toInput and fromInput != '' and toInput != '':
            return redirect('/page/chooseticket')
        else:
            err_msg = 'Dữ liệu không đúng'
    return render_template('Employees/sell_ticket.html', time_now=time_now.strftime('%Y-%m-%d'), airports=airports, areas=areas, err_msg=err_msg)


#Lấy dữ liệu trang sell_ticket lưu tạm thời
@app.route('/api/sellticket', methods=['post'])
def sell_ticket_session():
    info = session.get('info')
    if not info:
        info = {}

    loai_ve = request.json.get('loai_ve')
    so_luong_hanh_khach = request.json.get('so_luong_hanh_khach')
    hang_ve = request.json.get('hang_ve')
    noi_di = request.json.get('noi_di')
    noi_den = request.json.get('noi_den')
    ngay_di = request.json.get('ngay_di')
    ngay_ve = request.json.get('ngay_ve')

    info.update({
        "loai_ve": loai_ve,
        "so_luong_hanh_khach": so_luong_hanh_khach,
        "hang_ve": hang_ve,
        "noi_di": noi_di,
        "noi_den": noi_den,
        "ngay_di": ngay_di,
        "ngay_ve": ngay_ve
    })
    session['info'] = info
    return jsonify(info)


#Thanh Toán
@app.route('/page/paytickets', methods=['get', 'post'])
def pay_ticket():

    return render_template('Employees/pay_tickets.html')

#Ham gửi mail tự động
@app.route('/api/mailauto', methods=["GET","POST"])
def sent_mail_auto():
    print("hello")
    result = {
        "Thanh cong": 1
    }
    if request.method == "POST":
        user_mail = request.json.get('email')
        message_mail = f"Anh nhắc em có đã đặt một chuyến bay từ {session['info']['noi_di']} đến {session['info']['noi_den']} vao ngày {session['info']['ngay_di']}"
        if session['info']['loai_ve'] == 'Khứ Hồi':
            message_mail += f" va chuyến khứ hồi từ {session['info']['noi_den']} đến {session['info']['noi_di']} vao ngày {session['info']['ngay_ve']}"
        print(user_mail)
        msg = Message(
            'Thông tin vé máy bay của bạn',
            sender='thanhdan27102004sayhi@gmail.com',
            recipients=[user_mail]
        )
        msg.body = message_mail
        try:
            mail.send(msg)
            print("Email đã được gửi thành công!")
        except Exception as e:
            print(f"Lỗi khi gửi email: {str(e)}")
    return jsonify({"Data":result})


#Ham gửi mail tự động
@app.route('/api/send_email', methods=["GET", "POST"])
def send_mail():
    result = {
        "Thanh cong": 1
    }
    if request.method == "POST":
        order_id = session.get("orderId")

        user_mail = get_customer_email_by_order_id(order_id)
        print('email nef: ',user_mail)
        order_info = get_order_details_by_order_id(order_id)

        try:
            html_contents = generate_email_content(order_info)
        except Exception as e:
            return jsonify({"error": "Không thể render nội dung email", "details": str(e)}), 500

        # Cấu hình email
        msg = Message(
            subject=f"Thông tin đơn hàng #{order_id}",
            sender=app.config["MAIL_USERNAME"],
            recipients=[user_mail]
        )
        msg.html = html_contents  # Gắn nội dung HTML vào email

        # Gửi email
        try:
            mail.send(msg)
            print("Email đã được gửi thành công!")
            return jsonify({"success": True, "message": "Email đã được gửi thành công"})
        except Exception as e:
            print(f"Lỗi khi gửi email: {str(e)}")
            return jsonify({"success": False, "message": "Lỗi khi gửi email", "details": str(e)}), 500
    return jsonify({"Data": result})

if __name__ == '__main__':
    with app.app_context():
        from app import admin
        app.run(debug=True)



