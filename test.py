import pytest
from flask import Flask
import app  # Import your Flask app instance here
import os

app.config = {}  # Add this line

# Define a fixture to create a test client for your Flask app
@pytest.fixture
def client():
    app.app.config['TESTING'] = True  # Access the app instance using app.app
    with app.app.test_client() as client:
        yield client

def read_expected_html_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

# Define the path to your expected HTML file in the templates directory
expected_html_file_path = os.path.join(app.app.root_path, 'templates', 'homepage.html')

# Read the content of the expected HTML file
expected_content = read_expected_html_file(expected_html_file_path)


# Write test cases for form submissions and database interactions
def test_sign_up_route(client):
    response = client.get('/sign-up')
    assert b'Enter your first name' in response.data

def test_signup_process(client):
    response = client.post('/signup-process', data={
        'fname': 'John',
        'lname': 'Doe',
        'username': 'johnddoe48895449',
        'email': 'johndoe@example.com',
        'password': 'securepassword',
        'number': '1234567890',
        'address': '123 Main St'
    }, follow_redirects=True)

    # Compare the response data with the content from the HTML file
    assert b'Welcome to the homepage' in response.data

