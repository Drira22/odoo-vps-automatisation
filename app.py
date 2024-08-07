from flask import Flask, render_template, request
import subprocess
import os
import time
from flask_mail import Mail, Message
from celery import Celery

# Create the Mail instance
mail = Mail()

def create_app():
    app = Flask(__name__)

    # Initialize mail configuration
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USERNAME'] = 'khalildrira61@gmail.com'
    app.config['MAIL_PASSWORD'] = 'buix gohl lnyw uusg'
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True
    mail.init_app(app)

    # Celery configuration
    app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
    app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

    return app

app = create_app()

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

celery = make_celery(app)

@celery.task
def create_docker_containers(odoo_version, postgres_version, user_email):
    # Run the shell script to create containers
    process = subprocess.Popen(['./start-odoo.sh', odoo_version, postgres_version], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        return f"Error starting Odoo: {stderr.decode()}"

    # Extract the Odoo port from the script output
    odoo_port = None
    for line in stdout.decode().splitlines():
        if line.startswith("Using Odoo port:"):
            odoo_port = line.split(":")[1].strip()
            break

    if not odoo_port:
        return "Failed to retrieve Odoo port."

    # Wait for the signal file to be created
    signal_file = f'/tmp/odoo_ready_{odoo_port}'
    while not os.path.exists(signal_file):
        time.sleep(1)  # Check every second

    # Send URL via email
    msg = Message("Your Odoo Instance is Ready",
                  sender="khalildrira61@gmail.com",
                  recipients=[user_email])
    msg.body = f"Your Odoo instance is ready at http://vps-8c27c89c.vps.ovh.net:{odoo_port}"
    mail.send(msg)

    return f"Odoo instance setup complete on port {odoo_port}."

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        odoo_version = request.form.get('odoo_version', 'latest')  # Default to 'latest' if not provided
        postgres_version = request.form.get('postgres_version', 'latest')  # Default to 'latest' if not provided
        user_email = request.form['email']

        # Start the background task
        create_docker_containers.delay(odoo_version, postgres_version, user_email)

        return "The setup process has started. You'll receive an email once it's complete."

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
