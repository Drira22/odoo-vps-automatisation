from flask import Flask, render_template, request, redirect, url_for
import subprocess
import time
import os
from flask_mail import Mail, Message

app = Flask(__name__)

# Initialize mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'khalildrira61@gmail.com'
app.config['MAIL_PASSWORD'] = 'buix gohl lnyw uusg'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        odoo_version = request.form.get('odoo_version', 'latest')  # Default to 'latest' if not provided
        postgres_version = request.form.get('postgres_version', 'latest')  # Default to 'latest' if not provided
        user_email = request.form['email']

        # Pass the values to the shell script
        process = subprocess.Popen(['./start-odoo.sh', odoo_version, postgres_version], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            return f"Error starting Odoo: {stderr.decode()}"

        # Extract the Odoo port from the script output
        for line in stdout.decode().splitlines():
            if line.startswith("Using Odoo port:"):
                odoo_port = line.split(":")[1].strip()
                break
        else:
            return "Failed to retrieve Odoo port."

        # Wait for the signal file to be created
        signal_file = f'/tmp/odoo_ready_{odoo_port}'
        while not os.path.exists(signal_file):
            time.sleep(1)  # Check every second

        # Send URL via email
        msg = Message("Your Odoo Instance is Ready",
                      sender="khalildrira61@gmail.com",
                      recipients=[user_email])
        msg.body = f"Your Odoo instance is ready at http://localhost:{odoo_port}"
        mail.send(msg)

        return f"An email has been sent to you with the Odoo URL: http://localhost:{odoo_port}"

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
