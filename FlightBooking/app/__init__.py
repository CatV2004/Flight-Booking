from datetime import datetime
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote
import cloudinary
from flask_login import LoginManager
from authlib.integrations.flask_client import OAuth
from flask_mail import Mail, Message
from flask_admin import Admin


# Database flight
app = Flask(__name__)

app.secret_key = 'DQ23QE@#e@@ef2#$v2#4@#Rcr2453#$2wedE1@EX1@E'
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:%s@localhost/flightbookingsystem?charset=utf8mb4" % quote("Admin@123")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config['SESSION_TYPE'] = 'filesystem'
app.config["NUMBER_STOP"] = {
    'Bay trực tiếp': 0,
    'Một điểm dừng': 1,
    'Hai điểm dừng': 2,
}
app.config["TIME_FLIGHT"] = {
    'Chuyến Bay Sáng' : 12,
    'Chuyến Bay Chiều': 18,
    'Chuyến Bay Tối': 24,
}
app.config["TICKET_CATEGORY"] ={
    "Phổ thông" : "PHOTHONG",
    "Thương gia" : "THUONGGIA"
}
app.config["TYPE_TICKET"] ={
    'Phổ Thông': "MOTCHIEU",
    'Khứ Hồi': "KHUHOI"
}
app.config["TIME_NOW"] = datetime.now()

app.config["CHOOSE_TICKET_RETURN"] = False

#API Cloudinary
cloudinary.config(cloud_name='dohsfqs6d',
                  api_key='171281981285222',
                  api_secret='2Ev1q24vbeTTFZMOOd6QxgLDB98')

# Đăng ký OAuth
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id="181179286242-9rglc8esrv8a0qcju1e5nkvbdv0fi3hr.apps.googleusercontent.com",
    client_secret="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",
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    access_token_url='https://oauth2.googleapis.com/token',
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={
        'scope': 'openid email profile',
    },
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration"  # Cung cấp metadata
)

# Các thông tin cần thiết của bạn
VNP_TMN_CODE = "W5WZNPUN"  # Mã TmnCode được cung cấp bởi VNPay
VNP_HASH_SECRET = "8GLP430V0C89HBUADCLC22VL3ZTPKDNN"  # Khóa bí mật được cung cấp bởi VNPay
VNP_URL = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"  # URL Sandbox (thử nghiệm)

VNP_RETURN_URL  = "https://6649-125-235-239-168.ngrok-free.app/customer/vnpay_return"  # URL khách hàng quay lại sau thanh toán
CALLBACK_URL = "https://6649-125-235-239-168.ngrok-free.app/customer/vnpay_callback"  # URL nhận Webhook từ VNPay



app.config["MAIL_SERVER"] = 'smtp.gmail.com'
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] =True
app.config["MAIL_USERNAME"] = 'thanhdan27102004sayhi@gmail.com'
app.config["MAIL_PASSWORD"] = 'egtzwbkzzyhnscjn'



mail = Mail(app)
login = LoginManager(app)
db = SQLAlchemy(app)


from app.models import ChuyenBay, TuyenBay, SanBay, KhuyenMai, DieuKienKM, SanBayTrungGian, KhuVuc, HangMayBay, MayBay, \
    Ghe, DonHang, NhanVien, TaiKhoan, NguoiDung, VaiTro, HangVe, Admin as quantri, generate_unique_code, QuyDinh

from app.admin import DonHangView, KhuVucView, SanBayView, TuyenBayView, ChuyenBayView, SanBayTrungGianView, \
    HangMayBayView, MayBayView, GheView, KhuyenMaiView, DieuKienKMView, QuyDinhAdminView, NhanVienView, TaiKhoanView, \
    UserRegistrationView, LogoutView, StatsView
administrator_vp = Admin(app=app, name='FlightBooking Admin', template_mode='bootstrap4')

administrator_vp.add_view(DonHangView(DonHang, db.session, name="Đơn hàng"))
administrator_vp.add_view(KhuVucView(KhuVuc, db.session, name="Khu vực"))
administrator_vp.add_view(SanBayView(SanBay, db.session, name="Sân bay"))
administrator_vp.add_view(TuyenBayView(TuyenBay, db.session, name="Tuyến bay"))
administrator_vp.add_view(ChuyenBayView(ChuyenBay, db.session, name="Chuyến bay"))
administrator_vp.add_view(SanBayTrungGianView(SanBayTrungGian, db.session, name="Sân bay trung gian"))
administrator_vp.add_view(HangMayBayView(HangMayBay, db.session, name="Hãng máy bay"))
administrator_vp.add_view(MayBayView(MayBay,db.session, name="Máy bay"))
administrator_vp.add_view(GheView(Ghe, db.session, name="Ghế"))
administrator_vp.add_view(KhuyenMaiView(KhuyenMai, db.session, name="Khuyến mãi"))
administrator_vp.add_view(DieuKienKMView(DieuKienKM, db.session, name="Điều kiện khuyến mãi"))
administrator_vp.add_view(QuyDinhAdminView(QuyDinh, db.session))
administrator_vp.add_view(NhanVienView(NhanVien, db.session, name="Nhân Viên"))
administrator_vp.add_view(TaiKhoanView(TaiKhoan, db.session, name="Tài Khoản"))
administrator_vp.add_view(UserRegistrationView(name='Đăng ký tài khoản', endpoint='register_user'))
administrator_vp.add_view(LogoutView(name='Đăng xuất'))
administrator_vp.add_view(StatsView(name='Thống kê báo cáo', endpoint='stats'))

def generate_email_content(order_info):
    with app.app_context():  # Đảm bảo tạo application context
        return render_template('bill.html', order_info=order_info)