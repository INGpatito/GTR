const https = require('https');

const data = JSON.stringify({
    email: 'admin@gtr.com', // Replace with a user email
    password: 'password' // We don't have the password, we can generate a temporary dummy account
});

const req = https.request('https://papoys.me/api/login', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Content-Length': data.length
    }
}, (res) => {
    let responseData = '';
    res.on('data', chunk => responseData += chunk);
    res.on('end', () => console.log('LOGIN:', responseData));
});

req.write(data);
req.end();
