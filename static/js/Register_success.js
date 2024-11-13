window.onload = function() {
    var countdown = 5;
    var countdownElement = document.getElementById('countdown');
    var loginUrl = "{{ url_for('login') }}";
    
    var timer = setInterval(function() {
        countdown--;
        countdownElement.textContent = countdown;
        if (countdown <= 0) {
            clearInterval(timer);
            window.location.href = loginUrl;
        }
    }, 1000);
}