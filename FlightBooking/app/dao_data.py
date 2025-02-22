from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from app import db
from app.models import ChiTietVe, HanhLy, Ve, DonHang, NguoiDung, KhuyenMai, ChuyenBay, Ghe
from datetime import datetime

# Hàm thêm Chi Tiết Chuyến Bay vào database
def add_chi_tiet_ve(ma_chuyen_bay, ma_ve, ma_ghe, gia_ve, hanh_ly = None):
    try:
        add_chi_tiet_ve = ChiTietVe(
            ma_chuyen_bay=ma_chuyen_bay,
            ma_ve=ma_ve,
            hanh_ly=hanh_ly,
            ghe=ma_ghe,
            gia_ve=gia_ve
        )
        db.session.add(add_chi_tiet_ve)
        db.session.commit()
        return add_chi_tiet_ve
    except Exception as e:
        db.session.rollback()
        print(f"Error adding ChiTietChuyenBay: {e}")
        return None

def update_hanh_ly(ma_chuyen_bay, ma_ve, ma_hanh_ly):
    # Tìm bản ghi chi tiết vé theo ma_chuyen_bay và ma_ve
    chi_tiet_ve = ChiTietVe.query.filter_by(
        ma_chuyen_bay=ma_chuyen_bay,
        ma_ve=ma_ve
    ).first()

    # Kiểm tra nếu tìm thấy bản ghi chi tiết vé
    if chi_tiet_ve:
        # Cập nhật trường hanh_ly với giá trị mới
        chi_tiet_ve.hanh_ly = ma_hanh_ly

        # Lưu lại thay đổi
        db.session.commit()
        return True  # Thành công
    else:
        # Nếu không tìm thấy bản ghi
        print("Không tìm thấy bản ghi")
        return False  # Không tìm thấy bản ghi


# Hàm thêm Hành Lý vào database
def add_hanh_ly(ma_HL, loai_HL, trong_luong, chi_phi):
    try:
        hanh_ly = HanhLy(
            ma_HL=ma_HL,
            loai_HL=loai_HL,
            trong_luong=trong_luong,
            chi_phi=chi_phi
        )
        db.session.add(hanh_ly)
        db.session.commit()
        return hanh_ly
    except Exception as e:
        db.session.rollback()
        print(f"Error adding HanhLy: {e}")
        return None

# Hàm thêm Vé vào database
def add_ve(ma_ve, ma_don_hang, nguoi_so_huu, gia_ves, loai_ve):
    try:
        ve = Ve(
            ma_ve=ma_ve,
            ma_don_hang=ma_don_hang,
            nguoi_so_huu=nguoi_so_huu,
            gia_ves=gia_ves,
            loai_ve=loai_ve,
        )
        db.session.add(ve)
        db.session.commit()
        return ve
    except Exception as e:
        db.session.rollback()
        print(f"Error adding Ve: {e}")
        return None

# Hàm thêm Đơn Hàng vào database
def add_don_hang(ma_don_hang, khach_hang, ma_khuyen_mai, nhan_vien, so_luong_ve, tong_tien, ngay_dat, trang_thai):
    try:
        don_hang = DonHang(
            ma_DH=ma_don_hang,
            khach_hang=khach_hang,
            nhan_vien=nhan_vien,
            so_luong_ve=so_luong_ve,
            ma_KM=ma_khuyen_mai,
            tong_gia_tri_DH=tong_tien,
            trang_thai=trang_thai
        )
        db.session.add(don_hang)
        db.session.commit()
        return don_hang
    except Exception as e:
        db.session.rollback()
        print(f"Error adding DonHang: {e}")
        return None

# Hàm thêm Người Dùng vào database
def add_nguoi_dung(ten, ho, dia_chi, email, so_dien_thoai, ngay_sinh, so_cccd, loai_nguoi_dung):
    try:
        nguoi_dung = NguoiDung(
            fname=ten,
            lname=ho,
            dia_chi=dia_chi,
            email=email,
            so_dien_thoai=so_dien_thoai,
            ngay_sinh=ngay_sinh,
            so_CCCD=so_cccd
        )
        db.session.add(nguoi_dung)
        db.session.flush()  # Ghi vào bộ đệm ngay lập tức
        db.session.commit()
        return nguoi_dung
    except Exception as e:
        db.session.rollback()
        print(f"Error adding NguoiDung: {e}")
        return None


# Hàm trả về tỷ lệ giảm theo mã khuyến mãi
def get_discount_rate(ma_KM):
    # Truy vấn bảng KhuyenMai để tìm khuyến mãi theo ma_KM
    khuyen_mai = db.session.query(KhuyenMai).filter(KhuyenMai.ma_KM == ma_KM).first()

    # Kiểm tra nếu khuyến mãi tồn tại và chưa hết hạn
    if khuyen_mai:
        # Kiểm tra xem khuyến mãi còn hiệu lực không (so với ngày hiện tại)
        current_date = datetime.now().date()
        if khuyen_mai.ngay_bat_dau <= current_date <= khuyen_mai.ngay_ket_thuc:
            return khuyen_mai.ty_le_giam
        else:
            print("Khuyến mãi đã hết hạn")
            return None
    else:
        print("Mã khuyến mãi không tồn tại")
        return None


def lay_ghes_trong(ma_chuyen_bay, hang_ve):
    try:
        # Tạo session để làm việc với database
        session = sessionmaker(bind=db.engine)()

        # Lấy chuyến bay tương ứng với mã chuyến bay
        chuyen_bay = session.query(ChuyenBay).filter(ChuyenBay.ma_chuyen_bay == ma_chuyen_bay).first()
        if not chuyen_bay:
            raise Exception("Chuyến bay không tồn tại")

        # Lấy ghế trống của chuyến bay theo hạng ghế (Thương gia hoặc Phổ thông)
        ghe = session.query(Ghe).filter(Ghe.may_bay == chuyen_bay.may_bay, Ghe.hang_ve == hang_ve, Ghe.trang_thai == False).first()

        # Kiểm tra xem có ghế trống hay không
        if not ghe:
            raise Exception("Không còn ghế trống cho hạng ghế này")

        # Cập nhật trạng thái ghế đã được đặt (trang_thai = 1)
        ghe.trang_thai = True
        session.commit()

        # Trả về mã ghế đã chọn
        return ghe.ma_ghe

    except SQLAlchemyError as e:
        session.rollback()
        return None

    except Exception as e:
        session.rollback()
        return None

    finally:
        session.close()


def get_tong_gia_tri_don_hang(ma_dh):
    try:
        don_hang = db.session.query(DonHang).filter(DonHang.ma_DH == ma_dh).first()
        if don_hang:
            return don_hang.tong_gia_tri_DH
        return None
    except SQLAlchemyError as e:
        print(f"Lỗi khi lấy tổng giá trị đơn hàng: {e}")
        return None