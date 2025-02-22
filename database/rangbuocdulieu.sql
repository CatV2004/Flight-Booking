-- Quy định: Chỉ có tối đa 10 sân bay
DELIMITER $$
create trigger them_san_bay_moi
after insert on sanbay
for each row
begin
	declare soLuongSanBay int;
    select count(*) into soLuongSanBay
    from sanbay;
    
    if soLuongSanBay >= 10 then
		SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Không thể thêm sân bay: Đã đạt giới hạn tối đa là 10 sân bay.';
	end if;
end$$
DELIMITER ;

-- Quy định: thời gian bay tối thiểu 30 phút

delimiter $$
create trigger thoi_gian_bay_toi_thieu
before insert on chuyenbay
for each row
begin
	if timestampdiff(minute, new.thoi_gian_di, new.thoi_gian_den) < 30 then
		SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Khong the them chuyen bay do thoi gian toi thieu chua toi 30p';
	end if;
    if new.thoi_gian_den < new.thoi_gian_di then
		SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Khong the them chuyen bay do thoi gian den nho hon thoi gian di';
	end if;
end$$
delimiter ;
DROP TRIGGER IF EXISTS thoi_gian_bay_toi_thieu


-- Quy dinh: có tối đa 2 sân bay trung gian và thời gian dừng từ 20-30 phút
delimiter $$
create trigger san_bay_trung_gian
before insert on sanbaytrunggian
for each row
begin
	declare so_luong_sbtg int;
    
	-- Kiem tra xem thoi gian toi thieu co nam trong khoan tu 20-30p hay khong
	if timestampdiff(minute, new.thoi_gian_tiep_tuc, new.thoi_gian_dung_chan) < (-30) then
		signal sqlstate '45000'
        set message_text = 'Thoi gian dung chan lon hon 30phut';
	end if;
    if timestampdiff(minute, new.thoi_gian_tiep_tuc, new.thoi_gian_dung_chan) > (-20) then
		signal sqlstate '45000'
        set message_text = 'Thoi gian dung chan nho hon 20 phut';
	end if;
    -- Kiem tra xem co toi da hai san bay trung gian cho mot chuyen bay ghay khong
    
    select count(*) into so_luong_sbtg
    from sanbaytrunggian
    where sanbaytrunggian.ma_chuyen_bay = new.ma_chuyen_bay;
    
    if so_luong_sbtg = 2 then
		signal sqlstate '45000'
        set message_text = 'So luong san bay trung gian cua chuyen bay nay da la 2';
	end if;
end$$
delimiter ;

drop trigger if exists san_bay_trung_gian

-- Quy định: Chỉ bán vé còn chổ và bán vé cho các chuyến bay trước 4h trước khi chuyến bay khới hành
delimiter $$
create trigger them_chi_tiet_ve_khi_ban
before insert on chitietve
for each row
begin
	declare thoi_gian_bay datetime;
      
	if (select g.trang_thai from ghe g where new.ghe = g.ma_ghe) = 1 then
		signal sqlstate '45000'
        set message_text = 'Ghe da co nguoi dat cho';
    end if;
    
    select distinct thoi_gian_di into thoi_gian_bay
    from chuyenbay c
    where c.ma_chuyen_bay = new.ma_chuyen_bay;
    
    if timestampdiff(hour, now(), thoi_gian_bay) < 4 then
		signal sqlstate '45000'
        set message_text = 'Chuyen bay se bay it hon 4 gio nua nen khong the dat cho'; 
    end if;
end$$
delimiter ;

drop trigger if exists them_chi_tiet_ve_khi_ban

-- khách hàng chỉ được đặt những vé còn chổ và chỉ đặt cho các chuyến bay trước 12h lúc khởi hành
delimiter $$
create trigger them_chi_tiet_ve_khi_mua
before insert on chitietve
for each row
begin
	declare thoi_gian_bay datetime;
      
	if (select g.trang_thai from ghe g where new.ghe = g.ma_ghe) = 1 then
		signal sqlstate '45000'
        set message_text = 'Ghe da co nguoi dat cho';
    end if;
    
    select distinct thoi_gian_di into thoi_gian_bay
    from chuyenbay c, ve v, donhang d
    where c.ma_chuyen_bay = new.ma_chuyen_bay and v.ma_ve = new.ma_ve and v.ma_don_hang = d.ma_DH and d.nhan_vien is null;
    
    if timestampdiff(hour, now(), thoi_gian_bay) < 12 then
		signal sqlstate '45000'
        set message_text = 'Chuyen bay se bay it hon 12 gio nua nen khong the dat cho'; 
    end if;
end$$
delimiter ;

drop trigger if exists them_chi_tiet_ve_khi_mua