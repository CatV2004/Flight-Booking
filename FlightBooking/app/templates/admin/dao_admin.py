from calendar import month
from datetime import datetime
from tkinter.font import names

from sqlalchemy import func
from sqlalchemy.orm import aliased

from app import app, db
from app.models import TuyenBay, ChuyenBay, ChiTietVe, Ve, DonHang, HanhLy, KhuyenMai, SanBay, HangMayBay, MayBay


def get_total_income_per_route(session, month=None, year=None):
    sb_di = aliased(SanBay)
    sb_den = aliased(SanBay)

    query = session.query(
        TuyenBay.ma_tuyen_bay.label('MaTuyenBay'),
        (sb_di.ten_san_bay + ' - ' + sb_den.ten_san_bay).label('TuyenBay'),
        func.round(func.sum(ChiTietVe.gia_ve), 0).label('TongTienVe'),
        func.round(func.sum(func.coalesce(HanhLy.chi_phi, 0)), 0).label('TongTienHanhLy'),
        func.round(func.sum(ChiTietVe.gia_ve * func.coalesce(KhuyenMai.ty_le_giam, 0)), 0).label('TongTienGiamGia'),
        func.round(func.sum(ChiTietVe.gia_ve + func.coalesce(HanhLy.chi_phi, 0) -
                            (ChiTietVe.gia_ve * func.coalesce(KhuyenMai.ty_le_giam, 0))), 0).label('TongThuNhap')
    ).join(
        ChuyenBay, ChuyenBay.tuyen_bay == TuyenBay.ma_tuyen_bay
    ).join(
        ChiTietVe, ChiTietVe.ma_chuyen_bay == ChuyenBay.ma_chuyen_bay
    ).join(
        Ve, Ve.ma_ve == ChiTietVe.ma_ve
    ).join(
        DonHang, DonHang.ma_DH == Ve.ma_don_hang
    ).outerjoin(
        HanhLy, HanhLy.ma_HL == ChiTietVe.hanh_ly
    ).outerjoin(
        KhuyenMai, KhuyenMai.ma_KM == DonHang.ma_KM
    ).join(
        sb_di, TuyenBay.san_bay_di == sb_di.ma_san_bay
    ).join(
        sb_den, TuyenBay.san_bay_den == sb_den.ma_san_bay
    ).filter(
        DonHang.trang_thai == 'SUCCESS'
    )

    # Lọc theo tháng nếu tham số month được cung cấp
    if month is not None:
        query = query.filter(func.extract('month', DonHang.ngay_dat_DH) == month)

    # Lọc theo năm nếu tham số year được cung cấp
    if year is not None:
        query = query.filter(func.extract('year', DonHang.ngay_dat_DH) == year)

    query = query.group_by(
        TuyenBay.ma_tuyen_bay, sb_di.ten_san_bay, sb_den.ten_san_bay
    ).order_by(
        func.sum(ChiTietVe.gia_ve + func.coalesce(HanhLy.chi_phi, 0) -
                 (ChiTietVe.gia_ve * func.coalesce(KhuyenMai.ty_le_giam, 0))).desc()
    )

    return query.all()


def get_total_income_per_month(session, year=None):
    if year is None:
        year = datetime.now().year

    query = session.query(
        func.extract('month', DonHang.ngay_dat_DH).label('Month'),
        func.sum(DonHang.tong_gia_tri_DH).label('TotalIncome')
    ).filter(
        func.extract('year', DonHang.ngay_dat_DH) == year,  # Lọc theo năm
        DonHang.trang_thai == 'SUCCESS'
    ).group_by(
        func.extract('month', DonHang.ngay_dat_DH)
    ).order_by(
        func.extract('month', DonHang.ngay_dat_DH)
    )

    return query.all()

def get_total_income_per_airline(session, month=None, year=None):
    query = session.query(
        HangMayBay.so_hieu_hangmb.label('MaHangMayBay'),
        HangMayBay.ten_hang.label('TenHangMayBay'),
        func.round(func.sum(
            ChiTietVe.gia_ve + func.coalesce(HanhLy.chi_phi, 0) -
            (ChiTietVe.gia_ve * func.coalesce(KhuyenMai.ty_le_giam, 0))
        ), 0).label('TongDoanhThu')
    ).select_from(ChuyenBay).join(
        MayBay, MayBay.so_hieu_mb == ChuyenBay.may_bay
    ).join(
        HangMayBay, MayBay.hang_may_bay_ID == HangMayBay.so_hieu_hangmb
    ).join(
        TuyenBay, ChuyenBay.tuyen_bay == TuyenBay.ma_tuyen_bay
    ).join(
        ChiTietVe, ChiTietVe.ma_chuyen_bay == ChuyenBay.ma_chuyen_bay
    ).join(
        Ve, Ve.ma_ve == ChiTietVe.ma_ve
    ).join(
        DonHang, DonHang.ma_DH == Ve.ma_don_hang
    ).outerjoin(
        HanhLy, HanhLy.ma_HL == ChiTietVe.hanh_ly
    ).outerjoin(
        KhuyenMai, KhuyenMai.ma_KM == DonHang.ma_KM
    ).filter(
        DonHang.trang_thai == 'SUCCESS'
    )

    # Lọc theo tháng nếu tham số month được cung cấp
    if month is not None:
        query = query.filter(func.extract('month', DonHang.ngay_dat_DH) == month)

    # Lọc theo năm nếu tham số year được cung cấp
    if year is not None:
        query = query.filter(func.extract('year', DonHang.ngay_dat_DH) == year)

    query = query.group_by(
        HangMayBay.so_hieu_hangmb, HangMayBay.ten_hang
    ).order_by(
        func.sum(
            ChiTietVe.gia_ve + func.coalesce(HanhLy.chi_phi, 0) -
            (ChiTietVe.gia_ve * func.coalesce(KhuyenMai.ty_le_giam, 0))
        ).desc()
    )

    return query.all()




if __name__ == '__main__':
    with app.app_context():
        # print(get_total_income_per_route(db.session, month=12, year=2024))
        # print(get_total_income_per_month(db.session))
        print(get_total_income_per_airline(db.session))