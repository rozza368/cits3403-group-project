const signupForm = document.getElementById("signupForm");

signupForm.addEventListener("submit", (e) => {
    e.preventDefault();

    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    // Simulate signup (replace with real authentication logic)
    if (username && password) {
    localStorage.setItem("authToken", "dummyToken");
    window.location.href = "index.html";
    } else {
    alert("Please fill in all fields.");
    }
});