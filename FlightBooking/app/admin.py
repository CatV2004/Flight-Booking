import hashlib
from datetime import datetime

from flask_admin.contrib.sqla.fields import QuerySelectField

from app.models import ChuyenBay, TuyenBay, SanBay, KhuyenMai, DieuKienKM, SanBayTrungGian, KhuVuc, HangMayBay, MayBay, \
    Ghe, DonHang, NhanVien, TaiKhoan, NguoiDung, VaiTro, HangVe, Admin as quantri, generate_unique_code, QuyDinh
from flask_admin.contrib.sqla import ModelView
from flask_admin import BaseView,expose
from app import app, db
from flask_login import logout_user, current_user, login_user
from flask import redirect, request, jsonify, url_for, flash

from app.templates.admin.dao_admin import get_total_income_per_route, get_total_income_per_month, \
    get_total_income_per_airline




@app.before_request
def check_admin_access():
    # Chỉ kiểm tra các đường dẫn bắt đầu bằng /admin nhưng không phải /admin/logout
    if request.path.startswith('/admin') and not request.path == '/admin/logout':
        # Kiểm tra quyền truy cập
        if not current_user.is_authenticated or current_user.tai_khoan.vai_tro != VaiTro.ADMIN:
            logout_user()
            flash("Bạn không có quyền truy cập vào trang quản trị.", "danger")
            return redirect(url_for('login_view'))


class AuthenticatedBaseView(ModelView):
    def is_accessible(self):
        if current_user.is_authenticated and current_user.tai_khoan.vai_tro == VaiTro.ADMIN:
            return True

class logBaseView(BaseView):
    def is_accessible(self):
        if current_user.is_authenticated and current_user.tai_khoan.vai_tro == VaiTro.ADMIN:
            return True

class LogoutView(logBaseView):
    @expose('/')
    def index(self):
        logout_user()
        flash("Bạn đã đăng xuất thành công.", "success")
        return redirect('/admin')

class StatsView(logBaseView):
    @expose('/')
    def index(self):
        month = request.args.get('month', type=int)  # Lấy tháng từ URL query
        year = request.args.get('year', type=int)    # Lấy năm từ URL query
        current_year = datetime.now().year

        growth_chart = get_total_income_per_month(db.session)
        stats = get_total_income_per_route(db.session, month=month, year=year)
        airline_chart = get_total_income_per_airline(db.session)

        # Trả về giao diện HTML nếu không phải yêu cầu AJAX
        return self.render('admin/stats.html', stats=stats, growth_chart=growth_chart, airline_chart=airline_chart, current_year=current_year)


@app.route('/filter')
def filter_stats():
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)

    # Lấy dữ liệu phù hợp từ database
    stats = get_total_income_per_route(db.session, month=month, year=year)

    # Trả về kết quả dạng JSON
    data = [
        {
            "route_id": s[0],
            "route_name": s[1],
            "total_fare": s[2],
            "total_baggage": s[3],
            "total_discount": s[4],
            "total_revenue": s[5]
        }
        for s in stats
    ]
    return jsonify(data)


@app.route('/filter_gr')
def filter_gr():
    year_gr = request.args.get('year', type=int)

    if not year_gr:
        return jsonify({"error": "Year is required"}), 400

    growth_chart = get_total_income_per_month(db.session, year=year_gr)

    if not growth_chart:
        return jsonify([])

    data = [
        {
            "month": int(s[0]),
            "total_income": float(s[1])
        }
        for s in growth_chart
    ]

    return jsonify(data)


class UserRegistrationView(logBaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        if request.method == 'POST':
            user_type = request.form.get('user_type')  # Loại tài khoản: Admin hoặc Nhân viên
            fname = request.form.get('fname')         # Họ
            lname = request.form.get('lname')         # Tên
            email = request.form.get('email')         # Email
            username = request.form.get('username')   # Tên đăng nhập
            password = request.form.get('password')   # Mật khẩu
            hashed_password = hashlib.md5(password.encode('utf-8')).hexdigest()  # Mã hóa mật khẩu
            ngay_vao_lam = request.form.get('ngay_vao_lam')  # Ngày vào làm
            ghi_chu = request.form.get('ghi_chu')     # Ghi chú (cho nhân viên)
            kinh_nghiem = request.form.get('kinh_nghiem')  # Kinh nghiệm (cho Admin)
            luong = request.form.get('luong')         # Lương (cho nhân viên)

            try:
                # Tạo tài khoản người dùng
                if user_type == 'Admin':
                    admin_user = quantri(
                        fname=fname,
                        lname=lname,
                        email=email,
                        ngay_vao_lam=datetime.strptime(ngay_vao_lam, '%Y-%m-%d'),
                        kinh_nghiem=kinh_nghiem
                    )
                    db.session.add(admin_user)
                    db.session.flush()  # Lấy ID người dùng ngay sau khi thêm

                    tai_khoan = TaiKhoan(
                        ten_dang_nhap=username,
                        mat_khau=hashed_password,
                        vai_tro=VaiTro.ADMIN,
                        nguoi_dung_id=admin_user.id
                    )
                    db.session.add(tai_khoan)

                elif user_type == 'NhanVien':
                    nhan_vien_user = NhanVien(
                        fname=fname,
                        lname=lname,
                        email=email,
                        ngay_vao_lam=datetime.strptime(ngay_vao_lam, '%Y-%m-%d'),
                        luong=float(luong),
                        ghi_chu=ghi_chu
                    )
                    db.session.add(nhan_vien_user)
                    db.session.flush()  # Lấy ID người dùng ngay sau khi thêm

                    tai_khoan = TaiKhoan(
                        ten_dang_nhap=username,
                        mat_khau=hashed_password,
                        vai_tro=VaiTro.EMPLOYEE,
                        nguoi_dung_id=nhan_vien_user.id
                    )
                    db.session.add(tai_khoan)

                # Lưu thay đổi
                db.session.commit()
                flash('Tạo tài khoản thành công!', 'success')
                return redirect(url_for('.index'))
            except Exception as e:
                db.session.rollback()
                flash(f'Có lỗi xảy ra: {e}', 'danger')

        return self.render('admin/register_user.html')




class QuyDinhAdminView(AuthenticatedBaseView):
    # Các cột hiển thị trong bảng
    column_list = ['ma_QD', 'noi_dung', 'value']

    # Cột chỉ đọc (không cho phép chỉnh sửa, ngay cả khi thêm mới)
    form_widget_args = {
        'ma_QD': {'readonly': True}
    }
    column_labels = {
        'ma_QD': 'Mã quy định',
        'noi_dung': 'Nội dung',
        'value': 'Giá trị'
    }

    # Tùy chỉnh form tạo mới
    form_create_rules = ('noi_dung', 'value')

    # Tùy chỉnh form chỉnh sửa
    form_edit_rules = ('noi_dung', 'value')


class SanBayTrungGianView(AuthenticatedBaseView):
    edit_modal = True
    column_display_pk = True
    can_export = True
    column_searchable_list = ['ma_san_bay', 'ma_tuyen_bay', 'ma_chuyen_bay']  # Tìm kiếm theo tên sân bay
    page_size = 10
    column_filters = ['ma_san_bay', 'ma_tuyen_bay', 'ma_chuyen_bay']
    column_list = ['ma_san_bay', 'ma_tuyen_bay', 'ma_chuyen_bay', 'thoi_gian_dung_chan', 'thoi_gian_tiep_tuc', 'thu_tu', 'ghi_chu']
    column_labels = {
        'ma_san_bay': 'Mã sân bay',
        'ma_tuyen_bay': 'Mã tuyến bay',
        'ma_chuyen_bay': 'Mã chuyến bay',
        'thoi_gian_dung_chan': 'Thời gian dừng chân',
        'thoi_gian_tiep_tuc': 'Thời gian tiếp tục',
        'thu_tu': 'Thứ tự',
        'ghi_chu': 'Ghi chú'
    }




class TuyenBayView(AuthenticatedBaseView):
    edit_modal = True
    column_display_pk = True
    can_export = True
    column_searchable_list = ['san_bay_di', 'san_bay_den']  # Tìm kiếm theo tên sân bay
    page_size = 10
    column_filters = ['san_bay_di', 'san_bay_den']
    column_list = ['ma_tuyen_bay', 'san_bay_di', 'san_bay_den']
    column_labels = {
        'ma_tuyen_bay': 'Mã tuyến bay',
        'san_bay_di': 'Sân bay đi',
        'san_bay_den': 'Sân bay đến',
        'san_bay_trung_gian': 'Sân bay trung gian'
    }
    form_columns = ['ma_tuyen_bay', 'san_bay_di', 'san_bay_den']

    # Cung cấp query để hiển thị các lựa chọn
    def get_san_bay_choices():
        return SanBay.query

    form_overrides = {
        'san_bay_di': QuerySelectField,
        'san_bay_den': QuerySelectField
    }

    form_args = {
        'san_bay_di': {
            'query_factory': get_san_bay_choices,
            'allow_blank': True,
            'blank_text': 'Chọn sân bay đi'
        },
        'san_bay_den': {
            'query_factory': get_san_bay_choices,
            'allow_blank': True,
            'blank_text': 'Chọn sân bay đến'
        }
    }

class GheView(AuthenticatedBaseView):
    edit_modal = True
    column_display_pk = True
    can_export = True
    column_searchable_list = ['may_bay']
    page_size = 10
    column_filters = ['hang_ve', 'vi_tri', 'may_bay', 'gia_ghe', 'trang_thai']
    column_list = ['ma_ghe', 'hang_ve', 'vi_tri', 'may_bay', 'gia_ghe', 'trang_thai']
    column_labels = {
        'ma_ghe': 'Mã ghế',
        'hang_ve': 'Hạng vé',
        'may_bay': 'Máy bay',
        'gia_ghe': 'Giá ghế',
        'trang_thai': 'Trạng thái',
    }

    form_excluded_columns = ['chi_tiet_ve','trang_thai']

    def on_model_change(self, form, model, is_created):
        if is_created:
            if isinstance(model.hang_ve, str):
                try:
                    model.hang_ve = HangVe[model.hang_ve]  # Chuyển chuỗi thành Enum
                except KeyError:
                    raise ValueError(f"Hạng vé '{model.hang_ve}' không hợp lệ.")

            if model.hang_ve not in [HangVe.PHOTHONG, HangVe.THUONGGIA]:
                raise ValueError(f"Hạng vé '{model.hang_ve}' không hợp lệ.")



            return super(GheView, self).on_model_change(form, model, is_created)


class MayBayView(AuthenticatedBaseView):
    edit_modal = True
    column_display_pk = True
    can_export = True
    column_searchable_list = ['hang_may_bay_ID']
    page_size = 10
    column_filters = ['so_hieu_mb', 'hang_may_bay_ID']
    column_list = ['so_hieu_mb', 'hang_may_bay_ID']
    column_labels = {
        'so_hieu_mb': 'Số hiệu máy bay',
        'hang_may_bay_ID': 'Hãng máy bay',
    }
    form_excluded_columns = ['ghe', 'chuyen_bay']



class HangMayBayView(AuthenticatedBaseView):
    edit_modal = True
    column_display_pk = True
    can_export = True
    column_searchable_list = ['ten_hang']
    page_size = 10
    column_filters = ['ten_hang','so_hieu_hangmb']
    column_list = ['so_hieu_hangmb', 'ten_hang', 'lo_go', 'may_bay']
    column_exclude_list = ['may_bay']
    column_labels = {
        'so_hieu_hangmb':'Số hiệu hãng máy bay',
        'ten_hang': 'Tên hãng',
        'lo_go': 'Hình ảnh (logo)',
    }
    form_excluded_columns = ['may_bay']
    form_columns = ['so_hieu_hangmb', 'ten_hang', 'lo_go']


class KhuVucView(AuthenticatedBaseView):
    edit_modal = True
    column_display_pk = True
    can_export = True
    column_searchable_list = ['ma_khu_vuc','ten_khu_vuc']
    page_size = 10
    column_filters = ['ma_khu_vuc','ten_khu_vuc']
    column_list = ['ma_khu_vuc','ten_khu_vuc']
    column_labels = {
        'ma_khu_vuc': 'Mã khu vực',
        'ten_khu_vuc': 'Tên khu vực'
    }
    form_columns = ['ma_khu_vuc', 'ten_khu_vuc']


class SanBayView(AuthenticatedBaseView):
    edit_modal = True
    can_export = True
    column_display_pk = True
    column_searchable_list = ['dia_diem','ten_san_bay']
    page_size = 10
    column_filters = ['ten_san_bay','dia_diem']
    column_list = ['ma_san_bay','ten_san_bay','dia_diem','ma_khu_vuc']
    column_labels = {
        'ma_san_bay':'Mã sân bay',
        'ten_san_bay': 'Tên sân bay',
        'dia_diem': 'Địa điểm',
        'ma_khu_vuc': 'Mã khu vực'
    }
    form_columns = ['ma_san_bay', 'ten_san_bay', 'dia_diem', 'ma_khu_vuc']
    # Sử dụng QuerySelectField để hiển thị listbox
    form_overrides = {
        'ma_khu_vuc': QuerySelectField
    }

    # Cung cấp query để hiển thị các lựa chọn
    def get_khu_vuc_choices():
        return KhuVuc.query

    form_args = {
        'ma_khu_vuc': {
            'query_factory': get_khu_vuc_choices,
            'allow_blank': True,
            'blank_text': 'Chọn một khu vực'
        }
    }

class ChuyenBayView(AuthenticatedBaseView):
    can_view_details = True
    column_display_pk = True
    edit_modal = True
    details_modal = True
    can_export = True
    column_searchable_list = ['may_bay']
    page_size = 10
    column_filters = ['may_bay', 'tuyen_bay','thoi_gian_di','thoi_gian_den']
    column_list = ['ma_chuyen_bay', 'may_bay', 'tuyen_bay', 'lich_bay', 'thoi_gian_di', 'thoi_gian_den']
    column_exclude_list = ['lich_bay']
    column_labels = {
        'ma_chuyen_bay': 'Mã chuyến bay',
        'may_bay': 'Mã máy bay',
        'tuyen_bay': 'Mã tuyến bay',
        'thoi_gian_di': 'Thời gian đi',
        'thoi_gian_den': 'Thời gian đến'
    }
    form_columns = ['ma_chuyen_bay', 'may_bay', 'tuyen_bay', 'thoi_gian_di', 'thoi_gian_den']

    # Query factories cho listbox
    def get_may_bay_choices():
        return MayBay.query

    def get_tuyen_bay_choices():
        return TuyenBay.query

    form_overrides = {
        'may_bay': QuerySelectField,
        'tuyen_bay': QuerySelectField
    }

    form_args = {
        'may_bay': {
            'query_factory': get_may_bay_choices,
            'allow_blank': True,
            'blank_text': 'Chọn một máy bay'
        },
        'tuyen_bay': {
            'query_factory': get_tuyen_bay_choices,
            'allow_blank': True,
            'blank_text': 'Chọn một tuyến bay'
        }
    }

class DonHangView(AuthenticatedBaseView):
    can_create = False
    can_view_details = True
    details_modal = True
    can_edit = False
    column_display_pk = True
    can_export = True
    column_searchable_list = ['nhan_vien']
    page_size = 10
    column_filters = ['nhan_vien','ngay_dat_DH','trang_thai']
    column_list = ['ma_DH','khach_hang','nhan_vien','so_luong_ve','ma_KM','ngay_dat_DH', 'tong_gia_tri_DH', 'trang_thai']
    column_labels = {
        'ma_DH': 'Mã đơn hàng',
        'khach_hang': 'Mã hành khách',
        'nhan_vien': 'Mã nhân viên',
        'so_luong_ve': 'Số lượng vé',
        'ma_KM': 'Mã khuyến mãi',
        'ngay_dat_DH': 'Ngày đặt đơn hàng',
        'tong_gia_tri_DH': 'Tổng giá trị đơn hàng',
        'trang_thai': 'Trạng thái'
    }


class KhuyenMaiView(AuthenticatedBaseView):
    edit_modal = True
    column_display_pk = True
    can_export = True
    column_searchable_list = ['ma_KM']
    page_size = 10
    column_filters = ['ma_KM', 'ngay_bat_dau', 'ngay_ket_thuc']
    column_list = ['ma_KM', 'mo_ta', 'ty_le_giam', 'ngay_bat_dau', 'ngay_ket_thuc']
    column_labels = {
        'ma_KM': 'Mã khuyến mãi',
        'mo_ta': 'Mô tả',
        'ty_le_giam': 'Tỷ lệ giảm',
        'ngay_bat_dau': 'Ngày bắt đầu',
        'ngay_ket_thuc': 'Ngày kết thúc',
    }
    form_columns = ['ma_KM', 'mo_ta', 'ty_le_giam', 'ngay_bat_dau', 'ngay_ket_thuc', 'dieu_kien_KM']



class DieuKienKMView(AuthenticatedBaseView):
    edit_modal = True
    column_display_pk = True
    can_export = True
    column_searchable_list = ['ma_DK']
    page_size = 10
    column_list = ['ma_DK', 'noi_dung', 'ghi_chu']
    column_labels = {
        'ma_DK': 'Mã điều kiện',
        'noi_dung': 'Nội dung',
        'ghi_chu': 'Ghi chú',
    }
    form_columns = ['ma_DK', 'noi_dung', 'ghi_chu']



class NhanVienView(AuthenticatedBaseView):
    can_create = False
    can_edit = True
    can_delete = True
    column_filters = ['fname', 'ngay_vao_lam', 'so_dien_thoai', 'so_CCCD']

    column_display_pk = True
    column_list = ['id', 'fname', 'lname', 'email', 'luong', 'ngay_vao_lam', 'so_dien_thoai', 'so_CCCD']
    column_labels = {
        'id': 'ID',
        'fname': 'Họ',
        'lname': 'Tên',
        'email': 'Email',
        'luong': 'Lương',
        'ngay_vao_lam': 'Ngày vào làm',
        'so_dien_thoai': 'Số điện thoại',
        'so_CCCD': 'Số CCCD',
    }

    form_columns = ['fname', 'lname', 'email', 'luong', 'ngay_vao_lam', 'so_dien_thoai', 'so_CCCD']

    # Băm mật khẩu với hashlib.md5
    def hash_password(self, password):
        return hashlib.md5(password.encode('utf-8')).hexdigest()

    # Sử dụng trong `on_model_change`:
    def on_model_change(self, form, model, is_created):
        if is_created or form.mat_khau.data != model.mat_khau:
            model.mat_khau = self.hash_password(form.mat_khau.data)




class TaiKhoanView(AuthenticatedBaseView):
    can_create = False
    can_edit = True
    can_delete = True

    column_display_pk = True
    column_list = ['id', 'ten_dang_nhap', 'trang_thai', 'vai_tro', 'nguoi_dung_id']
    column_labels = {
        'id': 'ID Tài khoản',
        'ten_dang_nhap': 'Tên đăng nhập',
        'mat_khau': 'Mật khẩu',
        'trang_thai': 'Trạng thái',
        'vai_tro': 'Vai trò',
        'nguoi_dung_id': 'Người dùng'
    }

    form_columns = ['ten_dang_nhap', 'mat_khau', 'trang_thai', 'vai_tro', 'nguoi_dung_id']

    # Dropdown chọn người dùng
    form_args = {
        'nguoi_dung_id': {
            'query_factory': lambda: db.session.query(NguoiDung).all(),
            'allow_blank': True,
            'blank_text': 'Chọn người dùng'
        },
        'mat_khau': {'render_kw': {'type': 'password'}},  # Sử dụng type=password để ẩn mật khẩu
    }

    # Băm mật khẩu với hashlib.md5
    def hash_password(self, password):
        return hashlib.md5(password.encode('utf-8')).hexdigest()

    # Sử dụng trong `on_model_change`:
    def on_model_change(self, form, model, is_created):
        if is_created or form.mat_khau.data != model.mat_khau:
            model.mat_khau = self.hash_password(form.mat_khau.data)








