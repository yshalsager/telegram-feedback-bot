window.Telegram.WebApp.ready();

const tg = window.Telegram.WebApp;
const userInfoDiv = document.getElementById('user-info');

// Check if initData is available
if (tg.initData) {
    // Send initData to the backend for validation
    fetch('/app/validate_user/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ initData: tg.initData }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success' && data.user) {
            const user = data.user;
            userInfoDiv.innerHTML = `
                <p><b>Validation Successful!</b></p>
                <p>Welcome, ${user.first_name} ${user.last_name || ''} (@${user.username})</p>
                <p>Your User ID: ${user.id}</p>
            `;
        } else {
            userInfoDiv.textContent = `Authentication failed: ${data.message || 'Unknown error'}`;
        }
        // Make the Mini App responsive to the Telegram theme
        tg.expand();
    })
    .catch(error => {
        console.error('Error:', error);
        userInfoDiv.textContent = 'An error occurred during validation.';
    });
} else {
    userInfoDiv.textContent = "Welcome! It seems you're accessing this outside of Telegram.";
}