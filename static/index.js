
document.addEventListener("DOMContentLoaded", function () {

    // Xabarlarni avtomatik yopish
    const alerts = document.querySelectorAll(".alert");

    alerts.forEach(function (alert) {
        setTimeout(function () {
            if (document.body.contains(alert)) {
                const instance = bootstrap.Alert.getOrCreateInstance(alert);
                instance.close();
            }
        }, 5000);
    });

    // O'chirishdan oldin tasdiqlash
    const deleteForms = document.querySelectorAll(
        'form[action*="/products/delete/"]'
    );

    deleteForms.forEach(function (form) {
        form.addEventListener("submit", function (event) {
            const confirmed = confirm(
                "Haqiqatan ham ushbu mahsulotni o'chirmoqchimisiz?"
            );

            if (!confirmed) {
                event.preventDefault();
            }
        });
    });

    // Forma yuborilayotganda tugmani vaqtincha bloklash
    const forms = document.querySelectorAll("form");

    forms.forEach(function (form) {
        form.addEventListener("submit", function () {
            if (!form.checkValidity()) {
                return;
            }

            const button = form.querySelector(
                'button[type="submit"]'
            );

            if (button) {
                button.disabled = true;
                button.innerHTML =
                    '<span class="spinner-border spinner-border-sm me-2"></span>Yuklanmoqda...';
            }
        });
    });

    console.log("Ombor Pro JavaScript muvaffaqiyatli ishga tushdi!");

});
