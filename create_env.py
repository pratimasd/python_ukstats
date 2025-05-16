# Simple script to create a clean .env file
with open('.env', 'w', encoding='ascii') as f:
    f.write('GOOGLE_API_KEY=AIzaSyDBGZDFuX4QyBFuyucgZROViXJvOBnCdgY\n')

print("Created .env file successfully") 