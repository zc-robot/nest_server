# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from pydoc import doc
from re import template
import re
from time import sleep
from traceback import print_tb
from unittest import result
from urllib.parse import urldefrag
from apps.home import blueprint
from flask import render_template, request, redirect, url_for
from flask_login import login_required
from jinja2 import TemplateNotFound
from apps.authentication.models import IMU
from apps.home.docker_manager import DockerManager
from apps import db, user_manager
from werkzeug.utils import secure_filename
import _thread
from flask_login import (
    current_user,
    login_user,
    logout_user
)
@blueprint.route('/start_calibrate/', methods=['GET', 'POST'])
@login_required
def start_calibrate():
    # imu = IMU.query.get_or_404(imu_id)
    print("********************")
    imu_id = request.form.get("imu_id")
    imu = IMU.query.get_or_404(imu_id)
    current_user_id = current_user.id
    allan_variance(imu, current_user_id)
    # _thread.start_new_thread(allan_variance, (imu, current_user_id, ))
    
    # if imu.data:
    #     #start calibration
    #     print("file location: {}".format(imu.data))
    # else:
    #     print("imu data not exit")
    # imus = IMU.query.filter(IMU.user_id == current_user.id).all()
    return "done"

def allan_variance(imu, curent_user_id):
    ## Setup docker
    path = user_manager.fold_path + '/' + str(curent_user_id) + '/imu/'
    docker_volumn = {
        path: {'bind':'/imu', 'mode':'rw'}
    }
    docker_data = {
        "image": "ros:allan_variance",
        "entrypoint": "/ros_entrypoint.sh",
        "command": "roscore",
        "name": "allan_variance_{}".format(curent_user_id),
        "network": "bridge",
        "privileged": True,
        "volumes": docker_volumn,
        "environment": [],
        "remove": True,
        "detach": True
    }
    dm = DockerManager()
    container = dm.start_container(docker_data)
    sleep(3)
    print(imu.data)
    result = container.exec_run(cmd='bash -c "source /ros_entrypoint.sh && rosrun allan_variance_ros cookbag.py --input {} --output cooked.bag"'.format('/imu/' + imu.data), stream=False)
    print("Step 1 Done")
    print(result[0])
    result = container.exec_run(cmd='bash -c "source /ros_entrypoint.sh && rosrun allan_variance_ros allan_variance / /imu/{}.yaml"'.format(imu.id), stream=False)
    print("Step 2 Done")
    print(result[0])
    result = container.exec_run(cmd='bash -c "source /ros_entrypoint.sh && rosrun allan_variance_ros analysis.py --data allan_variance.csv"', stream=False)
    print("Step 3 Done")
    print(result[0])
    result = container.exec_run(cmd='cp imu.yaml /imu/{}_imu.yaml'.format(imu.id), stream=False)
    result = container.exec_run(cmd='cp acceleration.png /imu/{}_a.png'.format(imu.id), stream=False)
    result = container.exec_run(cmd='cp gyro.png /imu/{}_g.png'.format(imu.id), stream=False)
    print("Step 4 Done")
    data = user_manager.extract_result_from_imu_yaml(user_id=curent_user_id, imu_id=imu.id)
    a_noise = data['accelerometer_noise_density']
    a_random_walk = data['accelerometer_random_walk']
    g_noise = data['gyroscope_noise_density']
    g_random_walk = data['gyroscope_random_walk']
    imu.a_noise_density = a_noise
    imu.a_random_walk = a_random_walk
    imu.g_noise_density = g_noise
    imu.g_random_walk = g_random_walk
    db.session.add(imu)
    db.session.commit()
    


@blueprint.post('/<int:imu_id>/upload_file/')
@login_required
def upload_file(imu_id):
    f= request.files['file']
    print("-----------------")
    filename = secure_filename(f.filename)
    user_manager.save_imu_file(file=f, file_name=filename, user_id=current_user.id)
    imu = IMU.query.get_or_404(imu_id)
    imu.data = filename
    db.session.add(imu)
    db.session.commit()
    return redirect(url_for('home_blueprint.route_template', template='imu-calibration.html'))


@blueprint.route('/index')
@login_required
def index():
    return render_template('home/imu-calibration.html', segment='imu-calibration.html')

@blueprint.post('/<int:imu_id>/delete_imu/')
@login_required
def delete_imu(imu_id):
    imu = IMU.query.get_or_404(imu_id)
    db.session.delete(imu)
    db.session.commit()
    return redirect(url_for('home_blueprint.route_template', template='imu-calibration.html'))

  

@blueprint.route('/<template>', methods=['GET', 'POST'])
@login_required
def route_template(template):

    try:

        if not template.endswith('.html'):
            template += '.html'

        # Detect the current page
        segment = get_segment(request)
        if template == 'imu-calibration.html':
            if request.method == 'POST':
                name = request.form['name']
                imu_rate = request.form['feq']
                duration = request.form['duration']
                ros_topic = request.form['ros_topic']
                new_imu = IMU(name=name, feq=imu_rate, duration=duration, ros_topic=ros_topic, user_id=current_user.id)
                
                db.session.add(new_imu)
                db.session.commit()
                user_manager.generate_imu_yaml(imu_id=new_imu.id, imu_rate=imu_rate, ros_topic=ros_topic, sequence_time=duration, user_id=current_user.id)
            imus = IMU.query.filter(IMU.user_id == current_user.id).all()
            return render_template("home/" + template, segment=segment, imus=imus)

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template, segment=segment)

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except:
        return render_template('home/page-500.html'), 500


# Helper - Extract current page name from request
def get_segment(request):

    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment

    except:
        return None
