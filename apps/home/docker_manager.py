from unittest import result
import docker, _thread
from os.path import expanduser, exists
from datetime import datetime
class DockerManager:
    def __init__(self) -> None:
        self.client = docker.from_env()
        self.root_path = "{}/project_data/log/".format(expanduser("~"))

    def start_container(self, data):
        self.kill_container(data['name'])
        c = self.run_container(data)
        return c
    def run_container(self, data):
        try:
            c = self.client.containers.run(
                data['image'],
                entrypoint=data['entrypoint'],
                command=data['command'],
                name=data['name'],
                network_mode=data['network'],
                privileged=data['privileged'],
                volumes=data['volumes'],
                environment=data['environment'],
                detach=data['detach'],
                remove=data['remove']
            )
            return c
        except Exception as e:
            print("Docker error: {}".format(e))
            return 1
        
        # try:
        #     _thread.start_new_thread(self.keey_log, (c.logs(stream=True), data['name'], ))
        # except:
        #     print("Error: start log failed")
    
    def keey_log(self, log_generator, name):
        path = self.root_path + name
        index = 0
        for e in log_generator:
            mode = 'a' if exists(path) else 'w'
            with open(path, mode) as f:
                if index == 0:
                    f.write(datetime.now().strftime("%m/%d/%Y, %H:%M:%S")+'\n')
                    index = 1
                f.write(e.decode())
            
  

    def kill_container(self, c_name):
        try:
            self.client.containers.get(c_name).kill()
        except:
            pass
        try:
            self.client.containers.get(c_name).remove()
        except:
            pass
if __name__ == '__main__':
    dm = DockerManager()

    # client = docker.from_env()
    # try:
    #     # client.containers.run("ros:realsense", 
    #     # entrypoint=["/ros_entrypoint.sh"],
    #     # command="ros2 launch realsense2_camera rs_launch.py",
    #     # name="try",
    #     # remove=True,
    #     # privileged=True,
    #     # network_mode="bridge",
    #     # network_disabled=False)
        
    #     c = client.containers.run("ros:realsense_test", 
    #     entrypoint=["/ros_entrypoint.sh"],
    #     command="ros2 run py_pubsub talker",
    #     name="try1",
    #     remove=True,
    #     network_mode="bridge",
    #     network_disabled=False,
    #     privileged=True,
    #     volumes={
    #         '/home/zl/log/': {'bind':'/log', 'mode': 'rw'}
    #     })
        
    # except BaseException as e:
    #     print(e)
    #     client.containers.get("try1").kill()