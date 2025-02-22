
document.addEventListener('DOMContentLoaded', function() {
    // Lấy phần tử cần thay đổi
    const containerRight = document.querySelector('.container-right');
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
        containerRight.style.top = `${Math.max(scrollPosition, 0)}px`;

        // Lấy vị trí bottom của footer (vị trí cuối cùng của footer trên trang)
        const footerBottom = footer.getBoundingClientRect().bottom;

        containerRight.style.height = `${Math.max(footerBottom - headerHeight - 300, 0)}px`;  // Dừng lại trước footer

    }
    // Lắng nghe sự kiện cuộn
    window.addEventListener('scroll', updatePosition);



    // Lấy tất cả các nút "Chi tiết"
    const detailButtons = document.querySelectorAll(".btn-detail");

    detailButtons.forEach(button => {
        button.addEventListener("click", function () {
            const flightType = button.getAttribute("data-flight-type");

            // Đóng tất cả các modal
            const modals = document.querySelectorAll(".modal");
            modals.forEach(modal => {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) {
                    modalInstance.hide();
                }
            });

            // Hiển thị modal được chọn
            const modalToShow = document.getElementById(`flightDetailModal-${flightType}`);
            if (modalToShow) {
                const modalInstance = new bootstrap.Modal(modalToShow);
                modalInstance.show();

            }
        });
    });



    const selectLuggageButton = document.querySelector(".action a");
    const luggageModal = new bootstrap.Modal(document.getElementById("luggageModal"));

    selectLuggageButton.addEventListener("click", function (e) {
        e.preventDefault(); // Ngăn chặn hành động mặc định của thẻ <a>
        luggageModal.show(); // Hiển thị modal
    });


    const updateTotalWeight = (selector, groupNameBase, passengerCount) => {
        // Lặp qua từng hành khách
        for (let i = 1; i <= passengerCount; i++) {
            const groupName = `${groupNameBase}_${i}`; // Tạo groupName theo từng hành khách
            const baggageOptions = document.querySelectorAll(`input[name="${groupName}"]`);

            // Thêm sự kiện change cho từng lựa chọn hành lý
            baggageOptions.forEach(option => {
                option.addEventListener('change', function () {
                    // Tìm đúng phần tử '.text-danger.fb' trong phạm vi hành khách hiện tại
                    const passengerContainer = this.closest(selector); // Container của hành khách
                    const totalWeightElement = passengerContainer.querySelector(`p[name="weight_${i}"]`); // Tìm thẻ <p> với tên weight_i

                    // Cập nhật trọng lượng hành lý
                    const value = this.value === "none" ? "0 kg" : `${this.value} kg`; // Nếu không chọn hành lý, hiển thị "0 kg"
                    totalWeightElement.textContent = value; // Cập nhật nội dung thẻ <p>
                });
            });
        }
    };

    // Tổng số hành khách
    const passengerCount = document.getElementById('passenger-data').dataset.passengerCount;

    // Xử lý cho chuyến đi
    updateTotalWeight('.info-lug', 'baggage_trip', passengerCount);

    // Xử lý cho chuyến về
    updateTotalWeight('.info-lug', 'baggage_return', passengerCount);



    // Đảm bảo khi nhấn nút Xác nhận thì modal sẽ đóng
    document.getElementById('confirmBtn').addEventListener('click', function() {
        // Gửi dữ liệu form nếu cần thiết
        // ... (nếu cần thực hiện việc gửi dữ liệu form qua AJAX hoặc xử lý khác)

        // Đóng modal sau khi nhấn xác nhận
        $('#luggageModal').modal('hide');
    });


    // Lắng nghe sự thay đổi của tất cả các radio button hành lý
    document.querySelectorAll('input[name^="baggage_trip_"], input[name^="baggage_return_"]').forEach(function(input) {
        input.addEventListener('change', updateLuggageIcon);
    });

    // Hàm cập nhật icon hành lý
    function updateLuggageIcon() {
        let isLuggageSelected = false;

        // Kiểm tra tất cả hành lý và xem có hành lý nào được chọn > 0 kg không
        document.querySelectorAll('input[name^="baggage_trip_"]:checked, input[name^="baggage_return_"]:checked').forEach(function(input) {
            if (parseInt(input.value) > 0) {
                isLuggageSelected = true; // Nếu có hành lý > 0 kg
            }
        });

        // Cập nhật icon
        const luggageIcon = document.querySelector('.icon'); // Lấy phần tử icon vali
        if (isLuggageSelected) {
            luggageIcon.innerHTML = '<i class="fa fa-check-circle" style="color: green;"></i>'; // Dấu tick xanh
        } else {
            luggageIcon.innerHTML = '<i class="fa fa-suitcase"></i>'; // Icon vali ban đầu
        }
    }

    // Gọi hàm kiểm tra khi trang được tải lần đầu
    updateLuggageIcon();





    // Hàm kiểm tra form
    function validateForm() {
        // Lấy tất cả các trường input cần kiểm tra
        const inputs = document.querySelectorAll('.form-control, .form-select');
        let isValid = true; // Cờ kiểm tra trạng thái hợp lệ
        let firstInvalidInput = null;

        inputs.forEach(input => {
            if (input.value.trim() === '' || input.value === 'Ngày' || input.value === 'Tháng' || input.value === 'Năm') {
                // Nếu trường trống, thêm class cảnh báo
                input.classList.add('is-invalid');

                // Đánh dấu trường đầu tiên không hợp lệ
                if (!firstInvalidInput) {
                    firstInvalidInput = input;
                }

                isValid = false;
            } else {
                // Xóa cảnh báo nếu đã nhập dữ liệu
                input.classList.remove('is-invalid');
            }
        });

        // Nếu có trường không hợp lệ, cuộn đến đó
        if (!isValid && firstInvalidInput) {
            firstInvalidInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }

        return isValid;
    }

    // Xử lý khi nhấn nút Tiếp tục
    document.querySelector('#btn-continue-info1').addEventListener('click', function (event) {
        // Ngừng hành động mặc định của form (không gửi form)
//        event.preventDefault();

        if (validateForm()) {
            // Nếu hợp lệ, hiển thị modal
            const confirmationModal = new bootstrap.Modal(document.getElementById('confirmationModal'));
            confirmationModal.show();
        }
    });

    document.getElementById("proceedButton").addEventListener("click", function () {
        const form = document.getElementById("frm-info-pas");

        // Ngăn hành vi submit mặc định của form
        event.preventDefault();

        // Sử dụng fetch để gửi dữ liệu form
        fetch(form.action, {
            method: form.method,
            body: new FormData(form),
        })
        .then(response => {
            if (response.redirected) {
                // Nếu server trả về redirect, chuyển hướng đến URL mới
            } else if (response.ok) {
                // Xử lý thành công mà không cần chuyển hướng
                window.location.href = '/customer/payment';
            } else {
                // Nếu response không thành công, xử lý lỗi
                alert("Đã xảy ra lỗi khi gửi form. Vui lòng thử lại.");
            }
        })
        .catch(error => {
            // Xử lý lỗi kết nối hoặc lỗi fetch
            console.error("Error:", error);
            alert("Đã xảy ra lỗi kết nối.");
        });
    });




});


