
document.addEventListener('DOMContentLoaded', function() {
    // Lấy tất cả các nút Chi tiết
    const toggleButtons = document.querySelectorAll('.detail-toggle');

    toggleButtons.forEach(function(toggleButton) {
        // Khi người dùng nhấn vào "Chi tiết"
        toggleButton.addEventListener('click', function() {
            // Lấy tất cả các nút Chi tiết khác và xóa lớp active
            toggleButtons.forEach(function(button) {
                if (button !== toggleButton) {
                    button.classList.remove('active');  // Xóa hiệu ứng active của nút khác
                }
            });

            // Toggle trạng thái active cho nút Chi tiết vừa nhấn
            toggleButton.classList.toggle('active');

            // Tìm phần chi tiết tương ứng
            const detailCard = toggleButton.closest('.flight-card').querySelector('.detail-flight-card');

            // Ẩn tất cả các phần detail-flight-card khác
            document.querySelectorAll('.detail-flight-card').forEach(function(card) {
                if (card !== detailCard) {
                    card.style.display = 'none';
                }
            });

            // Kiểm tra xem phần chi tiết đã được mở hay chưa
            if (detailCard.style.display === 'none' || detailCard.style.display === '') {
                // Nếu phần chi tiết chưa hiển thị, hiển thị nó
                detailCard.style.display = 'block';
            } else {
                // Nếu phần chi tiết đang hiển thị, ẩn nó
                detailCard.style.display = 'none';
            }
        });
    });



    // Lấy phần tử arrow-icon và ul airline-list
    const arrowIcon = document.querySelector('.arrow-icon');
    const arrowIcon2 = document.querySelector('.arrow-icon2');
    const airlineList = document.querySelector('.airline-list');
    const flight_time = document.querySelector('.container-main')

    // Khi nhấn vào icon, thực hiện ẩn/hiện airline-list và quay icon
    arrowIcon.addEventListener('click', function() {
        // Toggle giữa việc ẩn/hiện danh sách
        airlineList.classList.toggle('hidden');

        // Toggle hiệu ứng quay cho icon
        arrowIcon.classList.toggle('rotate');
    });

    // Khi nhấn vào icon, thực hiện ẩn/hiện flight-time và quay icon
    arrowIcon2.addEventListener('click', function() {
        // Toggle giữa việc ẩn/hiện danh sách
        flight_time.classList.toggle('hidden')

        // Toggle hiệu ứng quay cho icon
        arrowIcon2.classList.toggle('rotate')
    });


    function updateFilterMaxHeight() {
        const tripCard = document.querySelector('.trip-card');
        const filterSection = document.querySelector('.filter-container');

        if (tripCard && filterSection) {
            const tripCardHeight = tripCard.offsetHeight; // Chiều cao thẻ .trip-card
            const windowHeight = window.innerHeight; // Chiều cao màn hình hiện tại

            // Tính toán max-height
            const maxHeight = windowHeight - tripCardHeight;

            // Cập nhật max-height
            filterSection.style.maxHeight = `${maxHeight - 100}px`;
        }
    }

    // Gọi hàm khi tải trang hoặc khi thay đổi kích thước cửa sổ
    window.addEventListener('load', updateFilterMaxHeight);
    window.addEventListener('resize', updateFilterMaxHeight);




    const slider1 = document.getElementById("slider-1");
    const slider2 = document.getElementById("slider-2");
    const rangeProgress = document.getElementById("range-progress");
    const sliderOutput = document.getElementById("slider-output");

    function updateSlider() {
        const min = Math.min(slider1.value, slider2.value);
        const max = Math.max(slider1.value, slider2.value);

        // Cập nhật giá trị hiển thị
        sliderOutput.textContent = `${min}h - ${max}h`;

        // Cập nhật vị trí và độ dài của thanh progress
        const percentMin = (min / slider1.max) * 100;
        const percentMax = (max / slider1.max) * 100;

        rangeProgress.style.left = `${percentMin}%`;
        rangeProgress.style.width = `${percentMax - percentMin}%`;
    }

    // Thêm sự kiện trượt cho cả hai slider
    slider1.addEventListener("input", updateSlider);
    slider2.addEventListener("input", updateSlider);

    // Khởi tạo
    updateSlider();


    // Lấy phần tử cần thay đổi
    const containerLeft = document.querySelector('.container-left');
    const header = document.querySelector('.header');
    const footer = document.querySelector('.footer');


    // Hàm cập nhật vị trí top của phần tử khi cuộn trang
    function updatePosition() {
        // Lấy chiều cao của cửa sổ trình duyệt
        const viewportHeight = window.innerHeight;

        // Lấy chiều cao của header và footer từ JavaScript
        const headerHeight = header.offsetHeight; // Lấy chiều cao thực tế của header
        const footerHeight = footer.offsetHeight; // Lấy chiều cao thực tế của footer

        // Lấy chiều cao của body
        const bodyHeight = document.body.scrollHeight;
        // Lấy vị trí cuộn trang theo trục dọc (vertical)
        const scrollPosition = window.scrollY;

        // Tính toán chiều cao của container-left
        const containerHeight = viewportHeight - headerHeight - footerHeight + 150;

        // Cập nhật giá trị top của phần tử (có thể thay đổi giá trị ở đây theo yêu cầu)
        containerLeft.style.top = `${Math.max(scrollPosition, 0)}px`;

        // Lấy vị trí bottom của footer (vị trí cuối cùng của footer trên trang)
        const footerBottom = footer.getBoundingClientRect().bottom;

        containerLeft.style.height = `${Math.max(footerBottom - headerHeight - 200, 0)}px`;  // Dừng lại trước footer


    }
    // Lắng nghe sự kiện cuộn
    window.addEventListener('scroll', updatePosition);


    // Tìm button "Đặt lại" và thêm sự kiện click
    const resetButton = document.querySelector('.reset-button');
    resetButton.addEventListener('click', function() {
        resetForm();
    });

    // Hàm reset form
    function resetForm() {
        // Reset tất cả checkbox
        const checkboxes = document.querySelectorAll('.airline-filter');
        checkboxes.forEach(checkbox => {
            checkbox.checked = false; // Đặt lại trạng thái checkbox
        });

        // Reset tất cả button (chọn giờ cất cánh và hạ cánh)
        const timeButtons = document.querySelectorAll('.time-box');
        timeButtons.forEach(button => {
            button.classList.remove('active'); // Gỡ bỏ lớp 'active' khi nhấn vào
        });

        // Reset slider
        const sliders = document.querySelectorAll('.range-slider');
        sliders.forEach(slider => {
            slider.value = slider.defaultValue; // Đặt lại giá trị slider về mặc định
        });

        // Xóa tham số 'selected_airlines' và 'departure_time' trong URL
        const url = new URL(window.location.href);
        url.searchParams.delete('selected_airlines');
        url.searchParams.delete('departure_time');

        // Tải lại trang với URL đã thay đổi (không có các tham số lọc)
        window.location.href = url.toString();

    }


    document.querySelectorAll('.choose-btn').forEach(button => {
        button.addEventListener('click', function(event) {
            // Lấy dữ liệu chuyến bay từ data-flight
            const flightData = JSON.parse(event.target.getAttribute('data-flight'));

            // Lấy giá trị round-trip từ data-round-trip
            const roundTrip = event.target.getAttribute('data-round-trip') === 'True'; // Chuyển đổi thành boolean

            console.log(roundTrip)

            // Gọi hàm selectFlight với dữ liệu chuyến bay và roundTrip
            selectFlight(flightData, roundTrip);
        });
    });

    function selectFlight(flightData, roundTrip) {
        // Kiểm tra dữ liệu trước khi gửi
        console.log('Dữ liệu chuyến bay:', flightData);  // Kiểm tra đối tượng flightData

        fetch('/customer/info_flight', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(flightData)  // Chuyển dữ liệu thành JSON trước khi gửi
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (roundTrip) {
                    if (data.next_step === "return_flight") {
                        // Chuyến bay lượt đi đã được lưu, yêu cầu chọn chuyến khứ hồi
                        alert('Chuyến bay lượt đi đã được chọn. Vui lòng chọn chuyến bay khứ hồi.');
                        window.location.href = '/customer/flights_roundtrip'; // Tải lại trang để hiển thị chuyến bay khứ hồi
                    } else if (data.next_step === "info_customer") {
//                        alert('Đã hoàn tất chọn chuyến. Vui lòng nhấn đặt vé để tiếp tục');
                        window.location.href = '/customer/flights_roundtrip';
                    }
                }
                else {
                    window.location.href = '/customer/info_customer';  // Chuyển hướng đến trang info_customer.html
                }


            } else {
                alert('Đã xảy ra lỗi khi gửi mã sân bay.');
            }
        })
        .catch((error) => {
            console.error('Error:', error);  // Xử lý lỗi nếu có
        });
    }







});

