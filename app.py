from flask import Flask, render_template, request, redirect, url_for
import subprocess
import time
import os

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        odoo_port = request.form['odoo_port']
        odoo_version = request.form.get('odoo_version', 'latest')  # Default to 'latest' if not provided
        postgres_version = request.form.get('postgres_version', 'latest')  # Default to 'latest' if not provided

        # Pass the values to the shell script
        subprocess.run(['./start-odoo.sh', odoo_port, postgres_version, odoo_version])

        # Wait for the signal file to be created
        signal_file = f'/tmp/odoo_ready_{odoo_port}'
        while not os.path.exists(signal_file):
            time.sleep(1)  # Check every second

        # Redirect to the Odoo page
        return redirect(f'http://localhost:{odoo_port}')

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
