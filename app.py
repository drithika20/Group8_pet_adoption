from flask import Flask, render_template
import sqlite3
import os
from flask import Flask, request, render_template, redirect, url_for,jsonify,session
from flask_session import Session

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'  # Use filesystem-based session
Session(app)
UPLOAD_FOLDER = 'static/images/foundpets'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
@app.route("/")
def index():
    session.pop('user', None)
    return render_template("index.html")
@app.route("/forgotPassword")
def forgotPassword():
    return render_template("forgot-password.html")
@app.route('/admin')
def admin():
    conn = sqlite3.connect('petadoption.sqlite')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM lostPets')
    lostPets=cursor.fetchall()
    cursor.execute('SELECT * FROM userDetails')
    users=cursor.fetchall()
    cursor.execute('SELECT * FROM pets')
    pets=cursor.fetchall()
    cursor.execute('SELECT * FROM contactUs')
    contact_requests=cursor.fetchall()
    cursor.execute('SELECT * FROM adoptionRequests')
    adoption_requests=cursor.fetchall()
    return render_template("admin.html", pets=pets, lost_pets=lostPets, users=users,contact_requests=contact_requests,adoption_requests=adoption_requests)
@app.route("/sign-up")
def sign_up():
    return render_template("sign-up.html")
@app.route("/contactUs")
def contact_us():
    return render_template("contact_us.html")

@app.route("/AdoptablePets")
def list():
    return render_template("list.html")

@app.route("/report-lost-pet")
def lost_pet():
    return render_template("report-lost-pet.html")
@app.route("/foundPets")
def found_pets():
    missing_pets_data = get_missing_pets_from_db()
    
    return render_template("found-pets.html",missing_pets=missing_pets_data)
@app.route("/profile")
def profile():
    conn = sqlite3.connect('petadoption.sqlite')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM userDetails WHERE username=?", (session['user'],))
    user_info = cursor.fetchone()
    conn.close()

    if user_info:
        fname = user_info[1]
        lname = user_info[2]
        username = user_info[3]
        cellno = user_info[5]
        address = user_info[6]
        password = user_info[4]
        email = user_info[7]

        return render_template('profile.html', fname=fname, lname=lname, username=username, cellno=cellno,
                               address=address, password=password, email=email, uname=username)
    else:
        # Handle the case when the user is not found in the database
        return render_template('error.html', error_message="User not found")

@app.route('/contact-us-process', methods=['POST'])
def contact_us_process():
    if request.method == 'POST':
        # Retrieve form data
        name = request.form['contactName']
        email = request.form['contactEmail']
        message = request.form['contactMessage']
        conn = sqlite3.connect('petadoption.sqlite')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO contactUs (name,email,message)
            VALUES (?, ?, ?)
        ''', (name,email,message))
        conn.commit()
        conn.close()
        success_message="Your message has been sent! We will Contact you soon."

        # You can redirect the user to a thank you page or simply render another template
        return render_template('contact_us.html',success_message=success_message)

@app.route('/logout')
def logout():
    # Implement your logout logic here
    # For demonstration, removing the user from the set of logged-in users
    session.pop('user', None)  # Clear user from session
    return redirect(url_for('index'))

@app.route('/signup-process', methods=['POST'])
def signup_process():
    if request.method == 'POST':
        # Get form data
        first_name = request.form['fname']
        last_name = request.form['lname']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        phone_number = request.form['number']
        address = request.form['address']
        session['user'] = username

        # Use a context manager to handle database connections
        with sqlite3.connect('petadoption.sqlite') as conn:
            c = conn.cursor()
            
            # Use parameterized queries to avoid SQL injection
            c.execute('''
                INSERT INTO userDetails (fname, lname, username, email, password, cellno, address)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (first_name, last_name, username, email, password, phone_number, address))

        # No need to commit or close the connection explicitly, the context manager handles that

        return render_template('list.html')

@app.route('/login', methods=['POST'])
def signin_process():
    if request.method == 'POST':
        # Get the entered username and password
        entered_username = request.form['username']
        entered_password = request.form['password']
        # Query the database to check if the user exists and the password is correct
        conn = sqlite3.connect('petadoption.sqlite')
        session['user'] = entered_username
        c = conn.cursor()
        c.execute('SELECT * FROM userDetails WHERE username=? AND password=?', (entered_username, entered_password))
        user = c.fetchone()  

        if user:
            if user[8] == 1:
                return redirect(url_for('admin'))

                # Fetch additional user details
            c.execute('SELECT * FROM userDetails WHERE username=?', (entered_username,))
            users = c.fetchone()
            name = f"{users[1]}, {users[2]}"

            session['user'] = entered_username  # Store the username in the session

            return render_template('list.html', name=name, uname=entered_username)
        else:
            error_message = "Invalid username or password. Please try again."
            return render_template('index.html', error_message=error_message)

    return render_template('index.html', error_message=error_message)
@app.route('/save', methods=['POST'])
def save():
    conn = sqlite3.connect('petadoption.sqlite')
    cursor = conn.cursor()

    if request.method == 'POST':
        # Update user information in the database
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        password = request.form['password']
        cursor.execute(
            "UPDATE userDetails SET fname=?, lname=?,  email=?, cellno=?, address=?, password=? WHERE username=?",
            (firstname, lastname, email, phone, address, password,username)
        )
        conn.commit()
        conn.close()
    return render_template('profile.html', success_message="Your information has been updated successfully.",fname=firstname,lname=lastname,username=username,cellno=phone,address=address,password=password,email=email,uname=username)


@app.route('/upload', methods=['POST'])
def upload():
    typeOfPet = request.form['typeOfPet']
    breed = request.form['breed']
    location = request.form['location']
    gender = request.form['gender']
    contact = request.form['contact']
    description = request.form['description']
    image = request.files['image']

    # Save the image to the file system
    if image and allowed_file(image.filename):
        filename = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
        image.save(filename)

        # Store the pet information in the database
        conn = sqlite3.connect('petadoption.sqlite')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO lostPets (species,breed,gender, description, image,location,contact) VALUES (?, ?, ?,?,?,?,?)', (typeOfPet, breed,gender,description, image.filename,location,contact))
        conn.commit()
        conn.close()

    return render_template('report-lost-pet.html',success_message="You have reported a found pet successfully.")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png', 'gif'}



def get_missing_pets_from_db():
    conn = sqlite3.connect('petadoption.sqlite')  # Replace 'your_database.db' with your actual database name
    cursor = conn.cursor()
    cursor.execute("SELECT  description, species, breed, gender, location, image, contact FROM lostPets")
    missing_pets_data = [
        {
            "description": description,
            "species": species,
            "breed": breed,
            "gender": gender,
            "location": location,
            "image": UPLOAD_FOLDER + "/" + image,
            "contact": contact
        } for  description, species, breed, gender, location, image, contact in cursor.fetchall()
    ]
    conn.close()
    return missing_pets_data

@app.route('/delete-user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    conn = sqlite3.connect('petadoption.sqlite')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM userDetails WHERE id=?", (user_id,))
    user = cursor.fetchone()

    if user:
        # Delete the user from the SQLite database
        cursor.execute("DELETE FROM userDetails WHERE id=?", (user_id,))
        conn.commit()
        conn.close()

        return render_template('admin.html')
    else:
        conn.close()
        return jsonify({'success': False, 'message': 'User not found'})

@app.route('/delete-contact-us/<int:rid>', methods=['DELETE'])
def delete_contact_us(rid):
    conn = sqlite3.connect('petadoption.sqlite')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contactUs WHERE id=?", (rid,))
    user = cursor.fetchone()

    if user:
        cursor.execute("DELETE FROM contactUs WHERE id=?", (rid,))
        conn.commit()
        conn.close()

        return render_template('admin.html')
    else:
        conn.close()
        return jsonify({'success': False, 'message': 'User not found'})
    
@app.route('/delete-pet/<int:pet_id>', methods=['DELETE'])
def delete_pet(pet_id):
    conn = sqlite3.connect('petadoption.sqlite')
    cursor = conn.cursor()

    # Check if the pet exists
    cursor.execute("SELECT * FROM pets WHERE id=?", (pet_id,))
    pet = cursor.fetchone()

    if pet:
        # Delete the pet
        cursor.execute("DELETE FROM pets WHERE id=?", (pet_id,))
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Pet deleted successfully'})
    else:
        conn.close()
        return jsonify({'success': False, 'message': 'Pet not found'})


@app.route('/delete-lost-pet/<int:lost_pet_id>', methods=['DELETE'])
def delete_lost_pet(lost_pet_id):
    conn = sqlite3.connect('petadoption.sqlite')
    cursor = conn.cursor()

    # Check if the lost pet exists
    cursor.execute("SELECT * FROM lostPets WHERE id=?", (lost_pet_id,))
    lost_pet = cursor.fetchone()

    if lost_pet:
        # Delete the lost pet
        cursor.execute("DELETE FROM lostPets WHERE id=?", (lost_pet_id,))
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Lost pet deleted successfully'})
    else:
        conn.close()
        return jsonify({'success': False, 'message': 'Lost pet not found'})

@app.route('/delete-adoption-request/<int:a_id>', methods=['DELETE'])
def delete_adoption_request(a_id):
    conn = sqlite3.connect('petadoption.sqlite')
    cursor = conn.cursor()
    print(a_id)
    # Check if the lost pet exists
    cursor.execute("SELECT * FROM adoptionRequests WHERE id=?", (a_id,))
    lost_pet = cursor.fetchone()

    if lost_pet:
        # Delete the lost pet
        cursor.execute("DELETE FROM adoptionRequests WHERE id=?", (a_id,))
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Adoption request deleted successfully'})
    else:
        conn.close()
        return jsonify({'success': False, 'message': 'adoption request not found'})


@app.route('/available-pets')
def get_available_pets():
    conn = sqlite3.connect('petadoption.sqlite')
    cursor = conn.cursor()
    # Fetch available pets from the database
    cursor.execute("SELECT * FROM pets")
    available_pets = cursor.fetchall()

    # Convert the data to a list of dictionaries for JSON response
    pets_data = [{'id': pet[0], 'name': pet[1], 'color': pet[2], 'breed': pet[3],'image':"/static/images/availablepets/"+pet[7] } for pet in available_pets]

    return jsonify(pets_data)


@app.route('/refreshToAdmin')
def refresh():
    return redirect(url_for('admin'))

@app.route('/view-pet-details/<int:pet_id>')
def view_pet_details(pet_id):
    conn = sqlite3.connect('petadoption.sqlite')
    cursor = conn.cursor()
    # Fetch the details of the selected pet from the database
    cursor.execute("SELECT * FROM pets WHERE id=?", (pet_id,))
    pet_details = cursor.fetchone()

    if pet_details:
        # Convert the pet details to a dictionary for rendering the template
        pet_data = {'id': pet_details[0], 'name': pet_details[1], 'species': pet_details[2], 'breed': pet_details[3],'image':"/static/images/availablepets/"+pet_details[7],'sex': pet_details[5], 'age': pet_details[6], 'description': pet_details[2]}
        return render_template('pet-details.html', pet=pet_data)
    else:
        return render_template('pet-not-found.html')
    
@app.route('/submit-adoption-request', methods=['POST'])
def submit_adoption_request():
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        message = request.form['message']
        conn = sqlite3.connect('petadoption.sqlite')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO adoptionRequests (name,email,message)
            VALUES (?, ?, ?)
        ''', (fullname,email,message))
        conn.commit()
        conn.close()
        success_message="Your request has been sent! We will Contact you soon."

        # You can redirect the user to a thank you page or simply render another template
        return render_template('list.html')


@app.route('/change-password', methods=['POST'])
def change_password():
    if request.method == 'POST':
        # Process the form submission
        username = request.form.get('username')
        new_password = request.form.get('password')
        conn = sqlite3.connect('petadoption.sqlite')
        cursor = conn.cursor()

        # Check if the username exists
        cursor.execute('SELECT * FROM userDetails WHERE username = ?', (username,))
        existing_user = cursor.fetchone()
        if existing_user:
            # Username exists, proceed with the password update
            cursor.execute('''
                UPDATE userDetails
                SET password = ?
                WHERE username = ?
            ''', (new_password, username))
            conn.commit()
            conn.close()

            # For simplicity, let's assume the password has been changed successfully
            return render_template('index.html',success_message="Password Changed Successfully.Try loggin in again")
        else:
            # Username does not exist, handle accordingly
            error_message = "Username not found. Please check your username and try again."
            return render_template('forgot-password.html', error_message=error_message)


if __name__ == '__main__':
    app.run(debug=True)
