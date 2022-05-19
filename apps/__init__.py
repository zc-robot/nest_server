# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from traceback import print_tb
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from importlib import import_module
import os 
import ruamel.yaml

class UserManager:
    def __init__(self) -> None:
        self.fold_path = None
        self.util_path = None
        self.yaml = ruamel.yaml.YAML()
        self.yaml.preserve_quotes = True

    def create_folder(self, user_id):
        path = self.fold_path + '/' + str(user_id)
        if not os.path.exists(path):
            os.mkdir(path)
            os.mkdir(path + '/imu')
    
    def save_imu_file(self, file, file_name, user_id):
        path = self.fold_path + '/' + str(user_id) + '/imu/'
        if not os.path.exists(path):
            os.mkdir(path)
        file.save(path + file_name)
    
    def generate_imu_yaml(self, user_id, imu_id, imu_rate, ros_topic, sequence_time):
        template_path = self.util_path + '/imu_cali_template.yaml'
        with open(template_path) as f:
            file = f.read()
        file = self.yaml.load(file)
        file['imu_topic'] =  ros_topic
        file['imu_rate'] = int(imu_rate)
        file['sequence_time'] = int(sequence_time)
        yaml_file_name = str(imu_id) + '.yaml'
        saved_yaml_path = self.fold_path + '/' + str(user_id) + '/' + 'imu/' + yaml_file_name
        print(saved_yaml_path)
        with open(saved_yaml_path, 'w') as f:
            self.yaml.dump(file, f)
        
        return yaml_file_name
        
    def extract_result_from_imu_yaml(self, user_id, imu_id):
        path = self.fold_path + '/' + str(user_id) + '/imu/' + str(imu_id) + '_imu.yaml'
        with open(path) as f:
            file = f.read()
        file = self.yaml.load(file)
        return file




db = SQLAlchemy()
login_manager = LoginManager()
user_manager = UserManager()
def create_user_manager(app):
    user_manager.fold_path = app.config['USER_FOLDER']
    user_manager.util_path = app.config['UTIL_FOLDER']
def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)


def register_blueprints(app):
    for module_name in ('authentication', 'home'):
        module = import_module('apps.{}.routes'.format(module_name))
        app.register_blueprint(module.blueprint)

def create_user_folder(app):
    isExist = os.path.exists(app.config['USER_FOLDER'])
    if not isExist:
        os.makedirs(app.config['USER_FOLDER'])

def configure_database(app):

    @app.before_first_request
    def initialize_database():
        db.create_all()

    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()


def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)
    register_extensions(app)
    register_blueprints(app)
    configure_database(app)
    create_user_folder(app)
    create_user_manager(app)
    return app
