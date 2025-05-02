const loginForm = document.getElementById("loginForm");
loginForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    // Simulate login (replace with real authentication logic)
    if (username && password) {
    localStorage.setItem("authToken", "dummyToken");
    window.location.href = "/"; // Redirect to home page
    } else {
    alert("Invalid username or password.");
    }
});