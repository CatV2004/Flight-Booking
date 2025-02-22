#Tổng vé
SELECT 
    tb.ma_tuyen_bay AS MaTuyenBay,
    CONCAT(sb_di.ten_san_bay, ' - ', sb_den.ten_san_bay) AS TuyenBay,
    SUM(ctv.gia_ve) AS TongThuNhap
FROM 
    TuyenBay tb
JOIN ChuyenBay cb ON tb.ma_tuyen_bay = cb.tuyen_bay
JOIN ChiTietVe ctv ON cb.ma_chuyen_bay = ctv.ma_chuyen_bay
JOIN Ve v ON ctv.ma_ve = v.ma_ve
JOIN DonHang dh ON v.ma_don_hang = dh.ma_DH
JOIN SanBay sb_di ON tb.san_bay_di = sb_di.ma_san_bay
JOIN SanBay sb_den ON tb.san_bay_den = sb_den.ma_san_bay
WHERE dh.trang_thai = 'SUCCESS'
GROUP BY tb.ma_tuyen_bay, sb_di.ten_san_bay, sb_den.ten_san_bay
ORDER BY TongThuNhap DESC;



#Tổng vé + hành lý
SELECT 
    tb.ma_tuyen_bay AS MaTuyenBay,
    CONCAT(sb_di.ten_san_bay, ' - ', sb_den.ten_san_bay) AS TuyenBay,
    SUM(ctv.gia_ve + IFNULL(hl.chi_phi, 0)) AS TongThuNhap
FROM 
    TuyenBay tb
JOIN ChuyenBay cb ON tb.ma_tuyen_bay = cb.tuyen_bay
JOIN ChiTietVe ctv ON cb.ma_chuyen_bay = ctv.ma_chuyen_bay
JOIN Ve v ON ctv.ma_ve = v.ma_ve
JOIN DonHang dh ON v.ma_don_hang = dh.ma_DH
LEFT JOIN HanhLy hl ON ctv.hanh_ly = hl.ma_HL
JOIN SanBay sb_di ON tb.san_bay_di = sb_di.ma_san_bay
JOIN SanBay sb_den ON tb.san_bay_den = sb_den.ma_san_bay
WHERE dh.trang_thai = 'SUCCESS'
GROUP BY tb.ma_tuyen_bay, sb_di.ten_san_bay, sb_den.ten_san_bay
ORDER BY TongThuNhap DESC;









#tổng vé + hành lý + giảm giá
SELECT 
    tb.ma_tuyen_bay AS MaTuyenBay,
    CONCAT(sb_di.ten_san_bay, ' - ', sb_den.ten_san_bay) AS TuyenBay,
    SUM((ctv.gia_ve * (1 - IFNULL(km.ty_le_giam, 0))) + IFNULL(hl.chi_phi, 0)) AS TongThuNhap
FROM 
    TuyenBay tb
JOIN ChuyenBay cb ON tb.ma_tuyen_bay = cb.tuyen_bay
JOIN ChiTietVe ctv ON cb.ma_chuyen_bay = ctv.ma_chuyen_bay
JOIN Ve v ON ctv.ma_ve = v.ma_ve
JOIN DonHang dh ON v.ma_don_hang = dh.ma_DH
LEFT JOIN HanhLy hl ON ctv.hanh_ly = hl.ma_HL
LEFT JOIN KhuyenMai km ON dh.ma_KM = km.ma_KM
JOIN SanBay sb_di ON tb.san_bay_di = sb_di.ma_san_bay
JOIN SanBay sb_den ON tb.san_bay_den = sb_den.ma_san_bay
WHERE dh.trang_thai = 'SUCCESS'
GROUP BY tb.ma_tuyen_bay, sb_di.ten_san_bay, sb_den.ten_san_bay
ORDER BY TongThuNhap DESC;







#Detail
SELECT 
    tb.ma_tuyen_bay AS MaTuyenBay,
    CONCAT(sb_di.ten_san_bay, ' - ', sb_den.ten_san_bay) AS TuyenBay,
    ROUND(SUM(ctv.gia_ve), 0) AS TongTienVe,
    ROUND(SUM(IFNULL(hl.chi_phi, 0)), 0) AS TongTienHanhLy,
    ROUND(SUM(ctv.gia_ve * IFNULL(km.ty_le_giam, 0)), 0) AS TongTienGiamGia,
    ROUND(SUM(ctv.gia_ve + IFNULL(hl.chi_phi, 0) - (ctv.gia_ve * IFNULL(km.ty_le_giam, 0))), 0) AS TongThuNhap
FROM 
    TuyenBay tb
JOIN ChuyenBay cb ON tb.ma_tuyen_bay = cb.tuyen_bay
JOIN ChiTietVe ctv ON cb.ma_chuyen_bay = ctv.ma_chuyen_bay
JOIN Ve v ON ctv.ma_ve = v.ma_ve
JOIN DonHang dh ON v.ma_don_hang = dh.ma_DH
LEFT JOIN HanhLy hl ON ctv.hanh_ly = hl.ma_HL
LEFT JOIN KhuyenMai km ON dh.ma_KM = km.ma_KM
JOIN SanBay sb_di ON tb.san_bay_di = sb_di.ma_san_bay
JOIN SanBay sb_den ON tb.san_bay_den = sb_den.ma_san_bay
WHERE dh.trang_thai = 'SUCCESS'
GROUP BY tb.ma_tuyen_bay, sb_di.ten_san_bay, sb_den.ten_san_bay
ORDER BY TongThuNhap DESC;
