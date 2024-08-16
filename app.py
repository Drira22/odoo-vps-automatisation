from flask import Flask, render_template, request
import subprocess
import os
import time
from flask_mail import Mail, Message
from celery import Celery
import jinja2
import ovh

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


def create_nginx_config(subdomain, output_text):
    try:
        # Define the Nginx config path
        nginx_config_path = f"/etc/nginx/sites-available/{subdomain}"

        # write the config with elevated permissions
        echo_process = subprocess.Popen(['sudo', 'tee', nginx_config_path], stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = echo_process.communicate(input=output_text.encode())

        if echo_process.returncode != 0:
            print(f"Failed to write Nginx config: {stderr.decode()}")
        else:
            print(f"Nginx config file created: {nginx_config_path}")

        # Symlink to sites-enabled with `sudo`
        nginx_enabled_path = f"/etc/nginx/sites-enabled/{subdomain}"
        if not os.path.exists(nginx_enabled_path):
            subprocess.run(['sudo', 'ln', '-s', nginx_config_path, nginx_enabled_path], check=True)

        # Reload Nginx with `sudo`
        subprocess.run(['sudo', 'nginx', '-s', 'reload'], check=True)

    except Exception as e:
        print(f"Error writing Nginx config: {e}")


@celery.task
def create_docker_containers(odoo_version, postgres_version, user_email, user_name):
    # Run the shell script to create containers
    process = subprocess.Popen(['./start-odoo.sh', odoo_version, postgres_version], stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
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

    # Create the subdomain using the OVH API
    client = ovh.Client(
        endpoint='ovh-eu',
        application_key='a8b1192f4fc8e8bc',
        application_secret='de915d69df597c10a0ac9c78136b93c7',
        consumer_key='a32112375888cff5d006fd91a67869bc'
    )

    subdomain = f"{user_name}.exploit-consult.com"
    try:
        client.post('/domain/zone/exploit-consult.com/record',
                    fieldType='A',
                    subDomain=user_name,
                    target='51.75.253.214')  # Replace with your VPS IP
        client.post('/domain/zone/exploit-consult.com/refresh')
    except ovh.exceptions.APIError as e:
        return f"Failed to create subdomain: {str(e)}"

    # Create Nginx configuration dynamically
    template_loader = jinja2.FileSystemLoader(searchpath="./")
    template_env = jinja2.Environment(loader=template_loader)
    template_file = "nginx_template"  
    template = template_env.get_template(template_file)

    # Generate the configuration file
    output_text = template.render(subdomain=subdomain, odoo_port=odoo_port)

    # Call the function to create the Nginx config and reload it
    create_nginx_config(subdomain, output_text)

    # Send URL via email
    try:
        msg = Message("Your Odoo Instance is Ready",
                      sender="khalildrira61@gmail.com",
                      recipients=[user_email])
        msg.body = f"Your Odoo instance is ready at http://{subdomain}"
        mail.send(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")

    return f"Odoo instance setup complete on port {odoo_port} with subdomain {subdomain}."


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        odoo_version = request.form.get('odoo_version', 'latest')  # Default to 'latest' if not provided
        postgres_version = request.form.get('postgres_version', 'latest')  # Default to 'latest' if not provided
        user_email = request.form['email']
        user_name = request.form['name']

        # Start the background task
        create_docker_containers.delay(odoo_version, postgres_version, user_email, user_name)

        return "The setup process has started. You'll receive an email once it's complete."

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
