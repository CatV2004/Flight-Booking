import hashlib
import hmac
import urllib

from sqlalchemy.orm import aliased

from .info_passenger import PassengerInfo, Luggage

from babel import Locale
from babel.dates import format_date
from sqlalchemy import and_, func
from datetime import datetime, timedelta
from .flight_detail import FlightDetail, FlightInfo
from app.models import TuyenBay, db, ChuyenBay, Ghe, SanBay, HangMayBay, MayBay, SanBayTrungGian, HangVe, QuyDinh, \
    DonHang, KhuyenMai, ChiTietVe, Ve, LoaiVe, HanhLy, KhachHang, ThanhToan
from .. import VNP_URL


def get_payment_url(request_data, secret_key):
    # Sắp xếp dữ liệu theo thứ tự alphabe
    inputData = sorted(request_data.items())
    queryString = ''
    seq = 0
    for key, val in inputData:
        if seq == 1:
            queryString = queryString + "&" + key + '=' + urllib.parse.quote_plus(str(val))
        else:
            seq = 1
            queryString = key + '=' + urllib.parse.quote_plus(str(val))

    # Tạo mã băm HMACSHA512
    hash_value = hmac.new(secret_key.encode('utf-8'), queryString.encode('utf-8'), hashlib.sha512).hexdigest()
    return f"{VNP_URL}?{queryString}&vnp_SecureHash={hash_value}"



# Định dạng format datetime
# Hàm định dạng ngày tháng sang tiếng Việt bằng Babel
def format_vietnamese_date(date_obj):
    locale = Locale('vi', 'VN')  # Đặt locale là tiếng Việt
    return format_date(date_obj, format='full', locale=locale)


# tìm địa điểm của sân bay dựa vào mã sân bay
def find_airport_location(airport_code):
    # Truy vấn và trả về địa điểm của sân bay dựa trên mã sân bay
    san_bay = db.session.query(SanBay.dia_diem).filter(SanBay.ma_san_bay == airport_code).first()

    if san_bay:
        return san_bay.dia_diem  # Trả về địa điểm của sân bay
    else:
        return None  # Trường hợp không tìm thấy sân bay


# tìm tên sân bay của sân bay dựa vào mã sân bay
def find_airport_name(airport_code):
    # Truy vấn và trả về địa điểm của sân bay dựa trên mã sân bay
    san_bay = db.session.query(SanBay.ten_san_bay).filter(SanBay.ma_san_bay == airport_code).first()

    if san_bay:
        return san_bay.ten_san_bay  # Trả về địa điểm của sân bay
    else:
        return None  # Trường hợp không tìm thấy sân bay


# hàm chuyển chuỗi thành kiểu dữ liệu datetime
def convert_to_datetime(date_input):
    if isinstance(date_input, str):  # Nếu là chuỗi
        try:
            return datetime.strptime(date_input, '%Y-%m-%d')
        except ValueError as e:
            # Nếu không thể chuyển đổi chuỗi, xử lý lỗi ở đây
            print(f"Error converting date: {e}")
            return None
    elif isinstance(date_input, datetime):  # Nếu đã là đối tượng datetime
        return date_input
    else:
        print("Invalid input type. Expected string or datetime.")
        return None


# hàm trả về tuyến bay phù hợp với nơi đi nơi đến
def find_route_by_airport_codes(from_code, to_code):
    # Truy vấn bảng TuyenBay để tìm tuyến bay từ mã sân bay đi (san_bay_di) đến mã sân bay đến (san_bay_den)
    tuyen_bay = db.session.query(TuyenBay).filter(
        TuyenBay.san_bay_di == from_code,
        TuyenBay.san_bay_den == to_code
    ).first()  # Lấy kết quả đầu tiên

    if tuyen_bay:
        # Nếu tìm thấy tuyến bay, trả về đối tượng TuyenBay (hoặc có thể trả về các thông tin cần thiết)
        return tuyen_bay.ma_tuyen_bay
    else:
        # Nếu không tìm thấy tuyến bay, trả về None
        return None


# hàm trả về danh sách các chuyến bay phù hợp với tuyến bay và ngày bay
def find_flights(departure_time_str, route_code, seat_class, ticket_quantity):
    # Chuyển đổi departure_time_str thành datetime nếu là chuỗi
    departure_time = convert_to_datetime(departure_time_str)

    # Kiểm tra nếu thời gian nhập không hợp lệ (None)
    if not departure_time:
        raise ValueError("Invalid departure time format.")

    current_time = datetime.now()
    hours_value = QuyDinh.get_value_by_ma_qd(ma_qd='QD00001')
    target_time = current_time + timedelta(hours=int(hours_value))

    flights = db.session.query(ChuyenBay).filter(
        ChuyenBay.tuyen_bay == route_code,  # Lọc theo mã tuyến bay
        ChuyenBay.thoi_gian_di >= target_time,  # Lọc các chuyến bay có thời gian đi sau 12 giờ
        ChuyenBay.thoi_gian_di.between(departure_time.replace(hour=0, minute=0, second=0, microsecond=0),
                                       departure_time.replace(hour=23, minute=59, second=59, microsecond=999999))
    ).all()

    # Lọc các chuyến bay có đủ số ghế trống theo hạng vé
    valid_flights = []
    for flight in flights:
        # Truy vấn số ghế trống theo hạng vé
        available_seats = db.session.query(Ghe).filter(
            Ghe.may_bay == flight.may_bay,
            Ghe.hang_ve == HangVe.from_value(int(seat_class)),  # Lọc theo hạng vé
            Ghe.trang_thai == False  # Ghế chưa được đặt
        ).count()

        # Kiểm tra nếu số ghế trống đủ cho yêu cầu
        if available_seats >= int(ticket_quantity):
            valid_flights.append(flight)

    # return valid_flights
    return flights


# # lấy danh sách hãng máy bay từ danh sách chuyến bay
# def get_airlines_by_flights(flights):
#     try:
#         # Lấy danh sách mã máy bay từ danh sách chuyến bay
#         flight_ids = [flight.may_bay for flight in flights]
#
#         # Truy vấn các hãng máy bay liên quan đến danh sách chuyến bay
#         airlines = db.session.query(HangMayBay).join(
#             MayBay, HangMayBay.so_hieu_hangmb == MayBay.hang_may_bay_ID
#         ).filter(
#             MayBay.so_hieu_mb.in_(flight_ids)  # Lọc theo danh sách mã máy bay
#         ).distinct().all()  # Tránh trùng lặp bằng distinct()
#
#         return airlines
#     except Exception as e:
#         print(f"Lỗi trong quá trình truy vấn: {e}")
#         return []
def get_airlines_by_flights(flights, seat_class):
    try:
        # Lấy danh sách mã máy bay từ danh sách chuyến bay
        flight_ids = [flight.may_bay for flight in flights]

        # Truy vấn các hãng máy bay liên quan đến danh sách chuyến bay và giá vé theo hạng vé
        airline_data = db.session.query(
            HangMayBay.so_hieu_hangmb,
            HangMayBay.ten_hang,
            HangMayBay.lo_go,
            func.min(Ghe.gia_ghe).label('price')
        ).join(
            MayBay, HangMayBay.so_hieu_hangmb == MayBay.hang_may_bay_ID
        ).join(
            Ghe, MayBay.so_hieu_mb == Ghe.may_bay
        ).filter(
            MayBay.so_hieu_mb.in_(flight_ids),  # Lọc theo danh sách mã máy bay
            Ghe.hang_ve == HangVe.from_value(int(seat_class)),  # Lọc theo hạng vé được chọn
            Ghe.trang_thai == False  # Chỉ lấy ghế chưa được đặt
        ).group_by(
            HangMayBay.so_hieu_hangmb, HangMayBay.ten_hang, HangMayBay.lo_go
        ).all()

        # Trả về danh sách các hãng máy bay với giá vé theo hạng vé
        return [{"airline_id": data.so_hieu_hangmb,
                 "name": data.ten_hang,
                 "price": data.price,
                 "lo_go": data.lo_go
                 } for data in airline_data
                ]

    except Exception as e:
        print(f"Lỗi trong quá trình truy vấn: {e}")
        return []



def get_full_flight_info_v2(flights, seat_class):
    all_flight_details = []  # Danh sách chứa tất cả các chặng bay
    flight_info_list = []  # Danh sách kết quả cuối cùng

    # Tạo danh sách tất cả các chặng bay
    for flight in flights:
        # Lấy thông tin tuyến bay
        tuyen_bay = db.session.query(TuyenBay).filter(TuyenBay.ma_tuyen_bay == flight.tuyen_bay).first()
        if not tuyen_bay:
            continue

        # Lấy danh sách sân bay trung gian, sắp xếp theo thứ tự
        intermediate_stops = db.session.query(SanBayTrungGian).filter(
            SanBayTrungGian.ma_chuyen_bay == flight.ma_chuyen_bay,
            SanBayTrungGian.ma_tuyen_bay == flight.tuyen_bay
        ).order_by(SanBayTrungGian.thu_tu).all()

        # Tạo danh sách các sân bay từ điểm đi, trung gian đến điểm đến
        airports = [tuyen_bay.san_bay_di_ref] + [stop.SanBay for stop in intermediate_stops] + [
            tuyen_bay.san_bay_den_ref
        ]

        # Lấy thông tin hãng máy bay
        may_bay = db.session.query(MayBay).filter(MayBay.so_hieu_mb == flight.may_bay).first()
        airline = may_bay.HangMayBay if may_bay else None
        airline_name = airline.ten_hang if airline else None
        airline_logo = airline.lo_go if airline else None

        # Tạo từng chặng bay và thêm vào danh sách tất cả các chặng bay
        for i in range(len(airports) - 1):
            departure_airport = airports[i]
            arrival_airport = airports[i + 1]

            # Tính toán thời gian cho chặng
            if i == 0:  # Chặng đầu tiên
                departure_time = flight.thoi_gian_di
                arrival_time = (
                    intermediate_stops[i].thoi_gian_dung_chan
                    if intermediate_stops else flight.thoi_gian_den
                )
            elif i == len(intermediate_stops):  # Chặng cuối
                departure_time = intermediate_stops[i - 1].thoi_gian_tiep_tuc
                arrival_time = flight.thoi_gian_den
            else:  # Các chặng trung gian
                departure_time = intermediate_stops[i - 1].thoi_gian_tiep_tuc
                arrival_time = intermediate_stops[i].thoi_gian_dung_chan

            # Tính thời lượng chặng

            duration = arrival_time - departure_time
            # duration = arrival_time - departure_time
            days = duration.days
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60

            # Tạo đối tượng FlightDetail mới
            new_flight_detail = FlightDetail(
                departure_time=departure_time.strftime('%H:%M'),
                departure_date=departure_time.strftime('%d thg %m'),
                arrival_time=arrival_time.strftime('%H:%M'),
                arrival_date=arrival_time.strftime('%d thg %m'),
                departure_airport={
                    'airport_name': departure_airport.ten_san_bay,
                    'airport_location': departure_airport.dia_diem,
                    'airport_code': departure_airport.ma_san_bay
                },
                arrival_airport={
                    'airport_name': arrival_airport.ten_san_bay,
                    'airport_location': arrival_airport.dia_diem,
                    'airport_code': arrival_airport.ma_san_bay
                },
                airline=airline_name,
                logo=airline_logo,
                duration=f'{hours}h {minutes:02}m',
                number_day=days,
                stops=len(intermediate_stops),
            )

            # Thêm đối tượng vào danh sách
            all_flight_details.append(new_flight_detail)


    # Gán chặng bay vào từng chuyến bay
    current_index = 0
    for flight in flights:
        # Lấy số lượng chặng bay cần thiết (số sân bay trung gian + 1)
        tuyen_bay = db.session.query(TuyenBay).filter(TuyenBay.ma_tuyen_bay == flight.tuyen_bay).first()
        if not tuyen_bay:
            continue

        intermediate_stops = db.session.query(SanBayTrungGian).filter(
            SanBayTrungGian.ma_chuyen_bay == flight.ma_chuyen_bay,
            SanBayTrungGian.ma_tuyen_bay == flight.tuyen_bay
        ).all()
        num_segments = len(intermediate_stops) + 1

        # Lấy các chặng bay tương ứng
        flight_segments = all_flight_details[current_index:current_index + num_segments]
        current_index += num_segments
        # In thông tin các chặng bay


        duration_all = flight.thoi_gian_den - flight.thoi_gian_di
        day_change = (flight.thoi_gian_den.date() - flight.thoi_gian_di.date()).days
        days_all = duration_all.days
        hours_all = duration_all.seconds // 3600
        minutes_all = (duration_all.seconds % 3600) // 60


        # Lấy giá chuyến bay dựa trên hạng vé và máy bay
        gia_chuyen_bay = db.session.query(Ghe.gia_ghe).filter(
            Ghe.may_bay == flight.may_bay,
            Ghe.hang_ve == HangVe.from_value(int(seat_class)),  # Sử dụng hạng vé được cung cấp
            Ghe.trang_thai == False
        ).first()
        gia_chuyen_bay = gia_chuyen_bay[0] if gia_chuyen_bay else 0

        # Lấy thông tin máy bay và hãng hàng không từ bảng MayBay và HangMayBay
        may_bay = db.session.query(MayBay).filter(MayBay.so_hieu_mb == flight.may_bay).first()
        if may_bay:
            airline = db.session.query(HangMayBay).filter(HangMayBay.so_hieu_hangmb == may_bay.hang_may_bay_ID).first()
            airline_name = airline.ten_hang if airline else None
            airline_logo = airline.lo_go if airline else None
            airline_code = airline.so_hieu_hangmb if airline else None
        else:
            airline_name = None
            airline_logo = None
            airline_code = None


        # Tạo đối tượng FlightInfo
        flight_info = FlightInfo(
            ma_chuyen_bay=flight.ma_chuyen_bay,
            details_flight=[segment.get_info() for segment in flight_segments],
            stops=len(intermediate_stops),
            logo=flight_segments[0].logo if flight_segments else "",
            number_day=day_change,
            airline=flight_segments[0].airline if flight_segments else "",
            duration=f'{hours_all}h {minutes_all:02}m',
            departure_time=flight.thoi_gian_di.strftime('%H:%M'),
            arrival_time=flight.thoi_gian_den.strftime('%H:%M'),
            # airline_code=flight_segments[0].airline if flight_segments else "",
            airline_code=airline_code if airline_code else "",
            price=gia_chuyen_bay
        )


        flight_info_list.append(flight_info.get_info())

    return flight_info_list



def filter_flights_by_departure_time(flights, selected_departure_times):
    filtered_flights = []

    # Nếu có khoảng thời gian cất cánh đã chọn
    if selected_departure_times:
        for flight in flights:
            # Lọc theo từng khoảng thời gian
            for time_range in selected_departure_times:
                start_time_str, end_time_str = time_range.split('-')

                # Xử lý trường hợp '24:00' thành '00:00'
                if start_time_str == '24:00':
                    start_time_str = '00:00'
                if end_time_str == '24:00':
                    end_time_str = '00:00'

                # Chuyển đổi thời gian bắt đầu và kết thúc thành đối tượng datetime
                start_time = datetime.strptime(start_time_str, '%H:%M').time()
                end_time = datetime.strptime(end_time_str, '%H:%M').time()

                # Chuyển đổi giờ cất cánh của chuyến bay thành đối tượng datetime
                departure_time = datetime.strptime(flight['departureTime'], '%H:%M').time()

                # Kiểm tra xem thời gian cất cánh có nằm trong khoảng không
                if start_time <= departure_time <= end_time:
                    filtered_flights.append(flight)
                    break

    return filtered_flights


def create_passenger(passenger_id, form_data, cost_map, is_return=False):
    # Lấy thông tin cá nhân
    last_name = form_data.get(f'lname_{passenger_id}')
    first_name = form_data.get(f'fname_{passenger_id}')
    phone = form_data.get(f'phone_{passenger_id}')
    email = form_data.get(f'email_{passenger_id}')
    id_number = form_data.get(f'idNumber_{passenger_id}')
    birth_day = form_data.get(f'birth_day_{passenger_id}')
    birth_month = form_data.get(f'birth_month_{passenger_id}')
    birth_year = form_data.get(f'birth_year_{passenger_id}')

    # Tạo hành lý cho chuyến đi
    baggage_weight_raw = form_data.get(f'baggage_trip_{passenger_id}', '0')
    baggage_weight = int(baggage_weight_raw) if baggage_weight_raw.isdigit() else 0
    baggage_cost = cost_map.get(baggage_weight, 0)
    luggage_trip = Luggage(weight=baggage_weight, cost=baggage_cost)

    # Tạo hành lý cho chuyến về (nếu có)
    luggage_return = None
    if is_return:
        baggage_weight_raw_return = form_data.get(f'baggage_return_{passenger_id}', '0')
        baggage_weight_return = int(baggage_weight_raw_return) if baggage_weight_raw_return.isdigit() else 0
        baggage_cost_return = cost_map.get(baggage_weight_return, 0)
        luggage_return = Luggage(weight=baggage_weight_return, cost=baggage_cost_return)

    # Tạo đối tượng PassengerInfo cho hành khách
    birth_date = {"day": birth_day, "month": birth_month, "year": birth_year}
    passenger = PassengerInfo(
        passenger_id=passenger_id,
        last_name=last_name,
        first_name=first_name,
        phone=phone,
        email=email,
        id_number=id_number,
        birth_date=birth_date,
        luggage=luggage_trip  # Gán hành lý chuyến đi
    )

    # Nếu có chuyến về, gán hành lý chuyến về
    if luggage_return:
        passenger.luggage_return = luggage_return

    return passenger


def update_trang_thai_don_hang(order_id, status):
    try:
        # Fetch the order by its ID
        don_hang = db.session.query(DonHang).filter_by(ma_DH=order_id).first()

        if not don_hang:
            print(f"Order with ID {order_id} not found.")
            return False

        # Update the status
        don_hang.trang_thai = status

        # Commit the changes to the database
        db.session.commit()
        print(f"Order {order_id} status updated to {status}.")
        return True

    except Exception as e:
        # Handle any exceptions that occur
        db.session.rollback()
        print(f"Error updating order status: {str(e)}")
        return False

def get_order_status(order_id):
    try:
        order = db.session.query(DonHang).filter(DonHang.ma_DH == order_id).first()

        if not order:
            raise ValueError(f"Không tìm thấy đơn hàng với mã: {order_id}")

        return order.trang_thai

    except Exception as e:
        print(f"Lỗi khi lấy trạng thái đơn hàng: {e}")
        return None


def get_order_details_by_order_id(ma_don_hang):
    sb_di = aliased(SanBay)
    sb_den = aliased(SanBay)
    sbtg = aliased(SanBay)
    sbtg_san_bay_trung_gian = aliased(SanBay)

    query = db.session.query(
        DonHang.ma_DH.label('ma_don_hang'),
        DonHang.tong_gia_tri_DH.label('tong_gia_tri'),
        DonHang.ngay_dat_DH.label('ngay_tao_don_hang'),
        Ve.ma_ve,
        HangMayBay.ten_hang.label('hang_may_bay'),
        HanhLy.loai_HL.label('hanh_ly_loai'),
        HanhLy.trong_luong.label('hanh_ly_trong_luong'),
        HanhLy.chi_phi.label('hanh_ly_chi_phi'),
        ChuyenBay.thoi_gian_di,
        ChuyenBay.thoi_gian_den,
        sb_di.ten_san_bay.label('san_bay_di'),
        sb_den.ten_san_bay.label('san_bay_den'),
        sbtg_san_bay_trung_gian.ten_san_bay.label('san_bay_trung_gian')
    ).join(
        Ve, Ve.ma_don_hang == DonHang.ma_DH
    ).join(
        ChiTietVe, ChiTietVe.ma_ve == Ve.ma_ve
    ).join(
        ChuyenBay, ChuyenBay.ma_chuyen_bay == ChiTietVe.ma_chuyen_bay
    ).join(
        MayBay, MayBay.so_hieu_mb == ChuyenBay.may_bay
    ).join(
        HangMayBay, HangMayBay.so_hieu_hangmb == MayBay.hang_may_bay_ID
    ).outerjoin(
        HanhLy, HanhLy.ma_HL == ChiTietVe.hanh_ly
    ).join(
        TuyenBay, TuyenBay.ma_tuyen_bay == ChuyenBay.tuyen_bay
    ).join(
        sb_di, sb_di.ma_san_bay == TuyenBay.san_bay_di
    ).join(
        sb_den, sb_den.ma_san_bay == TuyenBay.san_bay_den
    ).outerjoin(
        SanBayTrungGian, SanBayTrungGian.ma_tuyen_bay == TuyenBay.ma_tuyen_bay
    ).outerjoin(
        sbtg, sbtg.ma_san_bay == SanBayTrungGian.ma_san_bay
    ).outerjoin(
        sbtg_san_bay_trung_gian, sbtg_san_bay_trung_gian.ma_san_bay == sbtg.ma_san_bay
    ).filter(
        DonHang.ma_DH == ma_don_hang,  # Lọc theo mã đơn hàng
        DonHang.trang_thai == 'SUCCESS'
    ).order_by(
        DonHang.ngay_dat_DH.desc()
    )

    # Chuyển đổi kết quả thành danh sách từ điển
    result = query.all()
    result_dict = [row._asdict() for row in result]

    return result_dict


def get_customer_email_by_order_id(ma_dh):
    # Truy vấn đơn hàng theo mã đơn hàng
    don_hang = DonHang.query.filter_by(ma_DH=ma_dh).first()

    if don_hang:
        # Truy vấn khách hàng liên kết với đơn hàng
        khach_hang = KhachHang.query.filter_by(id=don_hang.khach_hang).first()

        if khach_hang:
            # Trả về email của khách hàng
            return khach_hang.email
        else:
            return None  # Không tìm thấy khách hàng
    else:
        return None  # Không tìm thấy đơn hàng

def luu_thanh_toan(ma_tt, ma_dh, phuong_thuc, so_tien):
    try:
        # Tạo đối tượng ThanhToan
        thanh_toan = ThanhToan(
            ma_TT=ma_tt,
            ma_DH=ma_dh,
            phuong_thuc=phuong_thuc,
            so_tien=so_tien
        )
        # Thêm vào session và commit
        db.session.add(thanh_toan)
        db.session.commit()
        return True
    except Exception as e:
        print(f"Lỗi khi lưu thông tin thanh toán: {e}")
        db.session.rollback()
        return False

