import random
import string
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Enum, Date, DateTime, event
from datetime import datetime  # Import đúng kiểu datetime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app import db, app
from enum import Enum as RoleEnum
from flask_login import UserMixin



# Database Flight Booking System
class VaiTro(RoleEnum):
    ADMIN = 1
    USER = 2
    EMPLOYEE = 3


class HangThanhVien(RoleEnum):
    BAC = 1
    VANG = 2
    KIMCUONG = 3


class HangVe(RoleEnum):
    PHOTHONG = 1
    THUONGGIA = 2

    @classmethod
    def from_value(cls, value):
        try:
            return cls(value).name  # Trả về tên từ giá trị
        except ValueError:
            return None


class LoaiVe(RoleEnum):
    MOTCHIEU = 1
    KHUHOI = 2

    @classmethod
    def from_value(cls, value):
        try:
            return cls(value).name  # Trả về tên từ giá trị
        except ValueError:
            return None


class TrangThaiDonHang(RoleEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"


def generate_unique_code(prefix, length=5):
    while True:
        # Sinh mã ngẫu nhiên
        code = prefix + ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        # Kiểm tra mã đã tồn tại chưa
        if not DonHang.query.filter_by(ma_DH=code).first():  # Kiểm tra mã trong DB
            return code  # Trả về mã duy nhất


class NguoiDung(db.Model, UserMixin):
    __tablename__ = 'NguoiDung'
    id = Column(Integer, primary_key=True, autoincrement=True)
    fname = Column(String(50), nullable=False, unique=False)
    lname = Column(String(50), nullable=False)
    dia_chi = Column(String(200))
    email = Column(String(100), nullable=False, unique=False)
    so_dien_thoai = Column(String(15), nullable=True)
    ngay_sinh = Column(Date)
    so_CCCD = Column(String(20), nullable=True)
    tai_khoan = relationship("TaiKhoan", backref='NguoiDung', uselist=False, cascade='all, delete-orphan')

    ve = relationship("Ve", backref='NguoiDung')

    def __init__(self, fname, lname, email, dia_chi=None, so_dien_thoai=None, ngay_sinh=None, so_CCCD=None):
        self.fname = fname
        self.lname = lname
        self.email = email
        self.dia_chi = dia_chi
        self.so_dien_thoai = so_dien_thoai
        self.ngay_sinh = ngay_sinh
        self.so_CCCD = so_CCCD

    def __str__(self):
        return self.lname

class TaiKhoan(db.Model, UserMixin):
    __tablename__ = 'TaiKhoan'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ten_dang_nhap = Column(String(50), nullable=False, unique=True)
    mat_khau = Column(String(100), nullable=False)
    trang_thai = Column(db.Boolean, default=True)
    vai_tro = Column(Enum(VaiTro), default=VaiTro.USER, nullable=False)

    nguoi_dung_id = Column(Integer, ForeignKey(NguoiDung.id), nullable=False)


    def __init__(self, ten_dang_nhap, mat_khau, vai_tro=VaiTro.USER, nguoi_dung_id=None, trang_thai=True):
        self.ten_dang_nhap = ten_dang_nhap
        self.mat_khau = mat_khau
        self.vai_tro = vai_tro
        self.nguoi_dung_id = nguoi_dung_id
        self.trang_thai = trang_thai

    @property
    def lname(self):
        return self.nguoi_dung.lname if self.nguoi_dung else None

    @property
    def fname(self):
        return self.nguoi_dung.fname if self.nguoi_dung else None

    @property
    def dia_chi(self):
        return self.nguoi_dung.dia_chi if self.nguoi_dung else None

    @property
    def so_CCCD(self):
        return self.nguoi_dung.so_CCCD if self.nguoi_dung else None

    @property
    def email(self):
        return self.nguoi_dung.email if self.nguoi_dung else None

    @property
    def so_dien_thoai(self):
        return self.nguoi_dung.so_dien_thoai if self.nguoi_dung else None

    def get_id(self):
        return str(self.id)


class Admin(NguoiDung, UserMixin):
    __tablename__ = 'Admin'
    id = Column(Integer, ForeignKey(NguoiDung.id), primary_key=True)
    ngay_vao_lam = Column(Date)
    kinh_nghiem = Column(String(200))


    __mapper_args__ = {
        'inherit_condition': id == NguoiDung.id,
    }

    def __init__(self, fname, lname, email, dia_chi=None, so_dien_thoai=None, ngay_sinh=None, so_CCCD=None,
                  ngay_vao_lam=None, kinh_nghiem=None, **kwargs):
        print("kwargs:", kwargs)
        super().__init__(fname=fname, lname=lname, email=email, dia_chi=dia_chi,
                         so_dien_thoai=so_dien_thoai, ngay_sinh=ngay_sinh, so_CCCD=so_CCCD, **kwargs)
        self.ngay_vao_lam = ngay_vao_lam
        self.kinh_nghiem = kinh_nghiem

class KhachHang(NguoiDung, UserMixin):
    __tablename__ = 'KhachHang'
    id = Column(Integer, ForeignKey(NguoiDung.id), primary_key=True)
    hang_thanh_vien = Column(Enum(HangThanhVien), default=HangThanhVien.BAC, nullable=False)
    don_hang_mua = relationship('DonHang', backref='KhachHang', cascade='all, delete-orphan')
    binh_luan = relationship('BinhLuan', backref='KhachHang')

    __mapper_args__ = {
        'inherit_condition': id == NguoiDung.id,
    }


class NhanVien(NguoiDung, UserMixin):
    __tablename__ = 'NhanVien'
    id = Column(Integer, ForeignKey(NguoiDung.id), primary_key=True)
    luong = Column(Float, nullable=False)
    ngay_vao_lam = Column(Date, nullable=False)
    ghi_chu = Column(String(200))
    don_hang_duyet = relationship('DonHang', backref='NhanVien')


    __mapper_args__ = {
        'inherit_condition': id == NguoiDung.id,
    }

    def __init__(self, fname, lname, email, dia_chi=None, so_dien_thoai=None, ngay_sinh=None, so_CCCD=None,
                 luong=None, ngay_vao_lam=None, ghi_chu=None, **kwargs):
        super().__init__(fname=fname, lname=lname, email=email, dia_chi=dia_chi,
                         so_dien_thoai=so_dien_thoai, ngay_sinh=ngay_sinh, so_CCCD=so_CCCD, **kwargs)
        self.luong = luong
        self.ngay_vao_lam = ngay_vao_lam
        self.ghi_chu = ghi_chu


class HangMayBay(db.Model):
    __tablename__ = 'HangMayBay'
    so_hieu_hangmb = Column(String(10), primary_key=True)
    ten_hang = Column(String(50), nullable=False)
    lo_go = Column(String(500))
    may_bay = relationship("MayBay", backref='HangMayBay', cascade='all, delete-orphan')

    def __str__(self):
        return self.ten_hang
    def __repr__(self):
        return self.so_hieu_hangmb

class MayBay(db.Model):
    __tablename__ = 'MayBay'
    so_hieu_mb = Column(String(10), primary_key=True)
    hang_may_bay_ID = Column(String(10), ForeignKey(HangMayBay.so_hieu_hangmb), nullable=False)
    ghe = relationship('Ghe', backref='MayBay', cascade='all, delete-orphan')
    chuyen_bay = relationship('ChuyenBay', backref='MayBay')

    @staticmethod
    def generate_so_hieu_mb():
        # Lấy danh sách các số hiệu máy bay hiện có trong cơ sở dữ liệu
        existing_codes = [
            may_bay.so_hieu_mb for may_bay in db.session.query(MayBay).all()
        ]

        # Tìm mã lớn nhất hiện có
        max_code = 0
        for code in existing_codes:
            if code.startswith("MB0"):  # Chỉ xét các mã có định dạng "MB0..."
                try:
                    num_part = int(code[2:])  # Lấy phần số phía sau "MB0"
                    max_code = max(max_code, num_part)
                except ValueError:
                    continue

        # Sinh mã mới bằng cách tăng max_code lên 1
        new_code = f"MB0{max_code + 1}"
        # Đảm bảo mã mới không trùng với mã hiện có
        while new_code in existing_codes:
            max_code += 1
            new_code = f"MB0{max_code + 1}"

        return new_code

    def __repr__(self):
        return self.so_hieu_mb


# Lắng nghe sự kiện 'before_insert' để tự động tạo mã
@event.listens_for(MayBay, 'before_insert')
def auto_generate_so_hieu_mb(mapper, connection, target):
    if not target.so_hieu_mb:  # Chỉ tạo nếu chưa có mã
        target.so_hieu_mb = MayBay.generate_so_hieu_mb()


class HanhLy(db.Model):
    __tablename__ = 'HanhLy'
    ma_HL = Column(String(10), primary_key=True)
    loai_HL = Column(String(20), nullable=True)
    trong_luong = Column(Integer, nullable=False)
    chi_phi = Column(Float, nullable=False)
    chi_tiet_ve = relationship("ChiTietVe", backref='HanhLy', uselist=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.ma_HL:
            self.ma_HL = generate_unique_code('HL', length=5)


class KhuyenMai(db.Model):
    __tablename__ = 'KhuyenMai'
    ma_KM = Column(String(10), primary_key=True)
    mo_ta = Column(String(50), nullable=True)
    ty_le_giam = Column(Float, nullable=False)
    ngay_bat_dau = Column(Date, nullable=False)
    ngay_ket_thuc = Column(Date, nullable=False)
    don_hang = relationship('DonHang', backref='KhuyenMai')
    dieu_kien_KM = relationship('DieuKienKM', backref='KhuyenMai')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.ma_KM:
            self.ma_KM = generate_unique_code('KM', length=5)

class DieuKienKM(db.Model):
    __tablename__ = 'DieuKienKM'
    ma_DK = Column(String(10), primary_key=True)
    noi_dung = Column(String(200), nullable=True)
    ghi_chu = Column(String(200), nullable=True)
    khuyen_mai_id = Column(String(10), ForeignKey(KhuyenMai.ma_KM), nullable=False)

    def __str__(self):
        return self.ma_DK


class Ghe(db.Model):
    __tablename__ = 'Ghe'
    ma_ghe = Column(String(10), primary_key=True)
    hang_ve = Column(Enum(HangVe), default=HangVe.PHOTHONG, nullable=False)
    vi_tri = Column(String(10), nullable=False)
    may_bay = Column(String(10), ForeignKey(MayBay.so_hieu_mb), nullable=False)
    gia_ghe = Column(Float, nullable=False)
    trang_thai = Column(Boolean, default=False)
    chi_tiet_ve = relationship('ChiTietVe', backref='Ghe')

    def __init__(self, hang_ve=None, vi_tri=None, trang_thai=None, may_bay=None, gia_ghe=None):
        # Gán giá trị mặc định cho hang_ve nếu là None
        if hang_ve is None:
            self.hang_ve = HangVe.PHOTHONG
        else:
            self.hang_ve = hang_ve

        # Đảm bảo giá trị hang_ve hợp lệ
        if self.hang_ve not in [HangVe.PHOTHONG, HangVe.THUONGGIA]:
            raise ValueError(f"Hạng vé '{self.hang_ve}' không hợp lệ.")

        # Gọi generate_ma_ghe sau khi hang_ve đã có giá trị hợp lệ

        # Gán các giá trị còn lại
        self.vi_tri = vi_tri
        self.trang_thai = trang_thai
        self.may_bay = may_bay
        self.gia_ghe = gia_ghe

    def generate_ma_ghe(self, may_bay):
        if isinstance(may_bay, str):
            if len(may_bay) < 2:
                raise ValueError("Số hiệu máy bay không hợp lệ.")
            so_hieu_mb = int(may_bay[2:])
        else:
            if hasattr(may_bay, 'so_hieu_mb') and len(may_bay.so_hieu_mb) >= 2:
                so_hieu_mb = int(may_bay.so_hieu_mb[2:])
            else:
                raise ValueError("Số hiệu máy bay không hợp lệ.")

        if self.hang_ve == HangVe.THUONGGIA:
            range_start, range_end = 0, 30
        elif self.hang_ve == HangVe.PHOTHONG:
            range_start, range_end = 30, 280
        else:
            raise ValueError(f"Hạng vé '{self.hang_ve}' không hợp lệ.")

        # Lấy danh sách các mã ghế đã tồn tại cho máy bay này
        existing_codes = [
            ghe.ma_ghe for ghe in db.session.query(Ghe).filter(Ghe.may_bay == may_bay).all()
        ]

        # Tìm mã ghế chưa được sử dụng
        for i in range(range_start, range_end):
            ma_ghe_moi = f"G{so_hieu_mb}{i:03d}"
            if ma_ghe_moi not in existing_codes:
                return str(ma_ghe_moi)

        raise ValueError("Không còn mã ghế khả dụng trong khoảng quy định.")


# Lắng nghe sự kiện 'before_insert' để tự động tạo mã ghế
@event.listens_for(Ghe, 'before_insert')
def auto_generate_ma_ghe(mapper, connection, target):
    # Kiểm tra xem ma_ghe đã có chưa, nếu chưa thì tạo mới
    if not target.ma_ghe:
        # Tạo mã ghế tự động
        target.ma_ghe = target.generate_ma_ghe(target.may_bay)



class DonHang(db.Model):
    __tablename__ = 'DonHang'
    ma_DH = Column(String(10), primary_key=True)
    khach_hang = Column(Integer, ForeignKey(KhachHang.id), nullable=False)
    nhan_vien = Column(Integer, ForeignKey(NhanVien.id), nullable=True)
    so_luong_ve = Column(Integer, nullable=False)
    ngay_dat_DH = Column(DateTime, nullable=False, default=func.now())
    ma_KM = Column(String(10), ForeignKey(KhuyenMai.ma_KM), nullable=True)
    tong_gia_tri_DH = Column(Float, default=0)
    trang_thai = Column(Enum(TrangThaiDonHang), default=TrangThaiDonHang.SUCCESS)
    thanh_toan = relationship('ThanhToan', backref='DonHang')
    ve = relationship('Ve', backref='DonHang')



    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.ma_DH:
            self.ma_DH = generate_unique_code('DH', length=5)


class Ve(db.Model):
    __tablename__ = 'Ve'
    ma_ve = Column(String(10), primary_key=True, default=lambda: generate_unique_code('VE', length=5))
    ma_don_hang = Column(String(10), ForeignKey(DonHang.ma_DH), nullable=False)
    nguoi_so_huu = Column(Integer, ForeignKey(NguoiDung.id), nullable=False)
    ngay_xuat_ve = Column(DateTime, nullable=True)
    loai_ve = Column(Enum(LoaiVe), default=LoaiVe.MOTCHIEU, nullable=False)
    gia_ves = Column(Float, nullable=False)
    chi_tiet_ve = relationship('ChiTietVe', backref='Ve')


class LichBay(db.Model):
    __tablename__ = 'LichBay'
    ma_LB = Column(String(10), primary_key=True)
    chuyen_bay = relationship('ChuyenBay', backref='LichBay')
    ngay_lap_lich = Column(Date, nullable=True)


class KhuVuc(db.Model):
    __tablename__ = 'KhuVuc'
    ma_khu_vuc = Column(String(10), primary_key=True)
    ten_khu_vuc = Column(String(50), nullable=False)
    san_bay = relationship('SanBay', backref='KhuVuc', cascade='all, delete-orphan')

    def __repr__(self):
        return self.ma_khu_vuc


class SanBay(db.Model):
    __tablename__ = 'SanBay'
    ma_san_bay = Column(String(10), primary_key=True)
    ten_san_bay = Column(String(50), nullable=False)
    dia_diem = Column(String(50), nullable=False)
    ma_khu_vuc = Column(String(10), ForeignKey(KhuVuc.ma_khu_vuc), nullable=False)

    # # Các tuyến bay liên kết với sân bay này
    # tuyen_bay = relationship('TuyenBay', backref='SanBay')

    san_bay_trung_gian = relationship('SanBayTrungGian', backref='SanBay')

    def __init__(self, ma_san_bay, ten_san_bay, dia_diem, ma_khu_vuc):
        self.ma_san_bay = ma_san_bay
        self.ten_san_bay = ten_san_bay
        self.dia_diem = dia_diem
        self.ma_khu_vuc = ma_khu_vuc

    # Định nghĩa __repr__ để trả về chuỗi mong muốn
    def __repr__(self):
        return self.ma_san_bay

class TuyenBay(db.Model):
    __tablename__ = 'TuyenBay'
    ma_tuyen_bay = Column(String(10), primary_key=True)

    san_bay_den = Column(String(10), ForeignKey(SanBay.ma_san_bay), nullable=False)
    san_bay_di = Column(String(10), ForeignKey(SanBay.ma_san_bay), nullable=False)
    san_bay_den_ref = db.relationship('SanBay', backref='tuyen_bay_den', uselist=False, foreign_keys=[san_bay_den])
    san_bay_di_ref = db.relationship('SanBay', backref='tuyen_bay_di', uselist=False, foreign_keys=[san_bay_di])

    san_bay_trung_gian = relationship('SanBayTrungGian', backref='TuyenBay')
    chuyen_bay = relationship('ChuyenBay', backref='Tuyenbay', cascade='all, delete-orphan')

    def __init__(self, ma_tuyen_bay, san_bay_den, san_bay_di):
        self.ma_tuyen_bay = ma_tuyen_bay
        self.san_bay_den = san_bay_den
        self.san_bay_di = san_bay_di

    # Định nghĩa __repr__ để trả về chuỗi mong muốn
    def __repr__(self):
        return self.ma_tuyen_bay
class SanBayTrungGian(db.Model):
    __tablename__ = 'SanBayTrungGian'
    ma_san_bay = Column(String(10), ForeignKey(SanBay.ma_san_bay), primary_key=True)
    ma_tuyen_bay = Column(String(10), ForeignKey(TuyenBay.ma_tuyen_bay), primary_key=True)
    ma_chuyen_bay = Column(String(10), ForeignKey('ChuyenBay.ma_chuyen_bay'), nullable=False)  # Thêm cột này
    thoi_gian_dung_chan = Column(DateTime, nullable=True)
    thoi_gian_tiep_tuc = Column(DateTime, nullable=True)
    thu_tu = Column(Integer, nullable=False)
    ghi_chu = Column(String(200), nullable=True)

    chuyen_bay = relationship('ChuyenBay', back_populates='san_bay_trung_gian')  # Thiết lập quan hệ


class ChuyenBay(db.Model):
    __tablename__ = 'ChuyenBay'
    ma_chuyen_bay = Column(String(10), primary_key=True)
    may_bay = Column(String(10), ForeignKey(MayBay.so_hieu_mb), nullable=False)
    tuyen_bay = Column(String(10), ForeignKey(TuyenBay.ma_tuyen_bay), nullable=False)
    lich_bay = Column(String(10), ForeignKey(LichBay.ma_LB), nullable=False)
    thoi_gian_di = Column(DateTime, nullable=False)
    thoi_gian_den = Column(DateTime, nullable=False)

    chi_tiet_ve = relationship('ChiTietVe', backref='ChuyenBay')
    san_bay_trung_gian = relationship('SanBayTrungGian', back_populates='chuyen_bay', cascade='all, delete-orphan')  # Thiết lập quan hệ

    def __init__(self, ma_chuyen_bay, may_bay, tuyen_bay, lich_bay, gia_chuyen_bay, thoi_gian_di, thoi_gian_den):
        self.ma_chuyen_bay = ma_chuyen_bay
        self.may_bay = may_bay
        self.tuyen_bay = tuyen_bay
        self.lich_bay = lich_bay
        self.gia_chuyen_bay = gia_chuyen_bay
        self.thoi_gian_di = thoi_gian_di
        self.thoi_gian_den = thoi_gian_den

    def __repr__(self):
        return self.ma_chuyen_bay

class ChiTietVe(db.Model):
    __tablename__ = 'ChiTietVe'
    ma_chuyen_bay = Column(String(10), ForeignKey(ChuyenBay.ma_chuyen_bay), primary_key=True)
    ma_ve = Column(String(10), ForeignKey(Ve.ma_ve), primary_key=True)
    ghe = Column(String(10), ForeignKey(Ghe.ma_ghe), nullable=False)
    hanh_ly = Column(String(10), ForeignKey(HanhLy.ma_HL), nullable=True)
    gia_ve = Column(Float, default=0)



class ThanhToan(db.Model):
    __tablename__ = 'ThanhToan'
    ma_TT = Column(String(10), primary_key=True)
    ma_DH = Column(String(10), ForeignKey(DonHang.ma_DH), primary_key=True, nullable=True)
    phuong_thuc = Column(String(50))
    so_tien = Column(Float, primary_key=True, nullable=False)
    ngay_TT = Column(DateTime, default=func.now())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.ma_TT:
            self.ma_TT = generate_unique_code('TT', length=5)

class BinhLuan(db.Model):
    __tablename__ = 'BinhLuan'
    ma_BL = Column(String(10), primary_key=True)
    khach_hang = Column(Integer, ForeignKey('KhachHang.id'), nullable=True)
    noi_dung = Column(String(255), nullable=False)
    thoi_gian = Column(DateTime, default=datetime.now)

    def __init__(self, khach_hang, noi_dung, **kwargs):
        super().__init__(**kwargs)
        self.khach_hang = khach_hang
        self.noi_dung = noi_dung


    @staticmethod
    def generate_ma_bl():
        # Lấy danh sách các mã hiện có
        existing_codes = [
            binh_luan.ma_BL for binh_luan in db.session.query(BinhLuan).all()
        ]

        # Tìm mã lớn nhất hiện có
        max_code = 0
        for code in existing_codes:
            if code.startswith("BL"):
                try:
                    num_part = int(code[2:])
                    max_code = max(max_code, num_part)
                except ValueError:
                    continue

        # Sinh mã mới
        new_code = f"BL{max_code + 1:05d}"
        while new_code in existing_codes:
            max_code += 1
            new_code = f"BL{max_code + 1:05d}"

        return new_code

# Lắng nghe sự kiện 'before_insert' để tự động tạo mã
@event.listens_for(BinhLuan, 'before_insert')
def auto_generate_ma_bl(mapper, connection, target):
    if not target.ma_BL:  # Chỉ tạo nếu chưa có mã
        target.ma_BL = BinhLuan.generate_ma_bl()


class QuyDinh(db.Model):
    __tablename__ = 'QuyDinh'
    ma_QD = Column(String(10), primary_key=True)
    noi_dung = Column(String(255))
    value = Column(Integer, nullable=False)

    def __init__(self, noi_dung, value, **kwargs):
        super().__init__(**kwargs)
        self.noi_dung = noi_dung
        self.value = value

    @staticmethod
    def get_value_by_ma_qd(ma_qd):
        quy_dinh = db.session.query(QuyDinh).filter_by(ma_QD=ma_qd).first()
        if quy_dinh:
            return quy_dinh.value
        return None

    @staticmethod
    def generate_ma_qd():
        # Lấy danh sách các mã hiện có
        existing_codes = [
            quy_dinh.ma_QD for quy_dinh in db.session.query(QuyDinh).all()
        ]

        # Tìm mã lớn nhất hiện có
        max_code = 0
        for code in existing_codes:
            if code.startswith("QD"):
                try:
                    num_part = int(code[2:])
                    max_code = max(max_code, num_part)
                except ValueError:
                    continue

        # Sinh mã mới
        new_code = f"QD{max_code + 1:05d}"
        while new_code in existing_codes:
            max_code += 1
            new_code = f"QD{max_code + 1:05d}"

        return new_code

# Lắng nghe sự kiện 'before_insert' để tự động tạo mã
@event.listens_for(QuyDinh, 'before_insert')
def auto_generate_ma_qd(mapper, connection, target):
    if not target.ma_QD:  # Chỉ tạo nếu chưa có mã
        target.ma_QD = QuyDinh.generate_ma_qd()

if __name__ == '__main__':
    with app.app_context():
        # ghe_moi = Ghe(hang_ve=HangVe.THUONGGIA, vi_tri="A03", trang_thai=False, may_bay="MB010", gia_ghe=500000)
        qd01 = QuyDinh(noi_dung='Chỉ đặt cho các chuyến bay trước 12h lúc khởi hành', value=12)
        db.session.add(qd01)
        db.session.commit()
        print(f"Mã ghế được tạo tự động: {qd01.ma_QD}")


        # Xóa tất cả dữ liệu trong cơ sở dữ liệu
        # db.drop_all()
        # Tái tạo các bảng nếu cần
        # db.create_all()
