import hashlib
import hmac
import urllib
import uuid
from datetime import datetime, date, time
from flask_mail import Message

from flask_login import current_user, login_required

from .info_passenger import PassengerInfo, Luggage

from flask import Flask, request, jsonify, Blueprint, session, Blueprint, render_template, flash, redirect
from .customer_dao import find_flights, get_full_flight_info_v2, find_airport_name, find_airport_location, \
    convert_to_datetime, find_route_by_airport_codes, get_airlines_by_flights, format_vietnamese_date, create_passenger, \
    get_payment_url, update_trang_thai_don_hang, get_order_status, get_order_details_by_order_id, \
    get_customer_email_by_order_id, luu_thanh_toan
from .customer__init__ import cost_map
from app import app, VNP_HASH_SECRET, VNP_TMN_CODE, VNP_RETURN_URL, VNP_URL, VNP_RETURN_URL, mail, generate_email_content
from app.dao_data import add_nguoi_dung, add_don_hang, add_ve, add_hanh_ly, add_chi_tiet_ve, get_discount_rate, \
    lay_ghes_trong, update_hanh_ly, get_tong_gia_tri_don_hang

from app.models import KhuyenMai, KhachHang, HangThanhVien, Ve, LoaiVe, TrangThaiDonHang, HangVe, ThanhToan

# Định nghĩa Blueprint
customer_bp = Blueprint('customer', __name__, template_folder='../templates')



# Định nghĩa filter format_currency
@app.template_filter('format_currency')
def format_currency(value):
    if isinstance(value, (int, float)):
        return f"{value:,.0f}".replace(",", ".") + " VND"
    return value

@app.route('/customer/submit-airport-codes', methods=['POST'])
def submit_airport_codes():
    # Sử dụng từ khóa global để sửa biến toàn cục
    # global from_code, to_code, departure_date_str, return_date, seat_class, ticket_quantity

    # Lấy dữ liệu từ request
    data = request.get_json()

    # Trích xuất mã sân bay và các thông tin cần thiết
    session['from_code'] = data.get('from')
    session['to_code'] = data.get('to')
    session['departure_date_str'] = data.get('departure_date')
    session['round_trip'] = data.get('round_trip')
    session['return_date_str'] = data.get('return_date')
    session['seat_class'] = data.get('seat_class')
    session['ticket_quantity'] = data.get('ticket_quantity')
    session['round_trip'] = data.get('round_trip')

    # Trả về phản hồi cho client
    return jsonify({'success': True, 'message': 'Dữ liệu đã được xử lý thành công'})


@customer_bp.route('/flights_normal', methods=['GET', 'POST'])
def flights_normal():
    session.pop('outbound_flight', None)
    session.pop('return_flight', None)

    # Lấy dữ liệu từ session
    from_code = session.get('from_code')
    to_code = session.get('to_code')
    departure_date_str = session.get('departure_date_str')
    seat_class = session.get('seat_class')
    ticket_quantity = session.get('ticket_quantity')
    round_trip = session.get('round_trip')

    # Lấy danh sách hãng hàng không được chọn từ query parameters
    selected_airlines = request.args.getlist('selected_airlines')

    # Chuyển đổi departure_date_str thành datetime nếu cần
    departure_date = convert_to_datetime(departure_date_str)
    departure_date_format = format_vietnamese_date(departure_date)

    # Tìm mã tuyến bay đi
    route_code = find_route_by_airport_codes(from_code, to_code)

    # Tìm thông tin sân bay
    start = find_airport_location(from_code)
    destination = find_airport_location(to_code)
    departure_airport_location = find_airport_name(from_code)
    arrival_airport_location = find_airport_name(to_code)

    # Tìm tất cả chuyến bay không bị lọc
    list_flights = find_flights(departure_date_str, route_code, seat_class, ticket_quantity)
    flight_info_list = get_full_flight_info_v2(list_flights, seat_class)

    # Nếu không có tham số lọc 'selected_airlines' thì hiển thị tất cả chuyến bay
    if selected_airlines:
        flight_info_list = [flight for flight in flight_info_list if flight['airline_code'] in selected_airlines]

    # Tìm danh sách hãng hàng không
    airlines = get_airlines_by_flights(list_flights, seat_class)

    return render_template('flights_normal.html',
                           from_code=from_code,
                           to_code=to_code,
                           start=start,
                           destination=destination,
                           departure_date=departure_date_format,
                           seat_class=seat_class,
                           ticket_quantity=ticket_quantity,
                           flights=flight_info_list,
                           airlines=airlines,
                           departure_airport_location=departure_airport_location,
                           arrival_airport_location=arrival_airport_location,
                           selected_airlines=selected_airlines,
                           round_trip=round_trip
                           )


@customer_bp.route('/flights_roundtrip', methods=['GET', 'POST'])
def flights_roundtrip():


    # Lấy thông tin chuyến bay từ session
    outbound_flight = session.get('outbound_flight', None)  # Chuyến bay lượt đi
    return_flight = session.get('return_flight', None)  # Chuyến bay khứ hồi (nếu đã chọn)

    print('outbound_flight: ',outbound_flight)
    print('return_flight: ', return_flight)

    # Lấy dữ liệu từ session
    return_date_str = session.get('return_date_str')  # Ngày khứ hồi
    from_code = session.get('from_code')
    to_code = session.get('to_code')
    departure_date_str = session.get('departure_date_str')
    seat_class = session.get('seat_class')
    ticket_quantity = session.get('ticket_quantity')
    round_trip = session.get('round_trip')


    # Chuyển đổi departure_date_str, return_date_str thành datetime nếu cần
    departure_date = convert_to_datetime(departure_date_str)
    departure_date_format = format_vietnamese_date(departure_date)
    return_date = convert_to_datetime(return_date_str)
    return_date_format = format_vietnamese_date(return_date)

    # Tìm mã tuyến bay đi
    route_code = find_route_by_airport_codes(from_code, to_code)
    # Tìm mã tuyến bay về
    route_code_return = find_route_by_airport_codes(to_code, from_code)

    # Tìm thông tin sân bay
    start = find_airport_location(from_code)
    destination = find_airport_location(to_code)
    departure_airport_location = find_airport_name(from_code)
    arrival_airport_location = find_airport_name(to_code)

    # Tìm tất cả chuyến bay ĐI không bị lọc
    list_flights = find_flights(departure_date_str, route_code, seat_class, ticket_quantity)
    flight_info_list = get_full_flight_info_v2(list_flights, seat_class)
    # Tìm tất cả chuyến bay VỀ không bị lọc
    list_flights_return = find_flights(return_date_str, route_code_return, seat_class, ticket_quantity)
    flight_info_list_return = get_full_flight_info_v2(list_flights_return, seat_class)



    # Lấy danh sách hãng hàng không được chọn từ query parameters
    selected_airlines = request.args.getlist('selected_airlines')
    # Nếu không có tham số lọc 'selected_airlines' thì hiển thị tất cả chuyến bay
    # if selected_airlines:
    #     flight_info_list = [flight for flight in flight_info_list if flight['airline_code'] in selected_airlines]
    #     flight_info_list_return = [flight for flight in flight_info_list if flight['airline_code'] in selected_airlines]
    if selected_airlines:
        if 'flight_info_list' in locals() and flight_info_list:
            # Nếu flight_info_list có trong phạm vi hiện tại và không rỗng
            flight_info_list = [flight for flight in flight_info_list if flight['airline_code'] in selected_airlines]

        if 'flight_info_list_return' in locals() and flight_info_list_return:
            # Nếu flight_info_list_return có trong phạm vi hiện tại và không rỗng
            flight_info_list_return = [flight for flight in flight_info_list_return if
                                       flight['airline_code'] in selected_airlines]

    # Tìm danh sách hãng hàng không
    airlines = get_airlines_by_flights(list_flights, seat_class)
    airlines_return = get_airlines_by_flights(list_flights_return, seat_class)
    return render_template('flights_normal.html',
                               from_code=from_code,
                               to_code=to_code,
                               start=start,
                               destination=destination,
                               departure_date=departure_date_format,
                               seat_class=seat_class,
                               ticket_quantity=ticket_quantity,

                               flights=flight_info_list,
                               flights_return=flight_info_list_return,

                               airlines=airlines,
                               airlines_return=airlines_return,

                               departure_airport_location=departure_airport_location,
                               arrival_airport_location=arrival_airport_location,
                               selected_airlines=selected_airlines,
                               round_trip=round_trip,
                               return_date_str = return_date_format,

                               outbound_flight=outbound_flight,
                               return_flight=return_flight
                                )

@customer_bp.route('/info_flight', methods=['POST'])
def info_flight():
    flight_data = request.get_json()  # Lấy dữ liệu chuyến bay từ client
    if flight_data is None:
        print("Không nhận được dữ liệu JSON!")
        return jsonify({"error": "Invalid JSON"}), 400  # Trả về lỗi nếu không nhận được JSON


    # Lưu thông tin chuyến bay đi vào session
    if 'outbound_flight' not in session:
        session['outbound_flight'] = flight_data
        session.pop('return_flight', None)
        return jsonify({"success": True, "next_step": "return_flight"})
    else:
        session['return_flight'] = flight_data  # Lưu chuyến bay khứ hồi nếu có
        print(f"Chuyến bay đi: {session.get('outbound_flight')}")
        print(f"Chuyến bay khứ hồi: {session.get('return_flight')}")
        return jsonify({"success": True, "next_step": "info_customer"})


@customer_bp.route('/info_customer', methods=['GET', 'POST'])
def info_customer():
    current_year = datetime.now().year  # Lấy năm hiện tại
    if request.method == 'POST':
        # Lấy dữ liệu từ form
        passengers = []
        ticket_quantity = int(session.get('ticket_quantity', 0))
        has_return_flight = session.get('return_flight') is not None  # Kiểm tra có chuyến khứ hồi hay không

        for i in range(ticket_quantity):
            passenger_id = i + 1


            # Nếu có chuyến khứ hồi, tạo PassengerInfo cho chuyến về
            if has_return_flight:
                return_passenger = create_passenger(passenger_id, request.form, cost_map, is_return=True)
                passengers.append(return_passenger)
            else:
                # Tạo PassengerInfo cho chuyến đi
                trip_passenger = create_passenger(passenger_id, request.form, cost_map, is_return=False)
                passengers.append(trip_passenger)

        # Lưu vào session hoặc cơ sở dữ liệu
        session['passengers'] = [p.get_info() for p in passengers]

        flash("Thông tin hành khách và hành lý đã được lưu thành công!", "success")

    # Xử lý GET
    flight_data = session.get('outbound_flight', None)
    flight_data_return = session.get('return_flight', None)
    ticket_quantity = session.get('ticket_quantity')
    seat_class = session.get('seat_class')

    return_date_str = session.get('return_date_str')
    departure_date_str = session.get('departure_date_str')
    departure_date = convert_to_datetime(departure_date_str).strftime('%d/%m/%Y')

    if return_date_str:
        return_date = convert_to_datetime(return_date_str).strftime('%d/%m/%Y')
    else:
        return_date = None

    # Kiểm tra xem có dữ liệu hành khách trong session không
    passengers = session.get('passengers', [])
    if not passengers:
        # Nếu không có hành khách trong session, tạo lại đối tượng PassengerInfo
        passengers = [PassengerInfo(passenger_id=i + 1) for i in range(int(ticket_quantity))]
        session['passengers'] = [p.get_info() for p in passengers]  # Lưu thông tin hành khách vào session

    print("Thông tin hành khách từ session info_passenger:")
    for passenger in passengers:
        print(passenger)

    return render_template('info_customer.html',
                           flight_data=flight_data,
                           flight_data_return=flight_data_return,
                           ticket_quantity=ticket_quantity,
                           seat_class=seat_class,
                           departure_date=departure_date,
                           return_date=return_date,
                           passengers=passengers,
                           current_year=current_year)


@customer_bp.route('/payment', methods=['GET', 'POST'])
@login_required
def payment():
    # Xử lý GET
    flight_data = session.get('outbound_flight', None)
    flight_data_return = session.get('return_flight', None)
    ticket_quantity = session.get('ticket_quantity')
    round_trip = session.get('round_trip')
    seat_class = session.get('seat_class')

    return_date_str = session.get('return_date_str')
    departure_date_str = session.get('departure_date_str')
    departure_date = convert_to_datetime(departure_date_str).strftime('%d/%m/%Y')

    if return_date_str:
        return_date = convert_to_datetime(return_date_str).strftime('%d/%m/%Y')
    else:
        return_date = None

    # Kiểm tra xem có dữ liệu hành khách trong session không
    passengers = session.get('passengers', [])
    if not passengers:
        # Nếu không có hành khách trong session, tạo lại đối tượng PassengerInfo
        passengers = [PassengerInfo(passenger_id=i + 1) for i in range(int(ticket_quantity))]
        session['passengers'] = [p.get_info() for p in passengers]  # Lưu thông tin hành khách vào session



    for p in passengers:
        print(p)
    return render_template('pay.html',
                           flight_data=flight_data,
                           flight_data_return=flight_data_return,
                           ticket_quantity=ticket_quantity,
                           seat_class=seat_class,
                           departure_date=departure_date,
                           return_date=return_date,
                           passengers=passengers,
                           )


@app.route('/search-discount', methods=['POST'])
def search_discount():
    data = request.get_json()
    discount_code = data.get('code', '').strip()

    # Lấy ngày hiện tại
    today = date.today()

    # Lọc các mã giảm giá còn hạn
    discounts = KhuyenMai.query.filter(
        KhuyenMai.ma_KM.like(f'%{discount_code}%'),
        KhuyenMai.ngay_bat_dau <= today,
        KhuyenMai.ngay_ket_thuc >= today
    ).all()

    if discounts:
        result = []
        for discount in discounts:
            result.append({
                'discount_code': discount.ma_KM,
                'discount_percentage': discount.ty_le_giam,
                'start_date': discount.ngay_bat_dau.strftime('%d/%m/%Y'),
                'end_date': discount.ngay_ket_thuc.strftime('%d/%m/%Y'),
                'description': discount.mo_ta or 'Không có mô tả'
            })
        return jsonify({'status': 'success', 'discounts': result})
    else:
        return jsonify({'status': 'error', 'message': 'Không tìm thấy mã giảm giá còn hạn!'})


@app.route('/apply-discount', methods=['POST'])
def apply_discount():
    data = request.json
    discount_code = data.get('code', 'none')  # Nếu không có mã, mặc định là 'none'

    # Nếu mã giảm giá là 'none', xóa mã giảm giá trong session và không áp dụng
    if discount_code == 'none':
        session.pop('applied_discount', None)  # Xóa mã giảm giá nếu có
        return jsonify({"status": "success", "message": "Không áp dụng mã giảm giá."})

    if not current_user.is_authenticated:
        return jsonify({"status": "error", "message": "Vui lòng đăng nhập."}), 401

    khuyen_mai = KhuyenMai.query.filter_by(ma_KM=discount_code).first()
    if not khuyen_mai:
        return jsonify({"status": "error", "message": "Mã khuyến mãi không tồn tại."}), 404

    # Kiểm tra hạng thành viên
    khach_hang = KhachHang.query.filter_by(id=current_user.id).first()
    if not khach_hang or khach_hang.hang_thanh_vien.value < HangThanhVien.BAC.value:
        return jsonify({"status": "error", "message": "Bạn không đủ điều kiện sử dụng mã khuyến mãi này."}), 403

    # Lưu vào session nếu mã giảm giá hợp lệ
    session.pop('applied_discount', None)  # Xóa mã giảm giá cũ (nếu có)
    session['applied_discount'] = discount_code

    return jsonify({"status": "success", "message": f"Mã khuyến mãi '{discount_code}' đã được áp dụng."})


@app.route('/place_order', methods=['POST'])
def place_order():
    try:
        # Kiểm tra dữ liệu đầu vào từ session
        flight_data = session.get('outbound_flight')
        flight_data_return = session.get('return_flight')
        passengers = session.get('passengers', [])
        count_ticket = len(passengers)
        discount_code = session.get('applied_discount')
        seat_class = session.get('seat_class')
        seat_class_name = HangVe.from_value(int(seat_class))

        if not flight_data or not passengers:
            return jsonify({'success': False, 'message': 'Thông tin không đầy đủ'}), 400

        # Loại vé
        round = LoaiVe.MOTCHIEU if flight_data_return is None else LoaiVe.KHUHOI
        discount_rate = get_discount_rate(discount_code)

        # Tính tổng giá trị đơn hàng
        SUM_total_order_value = 0
        for passenger in passengers:
            total_price = flight_data['price'] + (flight_data_return['price'] if flight_data_return else 0)
            total_price *= (1 - discount_rate) if discount_rate else 1
            total_luggage_cost = passenger['luggage']['cost'] + (
                passenger['luggage_return']['cost'] if flight_data_return else 0)
            total_order_value = total_price + total_luggage_cost
            SUM_total_order_value += total_order_value

        print(SUM_total_order_value)
        print(discount_rate)

        # Thêm đơn hàng
        don_hang = add_don_hang(
            ma_don_hang=None,
            khach_hang=current_user.id,
            ma_khuyen_mai=discount_code,
            nhan_vien=None,
            so_luong_ve=count_ticket,
            tong_tien=SUM_total_order_value,
            ngay_dat=datetime.now(),
            trang_thai=TrangThaiDonHang.PENDING
        )
        if not don_hang:
            return jsonify({'success': False, 'message': 'Thêm đơn hàng thất bại'}), 500
            # Danh sách các lỗi nếu có
        errors = []

        session.pop('orderId', None)
        session.pop('amount', None)

        session['orderId'] = don_hang.ma_DH  # Lưu mã đơn hàng
        session['amount'] = don_hang.tong_gia_tri_DH  # Lưu tổng tiền


        # Thêm từng hành khách và các thông tin liên quan
        for passenger in passengers:
            user = add_nguoi_dung(
                ho=passenger['last_name'],
                ten=passenger['first_name'],
                dia_chi=None,
                email=passenger['email'],
                so_dien_thoai=passenger['phone'],
                ngay_sinh=datetime(
                    int(passenger['birth_date']['year']),
                    int(passenger['birth_date']['month']),
                    int(passenger['birth_date']['day'])
                ),
                so_cccd=passenger['id_number'],
                loai_nguoi_dung="CUSTOMER"
            )

            if not user:
                print(f"Failed to add user {passenger['first_name']} {passenger['last_name']}")
                errors.append(f"Thêm người dùng {passenger['first_name']} {passenger['last_name']} thất bại.")
                continue

            total_price = flight_data['price'] + (flight_data_return['price'] if flight_data_return else 0)
            ve = add_ve(
                ma_ve=None,
                ma_don_hang=don_hang.ma_DH,
                nguoi_so_huu=user.id,
                gia_ves=total_price,
                loai_ve=round
            )

            if not ve:
                errors.append(f"Thêm vé cho hành khách {user.id} thất bại.")
                continue

            # Lưu chi tiết vé và ghế
            ghe_trong = lay_ghes_trong(flight_data['ma_chuyen_bay'], seat_class_name)
            add_chi_tiet_ve(
                ma_chuyen_bay=flight_data['ma_chuyen_bay'],
                ma_ve=ve.ma_ve,
                ma_ghe=ghe_trong,
                gia_ve=flight_data['price'],
            )

            # Nếu có hành lý, thêm hành lý vào chi tiết vé đã lưu
            if passenger['luggage']['weight'] > 0:
                hanh_ly_di = add_hanh_ly(
                    ma_HL=None,
                    loai_HL="Ký gửi",
                    trong_luong=passenger['luggage']['weight'],
                    chi_phi=passenger['luggage']['cost']
                )
                if not hanh_ly_di:
                    errors.append(f"Thêm hành lý chuyến đi cho hành khách {user.ho} thất bại.")
                else:
                    update_hanh_ly(flight_data['ma_chuyen_bay'], ve.ma_ve, hanh_ly_di.ma_HL)

            if flight_data_return:
                ghe_trong = lay_ghes_trong(flight_data_return['ma_chuyen_bay'], seat_class_name)
                add_chi_tiet_ve(
                    ma_chuyen_bay=flight_data_return['ma_chuyen_bay'],
                    ma_ve=ve.ma_ve,
                    ma_ghe=ghe_trong,
                    gia_ve=flight_data_return['price'],
                )

                if passenger['luggage_return']['weight'] > 0:
                    hanh_ly_ve = add_hanh_ly(
                        ma_HL=None,
                        loai_HL="Ký gửi",
                        trong_luong=passenger['luggage_return']['weight'],
                        chi_phi=passenger['luggage_return']['cost']
                    )
                    if not hanh_ly_ve:
                        errors.append(f"Thêm hành lý chuyến đi cho hành khách {user.ho} thất bại.")
                    else:
                        update_hanh_ly(flight_data['ma_chuyen_bay'], ve.ma_ve, hanh_ly_di.ma_HL)

        # Kiểm tra nếu có lỗi
        if errors:
            return jsonify(
                {'success': False, 'message': 'Có lỗi xảy ra trong quá trình xử lý', 'errors': errors}), 500

        print('don hang ne',don_hang.ma_DH)
        # Thành công
        return jsonify({'success': True, 'message': 'Đặt vé thành công!', 'order_id': don_hang.ma_DH})

    except Exception as e:
        # Bắt lỗi không mong đợi
        return jsonify({'success': False, 'message': f'Lỗi hệ thống: {str(e)}'}), 500


@app.route('/check_login_status')
def check_login_status():
    # Kiểm tra xem người dùng đã đăng nhập chưa (có thể dùng session hoặc current_user)
    if current_user.is_authenticated:
        return jsonify({"logged_in": True})
    else:
        return jsonify({"logged_in": False})






@customer_bp.route('/calculate_total_price', methods=['GET', 'POST'])
def calculate_total_price():
    discount_code = session.get('applied_discount')
    passengers = session.get('passengers', [])
    flight_data = session.get('outbound_flight', None)
    flight_data_return = session.get('return_flight', None)

    # Lấy tỷ lệ giảm từ mã khuyến mãi
    discount_rate = get_discount_rate(discount_code) if discount_code else None

    # Khởi tạo các biến tính toán
    total_price = 0
    total_luggage_cost = 0
    total_order_value = 0

    for passenger in passengers:
        # Tính tổng giá trị vé (đi và về)
        total_price = flight_data['price'] + flight_data_return['price']

        # Áp dụng giảm giá nếu có
        if discount_code:
            total_price = total_price * (1 - discount_rate)

        # Tính chi phí hành lý (bao gồm hành lý đi và về)
        total_luggage_cost = passenger['luggage']['cost'] + passenger['luggage_return']['cost']

        # Tổng giá trị đơn hàng (bao gồm giá vé và hành lý)
        total_order_value = total_price + total_luggage_cost

    return render_template('pay.html', total_price=total_price)


import hashlib
import hmac
import urllib
from datetime import datetime

@customer_bp.route('/create_payment', methods=['POST'])
def create_payment():
    order_id = session.get("orderId")  # Lấy từ session
    amount = session.get("amount")  # Lấy từ session

    print('oder-amount', order_id, amount)

    if not order_id or not amount:
        return jsonify({"error": "Thông tin đơn hàng không đầy đủ"}), 400

    order_desc = f"Thanh toán hóa đơn cho đơn hàng {order_id}"

    create_date = datetime.now().strftime('%Y%m%d%H%M%S')

    vnp_Amount = int(amount) * 100

    vnp_params = {
        "vnp_Version": '2.1.0',
        "vnp_Command": 'pay',
        "vnp_TmnCode": VNP_TMN_CODE,
        "vnp_Amount": vnp_Amount,
        "vnp_CurrCode": 'VND',
        "vnp_TxnRef": order_id,  # Mã đơn hàng
        "vnp_OrderInfo": order_desc,
        'vnp_OrderType': 'Đặt vé máy bay',
        "vnp_Locale": 'vn',  # Ngôn ngữ
        'vnp_BankCode': 'ncb',
        "vnp_CreateDate": create_date,
        "vnp_IpAddr": request.remote_addr,
        "vnp_ReturnUrl": VNP_RETURN_URL,
    }

    # Lấy URL thanh toán
    payment_url = get_payment_url(vnp_params, VNP_HASH_SECRET)
    print(f"Payment URL: {payment_url}")

    return jsonify({"paymentUrl": payment_url})


@customer_bp.route('/vnpay_return', methods=['GET'])
def vnpay_return():
    input_data = request.args
    result = {"success": False, "message": "Thanh toán thất bại!"}
    success = False

    if input_data:
        vnp_secure_hash = input_data.get('vnp_SecureHash')
        vnp_transaction_no = input_data.get('vnp_TransactionNo')
        vnp_response_code = input_data.get('vnp_ResponseCode')
        order_id = input_data.get('vnp_TxnRef')

        # Xác thực mã băm
        request_data = {key: value for key, value in input_data.items() if key != 'vnp_SecureHash'}
        hash_value = hmac.new(VNP_HASH_SECRET.encode('utf-8'), urllib.parse.urlencode(request_data).encode('utf-8'),
                              hashlib.sha512).hexdigest()

        if vnp_secure_hash == hash_value:
            if vnp_response_code == "00":
                update_trang_thai_don_hang(order_id, TrangThaiDonHang.SUCCESS)
                success = True  # Thành công
                amount = get_tong_gia_tri_don_hang(order_id)

                luu_thanh_toan(
                    ma_tt=vnp_transaction_no,
                    ma_dh=order_id,
                    phuong_thuc="VNPay",
                    so_tien=amount
                )
            else:
                update_trang_thai_don_hang(order_id, TrangThaiDonHang.FAILURE)
        else:
            result = {"success": False, "message": "Sai mã băm"}

        # Render template với thông tin `success` và `order_id`
        return render_template('vnpay_return.html', success=success, order_id=order_id)


@customer_bp.route('/vnpay_callback', methods=['POST'])
def vnpay_callback():
    vnp_data = request.form

    txn_ref = vnp_data.get('vnp_TxnRef')
    response_code = vnp_data.get('vnp_ResponseCode')

    if response_code == '00':
        pass
    else:
        pass

    return "OK"

@customer_bp.route('/check_payment_status', methods=['GET'])
def check_payment_status():
    order_id = session.get('orderId')
    print('ordeer id nè trời: ',order_id)
    if not order_id:
        return jsonify({"success": False, "message": "Không tìm thấy mã đơn hàng"}), 400

    # Lấy trạng thái đơn hàng từ cơ sở dữ liệu
    order_status = get_order_status(order_id)

    if order_status == TrangThaiDonHang.SUCCESS:
        return jsonify({"success": True, "message": "Thanh toán thành công!"})
    elif order_status == TrangThaiDonHang.FAILURE:
        return jsonify({"success": False, "pay": False, "message": "Thanh toán thất bại!"})
    else:
        return jsonify({"success": False, "message": "Đang xử lý thanh toán"})


@customer_bp.route('/get_order_id', methods=['GET'])
def get_order_id():
    order_id = session.get("orderId")
    if not order_id:
        return jsonify({"success": False, "message": "Không tìm thấy mã đơn hàng"}), 400
    return jsonify({"success": True, "orderId": order_id})




@customer_bp.route('/order/<order_id>', methods=["GET"])
def get_order_details_view(order_id):
    order_info = get_order_details_by_order_id(order_id)

    return render_template('bill.html', order_info=order_info)


