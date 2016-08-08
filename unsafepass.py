from flask import Flask, request, render_template, session, url_for, redirect
import RPi.GPIO as GPIO
import time
from collections import deque
import picamera

app = Flask(__name__)

motor_pin = 24
sensor_light_pin = 21
sensor_pin = 19
flash_pin = 4

@app.route('/login', methods=['POST', 'GET'])
def login():
    error = False
    if request.method == 'POST':
        if request.form['password'] == 'milanesa':
            session['logged_in'] = True
            return redirect('/')
        else:
            app.logger.info('Bad password: {}'.format(request.form['password']))
            error = True

    return render_template('login.html', error=error)

@app.route('/showlog')
def showlog():
    with open('log.txt', 'r') as f:
        data = deque(f, 100)
    return render_template('showlog.html', log=data)

@app.route('/logout')
def logout():
    session.pop('logged_in')
    return redirect('/login')


@app.route('/', methods=['POST', 'GET'])
def main():
    if not 'logged_in' in session:
        return redirect(url_for('login'))

    error = None
    url = None
    if request.method == 'POST':
        try:
            url = operate()
            print(url)
        except Exception as ex:
            error = ex.args[0]

    return render_template('main.html', error=error, img_url=url)


def operate():
    def turnoff():
        GPIO.output(motor_pin, 0)
        GPIO.output(sensor_light_pin, 0)
        GPIO.output(flash_pin, 0)

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(sensor_light_pin, GPIO.OUT)
    GPIO.setup(motor_pin, GPIO.OUT)
    GPIO.setup(flash_pin, GPIO.OUT)
    GPIO.setup(sensor_pin, GPIO.IN)

    GPIO.output(sensor_light_pin, 1)
    GPIO.output(motor_pin, 1)

    with picamera.PiCamera() as camera:
        camera.resolution = (640, 480)
        camera.rotation = -90
        try:
            # maybe the light sensor is still blocked
            n = 20
            while GPIO.input(sensor_pin) == 1 and n > 0:
                time.sleep(0.1)
                n = n - 1

            if n == 0:
                raise Exception('Something went wrong. Check the sensor light and motor.')

            n = 100
            while GPIO.input(sensor_pin) == 0 and n > 0:
                time.sleep(0.1)
                n = n - 1

            if n == 0:
                raise Exception('Something went wrong. Check the motor.')

            GPIO.output(motor_pin, 0)
            GPIO.output(flash_pin, 1)
            time.sleep(0.1)
            filename = "shots/shot_{}.jpg".format(int(time.time()))
            camera.capture('static/' + filename)

            turnoff()
            return url_for("static", filename=filename)
        except:
            turnoff()
            raise

if __name__ == '__main__':
    app.secret_key = 'yadayadayada'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(host='0.0.0.0', debug=True)
