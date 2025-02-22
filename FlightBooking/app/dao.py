from datetime import datetime, timedelta

from flask_login import current_user
from sqlalchemy.orm import aliased
from requests import session, delete
from sqlalchemy import func, and_, or_, update
from app.models import TaiKhoan, NguoiDung, Admin, KhachHang, NhanVien, HangThanhVien, ChuyenBay, Ghe, MayBay, \
    SanBayTrungGian, HangMayBay, TuyenBay, SanBay, KhuVuc, VaiTro, BinhLuan, DonHang, ChiTietVe, HanhLy, Ve, ThanhToan, \
    LichBay, KhuyenMai
from app import app, db
import hashlib
import re

def load_comments():
    comments = db.session.query(BinhLuan, KhachHang.fname, KhachHang.lname).outerjoin(KhachHang).all()
    return comments

def save_comment(content):
    khach_hang_id = current_user.id if current_user.is_authenticated else None

    if khach_hang_id and not KhachHang.query.get(khach_hang_id):
        raise ValueError("Khách hàng không hợp lệ")

    new_comment = BinhLuan(
        noi_dung=content,
        khach_hang=khach_hang_id,
        thoi_gian=datetime.now()
    )
    db.session.add(new_comment)
    db.session.commit()
    return new_comment


def add_or_get_user_from_google(first_name, last_name, username, email):
    user_account = TaiKhoan.query.filter_by(ten_dang_nhap=username).first()
    if not user_account:
        try:
            # Tạo đối tượng NguoiDung
            customer = KhachHang(fname=first_name, lname=last_name, email=email)
            db.session.add(customer)
            db.session.commit()

            # Sau đó, Tạo đối tượng tài khoản người dùng liên kết với người dùng
            account = TaiKhoan(ten_dang_nhap=username, mat_khau="", nguoi_dung_id=customer.id, trang_thai=True)
            db.session.add(account)
            db.session.commit()

            # Gán lại `user` với tài khoản vừa tạo
            user_account = customer

        except Exception as ex:
            db.session.rollback()
            print(f"Error while adding user: {ex}")
            raise ex
    else:
        # Nếu tài khoản đã tồn tại, lấy đối tượng NguoiDung từ TaiKhoan
        user_account = NguoiDung.query.get(user_account.nguoi_dung_id)

    return user_account



def add_user(first_name, last_name, username, password, email):
    try:
        # Mã hóa mật khẩu
        password = hashlib.md5(password.encode('utf-8')).hexdigest()

        # Tạo đối tượng NguoiDung
        customer = KhachHang(fname=first_name, lname=last_name, email=email)
        db.session.add(customer)
        db.session.commit()

        # Sau đó, Tạo đối tượng tài khoản người dùng liên kết với người dùng
        account = TaiKhoan(ten_dang_nhap=username, mat_khau=password, nguoi_dung_id = customer.id)
        db.session.add(account)
        db.session.commit()

        # # Sau đó, tạo đối tượng KhachHang
        # customer = KhachHang(id=user.id, hang_thanh_vien=HangThanhVien.BAC)
        # db.session.add(customer)
        # db.session.commit()

    except Exception as ex:
        db.session.rollback()
        print(f"Error: {ex}")
        raise ex


def auth_user(username, password, role=None):
    # # Mã hóa mật khẩu
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    # Kiểm tra tài khoản và mật khẩu
    acc = TaiKhoan.query.filter(TaiKhoan.ten_dang_nhap.__eq__(username.strip()),
                                 TaiKhoan.mat_khau.__eq__(password))
    if role:
        acc = acc.filter(TaiKhoan.vai_tro.__eq__(role))
    return acc.first()


# def get_user_by_id(user_id):
#     return db.session.query(NguoiDung).join(TaiKhoan, TaiKhoan.nguoi_dung_id == NguoiDung.id) \
#         .filter(NguoiDung.id == user_id).first()

def get_user_by_id(account_id):
    # Truy vấn bảng TaiKhoan để lấy đối tượng TaiKhoan theo ID tài khoản
    tai_khoan = TaiKhoan.query.filter(TaiKhoan.id == account_id).first()

    # Nếu không tìm thấy tài khoản, trả về None
    if not tai_khoan:
        return None

    # Trả về đối tượng NguoiDung dựa trên nguoi_dung_id của TaiKhoan
    return NguoiDung.query.filter(NguoiDung.id == tai_khoan.nguoi_dung_id).first()


# Kiểm tra username có tồn tại không
def is_username_exists(username):
    return TaiKhoan.query.filter(TaiKhoan.ten_dang_nhap == username).first() is not None


def validate_profile_data(data):
    # Kiểm tra họ và tên
    if not data['lname'] or not data['fname']:
        return False, "Họ và tên không được để trống."

    # Kiểm tra ngày sinh
    if data['ngay_sinh']:
        try:
            datetime.strptime(data['ngay_sinh'], '%d/%m/%Y')
        except ValueError:
            return False, "Ngày sinh không đúng định dạng (dd/mm/yyyy)."

    # Kiểm tra số CCCD
    if data['so_CCCD'] and len(data['so_CCCD']) != 12:
        return False, "Số CCCD phải có đúng 12 ký tự."

    # Kiểm tra số điện thoại (bắt đầu từ 0 và 10 chữ số)
    if data.get('so_dien_thoai'):
        if not re.match(r'^0\d{9}$', data['so_dien_thoai']):
            return False, "Số điện thoại không hợp lệ. Phải là 10 chữ số và bắt đầu bằng 0."

    # Kiểm tra email
    if data['email']:
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', data['email']):
            return False, "Email không hợp lệ."

    return True, None


def update_user_profile(user_id, fname, lname, ngay_sinh, dia_chi, so_CCCD, so_dien_thoai, email):
    try:
        # Lấy người dùng thông qua `nguoi_dung_id` trong bảng TaiKhoan
        user_account = TaiKhoan.query.filter_by(id=user_id).first()

        if user_account and user_account.nguoi_dung_id:
            # Lấy thông tin người dùng từ bảng NguoiDung
            user = NguoiDung.query.filter_by(id=user_account.nguoi_dung_id).first()

            if user:
                # Cập nhật thông tin cá nhân
                user.fname = fname
                user.lname = lname
                user.ngay_sinh = ngay_sinh
                user.dia_chi = dia_chi
                user.so_CCCD = so_CCCD
                user.so_dien_thoai = so_dien_thoai
                user.email = email

                # Lưu thay đổi vào database
                db.session.commit()
                return True
            else:
                print("Người dùng không tồn tại.")
                return False
        else:
            print("Tài khoản không tồn tại hoặc không liên kết với người dùng.")
            return False
    except Exception as ex:
        db.session.rollback()
        print(f"Error updating user profile: {ex}")
        raise ex



def check_current_password(user, current_password):
    hashed_password = hashlib.md5(current_password.encode('utf-8')).hexdigest()
    return user.tai_khoan.mat_khau == hashed_password


def update_password(user, new_password):
    try:
        hashed_password = hashlib.md5(new_password.encode('utf-8')).hexdigest()
        user.tai_khoan.mat_khau = hashed_password
        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        print(f"Error updating password: {ex}")
        raise ex

# load khu vuc
def load_area():
    return KhuVuc.query.all()


# load san bay
def load_airport():
    return SanBay.query.order_by('ma_khu_vuc').all()


# load hang may bay
def load_airline():
    return HangMayBay.query.all()


# Load chuyen bay ban dau de chon
def load_flight(noi_di, noi_den, ngay_bay, so_luong_hanh_khach, hang_ve):
    SanBayDi = aliased(SanBay)
    SanBayDen = aliased(SanBay)
    return (db.session.query(
        HangMayBay.ten_hang,
        SanBayDi.dia_diem.label("noi_di"),
        SanBayDen.dia_diem.label("noi_den"),
        ChuyenBay.thoi_gian_di,
        ChuyenBay.thoi_gian_den,
        Ghe.gia_ghe,
        func.count(func.distinct(SanBayTrungGian.ma_tuyen_bay)).label("diem_dung"),
        ChuyenBay.ma_chuyen_bay
    ).join(
        MayBay, MayBay.hang_may_bay_ID == HangMayBay.so_hieu_hangmb
    ).join(
        ChuyenBay, ChuyenBay.may_bay == MayBay.so_hieu_mb
    ).join(
        TuyenBay, TuyenBay.ma_tuyen_bay == ChuyenBay.tuyen_bay
    ).join(
        SanBayDi, SanBayDi.ma_san_bay == TuyenBay.san_bay_di
    ).join(
        SanBayDen, SanBayDen.ma_san_bay == TuyenBay.san_bay_den
    ).join(
        Ghe, MayBay.so_hieu_mb == Ghe.may_bay
    ).outerjoin(
        SanBayTrungGian, SanBayTrungGian.ma_chuyen_bay == ChuyenBay.ma_chuyen_bay
    ).filter(SanBayDi.dia_diem == noi_di,
        SanBayDen.dia_diem == noi_den,
        func.date(ChuyenBay.thoi_gian_di) == ngay_bay,
        ChuyenBay.thoi_gian_di >= app.config["TIME_NOW"] + timedelta(hours=4),
        Ghe.trang_thai == 0,
        Ghe.hang_ve == hang_ve
    ).group_by(
        HangMayBay.ten_hang, SanBayDi.dia_diem,
        SanBayDen.dia_diem, ChuyenBay.thoi_gian_di,
        ChuyenBay.thoi_gian_den,  Ghe.gia_ghe,ChuyenBay.ma_chuyen_bay
    ).having(func.count(Ghe.ma_ghe) >= so_luong_hanh_khach).all())


# Load chuyen bay sau khi nhan nut tim de chon
def load_flight_click_search(noi_di, noi_den, ngay_bay, so_diem_dung, thoi_gian_bay, hang_bay, temp_time_flight, hang_ve, so_luong_hanh_khach):
    SanBayDi = aliased(SanBay)
    SanBayDen = aliased(SanBay)
    return (db.session.query(
        HangMayBay.ten_hang,
        SanBayDi.dia_diem.label("noi_di"),
        SanBayDen.dia_diem.label("noi_den"),
        ChuyenBay.thoi_gian_di,
        ChuyenBay.thoi_gian_den,
        Ghe.gia_ghe,
        func.count(func.distinct(SanBayTrungGian.ma_tuyen_bay)).label("diem_dung"),
        ChuyenBay.ma_chuyen_bay
    ).join(
        MayBay, MayBay.hang_may_bay_ID == HangMayBay.so_hieu_hangmb
    ).join(
        ChuyenBay, ChuyenBay.may_bay == MayBay.so_hieu_mb
    ).join(
        TuyenBay, TuyenBay.ma_tuyen_bay == ChuyenBay.tuyen_bay
    ).join(
        SanBayDi, SanBayDi.ma_san_bay == TuyenBay.san_bay_di
    ).join(
        SanBayDen, SanBayDen.ma_san_bay == TuyenBay.san_bay_den
    ).join(
        Ghe, MayBay.so_hieu_mb == Ghe.may_bay
    ).outerjoin(
        SanBayTrungGian, SanBayTrungGian.ma_chuyen_bay == ChuyenBay.ma_chuyen_bay
    ).filter(SanBayDi.dia_diem == noi_di,
             SanBayDen.dia_diem == noi_den,
             func.date(ChuyenBay.thoi_gian_di) == ngay_bay,
             or_(hang_bay == "Hãng Bay", HangMayBay.ten_hang == hang_bay),
             or_(thoi_gian_bay == 35, and_(func.hour(ChuyenBay.thoi_gian_di) < thoi_gian_bay, func.hour(ChuyenBay.thoi_gian_di) >= thoi_gian_bay - temp_time_flight)),
             ChuyenBay.thoi_gian_di >= app.config["TIME_NOW"] + timedelta(hours=4),
             Ghe.trang_thai == 0,
             Ghe.hang_ve == hang_ve
    ).group_by(HangMayBay.ten_hang, ChuyenBay.thoi_gian_di, ChuyenBay.thoi_gian_den,
               Ghe.gia_ghe, SanBayDi.dia_diem, SanBayDen.dia_diem, ChuyenBay.ma_chuyen_bay
    ).having(and_(so_diem_dung == 0, func.count(SanBayTrungGian.ma_chuyen_bay) == 0
        ) if so_diem_dung == 0 else or_(
            func.count(func.distinct(SanBayTrungGian.ma_tuyen_bay)) == so_diem_dung,
            and_(
                so_diem_dung == 4,
                func.count(SanBayTrungGian.ma_chuyen_bay) != so_diem_dung
            )
        ),
        func.count(Ghe.ma_ghe) >= so_luong_hanh_khach
    ).all())


#Ham load so luong ghe cua mot chuyen
def load_chair(chuyen_bay, hang_ve):
    return db.session.query(
        MayBay.so_hieu_mb,
        Ghe.vi_tri,
        Ghe.trang_thai
    ).select_from(ChuyenBay  # Xác định bảng gốc là ChuyenBay
    ).join(
        MayBay, ChuyenBay.may_bay == MayBay.so_hieu_mb
    ).join(
        Ghe, Ghe.may_bay == MayBay.so_hieu_mb
    ).filter(
        ChuyenBay.ma_chuyen_bay == chuyen_bay,
        Ghe.hang_ve == hang_ve
    ).all()


#load giam gia
def load_discount(MaKM):
    return db.session.query(
        KhuyenMai.ty_le_giam
    ).filter(KhuyenMai.ma_KM == MaKM.upper()).all()
#load khach hang
def load_customer(cccd):
    return NguoiDung.query.with_entities(NguoiDung.id).filter(NguoiDung.so_CCCD == cccd).first()
#add Nguoi dung
def them_nguoi_dung(fname, lname, email, phone, birthday, cccd):
    u = NguoiDung(fname=fname, lname=lname, email=email, so_dien_thoai=phone, ngay_sinh=birthday, so_CCCD=cccd)
    db.session.add(u)
    db.session.commit()
#Load id người dùng
def load_id():
    return NguoiDung.query.order_by(NguoiDung.id.desc()).first()
#them khach hang
def them_khach_hang(fname, lname, email, phone, birthday, cccd):
    c = KhachHang(fname=fname, lname=lname, email=email, so_dien_thoai=phone, ngay_sinh=birthday, so_CCCD=cccd)
    db.session.add(c)
    db.session.commit()
#them don hang
def them_don_hang(id_khachHang, id_nhanVien, so_luong_ve, ma_KM, tong_gia_tri_DH, ma_DH):
    km = load_discount(ma_KM)
    if km:
        print('1')
        dh = DonHang(ma_DH=ma_DH,khach_hang = id_khachHang, nhan_vien = id_nhanVien, so_luong_ve=so_luong_ve, ma_KM=ma_KM, tong_gia_tri_DH=tong_gia_tri_DH)
    else:
        print('2')
        dh = DonHang(ma_DH=ma_DH, khach_hang = id_khachHang, nhan_vien = id_nhanVien, so_luong_ve=so_luong_ve, tong_gia_tri_DH=tong_gia_tri_DH)
    db.session.add(dh)
    db.session.commit()
#Load khach hang
def load_DH(soCCCD):
    return db.session.query(
        func.distinct(DonHang.ma_DH)
    ).select_from(NguoiDung
    ).join(
        KhachHang, NguoiDung.id == KhachHang.id
    ).join(
        DonHang, KhachHang.id == DonHang.khach_hang
    ).filter(NguoiDung.so_CCCD == soCCCD).all()
#def them thanh toan
def them_thanh_toan(cccd, phuong_thuc, so_tien, ma_DH):
    tt = ThanhToan(ma_DH=ma_DH, phuong_thuc=phuong_thuc, so_tien=so_tien)
    db.session.add(tt)
    db.session.commit()
#Xem người dùng thứ nhất đã là khách hàng hay chưua
def load_user(soCCCD):
    return NguoiDung.query.filter(NguoiDung.so_CCCD == soCCCD).first()
#Hàm thêm vé vào db
def them_ve(soCCCD, ma_ve, loai_ve, gia_ve, ma_DH):
    user = load_user(soCCCD)
    if user and ma_DH:
        ve = Ve(ma_don_hang=ma_DH, nguoi_so_huu=user.id, ngay_xuat_ve=datetime.now(), loai_ve=loai_ve, gia_ves=gia_ve, ma_ve=ma_ve)
        db.session.add(ve)
        db.session.commit()
#Ham them hanh ly
def them_hanh_ly(so_luong, ma_HL):
    hanh_ly = HanhLy(ma_HL=ma_HL,trong_luong = so_luong*10, chi_phi=so_luong*50000)
    db.session.add(hanh_ly)
    db.session.commit()
#Load ma hanh ly
def load_maHL():
    return HanhLy.query.with_entities(HanhLy.ma_HL).all()
#Hàm load ma ve de tao CHITIETVE
def load_ma_ve(so_cccd):
    return db.session.query(
        Ve.ma_ve,
        Ve.gia_ves
    ).join(
        NguoiDung, Ve.nguoi_so_huu == NguoiDung.id
    ).filter(NguoiDung.so_CCCD == so_cccd).all()
#Hàm đếm số lượng hành lý
def dem_so_luong_hanh_ly():
    return db.session.query(func.count(HanhLy.ma_HL)).scalar()
#load ma ghe
def tim_ma_ghe(chuyen_bay, hang_ve, vi_tri):
    return db.session.query(
        Ghe.ma_ghe
    ).select_from(ChuyenBay  # Xác định bảng gốc là ChuyenBay
    ).join(
        MayBay, ChuyenBay.may_bay == MayBay.so_hieu_mb
    ).join(
        Ghe, Ghe.may_bay == MayBay.so_hieu_mb
    ).filter(
        ChuyenBay.ma_chuyen_bay == chuyen_bay,
        Ghe.hang_ve == hang_ve,
        Ghe.vi_tri == vi_tri
    ).first()
# Ham them chi tiet ve
def them_chi_tiet_ve(ma_chuyen_bay, ma_ve, ghe, gia_ve, tong_so_luong_hanh_ly, hang_ve, so_luong_hanh_ly, ma_HL):
    count = dem_so_luong_hanh_ly()
    ma_ghe = tim_ma_ghe(ma_chuyen_bay, hang_ve, ghe)
    if tong_so_luong_hanh_ly < count:
        chi_tiet_ve = ChiTietVe(ma_chuyen_bay=ma_chuyen_bay, ma_ve=ma_ve,ghe=ma_ghe[0],
                                hanh_ly=ma_HL, gia_ve=(gia_ve + float(so_luong_hanh_ly)*50000))
    else:
        chi_tiet_ve = ChiTietVe(ma_chuyen_bay=ma_chuyen_bay, ma_ve=ma_ve, gia_ve=(gia_ve + float(so_luong_hanh_ly)*50000),
                                ghe=ma_ghe[0])
    db.session.add(chi_tiet_ve)
    db.session.commit()
#Ham load ma cac ma may bay
def load_id_plane():
    return MayBay.query.with_entities(MayBay.so_hieu_mb).order_by(MayBay.so_hieu_mb).all()
#ham load tuyen bay
def cac_tuyen_bay():
    SanBayDi = aliased(SanBay)
    SanBayDen = aliased(SanBay)
    return db.session.query(
        TuyenBay.ma_tuyen_bay,
        SanBayDi.dia_diem.label("noi_di"),
        SanBayDen.dia_diem.label('noi_den')
    ).join(
        SanBayDi, SanBayDi.ma_san_bay == TuyenBay.san_bay_di
    ).join(
        SanBayDen, SanBayDen.ma_san_bay == TuyenBay.san_bay_den).all()
#ham them lich bay
def them_lich_bay(ma_LB):
    lich_bay = LichBay(ngay_lap_lich=datetime.now(), ma_LB=ma_LB)
    db.session.add(lich_bay)
    db.session.commit()
#Ham load lich bay
#ham them chuyen bay
def them_chuyen_bay(may_bay, tuyen_bay, thoi_gian_di, thoi_gian_den, lich_bay, ma_chuyen_bay, gia_chuyen_bay):
    cb = ChuyenBay(ma_chuyen_bay=ma_chuyen_bay, may_bay=may_bay, tuyen_bay=tuyen_bay, thoi_gian_di=thoi_gian_di, thoi_gian_den=thoi_gian_den, lich_bay=lich_bay, gia_chuyen_bay=gia_chuyen_bay)
    db.session.add(cb)
    db.session.commit()
#Ham load ma san bay
def load_id_airport(ten_san_bay):
    return SanBay.query.filter(SanBay.ten_san_bay == ten_san_bay).first()
#ham them san bay trung gian
def them_san_bay_tg(ten_san_bay, ma_tuyen_bay, ma_chuyen_bay, thoi_gian_dung_chan, thoi_gian_tiep_tuc, thu_tu, ghi_chu):
    sb = load_id_airport(ten_san_bay)
    sbtg = SanBayTrungGian(ma_san_bay=sb.ma_san_bay, ma_tuyen_bay=ma_tuyen_bay, ma_chuyen_bay=ma_chuyen_bay,
                           thoi_gian_dung_chan=thoi_gian_dung_chan, thoi_gian_tiep_tuc=thoi_gian_tiep_tuc, thu_tu=thu_tu, ghi_chu=ghi_chu)
    db.session.add(sbtg)
    db.session.commit()
#ham update ghe da dat
def update_state_chari(vi_tri, so_hieu_mb):
    print(vi_tri)
    print(so_hieu_mb)
    u = update(Ghe).where(Ghe.may_bay == so_hieu_mb, Ghe.vi_tri == vi_tri).values(trang_thai=1)
    db.session.execute(u)
    db.session.commit()
    print("da update")


#Ham lay thong tin ve
def take_info_ve(ma_ve):
    SanBayDi = aliased(SanBay)
    SanBayDen = aliased(SanBay)
    return (db.session.query(
        NguoiDung.fname,
        NguoiDung.lname,
        NguoiDung.so_dien_thoai,
        NguoiDung.so_CCCD,
        SanBayDi.dia_diem.label('dia_diem_di'),
        SanBayDen.dia_diem.label('dia_diem_den'),
        ChuyenBay.thoi_gian_di,
        ChuyenBay.thoi_gian_den,
        HangMayBay.ten_hang,
        Ghe.vi_tri,
        Ve.loai_ve,
        Ghe.hang_ve,
        Ve.gia_ves,
        HanhLy.ma_HL,
        HanhLy.chi_phi
    ).join(
        Ve, NguoiDung.id == Ve.nguoi_so_huu
    ).join(
        ChiTietVe, Ve.ma_ve == ChiTietVe.ma_ve
    ).join(
        ChuyenBay, ChiTietVe.ma_chuyen_bay == ChuyenBay.ma_chuyen_bay
    ).join(
        Ghe, ChiTietVe.ghe == Ghe.ma_ghe
    ).join(
        MayBay, Ghe.may_bay == MayBay.so_hieu_mb
    ).join(
        HangMayBay, MayBay.hang_may_bay_ID == HangMayBay.so_hieu_hangmb
    ).join(
        TuyenBay, ChuyenBay.tuyen_bay == TuyenBay.ma_tuyen_bay
    ).join(
        SanBayDi, TuyenBay.san_bay_di == SanBayDi.ma_san_bay
    ).join(
        SanBayDen, TuyenBay.san_bay_den == SanBayDen.ma_san_bay
    ).outerjoin(
        HanhLy, ChiTietVe.hanh_ly == HanhLy.ma_HL
    ).filter(
        Ve.ma_ve == ma_ve
    ).first())

#Ham load hanh ly
def lay_hanh_ly(ma_ve):
    return ChiTietVe.query.with_entities(ChiTietVe.hanh_ly).filter(ChiTietVe.ma_ve == ma_ve).first()
#ham lay so luong ve trong don hang
def lay_so_luong_ve(ma_ve):
    return DonHang.query.with_entities(DonHang.so_luong_ve, DonHang.ma_DH).filter(DonHang.ma_DH ==
                                                                   (db.session.query(Ve.ma_don_hang).filter(Ve.ma_ve==ma_ve).first())[0]).first()
#Ham huy ve, huy ve chi tiet, huy don hang, huy hanh ly
def huy_ve(ma_ve):
    ma_hanh_ly = lay_hanh_ly(ma_ve)
    ctv = ChiTietVe.query.filter(ChiTietVe.ma_ve==ma_ve).all()
    hl = HanhLy.query.filter(ma_hanh_ly.hanh_ly == HanhLy.ma_HL).all()
    ve = Ve.query.filter(Ve.ma_ve == ma_ve).all()
    slve = lay_so_luong_ve(ma_ve)
    for i in ctv:
        db.session.delete(i)
        db.session.commit()
    if len(hl) != 0:
        for i in hl:
            db.session.delete(i)
            db.session.commit()
    for i in ve:
        db.session.delete(i)
        db.session.commit()
    if slve[0] == 1:
        dh = DonHang.query.filter(DonHang.ma_DH == slve[1]).all()
        tt = ThanhToan.query.filter(ThanhToan.ma_DH == slve[1]).all()
        for i in dh:
            for j in tt:
                db.session.delete(j)
                db.session.commit()
            db.session.delete(i)
            db.session.commit()